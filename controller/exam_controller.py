
from flask import Blueprint, render_template, request, redirect, url_for, session ,flash
from datetime import datetime
from datetime import datetime, timedelta
from models.exam_model import assign_exams_to_student
from models.exam_model import (
    create_exam,
    get_all_exams,
    get_questions_by_exam,
    get_attempt,
    create_attempt,
    get_db_connection,
    
)

import os
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from zeep import Client
import random
import json
from flask import jsonify
from models.exam_model import get_shuffled_questions
exam_bp = Blueprint('exam', __name__)

# ---------------- CREATE EXAM ----------------
@exam_bp.route('/create_exam')
def create_exam_page():
    return render_template('create_exam.html')


# ------- EXAM LIST (CLEAN VERSION) ----------------------

@exam_bp.route("/exams")
def exam_list_page():

    exam_type = request.args.get("type", "all")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        if exam_type == "online":
            cursor.execute("""
                SELECT *
                FROM exams
                WHERE exam_type = 'online'
                ORDER BY id DESC
            """)

        elif exam_type == "offline":
            cursor.execute("""
                SELECT *
                FROM exams
                WHERE exam_type = 'offline'
                ORDER BY id DESC
            """)

        else:
            cursor.execute("""
                SELECT *
                FROM exams
                ORDER BY id DESC
            """)

        exams = cursor.fetchall()

    except Exception as e:
        print("❌ Exam List Error:", e)
        exams = []

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "exam_list.html",
        exams=exams,
        exam_type=exam_type
    )

# ----------changed--------------


@exam_bp.route('/save_exam', methods=['POST'])
def save_exam():
    created_by = session.get('user').get('UserId')
    print("✅ Created By:", created_by)
    exam_type = request.form.get('exam_type')

    # ===============================
    # Common Data (SAFE)
    # ===============================

    title = request.form.get('title')
    if not title:
        return "Title is required", 400

    description = request.form.get('description')
    start_at = request.form.get('start_date')
    end_at = request.form.get('end_date')
    duration = request.form.get('duration')

    try:
        total_marks = float(request.form.get('total_marks', 0))
        pass_marks = float(request.form.get('pass_marks', 0))
    except ValueError:
        return "Invalid marks", 400


    # ===============================
    # COMMON CHECKBOX VALUES
    # ===============================

    publish = 1 if request.form.get('publish') else 0


    # ===============================
    # ONLINE EXAM
    # ===============================

    if exam_type == "online":

        shuffle_questions = 1 if request.form.get('shuffle_questions') else 0
        shuffle_options = 1 if request.form.get('shuffle_options') else 0
        allow_review = 1 if request.form.get('allow_review') else 0

        data = (
            title,
            description,
            start_at,
            end_at,
            duration,
            total_marks,
            pass_marks,
            shuffle_questions,
            shuffle_options,
            allow_review,
            publish,
            "online",
            created_by
        )

        exam_id = create_exam(data)

        if exam_id:
            print("✅ Online Exam Created:", exam_id)
        else:
            print("❌ Online Exam Create Failed")


    # ===============================
    # OFFLINE EXAM
    # ===============================

    elif exam_type == "offline":

        data = (
            title,
            description,
            start_at,
            end_at,
            duration,
            total_marks,
            pass_marks,
            0,          # shuffle_questions
            0,          # shuffle_options
            0,          # allow_review
            publish,    # 🔥 FIXED HERE (IMPORTANT)
            "offline",
            created_by
        )

        exam_id = create_exam(data)

        if exam_id:
            print("✅ Offline Exam Created:", exam_id)
        else:
            print("❌ Offline Exam Create Failed")


    else:
        print("❌ Invalid Exam Type")
        return "Invalid exam type", 400


    # ===============================
    # REDIRECT AFTER SAVE
    # ===============================

    return redirect(url_for('exam.exam_list_page'))







# ---------------- STUDENT LOGIN ----------------

@exam_bp.route('/student_login', methods=['GET', 'POST'])
def student_login():

    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)

    if request.method == 'POST':

        student_id = request.form['UserId']
        student_pwd = request.form['password']

        result = client.service.GetUser(student_id, student_pwd)

        print("Login Result:", result)

        if result.Status == "Success":

            # Local Database থেকে Student বের করুন
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT *
                FROM users
                WHERE userid = %s
            """, (result.UserId,))

            student = cursor.fetchone()

            cursor.close()
            conn.close()

            print("DATABASE STUDENT =", student)

            # Student পাওয়া না গেলে
            if not student:
                return "Student not found in local database."

            # Session Save
            session['user'] = {
                'id': student['id'],
                'name': student['name'],
                'StudentId': student['userid']
            }

            print("SESSION =", session['user'])

            return redirect(url_for('exam.student_portal'))

    return render_template('student_login.html')



# ================= STUDENT PORTAL =================

@exam_bp.route('/student_portal')
def student_portal():

    # Student Login Check
    if session.get('user'):
      student_id = session['user']['StudentId']
      print("User ID:", student_id)
    else:
        return redirect(url_for('exam.student_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


    # ===============================
    # Student Information
    # ===============================

    cursor.execute("""
        SELECT *
        FROM users
        WHERE userid = %s
    """, (student_id,))

    student = cursor.fetchone()
    student_id = student['userid']
    
    # ===============================
# Total Online Exams
# ===============================

    cursor.execute("""
    SELECT COUNT(DISTINCT e.id) AS total_online
    FROM student_exams se
    INNER JOIN exams e
    ON se.exam_id = e.id
    WHERE se.student_id = %s
    AND e.exam_type = 'online'
   """, (student_id,))

    total_online = cursor.fetchone()['total_online']
    print("Total Online Exams:"+ str(total_online))

# ===============================
# Total Offline Exams
# ===============================

    cursor.execute("""
    SELECT COUNT(DISTINCT e.id) AS total_offline
    FROM student_exams se
    INNER JOIN exams e
    ON se.exam_id = e.id
    WHERE se.student_id = %s
    AND e.exam_type = 'offline'
