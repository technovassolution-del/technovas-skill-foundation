# ============================================================
# student_listing.py
# ============================================================
# Student Listing / Edit / Update
# Flask + SQL Server + mssql_python
# ============================================================

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from config import get_sql_server_connection

import base64
import binascii
import traceback
from datetime import datetime


student_listing = Blueprint(
    "student_listing",
    __name__
)


# ============================================================
# Helper: Convert photo bytes to Base64
# ============================================================

def photo_to_base64(photo):

    if not photo:
        return None

    try:

        if isinstance(photo, bytes):
            return base64.b64encode(photo).decode("utf-8")

        if isinstance(photo, bytearray):
            return base64.b64encode(
                bytes(photo)
            ).decode("utf-8")

        if isinstance(photo, memoryview):
            return base64.b64encode(
                photo.tobytes()
            ).decode("utf-8")

    except Exception:
        traceback.print_exc()

    return None


# ============================================================
# Helper: Read form value
# ============================================================

def form_value(name):

    return request.form.get(
        name,
        ""
    ).strip()


# ============================================================
# EDIT STUDENT
# ============================================================

@student_listing.route(
    "/student/<admission_no>/edit",
    methods=["GET", "POST"]
)
def edit_student(admission_no):

    connection = None
    cursor = None

    # --------------------------------------------------------
    # Default student object
    # Prevents undefined variable in exception handling
    # --------------------------------------------------------

    student = {
        "AdmissionNo": admission_no,
        "FullName": "",
        "DOB": None,
        "Nationality": "",
        "GovernmentId": "",
        "Gender": "",
        "BloodGroup": "",
        "Category": "",
        "Email": "",
        "Mobile": "",

        "FatherName": "",
        "FatherMobile": "",
        "MotherName": "",
        "MotherMobile": "",
        "GuardianName": "",
        "GuardianMobile": "",

        "FatherOccupation": "",
        "MotherOccupation": "",
        "GuardianIncome": "",

        "PermanentAddress": "",
        "CurrentAddress": "",
        "City": "",
        "State": "",
        "PinCode": "",

        "HighestQualification": "",
        "BoardUniversity": "",
        "SchoolCollege": "",
        "PassingYear": "",
        "PercentageCgpa": "",
        "Medium": "",

        "CourseName": "",
        "PreferredBatch": "",
        "StudyMode": "",

        "DocumentsPath": "",

        "MedicalConditions": "",
        "EmergencyName": "",
        "EmergencyNumber": "",

        "ApplicantSignature": "",
        "SignatureDate": None,
        "Place": "",

        "ReviewedBy": "",
        "AdmissionStatus": "",

        "Photo": None,
        "PhotoBase64": None
    }

    try:

        connection = get_sql_server_connection()
        cursor = connection.cursor()

        # ====================================================
        # GET STUDENT
        # ====================================================

        select_sql = """
            SELECT
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

                ApplicantSignature,
                SignatureDate,
                Place,

                ReviewedBy,
                AdmissionStatus,

                PhotoBase64

            FROM tbl_student_admision

            WHERE AdmissionNo = ?
        """

        cursor.execute(
            select_sql,
            (admission_no,)
        )

        row = cursor.fetchone()

        if not row:

            flash(
                "Student record not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "student_listing.student_list"
                )
            )

        # ====================================================
        # Map database columns
        # ====================================================

        columns = [

            "AdmissionNo",
            "FullName",
            "DOB",
            "Nationality",
            "GovernmentId",
            "Gender",
            "BloodGroup",
            "Category",
            "Email",
            "Mobile",

            "FatherName",
            "FatherMobile",
            "MotherName",
            "MotherMobile",
            "GuardianName",
            "GuardianMobile",

            "FatherOccupation",
            "MotherOccupation",
            "GuardianIncome",

            "PermanentAddress",
            "CurrentAddress",
            "City",
            "State",
            "PinCode",

            "HighestQualification",
            "BoardUniversity",
            "SchoolCollege",
            "PassingYear",
            "PercentageCgpa",
            "Medium",

            "CourseName",
            "PreferredBatch",
            "StudyMode",

            "DocumentsPath",

            "MedicalConditions",
            "EmergencyName",
            "EmergencyNumber",

            "ApplicantSignature",
            "SignatureDate",
            "Place",

            "ReviewedBy",
            "AdmissionStatus",

            "PhotoBase64"
        ]

        student = dict(
            zip(
                columns,
                row
            )
        )

        # ====================================================
        # Convert Photo to Base64
        # ====================================================

        student["PhotoBase64"] = photo_to_base64(
            student.get("Photo")
        )

        print()
        print("=" * 60)
        print("EDIT STUDENT")
        print("=" * 60)
        print("URL Admission No :", admission_no)
        print("DB Admission No  :", student.get("AdmissionNo"))
        print("Student Name     :", student.get("FullName"))
        print("=" * 60)
        print()

        # ====================================================
        # GET REQUEST
        # ====================================================

        if request.method == "GET":

            return render_template(
                "edit_student.html",
                student=student
            )

        # ====================================================
        # POST REQUEST
        # ====================================================

        print()
        print("=" * 60)
        print("POST DATA")
        print("=" * 60)

        # ----------------------------------------------------
        # Personal Information
        # ----------------------------------------------------

        full_name = form_value("fullName")
        dob = form_value("dob")
        nationality = form_value("nationality")
        government_id = form_value("governmentId")
        gender = form_value("gender")
        blood_group = form_value("bloodGroup")
        category = form_value("category")
        email = form_value("email")
        mobile = form_value("mobile")

        # ----------------------------------------------------
        # Parent / Guardian
        # ----------------------------------------------------

        father_name = form_value("fatherName")
        father_mobile = form_value("fatherMobile")

        mother_name = form_value("motherName")
        mother_mobile = form_value("motherMobile")

        guardian_name = form_value("guardianName")
        guardian_mobile = form_value("guardianMobile")

        father_occupation = form_value(
            "fatherOccupation"
        )

        mother_occupation = form_value(
            "motherOccupation"
        )

        guardian_income = form_value(
            "guardianIncome"
        )

        # ----------------------------------------------------
        # Address
        # ----------------------------------------------------

        permanent_address = form_value(
            "permanentAddress"
        )

        current_address = form_value(
            "currentAddress"
        )

        city = form_value("city")
        state = form_value("state")
        pin_code = form_value("pinCode")

        # ----------------------------------------------------
        # Education
        # ----------------------------------------------------

        highest_qualification = form_value(
            "highestQualification"
        )

        board_university = form_value(
            "boardUniversity"
        )

        school_college = form_value(
            "schoolCollege"
        )

        passing_year = form_value(
            "passingYear"
        )

        percentage_cgpa = form_value(
            "percentageCgpa"
        )

        medium = form_value("medium")

        # ----------------------------------------------------
        # Course
        # ----------------------------------------------------

        course_name = form_value(
            "courseName"
        )

        preferred_batch = form_value(
            "preferredBatch"
        )

        study_mode = form_value(
            "studyMode"
        )

        # ----------------------------------------------------
        # Documents
        # ----------------------------------------------------

        documents_path = form_value(
            "documentsPath"
        )

        if not documents_path:

            documents_path = (
                student.get("DocumentsPath")
                or ""
            )

        # ----------------------------------------------------
        # Medical / Emergency
        # ----------------------------------------------------

        medical_conditions = form_value(
            "medicalConditions"
        )

        emergency_name = form_value(
            "emergencyName"
        )

        emergency_number = form_value(
            "emergencyNumber"
        )

        # ----------------------------------------------------
        # Declaration
        # ----------------------------------------------------

        applicant_signature = form_value(
            "applicantSignature"
        )

        signature_date = form_value(
            "signatureDate"
        )

        place = form_value("place")

        # ----------------------------------------------------
        # Administration
        # ----------------------------------------------------

        reviewed_by = form_value(
            "reviewedBy"
        )

        admission_status = form_value(
            "admissionStatus"
        )

        print("Full Name:", full_name)
        print("DOB:", dob)
        print("Mobile:", mobile)
        print("Course:", course_name)
        print("Status:", admission_status)

        # ====================================================
        # VALIDATION
        # ====================================================

        if not full_name:

            flash(
                "Student name is required.",
                "danger"
            )

            return render_template(
                "edit_student.html",
                student=student
            )

        # ====================================================
        # DOB
        # ====================================================

        dob_value = None

        if dob:

            try:

                dob_value = datetime.strptime(
                    dob,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid date of birth.",
                    "danger"
                )

                return render_template(
                    "edit_student.html",
                    student=student
                )

        # ====================================================
        # PASSING YEAR
        # ====================================================

        passing_year_value = None

        if passing_year:

            try:

                passing_year_value = int(
                    passing_year
                )

            except ValueError:

                flash(
                    "Passing year must be a valid number.",
                    "danger"
                )

                return render_template(
                    "edit_student.html",
                    student=student
                )

        # ====================================================
        # GUARDIAN INCOME
        # ====================================================

        guardian_income_value = None

        if guardian_income:

            try:

                guardian_income_value = float(
                    guardian_income
                )

            except ValueError:

                flash(
                    "Guardian income must be a valid number.",
                    "danger"
                )

                return render_template(
                    "edit_student.html",
                    student=student
                )

        # ====================================================
        # SIGNATURE DATE
        # ====================================================

        signature_date_value = None

        if signature_date:

            try:

                signature_date_value = datetime.strptime(
                    signature_date,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid signature date.",
                    "danger"
                )

                return render_template(
                    "edit_student.html",
                    student=student
                )

        # ====================================================
        # PHOTO
        # ====================================================

        photo_value = student.get("PhotoBase64")

        captured_photo = request.form.get(
            "capturedPhoto",
            ""
        ).strip()

        if captured_photo:

            try:

                # Remove:
                # data:image/jpeg;base64,
                # data:image/png;base64,

                if "," in captured_photo:

                    captured_photo = (
                        captured_photo
                        .split(",", 1)[1]
                    )

                photo_value = base64.b64decode(
                    captured_photo
                )

                print(
                    "New photo received:",
                    len(photo_value),
                    "bytes"
                )

            except (
                ValueError,
                binascii.Error
            ):

                flash(
                    "Invalid photo data.",
                    "danger"
                )

                return render_template(
                    "edit_student.html",
                    student=student
                )

        # ====================================================
        # UPDATE SQL
        # ====================================================

        update_sql = """

            UPDATE tbl_student_admision

            SET

                FullName = %(full_name)s,
                DOB = %(dob)s,
                Nationality = %(nationality)s,
                GovernmentId = %(government_id)s,
                Gender = %(gender)s,
                BloodGroup = %(blood_group)s,
                Category = %(category)s,
                Email = %(email)s,
                Mobile = %(mobile)s,

                FatherName = %(father_name)s,
                FatherMobile = %(father_mobile)s,

                MotherName = %(mother_name)s,
                MotherMobile = %(mother_mobile)s,

                GuardianName = %(guardian_name)s,
                GuardianMobile = %(guardian_mobile)s,

                FatherOccupation = %(father_occupation)s,
                MotherOccupation = %(mother_occupation)s,
                GuardianIncome = %(guardian_income)s,

                PermanentAddress = %(permanent_address)s,
                CurrentAddress = %(current_address)s,

                City = %(city)s,
                State = %(state)s,
                PinCode = %(pin_code)s,

                HighestQualification = %(highest_qualification)s,
                BoardUniversity = %(board_university)s,
                SchoolCollege = %(school_college)s,
                PassingYear = %(passing_year)s,
                PercentageCgpa = %(percentage_cgpa)s,
                Medium = %(medium)s,

                CourseName = %(course_name)s,
                PreferredBatch = %(preferred_batch)s,
                StudyMode = %(study_mode)s,

                DocumentsPath = %(documents_path)s,

                MedicalConditions = %(medical_conditions)s,
                EmergencyName = %(emergency_name)s,
                EmergencyNumber = %(emergency_number)s,

                ApplicantSignature = %(applicant_signature)s,
                SignatureDate = %(signature_date)s,
                Place = %(place)s,

                ReviewedBy = %(reviewed_by)s,
                AdmissionStatus = %(admission_status)s,

                PhotoBase64 = %(photo)s

            WHERE AdmissionNo = %(admission_no)s

        """

        params = {

            "full_name": full_name,
            "dob": dob_value,
            "nationality": nationality,
            "government_id": government_id,
            "gender": gender,
            "blood_group": blood_group,
            "category": category,
            "email": email,
            "mobile": mobile,

            "father_name": father_name,
            "father_mobile": father_mobile,

            "mother_name": mother_name,
            "mother_mobile": mother_mobile,

            "guardian_name": guardian_name,
            "guardian_mobile": guardian_mobile,

            "father_occupation": father_occupation,
            "mother_occupation": mother_occupation,
            "guardian_income": guardian_income_value,

            "permanent_address": permanent_address,
            "current_address": current_address,

            "city": city,
            "state": state,
            "pin_code": pin_code,

            "highest_qualification": highest_qualification,
            "board_university": board_university,
            "school_college": school_college,
            "passing_year": passing_year_value,
            "percentage_cgpa": percentage_cgpa,
            "medium": medium,

            "course_name": course_name,
            "preferred_batch": preferred_batch,
            "study_mode": study_mode,

            "documents_path": documents_path,

            "medical_conditions": medical_conditions,
            "emergency_name": emergency_name,
            "emergency_number": emergency_number,

            "applicant_signature": applicant_signature,
            "signature_date": signature_date_value,
            "place": place,

            "reviewed_by": reviewed_by,
            "admission_status": admission_status,

            "photo": photo_value,

            "admission_no": admission_no
        }

        # ====================================================
        # DEBUG
        # ====================================================

        print()
        print("=" * 60)
        print("EXECUTING UPDATE")
        print("=" * 60)
        print("Admission No:", admission_no)
        print("Student Name:", full_name)
        print("Parameters:", len(params))
        print("=" * 60)

        # ====================================================
        # VERIFY RECORD BEFORE UPDATE
        # ====================================================

        verify_sql = """

            SELECT
                AdmissionNo,
                FullName

            FROM tbl_student_admision

            WHERE AdmissionNo = ?

        """

        cursor.execute(
            verify_sql,
            (admission_no,)
        )

        verify_row = cursor.fetchone()

        if not verify_row:

            connection.rollback()

            flash(
                f"Student with Admission No {admission_no} was not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "student_listing.student_list"
                )
            )

        print(
            "Existing student:",
            verify_row
        )

        # ====================================================
        # EXECUTE UPDATE
        # ====================================================

        cursor.execute(
            update_sql,
            params
        )

        affected_rows = cursor.rowcount

        print(
            "Rows affected:",
            affected_rows
        )

        # ====================================================
        # CHECK UPDATE
        # ====================================================

        if affected_rows == 0:

            connection.rollback()

            flash(
                "No student record was updated. Please verify Admission No.",
                "warning"
            )

            return render_template(
                "edit_student.html",
                student=student
            )

        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()

        print(
            "Database COMMIT successful."
        )

        # ====================================================
        # VERIFY AFTER UPDATE
        # ====================================================

        cursor.execute(
            """
                SELECT
                    AdmissionNo,
                    FullName,
                    Mobile,
                    CourseName,
                    AdmissionStatus

                FROM tbl_student_admision

                WHERE AdmissionNo = ?
            """,
            (admission_no,)
        )

        updated_row = cursor.fetchone()

        print()
        print("=" * 60)
        print("AFTER UPDATE")
        print("=" * 60)
        print("Updated row:", updated_row)
        print("=" * 60)
        print()

        if not updated_row:

            flash(
                "Update was committed but record could not be verified.",
                "warning"
            )

        else:

            flash(
                "Student details updated successfully.",
                "success"
            )

        # ====================================================
        # AJAX RESPONSE
        # ====================================================

        if (
            request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest"
        ):

            return jsonify({
                "success": True,
                "message": "Student details updated successfully.",
                "admission_no": admission_no
            })

        # ====================================================
        # NORMAL REDIRECT
        # ====================================================

        return redirect(
            url_for(
                "student_listing.view_student",
                admission_no=admission_no
            )
        )

    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        if connection:

            try:
                connection.rollback()
            except Exception:
                pass

        print()
        print("=" * 60)
        print("ERROR IN edit_student()")
        print("=" * 60)
        print("Admission No:", admission_no)
        print("ERROR:", str(e))
        print("=" * 60)

        traceback.print_exc()

        # ----------------------------------------------------
        # AJAX
        # ----------------------------------------------------

        if (
            request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest"
        ):

            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

        # ----------------------------------------------------
        # Normal request
        # ----------------------------------------------------

        flash(
            f"Unable to update student: {str(e)}",
            "danger"
        )

        return render_template(
            "edit_student.html",
            student=student
        )

    # ========================================================
    # CLOSE CONNECTION
    # ========================================================

    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass

        try:

            if connection:
                connection.close()

        except Exception:
            pass


