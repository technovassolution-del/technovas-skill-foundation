from flask import (
    Blueprint,
    render_template,
    request,
    jsonify
)

from config import get_sql_server_connection

import traceback

from services.faceservice import (
    base64_to_image,
    get_face_encoding,
    bytes_to_encoding,
    compare_faces
)


attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/employeeattendance"
)


# --------------------------------------------------
# ATTENDANCE PAGE
# --------------------------------------------------

@attendance_bp.route(
    "/",
    methods=["GET"]
)
def attendance_page():

    return render_template(
        "employee_attendance.html"
    )


# --------------------------------------------------
# RECOGNIZE FACE
# --------------------------------------------------

@attendance_bp.route(
    "/recognize",
    methods=["POST"]
)
def recognize():

    connection = None
    cursor = None

    try:

        data = request.get_json(
            silent=True
        ) or request.form

        captured_photo = data.get(
            "capturedPhoto"
        )

        if not captured_photo:

            return jsonify({
                "success": False,
                "message": "Please capture a face"
            }), 400

        # ------------------------------------------
        # GENERATE UNKNOWN FACE ENCODING
        # ------------------------------------------

        image = base64_to_image(
            captured_photo
        )

        unknown_encoding = get_face_encoding(
            image
        )

        # ------------------------------------------
        # LOAD EMPLOYEES
        # ------------------------------------------

        connection = get_sql_server_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                EmployeeCode,
                FullName,
                FaceEncoding
            FROM Employees
            WHERE IsActive = 1
              AND FaceEncoding IS NOT NULL
            """
        )

        employees = cursor.fetchall()

        recognized_employee = None

        recognized_confidence = 0.0

        # ------------------------------------------
        # FACE COMPARISON
        # ------------------------------------------

        for employee in employees:

            employee_id = employee[0]

            employee_code = employee[1]

            full_name = employee[2]

            encoding_bytes = employee[3]

            try:

                known_encoding = bytes_to_encoding(
                    encoding_bytes
                )

                is_match, confidence = compare_faces(
                    known_encoding,
                    unknown_encoding,
                    tolerance=0.50
                )

                if (
                    is_match
                    and
                    confidence > recognized_confidence
                ):

                    recognized_employee = {
                        "employee_id": employee_id,
                        "employee_code": employee_code,
                        "full_name": full_name
                    }

                    recognized_confidence = confidence

            except Exception as encoding_error:

                print(
                    f"Invalid encoding for employee "
                    f"{employee_id}: {encoding_error}"
                )

                continue

        # ------------------------------------------
        # NO MATCH
        # ------------------------------------------

        if not recognized_employee:

            return jsonify({
                "success": False,
                "message": "Face not recognized"
            }), 404

        employee_id = recognized_employee[
            "employee_id"
        ]

        # ------------------------------------------
        # CHECK TODAY'S ATTENDANCE
        # ------------------------------------------

        cursor.execute(
            """
            SELECT
                AttendanceID,
                CheckInTime,
                CheckOutTime,
                Status
            FROM Attendance
            WHERE EmployeeID = ?
              AND AttendanceDate = CAST(GETDATE() AS DATE)
            """,
            (
                employee_id,
            )
        )

        existing_attendance = cursor.fetchone()

        # ------------------------------------------
        # FIRST SCAN → CHECK IN
        # ------------------------------------------

        if not existing_attendance:

            cursor.execute(
                """
                INSERT INTO Attendance
                (
                    EmployeeID,
                    AttendanceDate,
                    CheckInTime,
                    Status,
                    Confidence
                )
                VALUES
                (
                    ?,
                    CAST(GETDATE() AS DATE),
                    GETDATE(),
                    ?,
                    ?
                )
                """,
                (
                    employee_id,
                    "Present",
                    recognized_confidence
                )
            )

            connection.commit()

            return jsonify({
                "success": True,
                "action": "checkin",
                "message": "Check-in completed",
                "employee": recognized_employee,
                "confidence": round(
                    recognized_confidence,
                    2
                )
            }), 200

        # ------------------------------------------
        # EXISTING ATTENDANCE
        # ------------------------------------------

        attendance_id = existing_attendance[0]

        check_in_time = existing_attendance[1]

        check_out_time = existing_attendance[2]

        # ------------------------------------------
        # SECOND SCAN → CHECK OUT
        # ------------------------------------------

        if check_out_time is None:

            cursor.execute(
                """
                UPDATE Attendance
                SET
                    CheckOutTime = GETDATE()
                WHERE AttendanceID = ?
                """,
                (
                    attendance_id,
                )
            )

            connection.commit()

            # --------------------------------------
            # FETCH UPDATED ATTENDANCE
            # --------------------------------------

            cursor.execute(
                """
                SELECT
                    CheckInTime,
                    CheckOutTime
                FROM Attendance
                WHERE AttendanceID = ?
                """,
                (
                    attendance_id,
                )
            )

            updated_attendance = cursor.fetchone()

            updated_check_in = updated_attendance[0]

            updated_check_out = updated_attendance[1]

            # --------------------------------------
            # CALCULATE WORKING HOURS
            # --------------------------------------

            working_seconds = int(
                (
                    updated_check_out
                    -
                    updated_check_in
                ).total_seconds()
            )

            hours = working_seconds // 3600

            minutes = (
                working_seconds % 3600
            ) // 60

            seconds = working_seconds % 60

            working_hours = (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

            return jsonify({
                "success": True,
                "action": "checkout",
                "message": "Check-out completed",
                "employee": recognized_employee,
                "confidence": round(
                    recognized_confidence,
                    2
                ),
                "check_in_time": updated_check_in.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "check_out_time": updated_check_out.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "working_hours": working_hours
            }), 200

        # ------------------------------------------
        # THIRD SCAN → COMPLETED
        # ------------------------------------------

        return jsonify({
            "success": True,
            "action": "completed",
            "message": "Attendance already completed",
            "employee": recognized_employee,
            "confidence": round(
                recognized_confidence,
                2
            )
        }), 200

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:

        if connection:

            connection.rollback()

        print(
            "Attendance recognition error:",
            e
        )

        print(
            "\n========== FACE RECOGNITION ERROR =========="
        )

        traceback.print_exc()

        print(
            "============================================\n"
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()