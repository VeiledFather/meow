from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify
)

from flask_login import login_required, current_user

from app import db

from app.models import (
    Event,
    User,
    VolunteerApplication,
    Registration
)


volunteer_bp = Blueprint(
    "volunteer",
    __name__
)


# =========================================================
# SECURITY
# =========================================================

def volunteer_required():

    if not current_user.is_authenticated:
        return False

    return current_user.role == "volunteer"


def get_approved_assignment(event_id):

    return VolunteerApplication.query.filter_by(
        volunteer_id=current_user.id,
        event_id=event_id,
        status="approved"
    ).first()


# =========================================================
# VOLUNTEER DASHBOARD
# =========================================================

@volunteer_bp.route("/dashboard")
@login_required
def dashboard():

    if not volunteer_required():
        return "Unauthorized", 403

    events = Event.query.filter_by(
        status="approved"
    ).order_by(
        Event.date.asc(),
        Event.start_time.asc()
    ).all()

    applications = VolunteerApplication.query.filter_by(
        volunteer_id=current_user.id
    ).order_by(
        VolunteerApplication.created_at.desc()
    ).all()

    application_map = {
        application.event_id: application
        for application in applications
    }

    event_data = []

    assigned_events = []

    total_checkins = 0

    completed_events = 0

    for event in events:

        organizer = User.query.get(
            event.organizer_id
        )

        application = application_map.get(
            event.id
        )

        checked_in = Registration.query.filter_by(
            event_id=event.id,
            checked_in=True
        ).count()

        total_registered = Registration.query.filter_by(
            event_id=event.id
        ).count()

        event_info = {
            "event": event,
            "organizer": organizer,
            "application": application,
            "checked_in": checked_in,
            "total_registered": total_registered
        }

        event_data.append(
            event_info
        )

        if (
            application
            and application.status == "approved"
        ):

            assigned_events.append(
                event_info
            )

            total_checkins += checked_in

            # An event is considered completed when
            # its date has passed. The application remains
            # available as history.
            if event.date < "9999-99-99":
                pass

    approved_count = sum(
        1
        for application in applications
        if application.status == "approved"
    )

    pending_count = sum(
        1
        for application in applications
        if application.status == "pending"
    )

    rejected_count = sum(
        1
        for application in applications
        if application.status == "rejected"
    )

    return render_template(
        "dashboard/volunteer.html",

        events=event_data,

        total_events=len(event_data),

        applications=applications,

        assigned_events=assigned_events,

        approved_count=approved_count,

        pending_count=pending_count,

        rejected_count=rejected_count,

        total_checkins=total_checkins,

        completed_events=completed_events
    )


# =========================================================
# APPLY AS VOLUNTEER
# =========================================================

@volunteer_bp.route(
    "/apply/<int:event_id>",
    methods=["POST"]
)
@login_required
def apply(event_id):

    if not volunteer_required():
        return "Unauthorized", 403

    event = Event.query.get_or_404(
        event_id
    )

    if event.status != "approved":

        flash(
            "You can only apply for approved events.",
            "error"
        )

        return redirect(
            url_for("volunteer.dashboard")
        )

    existing = VolunteerApplication.query.filter_by(
        volunteer_id=current_user.id,
        event_id=event.id
    ).first()

    if existing:

        if existing.status == "pending":

            flash(
                "You have already applied for this event.",
                "info"
            )

        elif existing.status == "approved":

            flash(
                "You are already assigned to this event.",
                "info"
            )

        else:

            flash(
                "Your previous application was rejected.",
                "error"
            )

        return redirect(
            url_for("volunteer.dashboard")
        )

    message = request.form.get(
        "message",
        ""
    ).strip()

    application = VolunteerApplication(
        volunteer_id=current_user.id,
        event_id=event.id,
        status="pending",
        message=message
    )

    db.session.add(
        application
    )

    db.session.commit()

    flash(
        "Volunteer application submitted successfully.",
        "success"
    )

    return redirect(
        url_for("volunteer.dashboard")
    )


# =========================================================
# QR SCANNER
# =========================================================

@volunteer_bp.route("/scanner")
@login_required
def scanner():

    if not volunteer_required():
        return "Unauthorized", 403

    return render_template(
        "volunteer/scanner.html"
    )


# =========================================================
# QR VALIDATION
# =========================================================

@volunteer_bp.route(
    "/scanner/validate",
    methods=["POST"]
)
@login_required
def validate_qr():

    if not volunteer_required():

        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 403

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    registration_code = str(
        data.get(
            "registration_code",
            ""
        )
    ).strip()

    if not registration_code:

        return jsonify({
            "success": False,
            "message": "Registration code is required."
        }), 400

    registration = Registration.query.filter_by(
        registration_code=registration_code
    ).first()

    if not registration:

        return jsonify({
            "success": False,
            "message": "Invalid CampusHub ticket."
        }), 404

    if registration.status != "registered":

        return jsonify({
            "success": False,
            "message": "This registration is not active."
        }), 400

    if registration.checked_in:

        return jsonify({
            "success": False,
            "already_checked_in": True,
            "message": "This ticket has already been checked in."
        }), 409

    student = User.query.get(
        registration.student_id
    )

    event = Event.query.get(
        registration.event_id
    )

    if not student or not event:

        return jsonify({
            "success": False,
            "message": "Registration data is incomplete."
        }), 400

    if event.status != "approved":

        return jsonify({
            "success": False,
            "message": "This event is not active."
        }), 400

    assignment = get_approved_assignment(
        event.id
    )

    if not assignment:

        return jsonify({
            "success": False,
            "message": "You are not assigned to this event."
        }), 403

    return jsonify({
        "success": True,
        "message": "Valid ticket.",
        "registration": {
            "id": registration.id,
            "student_name": student.name,
            "student_email": student.email,
            "event_title": event.title,
            "event_date": event.date,
            "event_time": (
                f"{event.start_time} – "
                f"{event.end_time}"
            ),
            "venue": event.venue,
            "registration_code": registration.registration_code
        }
    })


# =========================================================
# CHECK-IN
# =========================================================

@volunteer_bp.route(
    "/scanner/check-in",
    methods=["POST"]
)
@login_required
def check_in():

    if not volunteer_required():

        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 403

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    registration_code = str(
        data.get(
            "registration_code",
            ""
        )
    ).strip()

    if not registration_code:

        return jsonify({
            "success": False,
            "message": "Registration code is required."
        }), 400

    registration = Registration.query.filter_by(
        registration_code=registration_code
    ).first()

    if not registration:

        return jsonify({
            "success": False,
            "message": "Invalid CampusHub ticket."
        }), 404

    event = Event.query.get(
        registration.event_id
    )

    student = User.query.get(
        registration.student_id
    )

    if not event or not student:

        return jsonify({
            "success": False,
            "message": "Registration data is incomplete."
        }), 400

    if event.status != "approved":

        return jsonify({
            "success": False,
            "message": "This event is not active."
        }), 400

    assignment = get_approved_assignment(
        event.id
    )

    if not assignment:

        return jsonify({
            "success": False,
            "message": "You are not assigned to this event."
        }), 403

    if registration.checked_in:

        return jsonify({
            "success": False,
            "already_checked_in": True,
            "message": "Student is already checked in."
        }), 409

    if registration.status != "registered":

        return jsonify({
            "success": False,
            "message": "Registration is not active."
        }), 400

    registration.checked_in = True

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Check-in successful.",
        "student_name": student.name,
        "event_title": event.title
    })
