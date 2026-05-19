
import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Passw0rd1$",
        database="technovas_skill_foundation"
        
    )