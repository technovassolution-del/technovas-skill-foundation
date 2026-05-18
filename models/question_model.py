
from config import get_db_connection


def get_all_exams():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title FROM exams ORDER BY id DESC")
    exams = cursor.fetchall()

    conn.close()
    return exams



def create_question(question_data, options, exam_id, marks, negative_marks):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO questions
            (question_text, question_type, difficulty, topic, explanation, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, question_data)

        question_id = cursor.lastrowid

        for opt in options:
            cursor.execute("""
                INSERT INTO question_options
                (question_id, option_text, is_correct, option_order)
                VALUES (%s, %s, %s, %s)
            """, (
                question_id,
                opt['text'],
                opt['is_correct'],
                opt['order']
            ))

        cursor.execute("""
            INSERT INTO exam_questions
            (exam_id, question_id, marks, negative_marks, question_order)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            exam_id,
            question_id,
            int(marks),
            int(negative_marks),
            1
        ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return f"❌ DB ERROR: {e}"   # 🔥 KEY LINE

    finally:
        conn.close()

def get_all_questions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM questions ORDER BY id DESC")
    data = cursor.fetchall()

    conn.close()
    return data