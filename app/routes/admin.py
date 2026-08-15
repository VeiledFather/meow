
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from flask_login import (
    login_required,
    current_user
)

from app import db
from app.models import (
    Event,
    User,
    Registration,
    Review,
    VolunteerApplication,
    Certificate,
    Notification,
    RoleApplication,
    CampusIdentity,
    RegistrationProfile,
    PasswordResetToken
)

from app.routes.notifications import create_notification


admin_bp = Blueprint(
    "admin",
    __name__
)



# =========================================================
# ADMIN IDENTITY MANAGEMENT
# =========================================================

PERMANENT_DEMO_EMAILS = {
    "admin@campus.com",
    "organizer@campus.com",
    "volunteer@campus.com",
    "student@campus.com",
}



# =========================================================
# COLLEGE ADMINISTRATION — CHC PROVISIONING
# =========================================================

HEAD_ADMIN_EMAIL = "admin@campus.com"


@admin_bp.route(
    "/college-admins/create",
    methods=["GET", "POST"]
)
@login_required
def create_college_admin():

    # -------------------------------------------------
    # ONLY THE PERMANENT HEAD ADMIN MAY CREATE CHC IDs
    # -------------------------------------------------

    if current_user.email.lower() != HEAD_ADMIN_EMAIL:
        return "Access denied", 403

    if request.method == "POST":

        name = request.form.get(
            "name",
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

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not name or not email or not password:

            flash(
                "Name, email and password are required.",
                "error"
            )

            return render_template(
                "admin/create_college_admin.html"
            )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

            return render_template(
                "admin/create_college_admin.html"
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "error"
            )

            return render_template(
                "admin/create_college_admin.html"
            )

        # ---------------------------------------------
        # CREATE USER
        # ---------------------------------------------

        user = User(
            name=name,
            email=email,
            role="admin"
        )

        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        # ---------------------------------------------
        # GENERATE CHC ID
        #
        # Example:
        # CHC-000014
        # ---------------------------------------------

        campus_id = (
            "CHC-"
            + str(user.id).zfill(6)
        )

        identity = CampusIdentity(
            user_id=user.id,
            campus_id=campus_id,
            identity_type="admin",
            status="active",
            activated_at=db.func.now()
        )

        db.session.add(identity)

        db.session.commit()

        flash(
            f"College Administrator created successfully: {campus_id}",
            "success"
        )

        return redirect(
            url_for("admin.users")
        )

    return render_template(
        "admin/create_college_admin.html"
    )

@admin_bp.route(
    "/identities/<int:identity_id>/suspend",
    methods=["POST"]
)
@login_required
def suspend_identity(identity_id):

    if current_user.role != "admin":
        return "Access denied", 403

    identity = db.session.get(
        CampusIdentity,
        identity_id
    )

    if identity is None:
        return "Identity not found", 404

    user = db.session.get(
        User,
        identity.user_id
    )

    if user is None:
        return "User not found", 404

    # -------------------------------------------------
    # PERMANENT DEMO ACCOUNTS CANNOT BE SUSPENDED
    # -------------------------------------------------

    if user.email.lower() in PERMANENT_DEMO_EMAILS:
        flash(
            "Permanent CampusHub demo identities cannot be suspended.",
            "warning"
        )

        return redirect(
            url_for("admin.users")
        )

    # -------------------------------------------------
    # SUSPEND ONLY THIS IDENTITY
    #
    # Other identities belonging to the same user
    # remain intact.
    # -------------------------------------------------

    identity.status = "suspended"
    identity.suspended_at = db.func.now()

    db.session.commit()

    create_notification(
        user_id=user.id,
        title="CampusHub identity suspended",
        message=(
            f"Your {identity.identity_type} identity "
            f"({identity.campus_id}) has been suspended "
            "by college administration."
        ),
        notification_type="identity_suspended"
    )

    flash(
        f"{identity.campus_id} has been suspended.",
        "success"
    )

    return redirect(
        url_for("admin.users")
    )


@admin_bp.route(
    "/identities/<int:identity_id>/activate",
    methods=["POST"]
)
@login_required
def activate_identity(identity_id):

    if current_user.role != "admin":
        return "Access denied", 403

    identity = db.session.get(
        CampusIdentity,
        identity_id
    )

    if identity is None:
        return "Identity not found", 404

    user = db.session.get(
        User,
        identity.user_id
    )

    if user is None:
        return "User not found", 404

    identity.status = "active"
    identity.suspended_at = None

    if identity.activated_at is None:
        identity.activated_at = db.func.now()

    db.session.commit()

    create_notification(
        user_id=user.id,
        title="CampusHub identity activated",
        message=(
            f"Your {identity.identity_type} identity "
            f"({identity.campus_id}) is now active."
        ),
        notification_type="identity_activated"
    )

    flash(
        f"{identity.campus_id} has been activated.",
        "success"
    )

    return redirect(
        url_for("admin.users")
    )

@admin_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "admin":
        return "Access denied", 403

    pending_events = Event.query.filter_by(
        status="pending"
    ).order_by(
        Event.id.desc()
    ).all()

    approved_events = Event.query.filter_by(
        status="approved"
    ).order_by(
        Event.id.desc()
    ).all()

    rejected_events = Event.query.filter_by(
        status="rejected"
    ).order_by(
        Event.id.desc()
    ).all()

    return render_template(
        "admin/dashboard.html",
        pending_events=pending_events,
        approved_events=approved_events,
        rejected_events=rejected_events
    )


@admin_bp.route(
    "/approve/<int:event_id>"
)
@login_required
def approve(event_id):

    if current_user.role != "admin":
        return "Access denied", 403

    event = db.session.get(
        Event,
        event_id
    )

    if event is None:
        return "Event not found", 404

    event.status = "approved"

    db.session.commit()

    flash(
        f'"{event.title}" is now published.',
        "success"
    )

    return redirect(
        url_for("admin.dashboard")
    )


@admin_bp.route(
    "/reject/<int:event_id>"
)
@login_required
def reject(event_id):

    if current_user.role != "admin":
        return "Access denied", 403

    event = db.session.get(
        Event,
        event_id
    )

    if event is None:
        return "Event not found", 404

    event.status = "rejected"

    db.session.commit()

    flash(
        f'"{event.title}" was rejected.',
        "success"
    )

    return redirect(
        url_for("admin.dashboard")
    )


# =========================================================
# EVENT MANAGEMENT
# =========================================================

@admin_bp.route("/events")
@login_required
def events():

    if current_user.role != "admin":
        return "Access denied", 403


    all_events = Event.query.order_by(
        Event.id.desc()
    ).all()


    pending_events = [
        event
        for event in all_events
        if event.status == "pending"
    ]


    approved_events = [
        event
        for event in all_events
        if event.status == "approved"
    ]


    rejected_events = [
        event
        for event in all_events
        if event.status == "rejected"
    ]


    return render_template(
        "admin/events.html",
        all_events=all_events,
        pending_events=pending_events,
        approved_events=approved_events,
        rejected_events=rejected_events
    )



# =========================================================
# CANCEL EVENT
# =========================================================

@admin_bp.route(
    "/cancel/<int:event_id>"
)
@login_required
def cancel(event_id):

    if current_user.role != "admin":
        return "Access denied", 403


    event = db.session.get(
        Event,
        event_id
    )


    if event is None:
        return "Event not found", 404


    if event.status != "approved":

        flash(
            "Only approved events can be cancelled.",
            "error"
        )

        return redirect(
            url_for("admin.events")
        )


    event.status = "cancelled"

    db.session.commit()


    flash(
        f'"{event.title}" has been cancelled.',
        "success"
    )


    return redirect(
        url_for("admin.events")
    )



# =========================================================
# POSTPONE EVENT
# =========================================================

@admin_bp.route(
    "/postpone/<int:event_id>",
    methods=["GET", "POST"]
)
@login_required
def postpone(event_id):

    if current_user.role != "admin":
        return "Access denied", 403


    event = db.session.get(
        Event,
        event_id
    )


    if event is None:
        return "Event not found", 404


    if event.status != "approved":

        flash(
            "Only approved events can be postponed.",
            "error"
        )

        return redirect(
            url_for("admin.events")
        )


    if request.method == "POST":

        new_date = request.form.get(
            "date",
            ""
        ).strip()

        new_start_time = request.form.get(
            "start_time",
            ""
        ).strip()

        new_end_time = request.form.get(
            "end_time",
            ""
        ).strip()


        if not new_date or not new_start_time or not new_end_time:

            flash(
                "Please provide the new date and time.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.postpone",
                    event_id=event.id
                )
            )


        if new_start_time >= new_end_time:

            flash(
                "End time must be after start time.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.postpone",
                    event_id=event.id
                )
            )


        event.date = new_date

        event.start_time = new_start_time

        event.end_time = new_end_time

        event.status = "postponed"


        db.session.commit()


        flash(
            f'"{event.title}" has been postponed.',
            "success"
        )


        return redirect(
            url_for("admin.events")
        )


    return render_template(
        "admin/postpone.html",
        event=event
    )