# ============================================================
# STUDENT LIST
# ============================================================

@student_listing.route(
    "/students",
    methods=["GET"]
)
def student_list():

    connection = None
    cursor = None

    try:

        connection = get_sql_server_connection()
        cursor = connection.cursor()

        sql = """

            SELECT

                AdmissionNo,
                FullName,
                DOB,
                Mobile,
                Email,
                CourseName,
                AdmissionStatus,
                Photo

            FROM tbl_student_admision

            ORDER BY AdmissionNo DESC

        """

        cursor.execute(sql)

        rows = cursor.fetchall()

        columns = [
            "AdmissionNo",
            "FullName",
            "DOB",
            "Mobile",
            "Email",
            "CourseName",
            "AdmissionStatus",
            "Photo"
        ]

        students = []

        for row in rows:

            student = dict(
                zip(
                    columns,
                    row
                )
            )

            student["PhotoBase64"] = photo_to_base64(
                student.get("Photo")
            )

            students.append(
                student
            )

        return render_template(
            "student_listing.html",
            students=students
        )

    except Exception as e:

        if connection:

            try:
                connection.rollback()
            except Exception:
                pass

        print()
        print("=" * 60)
        print("ERROR IN student_list()")
        print("=" * 60)
        print(str(e))
        print("=" * 60)

        traceback.print_exc()

        flash(
            f"Unable to load students: {str(e)}",
            "danger"
        )

        return render_template(
            "student_listing.html",
            students=[]
        )

    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass

        try:

            if connection:
                connection.close()

        except Exception:
            pass


