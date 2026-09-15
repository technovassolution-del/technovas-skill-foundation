from datetime import date, datetime
from flask import Blueprint, request, jsonify, render_template
from config import get_sql_server_connection

student_qrattendance = Blueprint("student_qrattendance", __name__)

@student_qrattendance.route("/student/attendance")
def attendance_page():
    return render_template("student_attendance.html")

@student_qrattendance.route("/student/attendance/scan", methods=["POST"])
def scan():
    try:
        data=request.get_json(silent=True) or {}
        token=(data.get("qrToken") or "").strip()
        print(f"Received QR token: {token}")
        remarks=(data.get("remarks") or "").strip() or None
        if not token:
            return jsonify(success=False,message="QR token is required."),400

        with get_sql_server_connection() as cn:
            cur=cn.cursor()
            cur.execute("""SELECT StudentId,AdmissionNo,FullName,CourseName
                           FROM dbo.Students
                           WHERE CONVERT(varchar(36),QrToken)=?
                             AND AdmissionStatus <> 'Rejected'""", token)
            s=cur.fetchone()
            print(s)

            if not s:
                return jsonify(success=False,message="Invalid or inactive student QR code."),404

            today=date.today()
            cur.execute("""SELECT AttendanceId FROM dbo.StudentAttendance
                           WHERE StudentId=? AND AttendanceDate=?""",s[0],today)
            if cur.fetchone():
                return jsonify(success=False,message=f"Attendance already marked today for {s[2]}."),409

            now=datetime.now().time()
            cur.execute("""INSERT INTO dbo.StudentAttendance
                           (StudentId,AttendanceDate,AttendanceTime,Status,ScanToken,Remarks)
                           VALUES (?,?,?,?,?,?)""",s[0],today,now,"Present",token,remarks)
            cn.commit()

        return jsonify(success=True,message=f"Attendance marked successfully for {s[2]}.",
                       student={"studentId":s[0],"admissionNo":s[1],"fullName":s[2],"courseName":s[3]},
                       attendanceTime=now.strftime("%H:%M:%S"))
    except Exception as e:
        return jsonify(success=False,message=f"Unable to mark attendance: {e}"),500

@student_qrattendance.route("/student/attendance/list")
def attendance_list():
    d=request.args.get("date") or date.today().isoformat()
    with get_sql_server_connection() as cn:
        cur=cn.cursor()
        cur.execute("""SELECT a.AttendanceId,s.AdmissionNo,s.FullName,s.CourseName,
                              a.AttendanceDate,a.AttendanceTime,a.Status,a.Remarks
                       FROM dbo.StudentAttendance a
                       JOIN dbo.Students s ON s.StudentId=a.StudentId
                       WHERE a.AttendanceDate=? ORDER BY a.AttendanceTime DESC""",d)
        rows=cur.fetchall()
    return jsonify(success=True,date=d,attendance=[
        {"attendanceId":r[0],"admissionNo":r[1],"fullName":r[2],"courseName":r[3],
         "attendanceDate":str(r[4]),"attendanceTime":str(r[5]),"status":r[6],"remarks":r[7]}
        for r in rows])