# =========================================================
# ADMIN PASSWORD RESET
# =========================================================

@admin_bp.route(
    "/users/<int:user_id>/reset-password",
    methods=["GET", "POST"]
)
@login_required
def reset_user_password(user_id):

    if current_user.role != "admin":
        return "Access denied", 403

    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        return "User not found", 404

    # The permanent head administrator cannot have their
    # password changed by another administrator.
    if (
        user.email.lower() == HEAD_ADMIN_EMAIL
        and current_user.email.lower() != HEAD_ADMIN_EMAIL
    ):
        flash(
            "The permanent head administrator account is protected.",
            "warning"
        )

        return redirect(
            url_for("admin.users")
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
                "admin/reset_user_password.html",
                user=user
            )

        if password != confirm_password:

            flash(
                "The passwords do not match.",
                "error"
            )

            return render_template(
                "admin/reset_user_password.html",
                user=user
            )

        user.set_password(password)

        # Invalidate outstanding self-service reset links.
        PasswordResetToken.query.filter_by(
            user_id=user.id,
            used=False
        ).update(
            {"used": True},
            synchronize_session=False
        )

        db.session.commit()

        flash(
            f"Password reset successfully for {user.email}.",
            "success"
        )

        return redirect(
            url_for("admin.users")
        )

    return render_template(
        "admin/reset_user_password.html",
        user=user
    )


