
from flask import Blueprint, render_template, request, redirect, url_for
from models.question_model import create_question, get_all_questions
from models.exam_model import get_all_exams

question_bp = Blueprint('question', __name__)



@question_bp.route('/add_question')
def add_question():
    exams = get_all_exams()  # 👈 create this function
    return render_template('add_question.html', exams=exams)


@question_bp.route('/save_question', methods=['POST'])
def save_question():
    try:
        exam_id = int(request.form.get("exam_id"))

        marks = request.form.get("marks", 1)
        negative_marks = request.form.get("negative_marks", 0)

        question_data = (
            request.form['question_text'],
            request.form['question_type'],
            request.form['difficulty'],
            request.form['topic'],
            request.form['explanation'],
            1
        )

        options = []
        for i in range(1, 5):
            text = request.form.get(f"option{i}")

            if not text:
                return f"❌ Option {i} missing"

            options.append({
                "text": text,
                "is_correct": 1 if request.form.get("correct") == str(i) else 0,
                "order": i
            })

        result = create_question(question_data, options, exam_id, marks, negative_marks)

        if result:
            return result  # error return

        return "✅ Question Added Successfully"

    except Exception as e:
        return f"❌ MAIN ERROR: {e}"

# -------- Question List --------
@question_bp.route('/questions')
def question_list():
    questions = get_all_questions()
    return render_template("question_list.html", questions=questions)

