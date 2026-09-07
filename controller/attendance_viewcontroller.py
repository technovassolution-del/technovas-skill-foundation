from flask import Blueprint, render_template, request, jsonify
from config import get_sql_server_connection

student_attendance_bp = Blueprint(
    "student_attendance",
    __name__,
    url_prefix="/student-attendance"
)


@student_attendance_bp.route("/view", methods=["GET"])
def view_student_attendance():

    try:
        employee_id = request.args.get("employee_id", "").strip()
        from_date = request.args.get("from_date", "").strip()
        to_date = request.args.get("to_date", "").strip()

        conn = get_sql_server_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                sa.AttendanceID,
                sa.EmployeeID,
                s.FullName,
                sa.AttendanceDate,
                sa.CheckInTime,
                sa.CheckOutTime,
                sa.Status
            FROM Attendance sa
            INNER JOIN Employees s
                ON sa.EmployeeID = s.EmployeeID
            WHERE 1 = 1
        """

        params = []

        if employee_id:
            query += " AND sa.EmployeeID = ?"
            params.append(employee_id)

        if from_date:
            query += " AND sa.AttendanceDate >= ?"
            params.append(from_date)

        if to_date:
            query += " AND sa.AttendanceDate <= ?"
            params.append(to_date)

        query += """
            ORDER BY
                sa.AttendanceDate DESC,
                sa.CheckInTime DESC
        """

        cursor.execute(query, params)

        columns = [column[0] for column in cursor.description]

        attendance = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return render_template(
            "attendanceview.html",
            attendance=attendance,
            employee_id=employee_id,
            from_date=from_date,
            to_date=to_date
        )

    except Exception as e:

        print("Employee Attendance Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500