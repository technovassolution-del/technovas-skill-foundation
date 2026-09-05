from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    current_app
)

from config import get_sql_server_connection

from services.faceservice import (
    base64_to_bytes,
    base64_to_image,
    get_face_encoding,
    encoding_to_bytes
)

from werkzeug.utils import secure_filename

import os
import uuid


# =====================================================
# BLUEPRINT
# =====================================================

employee_bp = Blueprint(
    "employee",
    __name__,
    url_prefix="/employee"
)






# =====================================================
# REGISTRATION PAGE
# =====================================================

@employee_bp.route(
    "/register",
    methods=["GET"]
)
def register_page():

    return render_template(
        "employee_register.html"
    )


# =====================================================
# GENERATE NEXT EMPLOYEE CODE
# =====================================================

@employee_bp.route(
    "/next-employee-code",
    methods=["GET"]
)
def next_employee_code():

    conn = None
    cursor = None

    try:

        conn = get_sql_server_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT ISNULL(MAX(EmployeeID), 0) + 1
            FROM Employees
            """
        )

        row = cursor.fetchone()

        next_employee_id = row[0]

        employee_code = (
            f"TS{next_employee_id:03d}"
        )

        return jsonify({

            "success": True,

            "employeeCode": employee_code

        })

    except Exception as e:

        print(
            "Employee Code Error:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500

    finally:

        if cursor:

            cursor.close()

        if conn:

            conn.close()


# =====================================================
# REGISTER EMPLOYEE
# =====================================================

def save_upload(uploaded_file, prefix):

    if uploaded_file is None:
        return None

    if not uploaded_file.filename:
        return None

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "pdf"
    }

    original_name = secure_filename(uploaded_file.filename)

    if "." not in original_name:
        raise ValueError(f"Invalid {prefix} file")

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions:
        raise ValueError(
            f"Invalid {prefix} file type. "
            f"Allowed: JPG, JPEG, PNG, PDF"
        )

    # Check maximum file size: 2 MB
    uploaded_file.stream.seek(0, os.SEEK_END)
    file_size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)

    if file_size > 2 * 1024 * 1024:
        raise ValueError(f"{prefix} file must not exceed 2 MB")

    upload_folder = os.path.join(
        current_app.root_path,
        "uploads",
        "employee_documents"
    )

    os.makedirs(upload_folder, exist_ok=True)

    unique_filename = (
        f"{prefix}_{uuid.uuid4().hex}.{extension}"
    )

    full_path = os.path.join(
        upload_folder,
        unique_filename
    )

    uploaded_file.save(full_path)

    # Store relative path in database
    return os.path.join(
        "uploads",
        "employee_documents",
        unique_filename
    ).replace("\\", "/")


@employee_bp.route(
    "/register",
    methods=["POST"]
)
def register_employee():

    connection = None
    cursor = None
    aadhar_file_path = None
    pan_file_path = None

    try:

        # -------------------------------------------------
        # REQUEST DATA
        # -------------------------------------------------

        data = request.get_json(silent=True) or request.form

         # Always initialize variables
        aadhar_file = None
        pan_file = None

        # Read uploaded files
        aadhar_file = request.files.get("aadharFile")
        pan_file = request.files.get("panFile")

        print("Aadhar file:", aadhar_file)
        print("PAN file:", pan_file)

        # Save files
        aadhar_path = save_upload(aadhar_file, "aadhar")
        pan_path = save_upload(pan_file, "pan")

        print("Aadhar path:", aadhar_path)
        print("PAN path:", pan_path)
        employee_code = data.get(
            "employeeCode"
        )

        full_name = data.get(
            "fullName"
        )

        mobile = data.get(
            "mobile"
        )

        email = data.get(
            "email"
        )

        department = data.get(
            "department",
            ""
        )

        designation = data.get(
            "designation",
            ""
        )

        employee_type = data.get(
            "employeeType",
            ""
        )

        captured_photo = data.get(
            "capturedPhoto"
        )

        address = data.get(
            "address"
        )

        city = data.get(
            "city"
        )

        state = data.get(
            "state"
        )

        pincode = data.get(
            "pincode"
        )

        aadharNumber = data.get(
            "aadharNumber"
        )

        panNumber = data.get(
            "panNumber"
        )

        accountNumber = data.get(
            "accountNumber"
        )

        bankName = data.get(
            "bankName"
        )

        ifscCode = data.get(
            "ifscCode"
        )

       
        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not employee_code:

            return jsonify({

                "success": False,

                "message": "Employee code is required"

            }), 400

        if not full_name:

            return jsonify({

                "success": False,

                "message": "Full name is required"

            }), 400

        if not captured_photo:

            return jsonify({

                "success": False,

                "message": "Please capture a face photo"

            }), 400

        
      

        # -------------------------------------------------
        # IMAGE PROCESSING
        # -------------------------------------------------

        image_bytes = base64_to_bytes(
            captured_photo
        )

        image = base64_to_image(
            captured_photo
        )

        face_encoding = get_face_encoding(
            image
        )

        encoding_bytes = encoding_to_bytes(
            face_encoding
        )

        # -------------------------------------------------
        # DATABASE CONNECTION
        # -------------------------------------------------

        connection = get_sql_server_connection()

        cursor = connection.cursor()

        # -------------------------------------------------
        # CHECK DUPLICATE EMPLOYEE CODE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT EmployeeID
            FROM Employees
            WHERE Mobile = ?
            """,
            (
                mobile,
            )
        )

        existing_employee = cursor.fetchone()

        if existing_employee:

            return jsonify({

                "success": False,

                "message": "Mobile number already exists"

            }), 409

        # -------------------------------------------------
        # INSERT EMPLOYEE
        # -------------------------------------------------

        sql = """
        INSERT INTO Employees
        (
            EmployeeCode,
            FullName,
            Mobile,
            Email,
            Department,
            Designation,
            EmployeeType,
            FaceImage,
            FaceEncoding,
            Address,
            City,
            State,
            Pincode,
            AadharNumber,
            PanNumber,
            AccountNumber,
            BankName,
            IFSCCode,
            aadharfilepath,
            panfilepath
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """

        values = (
            employee_code,
            full_name,
            mobile,
            email,
            department,
            designation,
            employee_type,
            image_bytes,
            encoding_bytes,
            address,
            city,
            state,
            pincode,
            aadharNumber,
            panNumber,
            accountNumber,
            bankName,
            ifscCode,
            aadhar_path,
            pan_path
        )

        cursor.execute(
            sql,
            values
        )

        connection.commit()

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "message": "Employee registered successfully"

        }), 201

    # =====================================================
    # VALIDATION ERROR
    # =====================================================

    except ValueError as e:

        if connection:

            connection.rollback()

       

      

        return jsonify({

            "success": False,

            "message": str(e)

        }), 400

    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as e:

        if connection:

            connection.rollback()

       
        

        print(
            "Employee registration error:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message": "Unable to register employee"

        }), 500



    # =====================================================
    # CLOSE CONNECTION
    # =====================================================

    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_from_directory
)

