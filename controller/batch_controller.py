from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from config import get_db_connection
from datetime import datetime, timedelta, time


# ==========================================================
# BATCH BLUEPRINT
# ==========================================================

batch_bp = Blueprint(
    'batch',
    __name__,
    url_prefix='/admin/batches'
)


# ==========================================================
# BATCH LIST
# URL:
# /admin/batches/
# ==========================================================

@batch_bp.route('/')
def batch_list():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        # --------------------------------------------------
        # GET ALL BATCHES + STUDENT COUNT
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                b.id,
                b.batch_code,
                b.batch_name,
                b.course_name,
                b.day_of_week,
                b.start_time,
                b.end_time,
                b.status,
                b.created_at,

                COUNT(
                    CASE
                        WHEN bs.status = 'ACTIVE'
                        THEN bs.id
                    END
                ) AS student_count

            FROM batches b

            LEFT JOIN batch_students bs
                ON bs.batch_id = b.id

            GROUP BY
                b.id,
                b.batch_code,
                b.batch_name,
                b.course_name,
                b.day_of_week,
                b.start_time,
                b.end_time,
                b.status,
                b.created_at

            ORDER BY
                FIELD(
                    b.day_of_week,
                    'Monday',
                    'Tuesday',
                    'Wednesday',
                    'Thursday',
                    'Friday',
                    'Saturday',
                    'Sunday'
                ),
                b.start_time
        """)

        batches = cursor.fetchall()

        print("======================================")
        print("BATCH LIST")
        print("TOTAL BATCHES =", len(batches))
        print("BATCH DATA =", batches)
        print("======================================")

        return render_template(
            'batch_list.html',
            batches=batches
        )

    except Exception as e:

        print("======================================")
        print("BATCH LIST ERROR =", e)
        print("======================================")

        flash(
            f"Unable to load batches: {str(e)}",
            "error"
        )

        return render_template(
            'batch_list.html',
            batches=[]
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==========================================================
# CREATE BATCH PAGE
# URL:
# /admin/batches/create
# ==========================================================

@batch_bp.route('/create', methods=['GET'])
def create_batch():

    return render_template(
        'batch_create.html'
    )


# ==========================================================
# SAVE NEW BATCH
# URL:
# /admin/batches/create
# METHOD:
# POST
# ==========================================================

@batch_bp.route('/create', methods=['POST'])
def save_batch():

    conn = None
    cursor = None

    try:

        # --------------------------------------------------
        # GET FORM DATA
        # --------------------------------------------------

        batch_code = request.form.get(
            'batch_code',
            ''
        ).strip()

        batch_name = request.form.get(
            'batch_name',
            ''
        ).strip()

        course_name = request.form.get(
            'course_name',
            ''
        ).strip()

        day_of_week = request.form.get(
            'day_of_week',
            ''
        ).strip()

        start_time = request.form.get(
            'start_time',
            ''
        ).strip()

        end_time = request.form.get(
            'end_time',
            ''
        ).strip()

        status = request.form.get(
            'status',
            'ACTIVE'
        ).strip().upper()


        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if not batch_code:

            flash(
                "Batch Code is required.",
                "error"
            )

            return redirect(
                url_for('batch.create_batch')
            )


        if not batch_name:

            flash(
                "Batch Name is required.",
                "error"
            )

            return redirect(
                url_for('batch.create_batch')
            )


        if not course_name:

            flash(
                "Course Name is required.",
                "error"
            )

            return redirect(
                url_for('batch.create_batch')
            )


        if not day_of_week:

            flash(
                "Please select a day.",
                "error"
            )

            return redirect(
                url_for('batch.create_batch')
            )


        if not start_time:

            flash(
                "Start Time is required.",
                "error"
            )

            return redirect(
                url_for('batch.create_batch')
            )


        if not end_time:

            flash(
                "End Time is required.",
                "error"
            )

            return redirect(
                url_for('batch.create_batch')
            )


        # --------------------------------------------------
        # DATABASE
        # --------------------------------------------------

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)


        # --------------------------------------------------
        # CHECK DUPLICATE BATCH CODE
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM batches
            WHERE batch_code = %s
            """,
            (batch_code,)
        )

        existing_batch = cursor.fetchone()


        if existing_batch:

            flash(
                f"Batch Code '{batch_code}' already exists.",
                "error"
            )

            return redirect(
                url_for('batch.create_batch')
            )


        # --------------------------------------------------
        # INSERT BATCH
        # --------------------------------------------------

        cursor.execute(
            """
            INSERT INTO batches
            (
                batch_code,
                batch_name,
                course_name,
                day_of_week,
                start_time,
                end_time,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                batch_code,
                batch_name,
                course_name,
                day_of_week,
                start_time,
                end_time,
                status
            )
        )


        conn.commit()


        new_batch_id = cursor.lastrowid


        print("======================================")
        print("BATCH CREATED")
        print("BATCH ID =", new_batch_id)
        print("BATCH CODE =", batch_code)
        print("======================================")


        flash(
            f"Batch '{batch_code}' created successfully.",
            "success"
        )


        return redirect(
            url_for('batch.batch_list')
        )


    except Exception as e:

        if conn:
            conn.rollback()


        print("======================================")
        print("CREATE BATCH ERROR =", e)
        print("======================================")


        flash(
            f"Unable to create batch: {str(e)}",
            "error"
        )


        return redirect(
            url_for('batch.create_batch')
        )


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==========================================================
# VIEW BATCH
# ==========================================================

@batch_bp.route('/view/<int:batch_id>')
def view_batch(batch_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        # ==================================================
        # GET BATCH INFORMATION
        # ==================================================

        cursor.execute(
            """
            SELECT
                b.id,
                b.batch_code,
                b.batch_name,
                b.course_name,
                b.day_of_week,
                b.start_time,
                b.end_time,
                b.status,
                b.created_at

            FROM batches b

            WHERE b.id = %s
            """,
            (batch_id,)
        )

        batch = cursor.fetchone()

        # ==================================================
        # BATCH NOT FOUND
        # ==================================================

        if not batch:

            flash(
                "Batch not found.",
                "error"
            )

            return redirect(
                url_for('batch.batch_list')
            )

        # ==================================================
        # GET STUDENTS ASSIGNED TO THIS BATCH
        # ==================================================

        cursor.execute(
            """
            SELECT

                bs.id AS assignment_id,

                bs.batch_id,

                bs.student_id,

                bs.assigned_at,

                bs.status AS assignment_status,

                u.id AS user_id,

                u.name,

                u.userid

            FROM batch_students bs

            INNER JOIN users u
                ON u.id = bs.student_id

            WHERE bs.batch_id = %s

            AND bs.status = 'ACTIVE'

            ORDER BY
                u.name ASC
            """,
            (batch_id,)
        )

        students = cursor.fetchall()

        # ==================================================
        # GET ALL STUDENTS
        #
        # Only users whose role = STUDENT
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                name,
                userid

            FROM users

            WHERE role = 'STUDENT'

            ORDER BY
                name ASC
            """
        )

        all_students = cursor.fetchall()

        # ==================================================
        # REMOVE STUDENTS ALREADY ASSIGNED TO THIS BATCH
        # FROM DROPDOWN
        # ==================================================

        assigned_student_ids = {
            student['student_id']
            for student in students
        }

        available_students = [
            student
            for student in all_students
            if student['id'] not in assigned_student_ids
        ]

        # ==================================================
        # STUDENT COUNT
        # ==================================================

        student_count = len(students)

        # ==================================================
        # DEBUG
        # ==================================================

        print("==========================================")
        print("VIEW BATCH")
        print("==========================================")

        print("BATCH ID       =", batch_id)

        print("BATCH          =", batch)

        print("STUDENTS       =", students)

        print(
            "ALL STUDENTS   =",
            len(all_students)
        )

        print(
            "AVAILABLE      =",
            len(available_students)
        )

        print("==========================================")

        # ==================================================
        # RENDER
        # ==================================================

        return render_template(
            'batch_view.html',

            batch=batch,

            students=students,

            all_students=all_students,

            available_students=available_students,

            student_count=student_count
        )

    # ======================================================
    # ERROR
    # ======================================================

    except Exception as e:

        print("==========================================")
        print("VIEW BATCH ERROR")
        print("==========================================")

        print(str(e))

        print("==========================================")

        flash(
            f"Unable to view batch: {str(e)}",
            "error"
        )

        return redirect(
            url_for('batch.batch_list')
        )

    # ======================================================
    # CLOSE CONNECTION
    # ======================================================

    finally:

        if cursor:

            cursor.close()

        if conn:

            conn.close()


