import xml

from flask import Flask, Response, render_template, request, jsonify,redirect,url_for,session
import mysql.connector
import face_recognition
import cv2
import numpy as np
import base64

from zeep import Client
from config import get_db_connection
# Import Blueprints
from controller.exam_controller import exam_bp
from controller.question_controller import question_bp   
from controller.user_controller import user_bp


app = Flask(__name__)
app.secret_key = "secret123"
# Register Blueprints
app.register_blueprint(exam_bp)
app.register_blueprint(question_bp)  
# Register Blueprint
app.register_blueprint(user_bp) 
db=get_db_connection()
cursor = db.cursor()

# Home page

@app.route('/')
def home():
       return render_template('default.html')

@app.route('/onlineattendance')
def onlineattendance():
       return render_template('index.html')

@app.route('/studentportal')
def studentportal():
       return render_template('student_portal.html')

@app.route('/studentlogin')
def studentlogin():
       return render_template('student_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
       return render_template('admin_dashboard.html')




# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    error = None

    
    if request.method == 'POST':

        phone = request.form['phone']
        password = request.form['password']
        result = client.service.GetUser(phone, password)
        if result.Status == "Success":
            session['user'] = {
                    'name': result.Name,
                    'phone': phone
                }
            return redirect(url_for('admin_dashboard'))

        else:

            error = "❌ Wrong Password"

    return render_template(
        'login.html',
        error=error
    )












# Register page
@app.route('/register')
def register():
    name = request.args.get('name')
    enrollmentId = request.args.get('enrollmLentId')
    return render_template('register.html',name=name,enrollmentId=enrollmentId)


# Save face
@app.route('/register_face', methods=['POST'])
def register_face():
    data = request.json
    name = data['name']
    enrollmentId=data['enrollmentId']
    image_data = data['image']
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    if len(faces) == 0:
        return jsonify({"status": "no_face"})
    encoding = face_recognition.face_encodings(rgb, faces)[0]
    encoding_str = ",".join(map(str, encoding))
    # Check duplicate enrollment ID
    check_sql = "SELECT * FROM users WHERE enrollmentId=%s"
    cursor.execute(check_sql,(enrollmentId,))
    existing_user = cursor.fetchone()
    if existing_user:
     return jsonify({"status": "EnrollmentId alraedy Exist"})
    sql = "INSERT INTO users(name, encoding,enrollmentId) VALUES(%s,%s,%s)"
    cursor.execute(sql, (name,encoding_str,enrollmentId,))
    db.commit()
    return jsonify({"status": "success"})

     


# Attendance page
@app.route('/attendance')
def attendance():
    return render_template('attendance.html')


# Mark attendance
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    image_data = data['image']
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    if len(faces) == 0:
        return jsonify({"status": "no_face"})

    encodings = face_recognition.face_encodings(rgb, faces)
    cursor.execute("SELECT name,encoding,enrollmentId FROM users")
    students = cursor.fetchall()
    for encoding in encodings:
        best_match_name = None
        best_match_enrollmentId=None
        best_distance = 999

        for student in students:
            student_name = student[0]
            student_enrollmentId=student[2]
            db_encoding = np.array(
                list(map(float, student[1].split(",")))
            )

            distance = np.linalg.norm(db_encoding - encoding)
            if distance < best_distance:
                best_distance = distance
                best_match_name = student_name
                best_match_enrollmentId=student_enrollmentId

        if best_distance < 0.5:
            cursor.execute("""
                SELECT * FROM attendance
                WHERE enrollmentId=%s AND DATE(date_time)=CURDATE()
            """, (best_match_enrollmentId,))
            existing = cursor.fetchone()
            print(existing)
            if not existing:
                
                cursor.execute(
                    "INSERT INTO attendance(student_name,enrollmentId) VALUES(%s,%s)",
                    (best_match_name,best_match_enrollmentId,)
                )
            else:
                cursor.execute(
                    "UPDATE attendance SET out_time=NOW() WHERE enrollmentId=%s",
                    (best_match_enrollmentId,)
                )

            db.commit()

            return jsonify({
                "status": "success",
                "name": best_match_name
                
            })

    return jsonify({"status": "unknown"})


@app.route('/attendance_view')
def attendance_view():
    cursor.execute("""
        SELECT student_name, enrollmentId, date_time, out_time
        FROM attendance
        ORDER BY date_time DESC
    """)
    records = cursor.fetchall()
    return render_template('attendance_view.html', records=records)
if __name__ == '__main__':
    app.run(debug=True)