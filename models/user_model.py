
from config import get_db_connection

def create_user(full_name, email, mobile, password_hash, role):
    db = get_db_connection()
    cursor = db.cursor()

    query = """
    INSERT INTO users (full_name, email, mobile, password_hash, role)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (full_name, email, mobile, password_hash, role))
    db.commit()

    cursor.close()
    db.close()