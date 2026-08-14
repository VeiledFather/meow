from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from app.models import User


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("auth.dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user is not None:

            if user.check_password(password):

                login_user(user)

                return redirect(
                    url_for("auth.dashboard")
                )

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "student":

        return redirect(
            url_for("auth.student_dashboard")
        )

    if current_user.role == "organizer":

        return redirect(
            url_for("organizer.dashboard")
        )

    if current_user.role == "admin":

        return redirect(
            url_for("auth.admin_dashboard")
        )

    if current_user.role == "volunteer":

        return redirect(
            url_for("auth.volunteer_dashboard")
        )

    return "Unknown role", 403


@auth_bp.route("/student")
@login_required
def student_dashboard():

    return render_template(
        "dashboard/student.html"
    )


@auth_bp.route("/admin")
@login_required
def admin_dashboard():

    return render_template(
        "dashboard/admin.html"
    )


@auth_bp.route("/volunteer")
@login_required
def volunteer_dashboard():

    return render_template(
        "dashboard/volunteer.html"
    )


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("auth.login")
    )
