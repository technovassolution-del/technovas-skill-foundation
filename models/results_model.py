

from config import get_db_connection

def create_result(attempt_id, total_marks, percentage, result_status):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO results 
            (attempt_id, total_marks, percentage, result_status, published, evaluated_at)
            VALUES (%s, %s, %s, %s, 0, NOW())
        """, (attempt_id, total_marks, percentage, result_status))

        conn.commit()
        return True

    except Exception as e:
        print("ERROR:", e)
        return False

    finally:
        cursor.close()
        conn.close()


def get_result_by_attempt(attempt_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM results WHERE attempt_id=%s", (attempt_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


def publish_result(attempt_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE results 
        SET published=1 
        WHERE attempt_id=%s
    """, (attempt_id,))

    conn.commit()
    cursor.close()
    conn.close()