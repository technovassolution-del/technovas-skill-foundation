import base64
import json
import os
import uuid
from datetime import datetime
import qrcode
from flask import Blueprint, render_template, request, jsonify
from config import get_sql_server_connection


student_admission = Blueprint("student_admission", __name__)




def val(f, name):
    return (f.get(name) or "").strip()


def dt(v):
    return datetime.strptime(v.strip(), "%d/%m/%Y").date()


def image_to_binary(data_url):
    """
    Converts:
        data:image/jpeg;base64,/9j/4AAQ...
    into:
        binary bytes suitable for SQL Server varbinary(max)
    """

    if not data_url:
        return None

    if not data_url.startswith("data:image/"):
        raise ValueError("Invalid student photo format.")

    try:
        header, encoded = data_url.split(",", 1)
        return base64.b64decode(encoded)
    except Exception as e:
        raise ValueError(f"Invalid photo data: {e}")


@student_admission.route(
    "/student/admission",
    methods=["GET", "POST"]
)



def admission():

    # -----------------------------
    # SHOW ADMISSION FORM
    # -----------------------------
    if request.method == "GET":
        return render_template("student_admission.html")

    # -----------------------------
    # SAVE ADMISSION
    # -----------------------------
    try:

        f = request.form

        required = [
            "fullName",
            "dob",
            "nationality",
            "governmentId",
            "gender",
            "email",
            "mobile",
            "fatherName",
            "motherName",
            "permanentAddress",
            "city",
            "state",
            "pinCode",
            "highestQualification",
            "boardUniversity",
            "schoolCollege",
            "passingYear",
            "percentageCgpa",
            "courseName",
            "studyMode"
        ]

        missing = [
            field
            for field in required
            if not val(f, field)
        ]

        if missing:
            return jsonify(
                success=False,
                message=(
                    "Missing required fields: "
                    + ", ".join(missing)
                )
            ), 400

        # -----------------------------
        # PHOTO
        # -----------------------------
        captured_photo = val(
            f,
            "capturedPhoto"
        )

        if not captured_photo:
            return jsonify(
                success=False,
                message="Please capture the student photo."
            ), 400

        photo_binary = image_to_binary(
            captured_photo
        )

        # -----------------------------
        # ADMISSION NUMBER
        # -----------------------------
        admission_no = (
            "TS-"
            + datetime.now().strftime("%Y%m%d")
            + "-"
            + uuid.uuid4().hex[:6].upper()
        )

        # -----------------------------
        # QR TOKEN
        # -----------------------------
        qr_token = uuid.uuid4()

        # -----------------------------
        # DOCUMENTS
        # -----------------------------
        documents = f.getlist("documents[]")

        # If DocumentsPath is NVARCHAR,
        # store JSON/text rather than binary.
        documents_path = json.dumps(
            documents,
            ensure_ascii=False
        )

        # -----------------------------
        # SQL INSERT
        # -----------------------------
        sql = """
        INSERT INTO tbl_student_admision
        (
            AdmissionNo,
            FullName,
            DOB,
            Nationality,
            GovernmentId,
            Gender,
            BloodGroup,
            Category,
            Email,
            Mobile,
            FatherName,
            FatherMobile,
            MotherName,
            MotherMobile,
            GuardianName,
            GuardianMobile,
            FatherOccupation,
            MotherOccupation,
            GuardianIncome,

            PermanentAddress,
            CurrentAddress,
            City,
            State,
            PinCode,

            HighestQualification,
            BoardUniversity,
            SchoolCollege,
            PassingYear,
            PercentageCgpa,
            Medium,

            CourseName,
            PreferredBatch,
            StudyMode,

            DocumentsPath,

            MedicalConditions,
            EmergencyName,
            EmergencyNumber,

            PhotoBase64,

            ApplicantSignature,
            SignatureDate,
            Place,

            ReviewedBy,
            AdmissionStatus,
            QrToken,
            ProgramCode

            
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?,
            ?, ?, ?,
            ?,
            ?, ?, ?,
            ?, ?, ?,?
            
        )
        """

        values = (
            admission_no,
            val(f, "fullName"),
            dt(f["dob"]),
            val(f, "nationality"),
            val(f, "governmentId"),
            val(f, "gender"),
            val(f, "bloodGroup") or None,
            val(f, "category") or None,
            val(f, "email"),
            val(f, "mobile"),

            val(f, "fatherName"),
            val(f, "fatherMobile") or None,
            val(f, "motherName"),
            val(f, "motherMobile") or None,
            val(f, "guardianName") or None,
            val(f, "guardianMobile") or None,
            val(f, "fatherOccupation") or None,
            val(f, "motherOccupation") or None,

            float(f["guardianIncome"])
            if val(f, "guardianIncome")
            else None,

            val(f, "permanentAddress"),
            val(f, "currentAddress") or None,
            val(f, "city"),
            val(f, "state"),
            val(f, "pinCode"),

            val(f, "highestQualification"),
            val(f, "boardUniversity"),
            val(f, "schoolCollege"),
            int(f["passingYear"]),
            val(f, "percentageCgpa"),
            val(f, "medium") or None,

            val(f, "courseName"),
            val(f, "preferredBatch") or None,
            val(f, "studyMode"),

            documents_path,

            val(f, "medicalConditions") or None,
            val(f, "emergencyName") or None,
            val(f, "emergencyNumber") or None,

            photo_binary,

            val(f, "applicantSignature") or None,
            dt(f["signatureDate"])
            if val(f, "signatureDate")
            else None,
            val(f, "place") or None,

            val(f, "reviewedBy") or None,
            val(f, "admissionStatus") or "Pending",
            qr_token,
            "1001"  # ProgramCode (hardcoded for now)
        )

      

        # -----------------------------
        # EXECUTE
        # -----------------------------
        with get_sql_server_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                sql,
                values
            )

            connection.commit()
             # Generate QR code after successful insertion

       


        # -----------------------------
        # GENERATE QR CODE
        # -----------------------------
        os.makedirs("static/qrcodes", exist_ok=True)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )

        qr.add_data(str(qr_token))
        qr.make(fit=True)

        qr_image = qr.make_image()

        qr_filename = f"{admission_no}.png"
        qr_path = os.path.join(
            "static",
            "qrcodes",
            qr_filename
        )

        qr_image.save(qr_path)


        return jsonify(
            success=True,
            message="Admission form submitted successfully.",
            admissionNo=admission_no,
            qrToken=str(qr_token),
            qrCodeUrl=f"/static/qrcodes/{qr_filename}"
        )

    except ValueError as e:

        return jsonify(
            success=False,
            message=f"Invalid date/number/photo format: {e}"
        ), 400

    except Exception as e:

        return jsonify(
            success=False,
            message=f"Unable to save admission: {e}"
        ), 500