""", (student_id,))

    total_offline = cursor.fetchone()['total_offline']
    print("Total Offline Exams:"+ str(total_offline))


    # ===============================
    # Total Exams
    # ===============================

    cursor.execute("""
        SELECT COUNT(DISTINCT exam_id) AS total_exam
        FROM student_exams
        WHERE student_id = %s
    """, (student_id,))

    total_exam = cursor.fetchone()['total_exam']


    # ===============================
    # Attempted Exams
    # ===============================

    cursor.execute("""
        SELECT COUNT(*) AS attempted
        FROM attempts
        WHERE student_id = %s
        AND status = 'SUBMITTED'
    """, (student_id,))

    attempted = cursor.fetchone()['attempted']


    # ===============================
    # Passed Exams
    # ===============================

    cursor.execute("""
        SELECT COUNT(*) AS passed
        FROM results r

        INNER JOIN attempts a
        ON r.attempt_id = a.id

        WHERE a.student_id = %s
        AND r.result_status = 'PASS'
    """, (student_id,))

    passed = cursor.fetchone()['passed']

    # ===============================
# Online Passed
# ===============================

    cursor.execute("""
    SELECT COUNT(*) AS online_passed

    FROM results r

    INNER JOIN attempts a
    ON r.attempt_id = a.id

    INNER JOIN exams e
    ON a.exam_id = e.id

    WHERE a.student_id = %s
    AND e.exam_type = 'online'
    AND r.result_status = 'PASS'
""", (student_id,))

    online_passed = cursor.fetchone()['online_passed']


# ===============================
# Offline Passed
# ===============================

    cursor.execute("""
    SELECT COUNT(*) AS offline_passed

    FROM offline_exam_results

    WHERE student_id = %s
    AND status = 'PASS'
    AND published = 1
""", (student_id,))

    offline_passed = cursor.fetchone()['offline_passed']


# ===============================
# Certificates
# ===============================

    certificates = online_passed + offline_passed


    


    # ===============================
    # Online Exam List
    # ===============================

    cursor.execute("""
        SELECT DISTINCT
            e.id,
            e.title,
            e.description,
            e.total_marks,
            e.pass_marks,
            e.duration_minutes,

            CASE
                WHEN a.id IS NULL THEN 0
                ELSE 1
            END AS attempted

        FROM student_exams se

        INNER JOIN exams e
        ON se.exam_id = e.id

        LEFT JOIN attempts a
        ON a.exam_id = e.id
        AND a.student_id = %s

        WHERE se.student_id = %s
        AND e.exam_type = 'online'

        ORDER BY e.id DESC

    """, (student_id, student_id))

    courses = cursor.fetchall()



 # ===============================
# Offline Exam Assigned List
# ===============================

    cursor.execute("""
    SELECT DISTINCT
        e.id,
        e.title,
        q.question_text AS pdf_file

    FROM student_exams se

    INNER JOIN exams e
    ON se.exam_id = e.id

    LEFT JOIN exam_questions eq
    ON e.id = eq.exam_id

    LEFT JOIN questions q
    ON eq.question_id = q.id

    WHERE se.student_id = %s
    AND e.exam_type = 'offline'

    ORDER BY e.id DESC