# =========================================================
# USER MANAGEMENT
# =========================================================

@admin_bp.route(
    "/users"
)
@login_required
def users():

    if current_user.role != "admin":
        return "Access denied", 403


    all_users = User.query.order_by(
        User.id.desc()
    ).all()


    students = [
        user
        for user in all_users
        if user.role == "student"
    ]


    organizers = [
        user
        for user in all_users
        if user.role == "organizer"
    ]


    volunteers = [
        user
        for user in all_users
        if user.role == "volunteer"
    ]


    admins = [
        user
        for user in all_users
        if user.role == "admin"
    ]


    return render_template(
        "admin/users.html",

        all_users=all_users,

        students=students,

        organizers=organizers,

        volunteers=volunteers,

        admins=admins
    )



# =========================================================
# VENUE MANAGEMENT
# =========================================================

@admin_bp.route(
    "/venues"
)
@login_required
def venues():

    if current_user.role != "admin":
        return "Access denied", 403


    events = Event.query.order_by(
        Event.date.asc(),
        Event.start_time.asc()
    ).all()


    venue_map = {}


    for event in events:

        venue_name = (
            event.venue.strip()
            if event.venue
            else "Unspecified"
        )


        if venue_name not in venue_map:

            venue_map[venue_name] = []


        venue_map[venue_name].append(
            event
        )


    venues = []


    for venue_name, venue_events in venue_map.items():

        venues.append({

            "name":
                venue_name,

            "events":
                venue_events,

            "event_count":
                len(venue_events)

        })


    venues.sort(
        key=lambda venue: venue["name"].lower()
    )


    return render_template(
        "admin/venues.html",
        venues=venues,
        total_venues=len(venues),
        total_events=len(events)
    )



# =========================================================
# ADMIN ANALYTICS
# =========================================================

