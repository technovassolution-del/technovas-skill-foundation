
import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="technovasuser",
        password="Pass",
        database="technovas_skill_foundation"
        
    )