""", (student_id,))


    offline_courses = cursor.fetchall()


# Debug Check
    print("======== OFFLINE COURSES ========")
    print(offline_courses)
    print("=================================")


# Close Database
    cursor.close()
    conn.close()


# ===============================
# Send Data to Template
# ===============================

    return render_template(
    "student_portal.html",

    student=student,

    total_exam=total_exam,

    total_online=total_online,
    total_offline=total_offline,

    attempted=attempted,

    passed=passed,

    online_passed=online_passed,
    offline_passed=offline_passed,

    certificates=certificates,

    courses=courses,

    offline_courses=offline_courses,
)





# ----------------------------student_dashboard-------------

@exam_bp.route('/student_dashboard')
def student_dashboard():

    # ======================================
    # Check Student Login
    # ======================================

    if session.get('user'):
        student_id = session['user']['StudentId']
        print("User ID:", student_id)
    else:
        return redirect(url_for('exam.student_login'))

    # ======================================
    # Database Connection
    # ======================================

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ======================================
    # Student Information
    # ======================================

    cursor.execute("""
        SELECT *
        FROM users
        WHERE userid = %s
    """, (student_id,))

    student = cursor.fetchone()

    # ======================================
    # Online Exam List
    # ======================================

    cursor.execute("""
        SELECT
            e.*,

            CASE
                WHEN NOW() < e.start_at THEN 'UPCOMING'
                WHEN NOW() >= e.start_at
                     AND NOW() <= e.end_at THEN 'LIVE'
                ELSE 'EXPIRED'
            END AS state

        FROM exams e

        INNER JOIN student_exams se
            ON e.id = se.exam_id

        WHERE se.student_id = %s
        AND e.exam_type = 'online'

        ORDER BY e.start_at ASC
    """, (student_id,))

    exams = cursor.fetchall()

    # ======================================
    # Prepare Dashboard Exam List
    # ======================================

    courses = []

    for exam in exams:

        # Skip expired exam
        if exam['state'] == 'EXPIRED':
            continue

        # Check Attempt
        cursor.execute("""
            SELECT id
            FROM attempts
            WHERE exam_id = %s
            AND student_id = %s
            LIMIT 1
        """, (exam['id'], student_id))

        attempt = cursor.fetchone()

        exam['attempted'] = attempt is not None

        courses.append(exam)

    # ======================================
    # Offline Exam Results
    # ======================================

    cursor.execute("""
        SELECT
            id,
            practical_marks,
            theory_marks,
            total_marks,
            grade,
            status,
            answer_sheet_file,
            created_at

        FROM offline_exam_results

        WHERE student_id = %s
        AND published = 1

        ORDER BY created_at DESC
    """, (student_id,))

    offline_results = cursor.fetchall()

    # ======================================
    # Debug
    # ======================================

    print("================================")
    print("Student ID:", student_id)
    print("Student:", student)
    print("ONLINE COURSES:", courses)
    print("OFFLINE RESULTS:", offline_results)
    print("================================")

    # ======================================
    # Close Connection
    # ======================================

    cursor.close()
    conn.close()

    # ======================================
    # Send Data To Template
    # ======================================

    return render_template(
        "student_dashboard.html",
        student=student,
        courses=courses,
        offline_results=offline_results
    )





 # ---------------- EXAM PAGE ----------------

@exam_bp.route('/exam', methods=['GET', 'POST'])
def exam():

    # ================= CHECK SESSION =================
    if 'exam_id' not in session or 'attempt_id' not in session:
        return redirect(url_for('exam.student_dashboard'))

    attempt_id = session['attempt_id']

    questions = get_shuffled_questions(session['attempt_id'])

    if not questions:

       questions = get_questions_by_exam(session['exam_id'])

    # ================= TIMER FIX =================
    # Create timer ONLY first time

    if 'end_time' not in session:

        end = datetime.now() + timedelta(minutes=30)

        session['end_time'] = end.strftime('%Y-%m-%d %H:%M:%S')

    end_time = session['end_time']

    # ================= CURRENT QUESTION INDEX =================
    index = int(request.args.get('q', 0))

    index = max(0, min(index, len(questions)-1))

    # ================= POST =================
    if request.method == 'POST':

        selected = request.form.get('answer')

        qid = request.form.get('question_id')

        action = request.form.get('action')

        conn = get_db_connection()

        cursor = conn.cursor()

        try:

            if qid:

                # REVIEW STATUS
                is_review = 1 if action == "review" else 0

                # ANSWER STATUS
                is_answered = 1 if selected else 0

                cursor.execute("""
                    INSERT INTO student_answers
                    (
                        attempt_id,
                        question_id,
                        selected_option_id,
                        answered,
                        marked_review
                    )
                    VALUES (%s,%s,%s,%s,%s)

                    ON DUPLICATE KEY UPDATE

                    selected_option_id=%s,
                    answered=%s,
                    marked_review=%s
                """, (

                    attempt_id,
                    qid,
                    selected,
                    is_answered,
                    is_review,

                    selected,
                    is_answered,
                    is_review
                ))

                conn.commit()

        finally:

            cursor.close()

            conn.close()

        # ================= NAVIGATION =================

        if action == "next":

            return redirect(
                url_for('exam.exam', q=index+1)
            )

        if action == "prev":

            return redirect(
                url_for('exam.exam', q=index-1)
            )

        if action == "review":

            return redirect(
                url_for('exam.exam', q=index+1)
            )

        # ================= SUBMIT =================
        if action == "submit":

            # CLEAR TIMER SESSION
            session.pop('end_time', None)

            return redirect(
                url_for('exam.result')
            )

        return redirect(
            url_for('exam.exam', q=index)
        )

    # ================= CURRENT QUESTION =================

    current_question = questions[index]

    # ================= LOAD ANSWERS =================

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                question_id,
                selected_option_id,
                marked_review,
                answered
            FROM student_answers
            WHERE attempt_id=%s
        """, (attempt_id,))

        answers = cursor.fetchall()

    finally:

        cursor.close()

        conn.close()

    # ================= PRESELECT SAVED ANSWER =================

    saved = None

    for a in answers:

        if a['question_id'] == current_question['id']:

            if a['selected_option_id']:

                saved = str(a['selected_option_id'])

            break

    # ================= QUESTION IDS =================

    question_ids = [q['id'] for q in questions]

    # ================= RENDER =================

    return render_template(
        'exam.html',

        question=current_question,

        index=index,

        total=len(questions),

        saved=saved,

        end_time=end_time,

        answers=answers,

        question_ids=question_ids,

        questionIds=[int(q['id']) for q in questions],

        answersData=answers
    )






# ---------------- START EXAM ----------------

@exam_bp.route('/start_exam/<int:exam_id>')
def start_exam(exam_id):




    if session.get('user'):
          student_id = session['user']['StudentId']
          print("User ID:", student_id)
    else:
           return redirect(url_for('exam.student_login'))

    print("✅ student_id =", student_id)
    print("✅ exam_id =", exam_id)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT e.* FROM exams e
        JOIN student_exams se ON e.id = se.exam_id
        WHERE e.id = %s AND se.student_id = %s
    """, (exam_id, student_id))

    exam = cursor.fetchone()

    if not exam:
        return "❌ Unauthorized"

    now = datetime.now()

    if now < exam['start_at']:
        return "❌ Not started"

    if now > exam['end_at']:
        return "❌ Expired"

    existing = get_attempt(exam_id, student_id)

    if existing:
        if existing['status'] == 'SUBMITTED':
           return """
        <div style='
            text-align:center;
            margin-top:80px;
            font-family:Segoe UI;
        '>

            <h2 style='color:red;'>
                ✅ Exam Already Submitted Successfully
            </h2>

            <br>

            <p style='font-size:20px;'>
                You Cannot Attend This Exam Again
            </p>

            <br><br>

            <a href="/student_dashboard">
                <button style='
                    padding:12px 25px;
                    background:#2563eb;
                    color:white;
                    border:none;
                    border-radius:10px;
                    font-size:16px;
                    cursor:pointer;
                '>
                    🏠 Back To Dashboard
                </button>
            </a>

        </div>
        """

        if existing['status'] == 'IN_PROGRESS':

            session['attempt_id'] = existing['id']
            session['exam_id'] = exam_id
            session.setdefault('answers', {})

            end_time = existing['started_at'] + timedelta(minutes=exam['duration_minutes'])

            session['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')

            return redirect(url_for('exam.exam'))

# ================= CREATE NEW ATTEMPT =================

    attempt_id = create_attempt(
    exam_id,
    student_id,
    request.remote_addr,
    request.headers.get("User-Agent")
)

# ================= FAILED =================

    if not attempt_id:
       return "❌ Failed to create attempt"

# ================= LOAD QUESTIONS =================

    questions = get_questions_by_exam(exam_id)

# ================= SHUFFLE QUESTIONS =================

    if exam.get("shuffle_questions"):
        random.shuffle(questions)

# ================= SHUFFLE OPTIONS =================

    if exam.get("shuffle_options"):
      for q in questions:
        random.shuffle(q["options"])

# ================= SAVE SHUFFLED DATA =================

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE attempts
    SET shuffled_data = %s
    WHERE id = %s
""", (
    json.dumps(questions),
    attempt_id
))

    conn.commit()
    cursor.close()
    conn.close()

