
import mysql.connector
import mssql_python


FACE_TOLERANCE = 0.50
ATTENDANCE_COOLDOWN_SECONDS = 30

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="technovasuser",
        password="Passw0rd1$",
        database="technovas_skill_foundation"
        
    )





import mssql_python


def get_sql_server_connection():

    connection_string = (
        "Server=103.14.121.8,34569;"
        "Database=technova_db;"
        "UID=technova;"
        "PWD=fUwAzxRZBN6t4fz%;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return mssql_python.connect(connection_string)
        
    