# ============================================================
# VIEW STUDENT
# ============================================================
# This route is included because edit_student() redirects to it.
# If you already have a separate view_student() route, you can
# remove this section and keep your existing route.
# ============================================================

@student_listing.route(
    "/student/<admission_no>",
    methods=["GET"]
)
def view_student(admission_no):

    connection = None
    cursor = None

    try:

        connection = get_sql_server_connection()
        cursor = connection.cursor()

        sql = """

            SELECT
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

                ApplicantSignature,
                SignatureDate,
                Place,

                ReviewedBy,
                AdmissionStatus,

                Photo

            FROM tbl_student_admision

            WHERE AdmissionNo = ?

        """

        cursor.execute(
            sql,
            (admission_no,)
        )

        row = cursor.fetchone()

        if not row:

            flash(
                "Student record not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "student_listing.student_list"
                )
            )

        columns = [

            "AdmissionNo",
            "FullName",
            "DOB",
            "Nationality",
            "GovernmentId",
            "Gender",
            "BloodGroup",
            "Category",
            "Email",
            "Mobile",

            "FatherName",
            "FatherMobile",
            "MotherName",
            "MotherMobile",
            "GuardianName",
            "GuardianMobile",

            "FatherOccupation",
            "MotherOccupation",
            "GuardianIncome",

            "PermanentAddress",
            "CurrentAddress",
            "City",
            "State",
            "PinCode",

            "HighestQualification",
            "BoardUniversity",
            "SchoolCollege",
            "PassingYear",
            "PercentageCgpa",
            "Medium",

            "CourseName",
            "PreferredBatch",
            "StudyMode",

            "DocumentsPath",

            "MedicalConditions",
            "EmergencyName",
            "EmergencyNumber",

            "ApplicantSignature",
            "SignatureDate",
            "Place",

            "ReviewedBy",
            "AdmissionStatus",

            "Photo"
        ]

        student = dict(
            zip(
                columns,
                row
            )
        )

        student["PhotoBase64"] = photo_to_base64(
            student.get("Photo")
        )

        return render_template(
            "view_student.html",
            student=student
        )

    except Exception as e:

        if connection:

            try:
                connection.rollback()
            except Exception:
                pass

        traceback.print_exc()

        flash(
            f"Unable to load student: {str(e)}",
            "danger"
        )

        return redirect(
            url_for(
                "student_listing.student_list"
            )
        )

    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass

        try:

            if connection:
                connection.close()

        except Exception:
            pass