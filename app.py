import xml
from flask import Flask, Response, render_template, request, jsonify,redirect,url_for,session
import mysql.connector
import face_recognition
import cv2
import numpy as np
import base64
from zeep.helpers import serialize_object
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
       session.clear()
       return render_template('default.html')

@app.route('/onlineattendance')
def onlineattendance():
       
       return render_template('index.html')
@app.route('/emp_onlineattendance')
def emp_onlineattendance():
       
       return render_template('emp_onlineattendance.html')

@app.route('/studenthome')
def studenthome():
       return render_template('student_home.html')

@app.route('/studentlogin')
def studentlogin():
       return render_template('student_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
       return render_template('admin_dashboard.html')

@app.route('/logout')
def logout():
    session.clear()   # removes all session data
    return render_template('default.html')


@app.route("/studentexam_view")
def studentexam_view():
    return render_template("studentexam_view.html")

@app.route("/showstudent_result")
def showstudent_result():
    return render_template("showstudent_result.html")

@app.route("/studentprofile_view")
def studentprofile():
    return render_template("studentprofile_view.html")

@app.route("/cirtificatepage")
def cirtificatepage():
    return render_template("cirtificatepage.html")



# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    error = None
    
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        result = client.service.GetUser(phone,password)
        print(result)
              
        if result.Status == "Success":
            session['user'] = {
                    'name': result.Name,
                    'UserId': result.UserId,
                    'UserType': result.Userrole
                }
            return redirect(url_for('admin_dashboard'))

        else:

            error = "❌ Wrong Password"

    return render_template(
        'login.html',
        error=error
    )

@app.route('/users')
def user():
    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    users = client.service.GetAllUsers()
        
    all_users = []

    for user in users:

      all_users.append({
        "Id": user.Id,
        "Name": user.Name,
        "Email": user.Email,
        "Userrole": user.Userrole,
        "UserId": user.UserId,
        "ProgramCode": user.ProgramCode,
        "ProgramName": user.ProgramName,
        "Batch_Name": user.Batch_Name
    })
    session['all_users'] = all_users
    return render_template('students.html', users=all_users)



@app.route('/employee')
def employee():
    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    users = client.service.GetEmployee()
        
    all_users = []

    for user in users:

      all_users.append({
        "Id": user.Id,
        "Name": user.Name,
        "Email": user.Email,
        "Userrole": user.Userrole,
        "UserId": user.UserId
        
    })
    session['all_users'] = all_users
    return render_template('employee.html', users=all_users)




# Register page
@app.route('/register')
def register():
    user = session.get('selected_user')
    return render_template(
        'register.html',
        user=user
    )
# Save face
@app.route('/register_face', methods=['POST'])
def register_face():
    data = request.json
    userid=data['userid']
    name = data['name']
    userrole=data['role']
    image_data = data['image']
    programCode = data['programCode']
    programName = data['programName']
    batchName = data['batchName']
    enrollmentId=data['enrollmentId']
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
    check_sql = "SELECT * FROM users WHERE userid=%s"
    cursor.execute(check_sql,(userid,))
    existing_user = cursor.fetchone()
    if existing_user:
     return jsonify({"status": "userid alraedy Exist"})
    sql = "INSERT INTO users(name,encoding,userid,role,enrollmentid,programcode,programname,batchname) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql,(name,encoding_str,userid,userrole,enrollmentId,programCode,programName,batchName))
    db.commit()
    return jsonify({"status": "success"})

     
@app.route('/select_user/<int:id>')
def select_user(id):
    users =session.get('all_users')
    selected_user = None
    for user in users:
        if user.get('Id') == id:
            selected_user = {
                "Id": user.get('Id'),
                "Name": user.get('Name'),
                "Email": user.get('Email'),
                "Userrole": user.get('Userrole'),
                "UserId": user.get('UserId'),
                "ProgramCode": user.get('ProgramCode'),
                "ProgramName": user.get('ProgramName'),
                "Batch_Name": user.get('Batch_Name')
            }

            break

    # Store in session
    session['selected_user'] = selected_user
    return redirect('/register')


@app.route('/select_user_employee/<int:id>')
def select_user_employee(id):
    users =session.get('all_users')
    selected_user = None
    for user in users:
        if user.get('Id') == id:
            selected_user = {
                "Id": user.get('Id'),
                "Name": user.get('Name'),
                "Email": user.get('Email'),
                "Userrole": user.get('Userrole'),
                "UserId": user.get('UserId')
               
            }

            break

    # Store in session
    session['selected_user'] = selected_user
    return redirect('/register')


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
    cursor.execute("SELECT name,encoding,userid FROM users")
    students = cursor.fetchall()
    for encoding in encodings:
        best_match_name = None
        best_match_enrollmentId=None
        best_distance = 999

        for student in students:
            student_name = student[0]
            userid=student[2]
            db_encoding = np.array(
                list(map(float, student[1].split(",")))
            )

            distance = np.linalg.norm(db_encoding - encoding)
            if distance < best_distance:
                best_distance = distance
                best_match_name = student_name
                best_match_userid=userid

        if best_distance < 0.5:
            cursor.execute("""
                SELECT * FROM attendance
                WHERE userid=%s AND DATE(date_time)=CURDATE()
            """, (best_match_userid,))
            existing = cursor.fetchone()
            print(existing)
            if not existing:
                
                cursor.execute(
                    "INSERT INTO attendance(student_name,userid) VALUES(%s,%s)",
                    (best_match_name,best_match_userid,)
                )
            else:
                cursor.execute(
                    "UPDATE attendance SET out_time=NOW() WHERE userid=%s",
                    (best_match_userid,)
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
        SELECT student_name, userid, date_time, out_time
        FROM attendance
        ORDER BY date_time DESC
    """)
    records = cursor.fetchall()
    return render_template('attendance_view.html', records=records)


# Autocomplete API
# Autocomplete API
@app.route('/autocomplete')
def autocomplete():
    search = request.args.get('q', '')
    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    users = client.service.GetAllUsers()
    # Extract suggestion values from API response
    suggestions = [
    item["Name"]
    for item in users
    if search.lower() in item["Name"].lower()
]
    return jsonify(suggestions)


@app.route('/autocompleteemployee')
def autocompleteemployee():
    search = request.args.get('q', '')
    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    users = client.service.GetEmployee()
    # Extract suggestion values from API response
    suggestions = [
    item["Name"]
    for item in users
    if search.lower() in item["Name"].lower()
]   
    return jsonify(suggestions)


@app.route('/get_user')
def get_user():

    selected_name = request.args.get('name','')

    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    users = serialize_object(
        client.service.GetAllUsers()
    )

    # Find selected record
    user = next(
        (
            item for item in users
            if item["Name"] == selected_name
        ),
        None
    )

    return jsonify(user)


@app.route('/get_employee')
def get_employee():

    selected_name = request.args.get('name', '')

    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)

    users = serialize_object(
        client.service.GetEmployee()
    )

    # Find selected record
    user = next(
        (
            item for item in users
            if item["Name"] == selected_name
        ),
        None
    )

    return jsonify(user)




if __name__ == '__main__':
    app.run(debug=True)