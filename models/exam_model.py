
from config import get_db_connection
from datetime import datetime

def create_exam(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 🔹 convert datetime format
        start_at = datetime.fromisoformat(data[2])
        end_at = datetime.fromisoformat(data[3])

        # 🔹 replace in tuple
        new_data = (
            data[0],  # title
            data[1],  # description
            start_at,
            end_at,
            data[4],  # duration
            data[5],  # total_marks
            data[6],  # pass_marks
            data[7],
            data[8],
            data[9],
            data[10],
            data[11]
        )

        query = """
        INSERT INTO exams
        (title, description, start_at, end_at, duration_minutes,
         total_marks, pass_marks, shuffle_questions, shuffle_options,
         allow_review, is_published, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        print(query)
        cursor.execute(query, new_data)
        conn.commit()

    except Exception as e:
        conn.rollback()
        print("ERROR:", e)

    finally:
        cursor.close()
        conn.close()


def get_all_exams():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM exams ORDER BY id DESC")
        exams = cursor.fetchall()
        return exams

    except Exception as e:
        print("ERROR:", e)
        return []

    finally:
        cursor.close()
        conn.close()



# 🔹 Get all exams
def get_all_exams():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM exams WHERE is_published=1 ORDER BY id DESC")
    exams = cursor.fetchall()
    conn.close()
    return exams



# ---------------- GET QUESTIONS BY EXAM ----------------
def get_questions_by_exam(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
SELECT 
    q.id AS question_id,
    q.question_text,
    qo.id AS option_id,
    qo.option_text
FROM exam_questions eq
JOIN questions q ON eq.question_id = q.id
LEFT JOIN question_options qo ON q.id = qo.question_id
WHERE eq.exam_id = %s
ORDER BY eq.question_order, qo.option_order
"""

        cursor.execute(query, (exam_id,))
        rows = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    questions = {}

    for row in rows:
        qid = row['question_id']

        if qid not in questions:
            questions[qid] = {
                "id": qid,
                "question_text": row['question_text'],
                "options": []
            }

        questions[qid]["options"].append({
            "id": row['option_id'],
            "text": row['option_text']
        })

    return list(questions.values())


# ---------------- CREATE ATTEMPT ----------------

def create_attempt(exam_id, student_id, ip_address, user_agent):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        print("DEBUG exam_id:", exam_id)
        print("DEBUG student_id:", student_id)

        # 🔹 Get next attempt number
        cursor.execute("""
            SELECT COUNT(*) + 1 FROM attempts
            WHERE exam_id = %s AND student_id = %s
        """, (exam_id, student_id))

        attempt_no = cursor.fetchone()[0]

        print("DEBUG attempt_no:", attempt_no)

        # 🔹 Insert attempt
        cursor.execute("""
            INSERT INTO attempts
            (
                exam_id,
                student_id,
                attempt_no,
                started_at,
                ip_address,
                user_agent,
                status
            )
            VALUES (%s, %s, %s, NOW(), %s, %s, 'IN_PROGRESS')
        """, (
            exam_id,
            student_id,
            attempt_no,
            ip_address,
            user_agent
        ))

        conn.commit()

        # ✅ GET INSERTED ID
        attempt_id = cursor.lastrowid

        print("✅ INSERT SUCCESS")
        print("DEBUG attempt_id:", attempt_id)

        return attempt_id

    except Exception as e:

        conn.rollback()

        import traceback

        print("❌ DATABASE ERROR:", e)

        traceback.print_exc()

        return None

    finally:

        cursor.close()
        conn.close()

# ---------------- GET ATTEMPT ----------------
def get_attempt(exam_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT * FROM attempts
            WHERE exam_id=%s AND student_id=%s
            ORDER BY id DESC LIMIT 1
        """, (exam_id, student_id))

        return cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

# ---------------- SUBMIT ATTEMPT ----------------
def submit_attempt(attempt_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE attempts
            SET status='SUBMITTED', submitted_at=NOW()
            WHERE id=%s
        """, (attempt_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("ERROR:", e)

    finally:
        cursor.close()
        conn.close()


# ---------------- AUTO ASSIGN EXAMS ----------------

def assign_exams_to_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM exams")
    exams = cursor.fetchall()

    for exam in exams:
        # check already assigned 
        cursor.execute("""
            SELECT id FROM student_exams
            WHERE student_id=%s AND exam_id=%s
        """, (student_id, exam['id']))

        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO student_exams (student_id, exam_id)
                VALUES (%s, %s)
            """, (student_id, exam['id']))

    conn.commit()
    cursor.close()
    conn.close()

