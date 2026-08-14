from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    Response,
    request
)

from flask_login import (
    login_required,
    current_user
)

from app import db

from app.models import (
    Event,
    Registration,
    Review,
    EventGallery
)

import secrets
import qrcode
import io


events_bp = Blueprint(
    "events",
    __name__
)


# =========================================================
# EVENT PINBOARD
# =========================================================

@events_bp.route("/")
@login_required
def pinboard():

    events = Event.query.filter_by(
        status="approved"
    ).order_by(
        Event.date.asc(),
        Event.start_time.asc()
    ).all()

    return render_template(
        "events/pinboard.html",
        events=events
    )


# =========================================================
# EVENT DETAILS
# =========================================================

@events_bp.route(
    "/<int:event_id>"
)
@login_required
def details(event_id):

    event = Event.query.get_or_404(
        event_id
    )

    photos = EventGallery.query.filter_by(
        event_id=event.id
    ).order_by(
        EventGallery.uploaded_at.desc()
    ).all()

    return render_template(
        "events/detail.html",
        event=event,
        photos=photos
    )


# =========================================================
# REGISTER
# =========================================================

@events_bp.route(
    "/<int:event_id>/register",
    methods=["POST"]
)
@login_required
def register(event_id):

    event = Event.query.get_or_404(
        event_id
    )

    if current_user.role != "student":

        flash(
            "Only students can register for events.",
            "error"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    if event.status != "approved":

        flash(
            "This event is not currently available for registration.",
            "error"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    existing = Registration.query.filter_by(
        student_id=current_user.id,
        event_id=event.id
    ).first()


    if existing:

        flash(
            "You are already registered for this event.",
            "info"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    if event.expected_attendees:

        registered_count = Registration.query.filter_by(
            event_id=event.id,
            status="registered"
        ).count()


        if registered_count >= event.expected_attendees:

            flash(
                "Sorry, this event has reached its registration capacity.",
                "error"
            )

            return redirect(
                url_for(
                    "events.details",
                    event_id=event.id
                )
            )


    registration_code = (
        "CH-"
        + secrets.token_hex(6).upper()
    )


    registration = Registration(

        student_id=current_user.id,

        event_id=event.id,

        registration_code=registration_code,

        status="registered",

        checked_in=False

    )


    db.session.add(
        registration
    )

    db.session.commit()


    flash(
        "Registration successful! Your CampusHub ticket is ready.",
        "success"
    )


    return redirect(
        url_for(
            "events.my_registrations"
        )
    )


# =========================================================
# MY REGISTRATIONS
# =========================================================

@events_bp.route(
    "/my-registrations"
)
@login_required
def my_registrations():

    registrations = Registration.query.filter_by(
        student_id=current_user.id
    ).order_by(
        Registration.created_at.desc()
    ).all()

    return render_template(
        "events/my_registrations.html",
        registrations=registrations
    )


# =========================================================
# DIGITAL TICKET
# =========================================================

@events_bp.route(
    "/ticket/<int:registration_id>"
)
@login_required
def ticket(registration_id):

    registration = Registration.query.get_or_404(
        registration_id
    )


    if current_user.role == "student":

        if registration.student_id != current_user.id:

            flash(
                "You are not authorized to view this ticket.",
                "error"
            )

            return redirect(
                url_for(
                    "events.my_registrations"
                )
            )


    return render_template(
        "events/ticket.html",
        registration=registration
    )


# =========================================================
# TICKET QR
# =========================================================

@events_bp.route(
    "/ticket/<int:registration_id>/qr"
)
@login_required
def ticket_qr(registration_id):

    registration = Registration.query.get_or_404(
        registration_id
    )


    if current_user.role == "student":

        if registration.student_id != current_user.id:

            return Response(
                "Unauthorized",
                status=403
            )


    qr = qrcode.QRCode(

        version=1,

        error_correction=
            qrcode.constants.ERROR_CORRECT_M,

        box_size=10,

        border=4

    )


    qr.add_data(
        registration.registration_code
    )


    qr.make(
        fit=True
    )


    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )


    buffer = io.BytesIO()


    image.save(
        buffer,
        format="PNG"
    )


    buffer.seek(0)


    return Response(

        buffer.getvalue(),

        mimetype="image/png",

        headers={
            "Cache-Control": "no-store"
        }

    )




# =========================================================
# MY REVIEWS
# =========================================================

@events_bp.route("/reviews")
@login_required
def my_reviews():

    if current_user.role != "student":
        return "Access denied", 403


    registrations = Registration.query.filter_by(
        student_id=current_user.id,
        checked_in=True
    ).order_by(
        Registration.created_at.desc()
    ).all()


    reviewed_event_ids = {
        review.event_id
        for review in Review.query.filter_by(
            student_id=current_user.id
        ).all()
    }


    return render_template(
        "events/my_reviews.html",
        registrations=registrations,
        reviewed_event_ids=reviewed_event_ids
    )

# =========================================================
# REVIEW
# =========================================================

@events_bp.route(
    "/<int:event_id>/review",
    methods=["POST"]
)
@login_required
def submit_review(event_id):

    event = Event.query.get_or_404(
        event_id
    )


    if current_user.role != "student":

        flash(
            "Only students can submit reviews.",
            "error"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    registration = Registration.query.filter_by(
        student_id=current_user.id,
        event_id=event.id
    ).first()


    if not registration:

        flash(
            "You must register for this event before reviewing it.",
            "error"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    if not registration.checked_in:

        flash(
            "You can review the event after attending it.",
            "info"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    existing_review = Review.query.filter_by(
        student_id=current_user.id,
        event_id=event.id
    ).first()


    if existing_review:

        flash(
            "You have already reviewed this event.",
            "info"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    try:

        rating = int(
            request.form.get(
                "rating",
                0
            )
        )

    except ValueError:

        rating = 0


    if rating < 1 or rating > 5:

        flash(
            "Please select a rating between 1 and 5.",
            "error"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    comment = request.form.get(
        "comment",
        ""
    ).strip()


    review = Review(

        student_id=current_user.id,

        event_id=event.id,

        rating=rating,

        comment=comment

    )


    db.session.add(
        review
    )

    db.session.commit()


    flash(
        "Your review has been submitted. Thank you!",
        "success"
    )


    return redirect(
        url_for(
            "events.details",
            event_id=event.id
        )
    )