from config import get_sql_server_connection
import os




# =====================================================
# VIEW ALL SUBMITTED EMPLOYEES
# =====================================================

@employee_bp.route("/submissions", methods=["GET"])
def submissions():
    conn = None
    cursor = None
    try:
        conn = get_sql_server_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                EmployeeID,
                EmployeeCode,
                FullName,
                Mobile,
                Email,
                AadharNumber,
                AadharFilePath,
                pannumber,
                PanFilePath,
                BankName,
                accountnumber,
                IFSCCode,
                EmployeeType,
                ApprovalStatus,
                ApprovedDate,
                FaceImage
            FROM Employees
            ORDER BY EmployeeID DESC
        """)

        rows = cursor.fetchall()
        employees = []

        for row in rows:
            employees.append({
                "EmployeeID": row[0],
                "EmployeeCode": row[1],
                "FullName": row[2],
                "Mobile": row[3],
                "Email": row[4],
                "AadharNumber": row[5],
                "AadharFilePath": row[6],
                "pannumber": row[7],
                "PanFilePath": row[8],
                "BankName": row[9],
                "accountnumber": row[10],
                "IFSCCode": row[11],
                "EmployeeType": row[12],
                "ApprovalStatus": row[13],
                "ApprovedDate": row[14],
                "FaceImage": row[15]
            })

        return render_template(
            "employee_submissions.html",
            employees=employees
        )

    except Exception as e:

        print("Submission error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# APPROVE EMPLOYEE
# =====================================================

@employee_bp.route("/approve/<int:employee_id>", methods=["POST"])
def approve_employee(employee_id):

    conn = None
    cursor = None

    try:

        conn = get_sql_server_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Employees
            SET
                ApprovalStatus = 'Approved',
                ApprovedDate = GETDATE()
            WHERE EmployeeID = ?
        """, (employee_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Employee approved successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print("Approval error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# REJECT EMPLOYEE
# =====================================================

@employee_bp.route("/reject/<int:employee_id>", methods=["POST"])
def reject_employee(employee_id):

    conn = None
    cursor = None

    try:

        conn = get_sql_server_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Employees
            SET
                ApprovalStatus = 'Rejected',
                ApprovedDate = NULL
            WHERE EmployeeID = ?
        """, (employee_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Employee rejected"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# SERVE EMPLOYEE DOCUMENTS
# =====================================================

@employee_bp.route("/uploads/<path:filename>")
def employee_document(filename):
    upload_folder = os.path.join(
        os.getcwd(),
        "uploads",
        "employee_documents"
    )

    return send_from_directory(
        upload_folder,
        filename
    )


from flask import send_file
from io import BytesIO

@employee_bp.route("/photo/<int:employee_id>")
def employee_photo(employee_id):
    conn = None
    cursor = None

    try:

        conn = get_sql_server_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT FaceImage
            FROM Employees
            WHERE EmployeeID = ?
        """, (employee_id,))

        row = cursor.fetchone()

        if not row or not row[0]:
            return "Photo not found", 404

        photo_data = bytes(row[0])

        return send_file(
            BytesIO(photo_data),
            mimetype="image/jpeg"
        )

    except Exception as e:

        print("Photo error:", e)

        return "Unable to load photo", 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()