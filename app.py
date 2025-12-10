import os
from flask import Flask, request, redirect, url_for, render_template
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

# ---------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# ---------------------------------------------------------------------
# SQLAlchemy setup
# ---------------------------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------------------------------------------------------------
# Flask-Login setup
# ---------------------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------
class User(db.Model, UserMixin):
    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name  = db.Column(db.String(100), nullable=True)
    last_name   = db.Column(db.String(100), nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login  = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------------------------------------------------
# Init DB *μετά* τα models
# ---------------------------------------------------------------------
def init_db():
    with app.app_context():
        db.create_all()

# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def index():
    year = datetime.now().year
    if current_user.is_authenticated:
        return render_template("index.html", current_year=year, user=current_user)
    return render_template("index.html", current_year=year, user=None)


@app.route("/profile")
@login_required
def profile():
    year = datetime.now().year
    return render_template("profile.html", user=current_user, current_year=year)


@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    error = None
    success = None

    if request.method == "POST":
        first = request.form.get("first_name")
        last = request.form.get("last_name")

        # Update fields
        current_user.first_name = first
        current_user.last_name = last

        try:
            db.session.commit()
            success = "Profile updated successfully."
        except Exception:
            db.session.rollback()
            error = "An error occurred while updating your profile."

    return render_template(
        "edit-profile.html",
        user=current_user,
        error=error,
        success=success
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for("index"))
        else:
            error = "Invalid email or password."

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        if password != password_confirm:
            error = "Passwords do not match."
        elif User.query.filter_by(email=email).first():
            error = "Email is already registered."
        else:
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("index"))

    return render_template("register.html", error=error)


@app.route("/protected")
@login_required
def protected():
    return f"Hello, {current_user.email}! You are logged in!"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)