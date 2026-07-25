from config import get_db_connection


# ==============================
# CREATE QUESTION
# ==============================

def create_question(
    question_data,
    options,
    exam_id,
    marks,
    negative_marks
):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # Insert Question
        cursor.execute("""
            INSERT INTO questions
            (
                question_text,
                question_type,
                difficulty,
                topic,
                explanation,
                created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, question_data)

        question_id = cursor.lastrowid


        # ==============================
        # Insert MCQ Options (Online only)
        # ==============================

        if options:

            for opt in options:

                cursor.execute("""
                    INSERT INTO question_options
                    (
                        question_id,
                        option_text,
                        is_correct,
                        option_order
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    question_id,
                    opt["text"],
                    opt["is_correct"],
                    opt["order"]
                ))


        # ==============================
        # Link Question with Exam
        # ==============================

        cursor.execute("""
            INSERT INTO exam_questions
            (
                exam_id,
                question_id,
                marks,
                negative_marks,
                question_order
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            exam_id,
            question_id,
            int(marks),
            int(negative_marks),
            1
        ))


        conn.commit()

        return None


    except Exception as e:

        conn.rollback()

        return f"❌ CREATE QUESTION ERROR: {e}"


    finally:

        cursor.close()
        conn.close()



# ==============================
# GET ALL QUESTIONS
# ==============================

def get_all_questions():

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute("""
            SELECT 
                *
            FROM questions
            ORDER BY id DESC
        """)

        questions = cursor.fetchall()

        return questions


    except Exception as e:

        print(
            "❌ GET QUESTIONS ERROR:",
            e
        )

        return []


    finally:

        cursor.close()
        conn.close()