# ==========================================================
# EDIT BATCH
# ==========================================================

@batch_bp.route(
    '/edit/<int:batch_id>',
    methods=['GET', 'POST']
)
def edit_batch(batch_id):

    conn = None
    cursor = None

    try:

        # ==================================================
        # DATABASE CONNECTION
        # ==================================================

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        # ==================================================
        # GET CURRENT BATCH
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                batch_code,
                batch_name,
                course_name,
                day_of_week,
                start_time,
                end_time,
                status

            FROM batches

            WHERE id = %s
            """,
            (batch_id,)
        )

        batch = cursor.fetchone()

        # ==================================================
        # BATCH NOT FOUND
        # ==================================================

        if not batch:

            flash(
                "Batch not found.",
                "error"
            )

            return redirect(
                url_for('batch.batch_list')
            )

        # ==================================================
        # POST - UPDATE BATCH
        # ==================================================

        if request.method == 'POST':

            # ----------------------------------------------
            # FORM DATA
            # ----------------------------------------------

            batch_code = request.form.get(
                'batch_code',
                ''
            ).strip()

            batch_name = request.form.get(
                'batch_name',
                ''
            ).strip()

            course_name = request.form.get(
                'course_name',
                ''
            ).strip()

            day_of_week = request.form.get(
                'day_of_week',
                ''
            ).strip()

            start_time = request.form.get(
                'start_time',
                ''
            ).strip()

            end_time = request.form.get(
                'end_time',
                ''
            ).strip()

            status = request.form.get(
                'status',
                'ACTIVE'
            ).strip()

            # ----------------------------------------------
            # VALIDATION
            # ----------------------------------------------

            if not batch_code:

                flash(
                    "Batch code is required.",
                    "error"
                )

                return render_template(
                    'batch_edit.html',
                    batch=batch
                )

            if not batch_name:

                flash(
                    "Batch name is required.",
                    "error"
                )

                return render_template(
                    'batch_edit.html',
                    batch=batch
                )

            if not day_of_week:

                flash(
                    "Please select a class day.",
                    "error"
                )

                return render_template(
                    'batch_edit.html',
                    batch=batch
                )

            if not start_time:

                flash(
                    "Start time is required.",
                    "error"
                )

                return render_template(
                    'batch_edit.html',
                    batch=batch
                )

            if not end_time:

                flash(
                    "End time is required.",
                    "error"
                )

                return render_template(
                    'batch_edit.html',
                    batch=batch
                )

            # ----------------------------------------------
            # CHECK START / END TIME
            # ----------------------------------------------

            try:

                start_obj = datetime.strptime(
                    start_time,
                    "%H:%M"
                ).time()

                end_obj = datetime.strptime(
                    end_time,
                    "%H:%M"
                ).time()

                if start_obj >= end_obj:

                    flash(
                        "End time must be later than start time.",
                        "error"
                    )

                    return render_template(
                        'batch_edit.html',
                        batch=batch
                    )

            except ValueError:

                flash(
                    "Invalid time format.",
                    "error"
                )

                return render_template(
                    'batch_edit.html',
                    batch=batch
                )

            # ----------------------------------------------
            # CHECK DUPLICATE BATCH CODE
            # ----------------------------------------------

            cursor.execute(
                """
                SELECT id

                FROM batches

                WHERE batch_code = %s
                AND id != %s

                LIMIT 1
                """,
                (
                    batch_code,
                    batch_id
                )
            )

            duplicate = cursor.fetchone()

            if duplicate:

                flash(
                    "This batch code already exists.",
                    "error"
                )

                return render_template(
                    'batch_edit.html',
                    batch=batch
                )

            # ----------------------------------------------
            # UPDATE BATCH
            # ----------------------------------------------

            cursor.execute(
                """
                UPDATE batches

                SET
                    batch_code = %s,
                    batch_name = %s,
                    course_name = %s,
                    day_of_week = %s,
                    start_time = %s,
                    end_time = %s,
                    status = %s

                WHERE id = %s
                """,
                (
                    batch_code,
                    batch_name,
                    course_name,
                    day_of_week,
                    start_time,
                    end_time,
                    status,
                    batch_id
                )
            )

            conn.commit()

            flash(
                "Batch updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    'batch.batch_list'
                )
            )

        # ==================================================
        # GET - PREPARE DATA FOR EDIT PAGE
        # ==================================================

        batch['start_time'] = format_time_for_input(
            batch.get('start_time')
        )

        batch['end_time'] = format_time_for_input(
            batch.get('end_time')
        )

        # ==================================================
        # SHOW EDIT PAGE
        # ==================================================

        return render_template(
            'batch_edit.html',
            batch=batch
        )

    # ======================================================
    # ERROR
    # ======================================================

    except Exception as e:

        if conn:

            conn.rollback()

        print("")
        print("==========================================")
        print("EDIT BATCH ERROR")
        print("==========================================")
        print("Batch ID :", batch_id)
        print("Error    :", str(e))
        print("==========================================")
        print("")

        flash(
            f"Unable to edit batch: {str(e)}",
            "error"
        )

        return redirect(
            url_for(
                'batch.batch_list'
            )
        )

    # ======================================================
    # CLOSE
    # ======================================================

    finally:

        if cursor:

            cursor.close()

        if conn:

            conn.close()


# ==========================================================
# DELETE BATCH
# URL:
# /admin/batches/delete/<batch_id>
# ==========================================================

@batch_bp.route(
    '/delete/<int:batch_id>',
    methods=['POST']
)
def delete_batch(batch_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)


        # --------------------------------------------------
        # CHECK BATCH
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT
                batch_code
            FROM batches
            WHERE id = %s
            """,
            (batch_id,)
        )

        batch = cursor.fetchone()


        if not batch:

            flash(
                "Batch not found.",
                "error"
            )

            return redirect(
                url_for('batch.batch_list')
            )


        # --------------------------------------------------
        # DELETE
        #
        # batch_students will automatically delete
        # if FOREIGN KEY uses ON DELETE CASCADE
        # --------------------------------------------------

        cursor.execute(
            """
            DELETE FROM batches
            WHERE id = %s
            """,
            (batch_id,)
        )


        conn.commit()


        flash(
            f"Batch '{batch['batch_code']}' deleted successfully.",
            "success"
        )


        return redirect(
            url_for('batch.batch_list')
        )


    except Exception as e:

        if conn:
            conn.rollback()


        print("======================================")
        print("DELETE BATCH ERROR =", e)
        print("======================================")


        flash(
            f"Unable to delete batch: {str(e)}",
            "error"
        )


        return redirect(
            url_for('batch.batch_list')
        )


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==========================================================
# ADD STUDENT TO BATCH
# ==========================================================

