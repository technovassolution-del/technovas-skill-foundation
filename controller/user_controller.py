
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from models.user_model import create_user
from config import get_db_connection   # 🔥 MUST

user_bp = Blueprint("user", __name__)

@user_bp.route("/user_creation", methods=["GET", "POST"])
def user_creation():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]
        role = request.form["role"]

        password_hash = generate_password_hash(password)

        try:
            create_user(full_name, email, mobile, password_hash, role)
            flash("User Registered Successfully!", "success")
            return redirect(url_for("user.register"))

        except Exception as e:
            flash(str(e), "danger")

    return render_template("user_creation.html")

# ------------------Users Fetch--------------------
@user_bp.route('/all_users')
def all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    return render_template('all_users.html', users=users)