# ================= START TIME =================

    started_at = datetime.now()

# ================= END TIME =================
    end_time = started_at + timedelta(
    minutes=exam["duration_minutes"]
)

# ================= SESSION =================

    session["attempt_id"] = attempt_id
    session["exam_id"] = exam_id
    session["answers"] = {}
    session["end_time"] = end_time.strftime("%Y-%m-%d %H:%M:%S")

    print("✅ Exam Started")
    print("Attempt ID:", attempt_id)

    return redirect(url_for("exam.exam"))


   


# ---------------- AFTER COMPPLETED RESULT ----------------

@exam_bp.route('/result')
def result():
    attempt_id = session.get('attempt_id')
    student = session.get('student')
    student_name = student['name'] if student else "Student"

    # 🔥 IMPORTANT: call submit only once
    if attempt_id:

        try:

            submit_attempt(attempt_id)

            # ✅ UPDATE STATUS
            conn = get_db_connection()

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE attempts
                SET status='SUBMITTED'
                WHERE id=%s
            """, (attempt_id,))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            print("ERROR in submit_attempt:", e)

    # 🔥 CLEAR SESSION (AFTER EVERYTHING)
    session.pop('answers', None)
    session.pop('exam_id', None)
    session.pop('attempt_id', None)

    return render_template(
        'result.html',
        student_name=student_name
    )



# ---------------------- STUDENT RESULT ---------------------

@exam_bp.route('/showstudent_result')
def showstudent_result():

    # =========================
    # Check Login
    # =========================

    if 'user' not in session:
        return redirect(url_for('exam.student_login'))

    # Student IDs
    student_userid = session['user']['StudentId']   # Login ID (8334886382)
    student_db_id = session['user']['id']           # users.id (134)

    print("Student UserID :", student_userid)
    print("Student DB ID  :", student_db_id)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # Student Information
    # =========================

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = %s
    """, (student_db_id,))

    student = cursor.fetchone()

    # =========================
    # Online Published Results
    # =========================

    cursor.execute("""
    SELECT

        e.title AS exam_title,

        r.online_marks,
        r.theory_marks,
        r.practical_marks,
        r.attendance_marks,

        r.total_marks,
        r.obtained_marks,
        r.percentage,
        r.grade,
        r.result_status,

        a.submitted_at

    FROM attempts a

    JOIN results r
        ON a.id = r.attempt_id

    JOIN exams e
        ON a.exam_id = e.id

    WHERE
        a.student_id = %s
        AND r.published = 1

    ORDER BY a.id DESC

""", (student_userid,))

    online_results = cursor.fetchall()

    # =========================
    # Offline Published Results
    # =========================

    cursor.execute("""
        SELECT

            e.title AS exam_title,

            o.theory_marks,
            o.practical_marks,
            o.total_marks,

            o.grade,
            o.status,

            o.answer_sheet_file,

            e.total_marks AS exam_total,

            GROUP_CONCAT(
                DISTINCT q.question_text
                SEPARATOR ' || '
            ) AS question_file,

            o.created_at

        FROM offline_exam_results o

        INNER JOIN exams e
            ON o.exam_id = e.id

        LEFT JOIN exam_questions eq
            ON e.id = eq.exam_id

        LEFT JOIN questions q
            ON eq.question_id = q.id

        WHERE
            o.student_id = %s
            AND o.published = 1

        GROUP BY
            o.id,
            e.title,
            o.theory_marks,
            o.practical_marks,
            o.total_marks,
            o.grade,
            o.status,
            o.answer_sheet_file,
            e.total_marks,
            o.created_at

        ORDER BY o.id DESC

    """, (student_db_id,))

    offline_results = cursor.fetchall()

    # =========================
    # Debug
    # =========================

    print("ONLINE RESULTS :", online_results)
    print("OFFLINE RESULTS:", offline_results)

    cursor.close()
    conn.close()

    return render_template(
        "showstudent_result.html",
        student=student,
        online_results=online_results,
        offline_results=offline_results
    )




