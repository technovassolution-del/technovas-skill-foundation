from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
import os

from models.question_model import create_question, get_all_questions
from models.exam_model import get_all_exams, get_exam_by_id


question_bp = Blueprint('question', __name__)


# ============================
# ADD QUESTION PAGE
# ============================

@question_bp.route('/add_question')
def add_question():

    selected_exam_id = request.args.get("exam_id")

    exams = get_all_exams()

    return render_template(
        "add_question.html",
        exams=exams,
        selected_exam_id=selected_exam_id
    )


# ============================
# SAVE QUESTION
# ============================

@question_bp.route('/save_question', methods=["POST"])
def save_question():

    try:
        created_by = session.get('user').get('UserId')
        exam_id = int(request.form.get("exam_id"))

        # Get selected exam
        exam = get_exam_by_id(exam_id)

        if not exam:
            return "❌ Exam not found"


        # =================================
        # OFFLINE EXAM
        # =================================

        if exam["exam_type"] == "offline":

            file = request.files.get("question_file")

            if not file or file.filename == "":
                return "❌ Please upload PDF/Image file"


            # Create upload folder
            upload_folder = "static/question_files"

            os.makedirs(
                upload_folder,
                exist_ok=True
            )


            # Secure filename
            filename = secure_filename(
                file.filename
            )


            filepath = os.path.join(
                upload_folder,
                filename
            )


            # Save file
            file.save(filepath)


            # Store file path in question_text
            question_data = (
                filepath,
                request.form.get("question_type"),
                request.form.get("difficulty"),
                request.form.get("topic"),
                request.form.get("explanation"),
                created_by
            )


            result = create_question(
                question_data,
                [],
                exam_id,
                0,
                0
            )


            if result:
                return result


            return "✅ Offline Question Uploaded Successfully"



        # =================================
        # ONLINE EXAM
        # =================================

        else:

            marks = request.form.get(
                "marks",
                1
            )


            negative_marks = request.form.get(
                "negative_marks",
                0
            )


            question_data = (
                request.form.get("question_text"),
                request.form.get("question_type"),
                request.form.get("difficulty"),
                request.form.get("topic"),
                request.form.get("explanation"),
                created_by
            )


            options = []


            for i in range(1, 5):

                option_text = request.form.get(
                    f"option{i}"
                )


                if not option_text:
                    return f"❌ Option {i} is missing"


                options.append({

                    "text": option_text,

                    "is_correct": 1
                    if request.form.get("correct") == str(i)
                    else 0,

                    "order": i
                })


            result = create_question(
                question_data,
                options,
                exam_id,
                marks,
                negative_marks
            )


            if result:
                return result


            return "✅ Online Question Added Successfully"


    except Exception as e:

        return f"❌ ERROR: {e}"



# ============================
# QUESTION LIST
# ============================

@question_bp.route('/questions')
def question_list():

    questions = get_all_questions()

    return render_template(
        "question_list.html",
        questions=questions
    )