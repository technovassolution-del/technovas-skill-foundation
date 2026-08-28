from flask import Flask, render_template, request, jsonify
import mssql_python
import face_recognition
import numpy as np
import cv2
import base64
import json
from datetime import datetime

app = Flask(__name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    connection_string = (
        "Server=DESKTOP-B4RCPPB\\SQLEXPRESS;"
        "Database=technovas_masterdb;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return mssql_python.connect(connection_string)


# ============================================================
# ATTENDANCE PAGE
# ============================================================

@app.route("/attendance")
def attendance():
    return render_template("employee_attendance.html")


# ============================================================
# TEST API
# ============================================================

@app.route("/api/test")
def api_test():

    return jsonify({
        "success": True,
        "message": "Flask attendance API is working"
    })


# ============================================================
# LOAD EMPLOYEE FACE EMBEDDINGS
# ============================================================

def load_employee_faces():

    db = None
    cursor = None

    known_encodings = []
    employee_ids = []
    employee_names = []

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            SELECT
                employee_id,
                full_name,
                face_embedding
            FROM employees
            WHERE face_embedding IS NOT NULL
        """)

        rows = cursor.fetchall()

        for row in rows:

            employee_id = row[0]
            full_name = row[1]
            face_embedding = row[2]

            try:

                if face_embedding is None:
                    continue

                # SQL Server may return bytes
                if isinstance(face_embedding, bytes):
                    face_embedding = face_embedding.decode("utf-8")

                # If already a Python object
                if isinstance(face_embedding, str):
                    embedding = json.loads(face_embedding)
                else:
                    embedding = face_embedding

                encoding = np.array(
                    embedding,
                    dtype=np.float64
                )

                # face_recognition uses 128-dimensional encoding
                if encoding.shape != (128,):

                    print(
                        f"Invalid embedding for employee "
                        f"{employee_id}: {encoding.shape}"
                    )

                    continue

                known_encodings.append(encoding)
                employee_ids.append(employee_id)
                employee_names.append(full_name)

            except Exception as e:

                print(
                    f"Invalid embedding for employee "
                    f"{employee_id}: {e}"
                )

        return (
            known_encodings,
            employee_ids,
            employee_names
        )

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# ============================================================
# RECOGNIZE FACE
# ============================================================

@app.route("/recognize", methods=["POST"])
def recognize():

    try:

        # ====================================================
        # READ JSON
        # ====================================================

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "Invalid JSON request"
            }), 400


        image_data = data.get("image")


        if not image_data:

            return jsonify({
                "success": False,
                "message": "No image received"
            }), 400


        # ====================================================
        # REMOVE BASE64 PREFIX
        # ====================================================

        if "," in image_data:

            image_data = image_data.split(",", 1)[1]


        # ====================================================
        # BASE64 DECODE
        # ====================================================

        try:

            image_bytes = base64.b64decode(
                image_data
            )

        except Exception:

            return jsonify({
                "success": False,
                "message": "Invalid Base64 image"
            }), 400


        # ====================================================
        # IMAGE ARRAY
        # ====================================================

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )


        image_bgr = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )


        if image_bgr is None:

            return jsonify({
                "success": False,
                "message": "Invalid image"
            }), 400


        # ====================================================
        # BGR -> RGB
        # ====================================================

        image_rgb = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2RGB
        )


        # ====================================================
        # FIND FACE
        # ====================================================

        face_locations = face_recognition.face_locations(
            image_rgb,
            model="hog"
        )


        if len(face_locations) == 0:

            return jsonify({
                "success": False,
                "message": "No face detected"
            })


        if len(face_locations) > 1:

            return jsonify({
                "success": False,
                "message": "Multiple faces detected. Please keep only one face in the camera."
            })


        # ====================================================
        # GENERATE LIVE FACE ENCODING
        # ====================================================

        live_encodings = face_recognition.face_encodings(
            image_rgb,
            face_locations
        )


        if not live_encodings:

            return jsonify({
                "success": False,
                "message": "Unable to encode face"
            })


        live_encoding = live_encodings[0]


        # ====================================================
        # LOAD DATABASE EMPLOYEES
        # ====================================================

        (
            known_encodings,
            employee_ids,
            employee_names
        ) = load_employee_faces()


        if not known_encodings:

            return jsonify({
                "success": False,
                "message": "No registered employee faces found"
            })


        # ====================================================
        # FACE DISTANCE
        # ====================================================

        distances = face_recognition.face_distance(
            known_encodings,
            live_encoding
        )


        best_match_index = int(
            np.argmin(distances)
        )


        best_distance = float(
            distances[best_match_index]
        )


        # ====================================================
        # MATCH THRESHOLD
        # ====================================================

        tolerance = 0.50


        if best_distance > tolerance:

            return jsonify({

                "success": False,

                "message": "Face not recognized",

                "distance": round(
                    best_distance,
                    4
                )

            })


        # ====================================================
        # EMPLOYEE FOUND
        # ====================================================

        employee_id = employee_ids[
            best_match_index
        ]

        employee_name = employee_names[
            best_match_index
        ]


        # ====================================================
        # MARK ATTENDANCE
        # ====================================================

        attendance_result = mark_attendance(
            employee_id,
            employee_name
        )


        # ====================================================
        # SUCCESS RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "employee_id": employee_id,

            "employee_name": employee_name,

            "distance": round(
                best_distance,
                4
            ),

            "attendance": attendance_result

        })


    except Exception as e:

        print(
            "RECOGNITION ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ============================================================
# MARK ATTENDANCE
# ============================================================

def mark_attendance(
    employee_id,
    employee_name
):

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor()

        now = datetime.now()
        today = now.date()


        # ====================================================
        # FIND TODAY'S ATTENDANCE
        # ====================================================

        cursor.execute(
            """
            SELECT
                id,
                in_time,
                out_time
            FROM attendance
            WHERE employee_id = ?
            AND attendance_date = ?
            """,
            (
                employee_id,
                today
            )
        )


        record = cursor.fetchone()


        # ====================================================
        # FIRST SCAN = CHECK IN
        # ====================================================

        if record is None:

            cursor.execute(
                """
                INSERT INTO attendance
                (
                    employee_id,
                    employee_name,
                    attendance_date,
                    in_time,
                    status
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
                """,
                (
                    employee_id,
                    employee_name,
                    today,
                    now,
                    "Present"
                )
            )

            db.commit()


            return {

                "type": "IN",

                "message": "Check-in successful",

                "time": now.strftime(
                    "%I:%M:%S %p"
                )

            }


        # ====================================================
        # EXISTING RECORD
        # ====================================================

        attendance_id = record[0]

        in_time = record[1]

        out_time = record[2]


        # ====================================================
        # SECOND SCAN = CHECK OUT
        # ====================================================

        if out_time is None:

            cursor.execute(
                """
                UPDATE attendance
                SET out_time = ?
                WHERE id = ?
                """,
                (
                    now,
                    attendance_id
                )
            )

            db.commit()


            return {

                "type": "OUT",

                "message": "Check-out successful",

                "time": now.strftime(
                    "%I:%M:%S %p"
                )

            }


        # ====================================================
        # ALREADY COMPLETED
        # ====================================================

        return {

            "type": "COMPLETED",

            "message": "Attendance already completed",

            "time": now.strftime(
                "%I:%M:%S %p"
            )

        }


    except Exception as e:

        if db:
            db.rollback()

        print(
            "ATTENDANCE ERROR:",
            str(e)
        )

        raise


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "success": False,

        "message": "API route not found",

        "error": str(error)

    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success": False,

        "message": "Internal server error",

        "error": str(error)

    }), 500


# ============================================================
# RUN
# ============================================================