# # ---------------- PUBLISH ONLINE RESULT ----------------
@exam_bp.route('/publish_result/<int:attempt_id>')
def publish_result_route(attempt_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE results
        SET published = 1
        WHERE attempt_id = %s
    """, (attempt_id,))

    conn.commit()

    print("Published Attempt ID =", attempt_id)
    print("Rows Updated =", cursor.rowcount)

    cursor.close()
    conn.close()

    return redirect(url_for('exam.result_processing'))





# ============================================================
# RESULT PROCESSING DASHBOARD
# ============================================================

@exam_bp.route('/result_processing')
def result_processing():

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    try:

        query = """

            SELECT

                r.attempt_id,

                a.student_id,

                COALESCE(u.name, 'Unknown Student') AS student_name,

                e.title AS exam_title,

                r.online_marks,

                r.theory_marks,

                r.practical_marks,

                r.total_marks,

                r.obtained_marks,

                r.percentage,

                r.grade,

                r.result_status,

                r.published,

                a.started_at,

                a.submitted_at

            FROM results r

            INNER JOIN attempts a
                ON r.attempt_id = a.id

            INNER JOIN exams e
                ON a.exam_id = e.id

            LEFT JOIN users u
                ON a.student_id = u.userid

            ORDER BY r.attempt_id DESC

        """

        cursor.execute(query)

        results = cursor.fetchall()

    except Exception as e:

        print("RESULT PROCESSING ERROR =>", e)

        results = []

    finally:

        cursor.close()
        conn.close()

    return render_template(
        'result_processing.html',
        results=results
    )





# ============================================================
# RESULT CALCULATION LOGIC
# ============================================================

def calculate_grade(percentage):

    percentage = float(percentage)

    if percentage >= 90:
        return 'A+'

    elif percentage >= 80:
        return 'A'

    elif percentage >= 70:
        return 'B+'

    elif percentage >= 60:
        return 'B'

    elif percentage >= 50:
        return 'C'

    elif percentage >= 40:
        return 'D'

    else:
        return 'F'


def calculate_result_values(
    online_marks,
    theory_marks,
    practical_marks,
    total_marks
):

    online_marks = float(online_marks or 0)
    theory_marks = float(theory_marks or 0)
    practical_marks = float(practical_marks or 0)
    total_marks = float(total_marks or 0)

    # --------------------------------
    # TOTAL MAXIMUM MARKS VALIDATION
    # --------------------------------

    if total_marks <= 0:

        return {
            'obtained_marks': 0,
            'percentage': 0,
            'grade': 'F',
            'result_status': 'PENDING'
        }

    # --------------------------------
    # OBTAINED MARKS
    # --------------------------------

    obtained_marks = (
        online_marks
        + theory_marks
        + practical_marks
    )

    # --------------------------------
    # PERCENTAGE
    # --------------------------------

    percentage = (
        (obtained_marks / total_marks) * 100
    )

    # --------------------------------
    # GRADE
    # --------------------------------

    grade = calculate_grade(percentage)

    # --------------------------------
    # PASS / FAIL
    # --------------------------------

    if percentage >= 40:
        result_status = 'PASS'
    else:
        result_status = 'FAIL'

    return {
        'obtained_marks': round(obtained_marks, 2),
        'percentage': round(percentage, 2),
        'grade': grade,
        'result_status': result_status
    }

    # except Exception as e:

    #     print("ERROR:", e)

    #     return 0, 0, 0, 'FAIL'

    # finally:

    #     cursor.close()

    #     conn.close()


    # ============================================================
# SAVE RESULT PROCESSING
# ============================================================

@exam_bp.route(
    '/update_offline_marks/<int:attempt_id>',
    methods=['POST']
)
def update_offline_marks(attempt_id):

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # GET FORM VALUES
        # ----------------------------------------------------

        total_marks = request.form.get(
            'total_marks',
            '0'
        )

        theory_marks = request.form.get(
            'theory_marks',
            '0'
        )

        practical_marks = request.form.get(
            'practical_marks',
            '0'
        )
        

        # ----------------------------------------------------
        # CONVERT TO FLOAT
        # ----------------------------------------------------

        try:

            total_marks = float(total_marks or 0)
            theory_marks = float(theory_marks or 0)
            practical_marks = float(practical_marks or 0)

        except ValueError:

            flash(
                'Invalid marks entered.',
                'error'
            )

            return redirect(
                url_for('exam.result_processing')
            )

        # ----------------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------------

        if total_marks <= 0:

            flash(
                'Total Marks must be greater than 0.',
                'error'
            )

            return redirect(
                url_for('exam.result_processing')
            )

        if theory_marks < 0:

            flash(
                'Theory Marks cannot be negative.',
                'error'
            )

            return redirect(
                url_for('exam.result_processing')
            )

        if practical_marks < 0:

            flash(
                'Practical Marks cannot be negative.',
                'error'
            )

            return redirect(
                url_for('exam.result_processing')
            )

        # ----------------------------------------------------
        # GET ONLINE MARKS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT online_marks
            FROM results
            WHERE attempt_id = %s
            """,
            (attempt_id,)
        )

        result_row = cursor.fetchone()

        if not result_row:

            flash(
                'Result record not found.',
                'error'
            )

            return redirect(
                url_for('exam.result_processing')
            )

        online_marks = float(
            result_row['online_marks'] or 0
        )

        # ----------------------------------------------------
        # CALCULATE
        # ----------------------------------------------------

        calculation = calculate_result_values(

            online_marks=online_marks,

            theory_marks=theory_marks,

            practical_marks=practical_marks,

            total_marks=total_marks

        )

        obtained_marks = calculation[
            'obtained_marks'
        ]

        percentage = calculation[
            'percentage'
        ]

        grade = calculation[
            'grade'
        ]

        result_status = calculation[
            'result_status'
        ]

        # ----------------------------------------------------
        # IMPORTANT VALIDATION
        # ----------------------------------------------------
        # Obtained marks cannot be greater than Total Marks
        # ----------------------------------------------------

        if obtained_marks > total_marks:

            flash(
                f'Obtained Marks ({obtained_marks}) '
                f'cannot be greater than Total Marks '
                f'({total_marks}).',
                'error'
            )

            return redirect(
                url_for('exam.result_processing')
            )

        # ----------------------------------------------------
        # UPDATE DATABASE
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE results

            SET

                total_marks = %s,

                theory_marks = %s,

                practical_marks = %s,

                obtained_marks = %s,

                percentage = %s,

                grade = %s,

                result_status = %s,

                evaluated_at = NOW()

            WHERE attempt_id = %s
            """,

            (
                total_marks,

                theory_marks,

                practical_marks,

                obtained_marks,

                percentage,

                grade,

                result_status,

                attempt_id
            )
        )

        conn.commit()

        flash(
            'Result saved successfully.',
            'success'
        )

    except Exception as e:

        conn.rollback()

        print(
            "UPDATE RESULT ERROR =>",
            e
        )

        flash(
            'Error while saving result.',
            'error'
        )

    finally:

        cursor.close()
        conn.close()

    return redirect(
        url_for('exam.result_processing')
    )



# ============================================================
# CALCULATE ONLINE EXAM MARKS
# ============================================================

def calculate_online_marks(attempt_id):

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                sa.question_id,
                sa.selected_option_id,
                qo.is_correct

            FROM student_answers sa

            INNER JOIN question_options qo
                ON sa.selected_option_id = qo.id

            WHERE sa.attempt_id = %s
        """, (attempt_id,))

        data = cursor.fetchall()


        # ====================================================
        # COUNT CORRECT ANSWERS
        # ====================================================

        correct_answers = 0

        for row in data:

            if row['is_correct'] == 1:

                correct_answers += 1


        # ====================================================
        # ONLINE MARKS
        # ====================================================

        online_marks = correct_answers


        print(
            "ONLINE MARKS CALCULATED =",
            online_marks
        )


        return online_marks


    except Exception as e:

        print(
            "❌ ONLINE MARK CALCULATION ERROR =>",
            e
        )

        return 0


    finally:

        cursor.close()

        conn.close()


