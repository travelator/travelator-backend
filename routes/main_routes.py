from flask import (
    Blueprint,
    request,
    redirect,
    render_template,
    url_for,
    flash,
    session,
)
from app.models import User
from app.database import db_session
from werkzeug.security import generate_password_hash, check_password_hash
import functools

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    # Pass the logged in user to the index template
    return render_template("ENTER HTML FILE HERE")


# ---------- AUTH ROUTES ----------
# Login route
@main_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_address = request.form["email_address"]
        password = request.form["password"]
        error = None
        user = User.query.filter_by(email_address=email_address).first()

        if user is None:
            error = "Invalid email address."
        elif not check_password_hash(
            user.password, password
        ):  # Make this secure
            error = "Invalid password."

        if error is None:
            session.clear()
            session["user_id"] = user.user_id
            session["user_first_name"] = user.first_name
            flash("Login successful!", "success")
            return redirect(url_for("main.index"))

        flash(error, "error")

    return render_template("login.html")


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        family_name = request.form["family_name"]
        email_address = request.form["email_address"]
        password = generate_password_hash(
            request.form["password"], method="pbkdf2"
        )

        u = User(first_name, family_name, email_address, password)

        db_session.add(u)
        db_session.commit()
        return redirect(url_for("main.login"))

    return render_template("signup.html")


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("main.login"))
        return view(**kwargs)

    return wrapped_view


@main_bp.route("/logout")
@login_required  # Only logged-in users can access this route
def logout():
    session.clear()
    return redirect(url_for("main.login"))
