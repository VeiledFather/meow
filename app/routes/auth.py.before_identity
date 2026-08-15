from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, RegistrationProfile, RoleApplication


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(
                url_for("main.dashboard")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template(
        "auth/login.html"
    )


# =========================================================
# CAMPUSHUB REGISTRATION
# =========================================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("main.dashboard")
        )


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        college_id = request.form.get(
            "college_id",
            ""
        ).strip()

        date_of_birth = request.form.get(
            "date_of_birth",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not name or not college_id or not date_of_birth or not email or not password:

            flash(
                "Please complete every required field.",
                "error"
            )

            return render_template(
                "auth/register.html"
            )


        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

            return render_template(
                "auth/register.html"
            )


        # -------------------------------------------------
        # DUPLICATE CHECKS
        # -------------------------------------------------

        existing_user = User.query.filter_by(
            email=email
        ).first()


        if existing_user:

            flash(
                "An account with this email already exists.",
                "error"
            )

            return render_template(
                "auth/register.html"
            )


        existing_college_id = RegistrationProfile.query.filter_by(
            college_id=college_id
        ).first()


        if existing_college_id:

            flash(
                "This college ID is already registered.",
                "error"
            )

            return render_template(
                "auth/register.html"
            )


        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        user = User(

            name=name,

            email=email,

            role="student"

        )


        user.set_password(
            password
        )


        db.session.add(
            user
        )

        db.session.flush()


        # -------------------------------------------------
        # GENERATE CAMPUSHUB ID
        # -------------------------------------------------

        campus_id = (
            "CH-S-"
            + str(user.id).zfill(6)
        )


        profile = RegistrationProfile(

            user_id=user.id,

            college_id=college_id,

            date_of_birth=date_of_birth,

            campus_id=campus_id

        )


        db.session.add(
            profile
        )


        db.session.commit()


        flash(
            f"Registration successful. Your CampusHub ID is {campus_id}.",
            "success"
        )


        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "auth/register.html"
    )



# =========================================================
# ROLE APPLICATION
# =========================================================

@auth_bp.route(
    "/apply-role",
    methods=["GET", "POST"]
)
@login_required
def role_application():

    if current_user.role != "student":
        return "Access denied", 403


    existing_application = RoleApplication.query.filter_by(
        user_id=current_user.id,
        status="pending"
    ).first()


    if request.method == "POST":

        if existing_application:

            flash(
                "You already have a pending role application.",
                "info"
            )

            return redirect(
                url_for("auth.role_application")
            )


        requested_role = request.form.get(
            "requested_role",
            ""
        ).strip().lower()

        cgpa_raw = request.form.get(
            "cgpa",
            ""
        ).strip()

        attendance_raw = request.form.get(
            "attendance",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()


        if requested_role not in (
            "volunteer",
            "organizer"
        ):

            flash(
                "Please select a valid role.",
                "error"
            )

            return render_template(
                "auth/apply_role.html"
            )


        try:

            cgpa = float(cgpa_raw)

        except ValueError:

            flash(
                "Please enter a valid CGPA.",
                "error"
            )

            return render_template(
                "auth/apply_role.html"
            )


        try:

            attendance = float(attendance_raw)

        except ValueError:

            flash(
                "Please enter a valid attendance percentage.",
                "error"
            )

            return render_template(
                "auth/apply_role.html"
            )


        if cgpa < 0 or cgpa > 10:

            flash(
                "CGPA must be between 0 and 10.",
                "error"
            )

            return render_template(
                "auth/apply_role.html"
            )


        if attendance < 0 or attendance > 100:

            flash(
                "Attendance must be between 0 and 100.",
                "error"
            )

            return render_template(
                "auth/apply_role.html"
            )


        application = RoleApplication(

            user_id=current_user.id,

            requested_role=requested_role,

            cgpa=cgpa,

            attendance=attendance,

            message=message,

            status="pending"

        )


        db.session.add(
            application
        )

        db.session.commit()


        flash(
            "Your role application has been submitted for admin review.",
            "success"
        )


        return redirect(
            url_for("auth.role_application")
        )


    applications = RoleApplication.query.filter_by(
        user_id=current_user.id
    ).order_by(
        RoleApplication.created_at.desc()
    ).all()


    return render_template(
        "auth/apply_role.html",
        applications=applications
    )



@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("auth.login")
    )
