import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, RegistrationProfile, RoleApplication, CampusIdentity, PasswordResetToken


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    if request.method == "GET":
        return render_template(
            "auth/login.html"
        )

    # =================================================
    # POST LOGIN
    # =================================================

    identifier = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if not identifier or not password:

        flash(
            "Please enter your email or CampusHub ID and password.",
            "error"
        )

        return render_template(
            "auth/login.html"
        )

    # =================================================
    # DIRECT CAMPUSHUB ID LOGIN
    # =================================================

    campus_id = identifier.upper()

    if campus_id.startswith(
        ("CHS-", "CHV-", "CHO-", "CHC-")
    ):

        identity = CampusIdentity.query.filter_by(
            campus_id=campus_id
        ).first()

        if identity is None:

            flash(
                "CampusHub ID not found.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        if identity.status != "active":

            flash(
                f"{campus_id} is currently suspended or inactive.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        user = db.session.get(
            User,
            identity.user_id
        )

        if user is None:

            flash(
                "The account linked to this identity no longer exists.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        if not user.check_password(password):

            flash(
                "Invalid CampusHub ID or password.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        session["active_identity_id"] = identity.id
        session["active_identity_type"] = identity.identity_type

        login_user(user)

        return _identity_destination(
            identity.identity_type
        )

    # =================================================
    # EMAIL LOGIN
    # =================================================

    email = identifier.lower()

    user = User.query.filter_by(
        email=email
    ).first()

    if user is None or not user.check_password(password):

        flash(
            "Invalid email or password.",
            "error"
        )

        return render_template(
            "auth/login.html"
        )

    identities = (
        CampusIdentity.query
        .filter_by(
            user_id=user.id,
            status="active"
        )
        .order_by(
            CampusIdentity.id.asc()
        )
        .all()
    )

    # =================================================
    # NO ACTIVE IDENTITY
    # =================================================

    if not identities:

        flash(
            "No active CampusHub identity is available for this account.",
            "error"
        )

        return render_template(
            "auth/login.html"
        )

    # =================================================
    # ONE ACTIVE IDENTITY
    # =================================================

    if len(identities) == 1:

        identity = identities[0]

        session["active_identity_id"] = identity.id
        session["active_identity_type"] = identity.identity_type

        login_user(user)

        return _identity_destination(
            identity.identity_type
        )

    # =================================================
    # MULTIPLE ACTIVE IDENTITIES
    # =================================================

    session["pending_identity_user_id"] = user.id

    return render_template(
        "auth/select_identity.html",
        identities=identities,
        user=user
    )



    # =================================================
    # NORMAL GET REQUEST
    # =================================================

    return render_template(
        "auth/login.html"
    )


def _identity_destination(identity_type):

    if identity_type == "student":
        return redirect(
            url_for("main.dashboard")
        )

    if identity_type == "volunteer":
        return redirect(
            url_for("volunteer.dashboard")
        )

    if identity_type == "organizer":
        return redirect(
            url_for("organizer.dashboard")
        )

    if identity_type == "admin":
        return redirect(
            url_for("admin.dashboard")
        )

    return redirect(
        url_for("main.dashboard")
    )


@auth_bp.route(
    "/select-identity/<int:identity_id>",
    methods=["POST"]
)
def select_identity(identity_id):

    pending_user_id = session.get(
        "pending_identity_user_id"
    )

    if not pending_user_id:

        flash(
            "Your login session expired. Please sign in again.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    identity = CampusIdentity.query.filter_by(
        id=identity_id,
        user_id=pending_user_id,
        status="active"
    ).first()

    if identity is None:

        flash(
            "That CampusHub identity is unavailable.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    user = db.session.get(
        User,
        pending_user_id
    )

    if user is None:

        session.pop(
            "pending_identity_user_id",
            None
        )

        flash(
            "Account not found.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    session.pop(
        "pending_identity_user_id",
        None
    )

    session["active_identity_type"] = (
        identity.identity_type
    )

    session["active_identity_id"] = identity.id

    login_user(user)

    return _identity_destination(
        identity.identity_type
    )


@auth_bp.route(
    "/cancel-identity-selection",
    methods=["POST"]
)
def cancel_identity_selection():

    session.pop(
        "pending_identity_user_id",
        None
    )

    return redirect(
        url_for("auth.login")
    )




# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    if request.method == "POST":

        identifier = request.form.get(
            "identifier",
            ""
        ).strip().lower()

        user = None

        # -------------------------------------------------
        # Allow email OR CampusHub ID
        # -------------------------------------------------

        if identifier.upper().startswith(
            ("CHS-", "CHV-", "CHO-", "CHC-")
        ):

            identity = CampusIdentity.query.filter_by(
                campus_id=identifier.upper()
            ).first()

            if identity:
                user = db.session.get(
                    User,
                    identity.user_id
                )

        else:

            user = User.query.filter_by(
                email=identifier
            ).first()

        # -------------------------------------------------
        # Never reveal whether account exists
        # -------------------------------------------------

        if user:

            # Invalidate previous unused tokens
            PasswordResetToken.query.filter_by(
                user_id=user.id,
                used=False
            ).update(
                {"used": True},
                synchronize_session=False
            )

            token = secrets.token_urlsafe(48)

            reset = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(
                    minutes=30
                )
            )

            db.session.add(reset)
            db.session.commit()

            reset_url = url_for(
                "auth.reset_password",
                token=token,
                _external=True
            )

            # Development mode:
            # Print the reset URL to the Flask terminal.
            print()
            print("=" * 70)
            print("CAMPUSHUB PASSWORD RESET LINK")
            print("=" * 70)
            print(reset_url)
            print("=" * 70)
            print()

        flash(
            "If an account exists, a password reset link has been generated.",
            "success"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    return render_template(
        "auth/forgot_password.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    reset = PasswordResetToken.query.filter_by(
        token=token,
        used=False
    ).first()

    if reset is None:

        flash(
            "This password reset link is invalid or has already been used.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    if reset.expires_at < datetime.utcnow():

        reset.used = True
        db.session.commit()

        flash(
            "This password reset link has expired. Please request a new one.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user = db.session.get(
        User,
        reset.user_id
    )

    if user is None:

        reset.used = True
        db.session.commit()

        flash(
            "The account associated with this reset link no longer exists.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

            return render_template(
                "auth/reset_password.html"
            )

        if password != confirm_password:

            flash(
                "The passwords do not match.",
                "error"
            )

            return render_template(
                "auth/reset_password.html"
            )

        user.set_password(password)

        reset.used = True

        # Invalidate every other outstanding reset token.
        PasswordResetToken.query.filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset.id,
            PasswordResetToken.used == False
        ).update(
            {"used": True},
            synchronize_session=False
        )

        db.session.commit()

        flash(
            "Your password has been reset successfully. You can now sign in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html"
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

        # -------------------------------------------------
        # CREATE THE NEW STUDENT IDENTITY
        # -------------------------------------------------

        student_identity = CampusIdentity(
            user_id=user.id,
            campus_id=(
                "CHS-"
                + str(user.id).zfill(6)
            ),
            identity_type="student",
            status="active",
            activated_at=db.func.now()
        )

        db.session.add(
            student_identity
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

    active_identity_id = session.get("active_identity_id")

    active_identity = None

    if active_identity_id:
        active_identity = db.session.get(
            CampusIdentity,
            active_identity_id
        )

    if (
        active_identity is None
        or active_identity.user_id != current_user.id
        or active_identity.identity_type != "student"
        or active_identity.status != "active"
    ):
        return "Student identity required", 403


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