@batch_bp.route(
    '/<int:batch_id>/add-student',
    methods=['POST']
)
def add_student(batch_id):

    conn = None
    cursor = None

    try:

        # ==================================================
        # GET STUDENT ID
        # ==================================================

        student_id = request.form.get('student_id')

        if not student_id:

            flash(
                "Please select a student.",
                "error"
            )

            return redirect(
                url_for(
                    'batch.view_batch',
                    batch_id=batch_id
                )
            )

        # ==================================================
        # DATABASE CONNECTION
        # ==================================================

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        # ==================================================
        # CHECK BATCH
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                batch_code,
                batch_name,
                course_name,
                day_of_week,
                start_time,
                end_time,
                status

            FROM batches

            WHERE id = %s
            """,
            (batch_id,)
        )

        batch = cursor.fetchone()

        if not batch:

            flash(
                "Batch not found.",
                "error"
            )

            return redirect(
                url_for('batch.batch_list')
            )

        # ==================================================
        # CHECK STUDENT
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                name,
                userid,
                role

            FROM users

            WHERE id = %s
            AND role = 'STUDENT'
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for(
                    'batch.view_batch',
                    batch_id=batch_id
                )
            )

        # ==================================================
        # CHECK WHETHER ALREADY ASSIGNED
        # ==================================================

        cursor.execute(
            """
            SELECT
                id,
                status

            FROM batch_students

            WHERE batch_id = %s
            AND student_id = %s
            """,
            (
                batch_id,
                student_id
            )
        )

        existing = cursor.fetchone()

        # ==================================================
        # IF ALREADY EXISTS
        # ==================================================

        if existing:

            # ----------------------------------------------
            # Already Active
            # ----------------------------------------------

            if existing['status'] == 'ACTIVE':

                flash(
                    f"{student['name']} is already assigned to this batch.",
                    "error"
                )

            # ----------------------------------------------
            # Previously Removed
            # ----------------------------------------------

            else:

                cursor.execute(
                    """
                    UPDATE batch_students

                    SET
                        status = 'ACTIVE',
                        assigned_date = CURRENT_DATE,
                        assigned_at = CURRENT_TIMESTAMP

                    WHERE id = %s
                    """,
                    (
                        existing['id'],
                    )
                )

                conn.commit()

                flash(
                    f"{student['name']} assigned to the batch again.",
                    "success"
                )

        # ==================================================
        # NEW STUDENT ASSIGNMENT
        # ==================================================

        else:

            cursor.execute(
                """
                INSERT INTO batch_students
                (
                    batch_id,
                    student_id,
                    assigned_date,
                    assigned_at,
                    status
                )

                VALUES
                (
                    %s,
                    %s,
                    CURRENT_DATE,
                    CURRENT_TIMESTAMP,
                    'ACTIVE'
                )
                """,
                (
                    batch_id,
                    student_id
                )
            )

            conn.commit()

            flash(
                f"{student['name']} assigned to {batch['batch_code']} successfully.",
                "success"
            )

        # ==================================================
        # RETURN TO BATCH VIEW
        # ==================================================

        return redirect(
            url_for(
                'batch.view_batch',
                batch_id=batch_id
            )
        )

    # ======================================================
    # DATABASE / OTHER ERROR
    # ======================================================

    except Exception as e:

        if conn:

            conn.rollback()

        print("")
        print("==========================================")
        print("ADD STUDENT TO BATCH ERROR")
        print("==========================================")
        print("Batch ID   :", batch_id)
        print("Student ID :", request.form.get('student_id'))
        print("ERROR      :", str(e))
        print("==========================================")
        print("")

        flash(
            f"Unable to add student: {str(e)}",
            "error"
        )

        return redirect(
            url_for(
                'batch.view_batch',
                batch_id=batch_id
            )
        )

    # ======================================================
    # CLOSE DATABASE
    # ======================================================

    finally:

        if cursor:

            cursor.close()

        if conn:

            conn.close()


# ==========================================================
# REMOVE STUDENT FROM BATCH
# ==========================================================

@batch_bp.route(
    '/<int:batch_id>/remove-student/<int:assignment_id>',
    methods=['POST']
)
def remove_student(
    batch_id,
    assignment_id
):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE batch_students

            SET status = 'INACTIVE'

            WHERE id = %s
            AND batch_id = %s
            """,
            (
                assignment_id,
                batch_id
            )
        )


        conn.commit()


        flash(
            "Student removed from this batch.",
            "success"
        )


        return redirect(
            url_for(
                'batch.view_batch',
                batch_id=batch_id
            )
        )


    except Exception as e:

        if conn:
            conn.rollback()


        print(
            "REMOVE STUDENT ERROR =",
            e
        )


        flash(
            f"Unable to remove student: {str(e)}",
            "error"
        )


        return redirect(
            url_for(
                'batch.view_batch',
                batch_id=batch_id
            )
        )


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==========================================================
# FORMAT MYSQL TIME
# ==========================================================