@admin_bp.route(
    "/analytics"
)
@login_required
def analytics():

    if current_user.role != "admin":
        return "Access denied", 403


    total_users = User.query.count()

    total_students = User.query.filter_by(
        role="student"
    ).count()

    total_organizers = User.query.filter_by(
        role="organizer"
    ).count()

    total_volunteers = User.query.filter_by(
        role="volunteer"
    ).count()


    total_events = Event.query.count()

    approved_events = Event.query.filter_by(
        status="approved"
    ).count()

    pending_events = Event.query.filter_by(
        status="pending"
    ).count()

    rejected_events = Event.query.filter_by(
        status="rejected"
    ).count()

    cancelled_events = Event.query.filter_by(
        status="cancelled"
    ).count()

    postponed_events = Event.query.filter_by(
        status="postponed"
    ).count()


    total_registrations = Registration.query.count()

    total_checkins = Registration.query.filter_by(
        checked_in=True
    ).count()


    if total_registrations > 0:

        attendance_rate = round(
            (
                total_checkins
                /
                total_registrations
            )
            * 100,
            1
        )

    else:

        attendance_rate = 0


    total_reviews = Review.query.count()


    if total_reviews > 0:

        average_rating = round(
            (
                db.session.query(
                    db.func.avg(
                        Review.rating
                    )
                ).scalar()
            ),
            1
        )

    else:

        average_rating = 0


    total_certificates = Certificate.query.count()


    total_volunteer_applications = (
        VolunteerApplication.query.count()
    )


    approved_volunteer_applications = (
        VolunteerApplication.query.filter_by(
            status="approved"
        ).count()
    )


    # -----------------------------------------------------
    # ROLE ACCESS APPLICATIONS
    # -----------------------------------------------------

    total_role_applications = (
        RoleApplication.query.count()
    )


    pending_role_applications = (
        RoleApplication.query.filter_by(
            status="pending"
        ).count()
    )


    approved_role_applications = (
        RoleApplication.query.filter_by(
            status="approved"
        ).count()
    )


    rejected_role_applications = (
        RoleApplication.query.filter_by(
            status="rejected"
        ).count()
    )


    event_registration_counts = []

    events = Event.query.all()


    for event in events:

        registration_count = Registration.query.filter_by(
            event_id=event.id
        ).count()


        event_registration_counts.append({

            "event":
                event,

            "registrations":
                registration_count

        })


    event_registration_counts.sort(
        key=lambda item: item["registrations"],
        reverse=True
    )


    top_events = event_registration_counts[:5]


    return render_template(

        "admin/analytics.html",

        total_users=
            total_users,

        total_students=
            total_students,

        total_organizers=
            total_organizers,

        total_volunteers=
            total_volunteers,

        total_events=
            total_events,

        approved_events=
            approved_events,

        pending_events=
            pending_events,

        rejected_events=
            rejected_events,

        cancelled_events=
            cancelled_events,

        postponed_events=
            postponed_events,

        total_registrations=
            total_registrations,

        total_checkins=
            total_checkins,

        attendance_rate=
            attendance_rate,

        total_reviews=
            total_reviews,

        average_rating=
            average_rating,

        total_certificates=
            total_certificates,

        total_volunteer_applications=
            total_volunteer_applications,

        approved_volunteer_applications=
            approved_volunteer_applications,

        total_role_applications=
            total_role_applications,

        pending_role_applications=
            pending_role_applications,

        approved_role_applications=
            approved_role_applications,

        rejected_role_applications=
            rejected_role_applications,

        top_events=
            top_events

    )



# =========================================================
# ADMIN ANNOUNCEMENTS
# =========================================================

@admin_bp.route(
    "/announcements",
    methods=["GET", "POST"]
)
@login_required
def announcements():

    if current_user.role != "admin":
        return "Access denied", 403


    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        audience = request.form.get(
            "audience",
            "all"
        ).strip()


        if not title or not message:

            flash(
                "Please provide both a title and message.",
                "error"
            )

            return redirect(
                url_for("admin.announcements")
            )


        if audience == "students":

            recipients = User.query.filter_by(
                role="student"
            ).all()

        elif audience == "organizers":

            recipients = User.query.filter_by(
                role="organizer"
            ).all()

        elif audience == "volunteers":

            recipients = User.query.filter_by(
                role="volunteer"
            ).all()

        else:

            recipients = User.query.all()


        created = 0


        for user in recipients:

            create_notification(

                user_id=user.id,

                title=title,

                message=message,

                notification_type="announcement"

            )

            created += 1


        db.session.commit()


        flash(
            f"Announcement sent to {created} user(s).",
            "success"
        )


        return redirect(
            url_for("admin.announcements")
        )


    recent_announcements = Notification.query.filter_by(
        notification_type="announcement"
    ).order_by(
        Notification.created_at.desc()
    ).limit(20).all()


    return render_template(
        "admin/announcements.html",
        recent_announcements=recent_announcements
    )



# =========================================================
# EVENT DETAILS / MODERATION
# =========================================================

@admin_bp.route(
    "/events/<int:event_id>"
)
@login_required
def event_details(event_id):

    if current_user.role != "admin":
        return "Access denied", 403


    event = db.session.get(
        Event,
        event_id
    )


    if event is None:
        return "Event not found", 404


    organizer = db.session.get(
        User,
        event.organizer_id
    )


    registration_count = Registration.query.filter_by(
        event_id=event.id
    ).count()


    volunteer_count = VolunteerApplication.query.filter_by(
        event_id=event.id
    ).count()


    return render_template(
        "admin/event_details.html",

        event=event,

        organizer=organizer,

        registration_count=
            registration_count,

        volunteer_count=
            volunteer_count
    )



# =========================================================
# ROLE APPLICATION MANAGEMENT
# =========================================================