# ============================================================
# SUBMIT ATTEMPT
# ============================================================

def submit_attempt(attempt_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        # ====================================================
        # 1. CALCULATE ONLINE MARKS
        # ====================================================

        online_marks = calculate_online_marks(
            attempt_id
        )


        print(
            "======================================"
        )

        print(
            "ATTEMPT ID =",
            attempt_id
        )

        print(
            "ONLINE MARKS =",
            online_marks
        )

        print(
            "======================================"
        )


        # ====================================================
        # 2. MARK ATTEMPT AS SUBMITTED
        # ====================================================

        cursor.execute("""
            UPDATE attempts

            SET
                status = 'SUBMITTED',
                submitted_at = NOW()

            WHERE id = %s
        """, (attempt_id,))


        # ====================================================
        # 3. CHECK RESULT ALREADY EXISTS
        # ====================================================

        cursor.execute("""
            SELECT id

            FROM results

            WHERE attempt_id = %s
        """, (attempt_id,))

        existing_result = cursor.fetchone()


        # ====================================================
        # 4. CREATE RESULT IF NOT EXISTS
        # ====================================================

        if not existing_result:

            cursor.execute("""
                INSERT INTO results
                (
                    attempt_id,

                    online_marks,

                    total_marks,

                    theory_marks,

                    practical_marks,

                    obtained_marks,

                    attendance_marks,

                    percentage,

                    grade,

                    result_status,

                    published,

                    evaluated_at
                )

                VALUES
                (
                    %s,
                    %s,
                    0.00,
                    0.00,
                    0.00,
                    0.00,
                    0.00,
                    0.00,
                    NULL,
                    'PENDING',
                    0,
                    NOW()
                )
            """, (

                attempt_id,

                online_marks

            ))


            print(
                "✅ NEW RESULT RECORD CREATED"
            )


        # ====================================================
        # 5. IF RESULT ALREADY EXISTS
        # ====================================================

        else:

            cursor.execute("""
                UPDATE results

                SET
                    online_marks = %s

                WHERE attempt_id = %s
            """, (

                online_marks,

                attempt_id

            ))


            print(
                "✅ EXISTING RESULT UPDATED"
            )


        # ====================================================
        # 6. COMMIT
        # ====================================================

        conn.commit()


        print(
            "======================================"
        )

        print(
            "✅ RESULT SAVED SUCCESSFULLY"
        )

        print(
            "ATTEMPT ID:",
            attempt_id
        )

        print(
            "ONLINE MARKS:",
            online_marks
        )

        print(
            "STATUS: PENDING"
        )

        print(
            "======================================"
        )


    except Exception as e:

        conn.rollback()

        print(
            "❌ SUBMIT ATTEMPT ERROR =>",
            e
        )


    

        raise


    finally:

        cursor.close()

        conn.close()





# --------------------update offline marks-------------------------

@exam_bp.route('/update_offline_marks/<int:attempt_id>', methods=['POST'])
def update_offline_marks(attempt_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        theory_marks = float(request.form.get('theory_marks', 0))
        practical_marks = float(request.form.get('practical_marks', 0))
        attendance_marks = float(request.form.get('attendance_marks', 0))

        # Current Online Marks
        cursor.execute("""
            SELECT online_marks
            FROM results
            WHERE attempt_id=%s
        """, (attempt_id,))

        result = cursor.fetchone()

        if not result:
            flash("Result not found", "error")
            return redirect(url_for('exam.result_processing'))

        online_marks = float(result['online_marks'])

        total_marks = (
            online_marks +
            theory_marks +
            practical_marks +
            attendance_marks
        )

        cursor.execute("""
            UPDATE results
            SET
                theory_marks=%s,
                practical_marks=%s,
                attendance_marks=%s,
                total_marks=%s
            WHERE attempt_id=%s
        """, (
            theory_marks,
            practical_marks,
            attendance_marks,
            total_marks,
            attempt_id
        ))

        conn.commit()

        flash("Offline Marks Updated Successfully", "success")

    except Exception as e:

        conn.rollback()
        print("ERROR:", e)

        flash("Update Failed", "error")

    finally:

        cursor.close()
        conn.close()

    return redirect(url_for('exam.result_processing'))








# -------------------- EDIT EXAM ------------------------

@exam_bp.route('/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
def edit_exam(exam_id):

    # DATABASE CONNECTION
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- EXAM DATA ----------------

    cursor.execute(
        "SELECT * FROM exams WHERE id=%s",
        (exam_id,)
    )

    exam = cursor.fetchone()

    # ---------------- ALL STUDENTS ----------------

    cursor.execute(
        "SELECT * FROM users"
    )

    students = cursor.fetchall()

    # ---------------- ASSIGNED STUDENTS ----------------

    cursor.execute("""
        SELECT student_id
        FROM student_exams
        WHERE exam_id=%s
    """, (exam_id,))

    assigned_data = cursor.fetchall()

    assigned_students = [
        str(x['student_id'])
        for x in assigned_data
    ]

    print("Assigned Students:", assigned_students)

    # ---------------- UPDATE EXAM ----------------

    if request.method == 'POST':

        title = request.form['title']
        start_at = request.form['start_at']
        end_at = request.form['end_at']
        duration = request.form['duration']
        total_marks = request.form['total_marks']
        pass_marks = request.form['pass_marks']

        # CHECKBOX SELECTED STUDENTS

        selected_students = request.form.getlist(
            'selected_students'
        )

        # ---------------- UPDATE EXAM TABLE ----------------

        cursor.execute("""
            UPDATE exams
            SET title=%s,
                start_at=%s,
                end_at=%s,
                duration_minutes=%s,
                total_marks=%s,
                pass_marks=%s
            WHERE id=%s
        """, (
            title,
            start_at,
            end_at,
            duration,
            total_marks,
            pass_marks,
            exam_id
        ))

        # ---------------- DELETE OLD STUDENT EXAMS ----------------

        cursor.execute("""
            DELETE FROM student_exams
            WHERE exam_id=%s
        """, (exam_id,))

        # ---------------- INSERT NEW STUDENT EXAMS ----------------

        for student_id in selected_students:

            cursor.execute("""
                INSERT INTO student_exams
                (student_id, exam_id)
                VALUES (%s, %s)
            """, (
                student_id,
                exam_id
            ))

        # ---------------- SAVE DATABASE ----------------

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(
            url_for('exam.exam_list_page')
        )

    # ---------------- RETURN TEMPLATE ----------------

    return render_template(
        'edit_exam.html',
        exam=exam,
        students=students,
        assigned_students=assigned_students
    )


# Now your selected exam will show only for checked students.

@exam_bp.route('/student_exams')
def student_exams():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    student_id = session['student_id']

    cursor.execute("""
        SELECT exams.*
        FROM exams
        JOIN student_exams
        ON exams.id = student_exams.exam_id
        WHERE student_exams.student_id=%s
    """, (student_id,))

    exams = cursor.fetchall()

    return render_template(
        'student_exams.html',
        exams=exams
     )

# --------------------REATTEMPT EXAM---------------------------------------------

@exam_bp.route('/reset_exam_attempt/<int:exam_id>/<student_id>', methods=['POST'])
def reset_exam_attempt(exam_id, student_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # Find Attempt
        cursor.execute("""
            SELECT id
            FROM attempts
            WHERE exam_id=%s
            AND student_id=%s
            LIMIT 1
        """, (exam_id, student_id))

        attempt = cursor.fetchone()

        if not attempt:
            return jsonify({
                "status": "error",
                "message": "Attempt not found."
            })

        attempt_id = attempt["id"]

        # Delete Result
        cursor.execute("""
            DELETE FROM results
            WHERE attempt_id=%s
        """, (attempt_id,))

        # Delete Answers
        cursor.execute("""
            DELETE FROM student_answers
            WHERE attempt_id=%s
        """, (attempt_id,))

        # Delete Attempt
        cursor.execute("""
            DELETE FROM attempts
            WHERE id=%s
        """, (attempt_id,))

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Student can now re-attempt this exam."
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        cursor.close()
        conn.close()







#------------OFFLINE RESULT ------------------------

@exam_bp.route("/all_offline_results")
def all_offline_results():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT

        u.id AS user_id,
        u.userid,
        se.student_id,
        se.exam_id,

        u.name,

        e.title,
        e.total_marks,
        e.pass_marks,

        r.id AS result_id,
        r.theory_marks,
        r.practical_marks,
        r.total_marks AS saved_total,
        r.grade,
        r.status,
        r.answer_sheet_file,
        r.published,

        GROUP_CONCAT(
            DISTINCT q.question_text
            SEPARATOR '|'
        ) AS question_files

    FROM student_exams se

    INNER JOIN users u
        ON u.userid = se.student_id

    INNER JOIN exams e
        ON e.id = se.exam_id

    LEFT JOIN exam_questions eq
        ON eq.exam_id = e.id

    LEFT JOIN questions q
        ON q.id = eq.question_id

    LEFT JOIN offline_exam_results r
        ON r.student_id = u.id
        AND r.exam_id = se.exam_id

    WHERE e.exam_type = 'offline'

    GROUP BY

        u.id,
        u.userid,
        se.student_id,
        se.exam_id,

        u.name,

        e.title,
        e.total_marks,
        e.pass_marks,

        r.id,
        r.theory_marks,
        r.practical_marks,
        r.total_marks,
        r.grade,
        r.status,
        r.answer_sheet_file,
        r.published

    ORDER BY
        se.exam_id DESC,
        u.name ASC
    """

    cursor.execute(query)
    results = cursor.fetchall()

    for row in results:

        if row["question_files"]:

            files = row["question_files"].split("|")

            clean_files = []

            for f in files:
                f = f.replace("\\", "/")
                f = f.replace("static/", "")
                clean_files.append(f)

            row["question_files"] = clean_files

        else:
            row["question_files"] = []

    cursor.close()
    conn.close()

    return render_template(
        "all_offline_results.html",
        results=results
    )




#-----------SAVE OFFLINE EXAM--------------------------


@exam_bp.route("/save_offline_result", methods=["POST"])
def save_offline_result():

    conn = get_db_connection()
    cursor = conn.cursor()


    # =========================
    # Form Data
    # =========================

    student_id = request.form.get("student_id")
    exam_id = request.form.get("exam_id")

    theory_marks = request.form.get("theory_marks")
    practical_marks = request.form.get("practical_marks")
    total_marks = request.form.get("total_marks")

    grade = request.form.get("grade")
    status = request.form.get("status")

    action = request.form.get("action")


    # =========================
    # Publish Status
    # =========================

    if action == "publish":
        published = 1
    else:
        published = 0


    # =========================
    # Check Existing Result
    # =========================

    cursor.execute("""
        SELECT id, answer_sheet_file
        FROM offline_exam_results
        WHERE student_id = %s
        AND exam_id = %s
    """, (student_id, exam_id))

    old_result = cursor.fetchone()


    # =========================
    # File Upload
    # =========================

    filename = None

    answer_file = request.files.get("answer_sheet")

    if answer_file and answer_file.filename != "":

        filename = secure_filename(answer_file.filename)

        folder_path = os.path.join(
            "static",
            "uploads",
            "answer_sheets"
        )

        os.makedirs(folder_path, exist_ok=True)

        save_path = os.path.join(
            folder_path,
            filename
        )

        answer_file.save(save_path)

        filename = (
            "uploads/answer_sheets/" +
            filename
        )


    # =========================
    # If no new file use old file
    # =========================

    if old_result and filename is None:
        filename = old_result[1]


    # =========================
    # UPDATE Existing Result
    # =========================

    if old_result:

        query = """
        UPDATE offline_exam_results
        SET
            theory_marks = %s,
            practical_marks = %s,
            total_marks = %s,
            grade = %s,
            status = %s,
            answer_sheet_file = %s,
            published = %s

        WHERE student_id = %s
        AND exam_id = %s
        """

        values = (
            theory_marks,
            practical_marks,
            total_marks,
            grade,
            status,
            filename,
            published,
            student_id,
            exam_id
        )

        cursor.execute(query, values)


    # =========================
    # INSERT New Result
    # =========================

    else:

        query = """
        INSERT INTO offline_exam_results
        (
            student_id,
            exam_id,
            theory_marks,
            practical_marks,
            total_marks,
            grade,
            status,
            answer_sheet_file,
            published
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            student_id,
            exam_id,
            theory_marks,
            practical_marks,
            total_marks,
            grade,
            status,
            filename,
            published
        )

        cursor.execute(query, values)


    # =========================
    # Save Database
    # =========================

    conn.commit()

    cursor.close()
    conn.close()


    # =========================
    # Back to Same Page
    # =========================

    return redirect(
        url_for("exam.all_offline_results")
    )


# --------------------fatch all question----------------------

@exam_bp.route("/all_exam_questions")
def all_exam_questions():

    conn = get_db_connection()

    cur = conn.cursor(dictionary=True)

    cur.execute("""

        SELECT
            id,
            title
        FROM exams
        ORDER BY title ASC

    """)

    exams = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "all_exam_questions.html",
        exams=exams
    )

# ------------------------EXAM QUESTIONS---------------------
@exam_bp.route("/get_exam_questions/<int:exam_id>")
def get_exam_questions(exam_id):

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""

    SELECT
        q.id,
        q.question_text,
        q.question_type,
        q.difficulty,
        qo.id AS option_id,
        qo.option_text,
        qo.is_correct,
        qo.option_order

    FROM exam_questions eq

    INNER JOIN questions q
        ON q.id=eq.question_id

    LEFT JOIN question_options qo
        ON qo.question_id=q.id

    WHERE eq.exam_id=%s

    ORDER BY q.id,qo.option_order

    """,(exam_id,))

    data=cur.fetchall()

    cur.close()
    conn.close()

    questions={}

    for row in data:

        qid=row["id"]

        if qid not in questions:

            questions[qid]={
                "id":qid,
                "question_text":row["question_text"],
                "question_type":row["question_type"],
                "difficulty":row["difficulty"],
                "options":[]
            }

        questions[qid]["options"].append({

            "id":row["option_id"],
            "text":row["option_text"],
            "correct":row["is_correct"]

        })

    return render_template(
        "exam_question_list.html",
        questions=questions.values()
    )


# -----------------Edit Exam Question------------------
@exam_bp.route("/edit_question/<int:question_id>")
def edit_question(question_id):

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Question Details
    cur.execute("""
        SELECT
            id,
            question_text,
            question_type,
            difficulty,
            topic,
            explanation
        FROM questions
        WHERE id=%s
    """,(question_id,))

    question=cur.fetchone()

    # Options
    cur.execute("""
        SELECT
            id,
            option_text,
            is_correct,
            option_order
        FROM question_options
        WHERE question_id=%s
        ORDER BY option_order
    """,(question_id,))

    options=cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "edit_exam_question.html",
        question=question,
        options=options
    )

# ------------------Update Question answer------------------------
@exam_bp.route("/update_question/<int:question_id>", methods=["POST"])
def update_question(question_id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # ------------------------
        # Question Data
        # ------------------------

        question_text = request.form.get("question_text")
        question_type = request.form.get("question_type")
        difficulty = request.form.get("difficulty")
        correct_option = request.form.get("correct_option")

        # ------------------------
        # Update Question
        # ------------------------

        cur.execute("""
            UPDATE questions
            SET
                question_text=%s,
                question_type=%s,
                difficulty=%s
            WHERE id=%s
        """,(
            question_text,
            question_type,
            difficulty,
            question_id
        ))

        # ------------------------
        # Get All Option IDs
        # ------------------------

        cur.execute("""
            SELECT id
            FROM question_options
            WHERE question_id=%s
        """,(question_id,))

        option_ids = cur.fetchall()

        # ------------------------
        # Update Every Option
        # ------------------------

        for row in option_ids:

            option_id = row[0]

            option_text = request.form.get(f"option_{option_id}")

            is_correct = 1 if str(option_id) == str(correct_option) else 0

            cur.execute("""
                UPDATE question_options
                SET
                    option_text=%s,
                    is_correct=%s
                WHERE id=%s
            """,(
                option_text,
                is_correct,
                option_id
            ))

        conn.commit()

        flash("Question Updated Successfully", "success")

    except Exception as e:

        conn.rollback()

        flash(str(e), "danger")

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for(
            "exam.edit_question",
            question_id=question_id
        )
    )


# ---------------- DELETE QUESTION ----------------

@exam_bp.route("/delete_question/<int:question_id>")
def delete_question(question_id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # 1. আগে exam_questions থেকে Delete
        cur.execute("""
            DELETE FROM exam_questions
            WHERE question_id = %s
        """, (question_id,))

        # 2. তারপর question_options থেকে Delete
        cur.execute("""
            DELETE FROM question_options
            WHERE question_id = %s
        """, (question_id,))

        # 3. শেষে questions Table থেকে Delete
        cur.execute("""
            DELETE FROM questions
            WHERE id = %s
        """, (question_id,))

        conn.commit()

        flash("Question Deleted Successfully.", "success")

    except Exception as e:

        conn.rollback()

        flash(str(e), "danger")

    finally:

        cur.close()
        conn.close()

    return redirect(url_for("exam.all_exam_questions"))