def format_time_for_input(value):

    if value is None:
        return ""

    # ------------------------------------------
    # Python datetime.time
    # ------------------------------------------

    if isinstance(value, time):
        return value.strftime("%H:%M")

    # ------------------------------------------
    # Python timedelta
    # MySQL TIME often comes as timedelta
    # ------------------------------------------

    if isinstance(value, timedelta):

        total_seconds = int(value.total_seconds())

        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60

        return f"{hours:02d}:{minutes:02d}"

    # ------------------------------------------
    # String
    # ------------------------------------------

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return ""

        # 10:00:00
        if len(value) >= 5:
            return value[:5]

        return value

    return ""


@batch_bp.route('/student/<int:enrollment_id>/schedule')
def student_batch_schedule(enrollment_id):

    db = None
    cursor = None

    try:

        # =====================================================
        # DATABASE CONNECTION
        # =====================================================

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # =====================================================
        # STEP 1
        # FIND STUDENT USING ENROLLMENT ID
        #
        # DO NOT USE users.id HERE
        # =====================================================

        cursor.execute(
            """
            SELECT
                id,
                name,
                userid,
                enrollmentid,
                programcode,
                programname,
                role
            FROM users
            WHERE enrollmentid = %s
              AND role = 'STUDENT'
            LIMIT 1
            """,
            (enrollment_id,)
        )

        student = cursor.fetchone()

        # =====================================================
        # STUDENT NOT FOUND
        # =====================================================

        if not student:

            print()
            print("=" * 70)
            print("STUDENT NOT FOUND")
            print("=" * 70)
            print("Enrollment ID:", enrollment_id)
            print("=" * 70)
            print()

            return jsonify({

                "success": False,

                "message":
                    f"Student not found for Enrollment ID: {enrollment_id}",

                "enrollment_id":
                    enrollment_id

            }), 404

        # =====================================================
        # DEBUG
        # =====================================================

        print()
        print("=" * 70)
        print("STUDENT SCHEDULE REQUEST")
        print("=" * 70)
        print("Enrollment ID:", enrollment_id)
        print("User DB ID:", student.get("id"))
        print("Student Name:", student.get("name"))
        print("User ID:", student.get("userid"))
        print("=" * 70)
        print()

        # =====================================================
        # STEP 2
        # GET ACTIVE BATCHES
        #
        # IMPORTANT:
        #
        # batch_students.student_id
        # contains ENROLLMENT ID
        #
        # Therefore:
        #
        # bs.student_id = users.enrollmentid
        #
        # =====================================================

        cursor.execute(
            """
            SELECT

                b.id AS batch_id,

                b.batch_code,

                b.batch_name,

                b.course_name,

                b.day_of_week,

                TIME_FORMAT(
                    b.start_time,
                    '%h:%i %p'
                ) AS start_time,

                TIME_FORMAT(
                    b.end_time,
                    '%h:%i %p'
                ) AS end_time,

                b.status

            FROM batch_students bs

            INNER JOIN batches b
                ON b.id = bs.batch_id

            WHERE
                bs.student_id = %s

                AND bs.status = 'ACTIVE'

                AND b.status = 'ACTIVE'

            ORDER BY

                CASE
                    WHEN UPPER(TRIM(b.day_of_week)) = 'MONDAY'
                        THEN 1

                    WHEN UPPER(TRIM(b.day_of_week)) = 'TUESDAY'
                        THEN 2

                    WHEN UPPER(TRIM(b.day_of_week)) = 'WEDNESDAY'
                        THEN 3

                    WHEN UPPER(TRIM(b.day_of_week)) = 'THURSDAY'
                        THEN 4

                    WHEN UPPER(TRIM(b.day_of_week)) = 'FRIDAY'
                        THEN 5

                    WHEN UPPER(TRIM(b.day_of_week)) = 'SATURDAY'
                        THEN 6

                    WHEN UPPER(TRIM(b.day_of_week)) = 'SUNDAY'
                        THEN 7

                    ELSE 8
                END,

                b.start_time ASC

            """,
            (student.get("id"),)
        )

        schedules = cursor.fetchall()

        # =====================================================
        # DEBUG BATCH COUNT
        # =====================================================

        print(
            "Active batches found:",
            len(schedules)
        )

        # =====================================================
        # FORMAT SCHEDULE
        # =====================================================

        formatted_schedules = []

        for schedule in schedules:

            day_of_week = (
                str(
                    schedule.get("day_of_week")
                    or "-"
                )
                .strip()
                .upper()
            )

            start_time = (
                schedule.get("start_time")
                or "-"
            )

            end_time = (
                schedule.get("end_time")
                or "-"
            )

            formatted_schedules.append({

                "batch_id":
                    schedule.get("batch_id"),

                "batch_code":
                    schedule.get("batch_code")
                    or "-",

                "batch_name":
                    schedule.get("batch_name")
                    or "-",

                "course_name":
                    schedule.get("course_name")
                    or "-",

                "day_of_week":
                    day_of_week,

                "start_time":
                    start_time,

                "end_time":
                    end_time,

                "class_time":
                    f"{start_time} - {end_time}",

                "status":
                    schedule.get("status")
                    or "ACTIVE"

            })

        # =====================================================
        # FINAL JSON RESPONSE
        # =====================================================

        return jsonify({

            "success": True,

            "student": {

                "id":
                    student.get("id"),

                "name":
                    student.get("name")
                    or "-",

                "userid":
                    student.get("userid")
                    or "-",

                "enrollmentid":
                    student.get("enrollmentid")
                    or "-",

                "programcode":
                    student.get("programcode")
                    or "-",

                "programname":
                    student.get("programname")
                    or "-",

                "role":
                    student.get("role")
                    or "STUDENT"

            },

            "total_batches":
                len(formatted_schedules),

            "schedules":
                formatted_schedules

        })

    # =========================================================
    # ERROR HANDLING
    # =========================================================

    except Exception as e:

        print()
        print("=" * 70)
        print("STUDENT BATCH SCHEDULE ERROR")
        print("=" * 70)
        print("Enrollment ID:", enrollment_id)
        print("Error:", str(e))
        print("=" * 70)
        print()

        return jsonify({

            "success": False,

            "message":
                "Unable to load student schedule.",

            "error":
                str(e),

            "enrollment_id":
                enrollment_id

        }), 500

    # =========================================================
    # CLOSE DATABASE
    # =========================================================

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