@admin_bp.route(
    "/role-applications"
)
@login_required
def role_applications():

    if current_user.role != "admin":
        return "Access denied", 403


    applications = (
        RoleApplication.query
        .order_by(
            RoleApplication.created_at.desc()
        )
        .all()
    )


    pending_applications = [
        application
        for application in applications
        if application.status == "pending"
    ]


    approved_applications = [
        application
        for application in applications
        if application.status == "approved"
    ]


    rejected_applications = [
        application
        for application in applications
        if application.status == "rejected"
    ]


    return render_template(
        "admin/role_applications.html",

        applications=applications,

        pending_applications=
            pending_applications,

        approved_applications=
            approved_applications,

        rejected_applications=
            rejected_applications
    )


# =========================================================
# APPROVE ROLE APPLICATION
# =========================================================

@admin_bp.route(
    "/role-applications/<int:application_id>/approve",
    methods=["POST"]
)
@login_required
def approve_role_application(application_id):

    if current_user.role != "admin":
        return "Access denied", 403


    application = db.session.get(
        RoleApplication,
        application_id
    )


    if application is None:
        return "Application not found", 404


    if application.status != "pending":

        flash(
            "This application has already been reviewed.",
            "info"
        )

        return redirect(
            url_for("admin.role_applications")
        )


    user = db.session.get(
        User,
        application.user_id
    )


    if user is None:
        return "Applicant not found", 404


    # -------------------------------------------------
    # PRESERVE THE USER'S EXISTING BASE ROLE
    #
    # A user may own multiple CampusHub identities.
    # Approving CHV / CHO / CHC must NEVER overwrite
    # the existing CHS / base account role.
    #
    # The active CampusHub identity will determine
    # which portal the user enters.
    # -------------------------------------------------

    requested_role = application.requested_role.lower().strip()


    # -------------------------------------------------
    # CAMPUSHUB MULTI-IDENTITY SYSTEM
    #
    # Existing identities are NEVER deleted.
    #
    # Student   -> CHS-000013
    # Volunteer -> CHV-000013
    # Organizer -> CHO-000013
    # Admin     -> CHC-000013
    # -------------------------------------------------

    role_code = {

        "student": "CHS",

        "volunteer": "CHV",

        "organizer": "CHO",

        "admin": "CHC"

    }.get(requested_role)


    if role_code:

        campus_id = (
            f"{role_code}-"
            f"{str(user.id).zfill(6)}"
        )

        identity = CampusIdentity.query.filter_by(
            user_id=user.id,
            identity_type=requested_role
        ).first()

        if identity is None:

            identity = CampusIdentity(
                user_id=user.id,
                campus_id=campus_id,
                identity_type=requested_role,
                status="active",
                activated_at=db.func.now()
            )

            db.session.add(identity)

        else:

            identity.status = "active"
            identity.suspended_at = None

            if identity.activated_at is None:
                identity.activated_at = db.func.now()


    # -------------------------------------------------
    # KEEP THE ORIGINAL REGISTRATION PROFILE INTACT
    #
    # We deliberately DO NOT overwrite
    # RegistrationProfile.campus_id here.
    #
    # This preserves the user's original student /
    # registration identity and existing relationships.
    # -------------------------------------------------


    application.status = "approved"

    application.reviewed_at = db.func.now()


    create_notification(

        user_id=user.id,

        title="Role application approved",

        message=(
            f"Your application for the "
            f"{application.requested_role} role has "
            "been approved by college administration."
        ),

        notification_type="role_approved"

    )


    db.session.commit()


    flash(
        f"{user.name}'s application was approved.",
        "success"
    )


    return redirect(
        url_for("admin.role_applications")
    )


# =========================================================
# REJECT ROLE APPLICATION
# =========================================================

@admin_bp.route(
    "/role-applications/<int:application_id>/reject",
    methods=["POST"]
)
@login_required
def reject_role_application(application_id):

    if current_user.role != "admin":
        return "Access denied", 403


    application = db.session.get(
        RoleApplication,
        application_id
    )


    if application is None:
        return "Application not found", 404


    if application.status != "pending":

        flash(
            "This application has already been reviewed.",
            "info"
        )

        return redirect(
            url_for("admin.role_applications")
        )


    user = db.session.get(
        User,
        application.user_id
    )


    application.status = "rejected"

    application.reviewed_at = db.func.now()


    if user:

        create_notification(

            user_id=user.id,

            title="Role application update",

            message=(
                f"Your application for the "
                f"{application.requested_role} role "
                "was not approved by college administration."
            ),

            notification_type="role_rejected"

        )


    db.session.commit()


    flash(
        "Role application rejected.",
        "success"
    )


    return redirect(
        url_for("admin.role_applications")
    )

