
from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from datetime import datetime, timedelta
from models.exam_model import assign_exams_to_student
from models.exam_model import (
    create_exam,
    get_all_exams,
    get_questions_by_exam,
    get_attempt,
    create_attempt,
    get_db_connection
)
from zeep import Client

exam_bp = Blueprint('exam', __name__)

# ---------------- CREATE EXAM ----------------
@exam_bp.route('/create_exam')
def create_exam_page():
    return render_template('create_exam.html')


@exam_bp.route('/exams')
def exam_list():
    exams = get_all_exams()
    return render_template('exam_list.html',exams=exams)


@exam_bp.route('/save_exam', methods=['POST'])
def save_exam():
    created_by = session.get('user').get('UserId')

    print("Created By:", created_by )

    data = (
        request.form['title'],
        request.form.get('description'),
        request.form['start_at'],
        request.form['end_at'],
        request.form['duration'],
        float(request.form.get('total_marks') or 0),
        float(request.form.get('pass_marks') or 0),
        int(request.form.get('shuffle_questions', 0)),
        int(request.form.get('shuffle_options', 0)),
        int(request.form.get('allow_review', 1)),
        int(request.form.get('is_published', 0)),
        created_by
    )
    create_exam(data)
    return redirect(url_for('exam.exam_list'))


# ---------------- STUDENT LOGIN ----------------

@exam_bp.route('/student-login', methods=['GET', 'POST'])
def student_login():

    wsdl = "https://technovas.in/WebService.asmx?WSDL"
    client = Client(wsdl)
    error = None
    if request.method == 'POST':
        student_id = request.form['UserId']
        student_pwd = request.form['password']
        result = client.service.GetUser(student_id, student_pwd)
        print("Login Result:", result)
        if result.Status == "Success":
            session['user'] = {
                    'name': result.Name,
                    'UserId': result.Id
                }

            return redirect(url_for('exam.student_portal'))

    return render_template('student_login.html')


# ================= STUDENT PORTAL =================

@exam_bp.route('/student-portal')
def student_portal():
    print("shimul"+ str(session['user']))
    # CHECK LOGIN (FIXED)
    if session.get('user'):
         return render_template(
        'student_portal.html',
         student_name=session['user']['name']
    )
        
    return redirect(url_for('exam.student_login'))

