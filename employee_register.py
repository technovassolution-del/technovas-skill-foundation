from flask import Flask, request, jsonify, render_template
import os
import base64
import mssql_python
import numpy as np
import cv2
import face_recognition
from werkzeug.utils import secure_filename


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

AADHAR_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "aadhar"
)

PAN_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "pan"
)


os.makedirs(
    AADHAR_FOLDER,
    exist_ok=True
)

os.makedirs(
    PAN_FOLDER,
    exist_ok=True
)


# Allowed file extensions

ALLOWED_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}


# =========================================================
# CHECK FILE EXTENSION
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# SQL SERVER CONNECTION
# =========================================================

def get_db_connection():

   return mssql_python.connect(
           "Server=103.14.121.8,34569;"
           "Database=technova_db;"
           "User Id=technova;"
           "Password=fUwAzxRZBN6t4fz%;"
           "Trusted_Connection=yes;"
           "Encrypt=yes;"
           "TrustServerCertificate=yes;"
       )
   


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def index():

    return render_template(
        "employee_register.html"
    )


# =========================================================
# REGISTER EMPLOYEE
# =========================================================

@app.route(
    "/employee/register",
    methods=["POST"]
)
def register_employee():

    db = None
    cursor = None

    try:

        # =================================================
        # GET FORM DATA
        # =================================================

        employee_id = request.form.get(
            "employeeId"
        )

        full_name = request.form.get(
            "fullName"
        )

        mobile = request.form.get(
            "mobile"
        )

        email = request.form.get(
            "email"
        )

        aadhar_number = request.form.get(
            "aadharNumber"
        )

        pan_no = request.form.get(
            "panNo"
        )

        bank_name = request.form.get(
            "bankName"
        )

        account_no = request.form.get(
            "accountNo"
        )

        ifsc_code = request.form.get(
            "ifscCode"
        )

        employee_type = request.form.get(
            "employeeType"
        )

        photo_data = request.form.get(
            "capturedPhoto"
        )

        qualification = request.form.get(
            "qualification"
        )


        # =================================================
        # VALIDATION
        # =================================================

        


        if not full_name:

            return jsonify({

                "success": False,

                "message":
                    "Employee name is required"

            }), 400


        if not photo_data:

            return jsonify({

                "success": False,

                "message":
                    "Please capture employee photo"

            }), 400


        # =================================================
        # PROCESS BASE64 PHOTO
        # =================================================

        # Remove Base64 header

        if "," in photo_data:

            photo_data = photo_data.split(
                ",",
                1
            )[1]


        # Convert Base64 to bytes

        try:

            image_bytes = base64.b64decode(
                photo_data
            )

        except Exception:

            return jsonify({

                "success": False,

                "message":
                    "Invalid photo data"

            }), 400


        # Convert bytes to numpy array

        image_array = np.frombuffer(

            image_bytes,

            dtype=np.uint8
        )


        # Decode image

        image_bgr = cv2.imdecode(

            image_array,

            cv2.IMREAD_COLOR
        )


        if image_bgr is None:

            return jsonify({

                "success": False,

                "message":
                    "Invalid image"

            }), 400


        # Convert BGR to RGB

        image_rgb = cv2.cvtColor(

            image_bgr,

            cv2.COLOR_BGR2RGB
        )


        # =================================================
        # DETECT FACE
        # =================================================

        face_locations = face_recognition.face_locations(

            image_rgb
        )


        if len(face_locations) == 0:

            return jsonify({

                "success": False,

                "message":
                    "No face detected. Please capture again."

            }), 400


        if len(face_locations) > 1:

            return jsonify({

                "success": False,

                "message":
                    "Multiple faces detected. Only one person should be visible."

            }), 400


        # =================================================
        # GENERATE FACE EMBEDDING
        # =================================================

        face_encodings = face_recognition.face_encodings(

            image_rgb,

            face_locations
        )


        if not face_encodings:

            return jsonify({

                "success": False,

                "message":
                    "Face embedding could not be generated"

            }), 400


        face_embedding = face_encodings[0]


        # Convert embedding to binary

        embedding_bytes = face_embedding.astype(

            np.float64

        ).tobytes()


        # =================================================
        # GET DOCUMENT FILES
        # =================================================

        aadhar_file = request.files.get(

            "aadharFile"
        )

        pan_file = request.files.get(

            "panFile"
        )


        aadhar_file_path = None

        pan_file_path = None


        # =================================================
        # SAVE AADHAR FILE
        # =================================================

        if aadhar_file and aadhar_file.filename:


            if not allowed_file(

                aadhar_file.filename

            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid Aadhaar file format"

                }), 400


            original_filename = secure_filename(

                aadhar_file.filename

            )


            filename = (

                full_name
                + "_aadhar_"
                + original_filename
            )


            full_path = os.path.join(

                AADHAR_FOLDER,

                filename
            )


            aadhar_file.save(

                full_path
            )


            # Store relative path

            aadhar_file_path = os.path.join(

                "uploads",

                "aadhar",

                filename
            )


        # =================================================
        # SAVE PAN FILE
        # =================================================

        if pan_file and pan_file.filename:


            if not allowed_file(

                pan_file.filename

            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid PAN file format"

                }), 400


            original_filename = secure_filename(

                pan_file.filename

            )


            filename = (

                full_name
                + "_pan_"
                + original_filename
            )


            full_path = os.path.join(

                PAN_FOLDER,

                filename
            )


            pan_file.save(

                full_path
            )


            # Store relative path

            pan_file_path = os.path.join(

                "uploads",

                "pan",

                filename
            )


        # =================================================
        # DATABASE CONNECTION
        # =================================================

        db = get_db_connection()

        cursor = db.cursor()


        # =================================================
        # CHECK DUPLICATE EMPLOYEE ID
        # =================================================

        cursor.execute(

            """
            SELECT COUNT(*)
            FROM employees
            WHERE employee_id = ?
            """,

            (employee_id,)
        )


        result = cursor.fetchone()


        if result[0] > 0:

            return jsonify({

                "success": False,

                "message":
                    "Employee ID already exists"

            }), 409


        # =================================================
        # INSERT EMPLOYEE
        # =================================================

        sql = """

            INSERT INTO employees
            (

                

                full_name,

                mobile,

                email,

                aadhar_number,

                aadhar_file_path,

                pan_no,

                pan_file_path,

                bank_name,

                account_no,

                ifsc_code,

                employee_type,

                photo,

                face_embedding,
                status,
                qualification

            )

            VALUES
            (

                ?, ?, ?, ?, ?, ?, ?,

                ?, ?, ?, ?, ?, ?,?,?

            )

        """


        values = (

            

            full_name,

            mobile,

            email,

            aadhar_number,

            aadhar_file_path,

            pan_no,

            pan_file_path,

            bank_name,

            account_no,

            ifsc_code,

            employee_type,

            image_bytes,

            embedding_bytes,
            0,
            qualification
        )


        cursor.execute(

            sql,

            values
        )


        db.commit()


        # =================================================
        # SUCCESS RESPONSE
        # =================================================

        return jsonify({

            "success": True,

            "message":
                "Employee registered successfully",

            "employee_id":
                employee_id

        })


    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except Exception as error:


        if db:

            try:

                db.rollback()

            except Exception:

                pass


        return jsonify({

            "success": False,

            "message":
                "Registration failed",

            "error":
                str(error)

        }), 500


    # =====================================================
    # CLOSE DATABASE CONNECTION
    # =====================================================

    finally:


        if cursor:

            try:

                cursor.close()

            except Exception:

                pass


        if db:

            try:

                db.close()

            except Exception:

                pass


# =========================================================
# RUN APPLICATION
# =========================================================