# ----------------------------student_dashboard-------------
@exam_bp.route('/student_dashboard')
def student_dashboard():
    if session.get('user'):
      student_id = session['user']['UserId']
      print("Student ID:", student_id)
    else:
        return redirect(url_for('exam.student_login'))
    
    # assign exams
    assign_exams_to_student(student_id)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT e.*,
        CASE 
            WHEN NOW() < e.start_at THEN 'UPCOMING'
            WHEN NOW() >= e.start_at AND NOW() <= e.end_at THEN 'LIVE'
            ELSE 'EXPIRED'
        END AS state
        FROM exams e
        JOIN student_exams se ON e.id = se.exam_id
        WHERE se.student_id = %s
    """, (student_id,))

    exams = cursor.fetchall()

    cursor.close()
    conn.close()

    #FILTER: remove expired exams (Python level extra safety)
    active_exams = []
    now = datetime.now()

    for exam in exams:
        if exam['state'] != 'EXPIRED':
            active_exams.append(exam)

    return render_template('student_dashboard.html', exams=active_exams)


 # ---------------- EXAM PAGE ----------------

@exam_bp.route('/exam', methods=['GET', 'POST'])
def exam():

    # ================= CHECK SESSION =================
    if 'exam_id' not in session or 'attempt_id' not in session:
        return redirect(url_for('exam.student_dashboard'))

    attempt_id = session['attempt_id']

    questions = get_questions_by_exam(session['exam_id'])

    if not questions:
        return "❌ No questions found"

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

    student = session.get('student')
    if not student:
        return redirect(url_for('exam.student_login'))

    student_id = student.get('student_id')

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

    # CREATE NEW ATTEMPT


# CREATE NEW ATTEMPT
    attempt_id = create_attempt(
    exam_id,
    student_id,
    request.remote_addr,
    request.headers.get('User-Agent')
)

# FAILED
    if not attempt_id:
        return "❌ Failed to create attempt"

# 🔥 USE CURRENT TIME
    started_at = datetime.now()

# END TIME
    end_time = started_at + timedelta(
    minutes=exam['duration_minutes']
)

# SESSION
    session['attempt_id'] = attempt_id
    session['exam_id'] = exam_id
    session['answers'] = {}
    session['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
    print("✅ Exam Started")
    print("Attempt ID:", attempt_id)
    return redirect(url_for('exam.exam'))


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




# # ---------------- PUBLISH RESULT ----------------
@exam_bp.route('/publish_result/<int:attempt_id>')
def publish_result_route(attempt_id):

    try:
        # 🔥 IMPORT (TOP-LEVEL recommended, but safe here)
        from models.results_model import publish_result

        publish_result(attempt_id)

    except Exception as e:
        print("ERROR:", e)

    return redirect(url_for('exam.result_processing'))


# ---------------- RESULT PROCESSING ----------------
@exam_bp.route('/result_processing')
def result_processing():

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    try:

        query = """

            SELECT

                r.attempt_id,

                a.student_id,

                e.title AS exam_title,

                r.total_marks,

                r.percentage,

                r.result_status,

                r.published,

                a.started_at,

                a.submitted_at

            FROM results r

            INNER JOIN attempts a
                ON r.attempt_id = a.id

            INNER JOIN exams e
                ON a.exam_id = e.id

            ORDER BY r.attempt_id DESC

        """

        cursor.execute(query)

        results = cursor.fetchall()

        print(results)

    except Exception as e:

        print("ERROR => ", e)

        results = []

    finally:

        cursor.close()
        conn.close()

    return render_template(
        'result_processing.html',
        results=results
    )


# ----------------Real Calculation Logic----------------------
def calculate_result(attempt_id):

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT 
                sa.question_id,
                sa.selected_option_id,
                qo.is_correct

            FROM student_answers sa

            JOIN question_options qo
            ON sa.selected_option_id = qo.id

            WHERE sa.attempt_id = %s
        """, (attempt_id,))

        data = cursor.fetchall()

        total_questions = len(data)

        correct_answers = 0

        for row in data:

            if row['is_correct'] == 1:

                correct_answers += 1

        total_marks = total_questions

        obtained_marks = correct_answers

        percentage = (
            (obtained_marks / total_marks) * 100
            if total_marks > 0 else 0
        )

        result_status = (
            'PASS'
            if percentage >= 40
            else 'FAIL'
        )

        return (
            obtained_marks,
            total_marks,
            percentage,
            result_status
        )

    except Exception as e:

        print("ERROR:", e)

        return 0, 0, 0, 'FAIL'

    finally:

        cursor.close()

        conn.close()

# --------------------submit function---------------------------------
def submit_attempt(attempt_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        # =========================
        # MARK SUBMITTED
        # =========================

        cursor.execute("""
            UPDATE attempts
            SET
                status='SUBMITTED',
                submitted_at=NOW()
            WHERE id=%s
        """, (attempt_id,))

        # =========================
        # CALCULATE RESULT
        # =========================

        obtained_marks, total_marks, percentage, result_status = calculate_result(attempt_id)

        # =========================
        # INSERT RESULT
        # =========================

        cursor.execute("""
            INSERT INTO results
            (
                attempt_id,
                total_marks,
                percentage,
                result_status,
                published,
                evaluated_at
            )
            VALUES (%s, %s, %s, %s, 0, NOW())
        """, (
            attempt_id,
            obtained_marks,
            percentage,
            result_status
        ))

        conn.commit()

        print("✅ RESULT SAVED")

    except Exception as e:

        conn.rollback()

        print("ERROR:", e)

    finally:

        cursor.close()

        conn.close()

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
        "SELECT * FROM users where role='STUDENT'"
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
        x['student_id']
        for x in assigned_data
    ]

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
            url_for('exam.exam_list')
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









