from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

import os
import uuid

from werkzeug.utils import secure_filename

from flask_login import (
    login_required,
    current_user
)

from app import db

from app.models import (
    Event,
    VolunteerApplication,
    Registration,
    EventGallery,
    Review,
    Certificate
)


organizer_bp = Blueprint(
    "organizer",
    __name__
)


# =========================================================
# SECURITY
# =========================================================

def organizer_required():

    if not current_user.is_authenticated:
        return False

    return current_user.role == "organizer"


def get_owned_event(event_id):

    return Event.query.filter_by(
        id=event_id,
        organizer_id=current_user.id
    ).first()


# =========================================================
# EVENT CLASH DETECTOR
# =========================================================

def find_event_clashes(
    date,
    start_time,
    end_time,
    venue,
    organizer_id
):

    events = Event.query.filter_by(
        date=date
    ).all()

    clashes = []

    for event in events:

        if not event.start_time or not event.end_time:
            continue

        if event.status == "rejected":
            continue

        overlaps = (
            event.start_time < end_time
            and
            event.end_time > start_time
        )

        if not overlaps:
            continue

        if (
            event.venue.strip().lower()
            ==
            venue.strip().lower()
        ):

            clashes.append({
                "type": "venue",
                "event": event
            })

            continue

        if event.organizer_id == organizer_id:

            clashes.append({
                "type": "organizer",
                "event": event
            })

    return clashes


# =========================================================
# ORGANIZER DASHBOARD
# =========================================================

@organizer_bp.route("/dashboard")
@login_required
def dashboard():

    if not organizer_required():
        return "Access denied", 403

    events = Event.query.filter_by(
        organizer_id=current_user.id
    ).order_by(
        Event.id.desc()
    ).all()

    all_applications = []

    total_registrations = 0
    total_checkins = 0

    approved_events = 0
    pending_events = 0
    rejected_events = 0

    for event in events:

        if event.status == "approved":
            approved_events += 1

        elif event.status == "pending":
            pending_events += 1

        elif event.status == "rejected":
            rejected_events += 1


        registrations = Registration.query.filter_by(
            event_id=event.id
        ).all()

        event.total_registrations = len(
            registrations
        )

        event.total_checkins = sum(
            1
            for registration in registrations
            if registration.checked_in
        )

        total_registrations += (
            event.total_registrations
        )

        total_checkins += (
            event.total_checkins
        )


        event_applications = (
            VolunteerApplication.query
            .filter_by(
                event_id=event.id
            )
            .order_by(
                VolunteerApplication.created_at.desc()
            )
            .all()
        )

        for application in event_applications:

            all_applications.append({
                "application": application,
                "event": event
            })


    pending_applications = sum(
        1
        for item in all_applications
        if item["application"].status == "pending"
    )

    approved_volunteers = sum(
        1
        for item in all_applications
        if item["application"].status == "approved"
    )

    rejected_applications = sum(
        1
        for item in all_applications
        if item["application"].status == "rejected"
    )


    pending_volunteer_applications = [
        item
        for item in all_applications
        if item["application"].status == "pending"
    ]


    approved_volunteer_applications = [
        item
        for item in all_applications
        if item["application"].status == "approved"
    ]


    rejected_volunteer_applications = [
        item
        for item in all_applications
        if item["application"].status == "rejected"
    ]


    return render_template(

        "organizer/dashboard.html",

        events=events,

        applications=all_applications,

        pending_volunteer_applications=
            pending_volunteer_applications,

        approved_volunteer_applications=
            approved_volunteer_applications,

        rejected_volunteer_applications=
            rejected_volunteer_applications,

        pending_applications=
            pending_applications,

        approved_volunteers=
            approved_volunteers,

        rejected_applications=
            rejected_applications,

        approved_events=
            approved_events,

        pending_events=
            pending_events,

        rejected_events=
            rejected_events,

        total_registrations=
            total_registrations,

        total_checkins=
            total_checkins

    )


# =========================================================
# CREATE EVENT
# =========================================================

@organizer_bp.route(
    "/create",
    methods=["GET", "POST"]
)
@login_required
def create_event():

    if not organizer_required():
        return "Access denied", 403

    if request.method == "POST":

        try:

            title = request.form[
                "title"
            ].strip()

            description = request.form[
                "description"
            ].strip()

            event_type = request.form[
                "event_type"
            ]

            date = request.form[
                "date"
            ]

            start = request.form[
                "start_time"
            ]

            end = request.form[
                "end_time"
            ]

            venue = request.form[
                "venue"
            ].strip()

            expected_attendees = int(
                request.form[
                    "expected_attendees"
                ]
            )

            budget = float(
                request.form[
                    "budget"
                ]
            )

            food_requirements = request.form.get(
                "food_requirements",
                ""
            ).strip()

            equipment_requirements = request.form.get(
                "equipment_requirements",
                ""
            ).strip()


            if start >= end:

                flash(
                    "End time must be after start time.",
                    "error"
                )

                return render_template(
                    "organizer/create_event.html"
                )


            # =================================================
            # CLASH DETECTION
            # =================================================

            clashes = find_event_clashes(

                date=date,

                start_time=start,

                end_time=end,

                venue=venue,

                organizer_id=current_user.id

            )


            if clashes:

                for clash in clashes:

                    existing = clash["event"]


                    if clash["type"] == "venue":

                        flash(
                            (
                                f"⚠ Venue clash: "
                                f"'{existing.title}' is already "
                                f"scheduled at {existing.venue} "
                                f"from {existing.start_time} "
                                f"to {existing.end_time}."
                            ),
                            "error"
                        )


                    elif clash["type"] == "organizer":

                        flash(
                            (
                                f"⚠ Schedule clash: your event "
                                f"overlaps with "
                                f"'{existing.title}' "
                                f"({existing.start_time}–"
                                f"{existing.end_time})."
                            ),
                            "error"
                        )


                return render_template(
                    "organizer/create_event.html"
                )


            # =================================================
            # CREATE EVENT
            # =================================================

            event = Event(

                title=title,

                description=description,

                event_type=event_type,

                date=date,

                start_time=start,

                end_time=end,

                venue=venue,

                expected_attendees=
                    expected_attendees,

                budget=budget,

                food_requirements=
                    food_requirements,

                equipment_requirements=
                    equipment_requirements,

                organizer_id=
                    current_user.id,

                status="pending"

            )


            db.session.add(event)

            db.session.commit()


            flash(
                "Event submitted for management approval.",
                "success"
            )


            return redirect(
                url_for(
                    "organizer.dashboard"
                )
            )


        except (
            ValueError,
            KeyError
        ):

            db.session.rollback()

            flash(
                "Please enter valid event information.",
                "error"
            )


    return render_template(
        "organizer/create_event.html"
    )


# =========================================================
# APPROVE VOLUNTEER
# =========================================================

@organizer_bp.route(
    "/volunteers/<int:application_id>/approve",
    methods=["POST"]
)
@login_required
def approve_volunteer(
    application_id
):

    if not organizer_required():
        return "Access denied", 403


    application = (
        VolunteerApplication.query
        .get_or_404(
            application_id
        )
    )


    event = Event.query.get_or_404(
        application.event_id
    )


    if event.organizer_id != current_user.id:

        return "Access denied", 403


    if application.status != "pending":

        flash(
            "This application has already been processed.",
            "info"
        )

        return redirect(
            url_for(
                "organizer.dashboard"
            )
        )


    application.status = "approved"

    db.session.commit()


    flash(
        "Volunteer application approved.",
        "success"
    )


    return redirect(
        url_for(
            "organizer.dashboard"
        )
    )


# =========================================================
# REJECT VOLUNTEER
# =========================================================

@organizer_bp.route(
    "/volunteers/<int:application_id>/reject",
    methods=["POST"]
)
@login_required
def reject_volunteer(
    application_id
):

    if not organizer_required():
        return "Access denied", 403


    application = (
        VolunteerApplication.query
        .get_or_404(
            application_id
        )
    )


    event = Event.query.get_or_404(
        application.event_id
    )


    if event.organizer_id != current_user.id:

        return "Access denied", 403


    if application.status != "pending":

        flash(
            "This application has already been processed.",
            "info"
        )

        return redirect(
            url_for(
                "organizer.dashboard"
            )
        )


    application.status = "rejected"

    db.session.commit()


    flash(
        "Volunteer application rejected.",
        "success"
    )


    return redirect(
        url_for(
            "organizer.dashboard"
        )
    )


# =========================================================
# EVENT ATTENDEES
# =========================================================

@organizer_bp.route(
    "/events/<int:event_id>/attendees"
)
@login_required
def attendees(event_id):

    if not organizer_required():
        return "Access denied", 403


    event = Event.query.filter_by(
        id=event_id,
        organizer_id=current_user.id
    ).first_or_404()


    registrations = (
        Registration.query
        .filter_by(
            event_id=event.id
        )
        .order_by(
            Registration.created_at.asc()
        )
        .all()
    )


    total = len(
        registrations
    )


    checked_in = sum(
        1
        for registration in registrations
        if registration.checked_in
    )


    not_checked_in = (
        total - checked_in
    )


    if total > 0:

        attendance_percentage = round(
            (
                checked_in
                /
                total
            )
            * 100,
            1
        )

    else:

        attendance_percentage = 0


    return render_template(

        "organizer/attendees.html",

        event=event,

        registrations=registrations,

        total=total,

        checked_in=checked_in,

        not_checked_in=not_checked_in,

        attendance_percentage=
            attendance_percentage

    )


# =========================================================
# EVENT GALLERY
# =========================================================

ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


def allowed_image(filename):

    if "." not in filename:
        return False

    extension = (
        filename.rsplit(".", 1)[1]
        .lower()
    )

    return extension in ALLOWED_IMAGE_EXTENSIONS


# =========================================================
# GALLERY MANAGEMENT
# =========================================================

@organizer_bp.route(
    "/events/<int:event_id>/gallery",
    methods=["GET", "POST"]
)
@login_required
def gallery(event_id):

    if not organizer_required():
        return "Access denied", 403


    event = Event.query.filter_by(
        id=event_id,
        organizer_id=current_user.id
    ).first_or_404()


    if request.method == "POST":

        files = request.files.getlist(
            "photos"
        )


        if not files:

            flash(
                "Please select at least one image.",
                "error"
            )

            return redirect(
                url_for(
                    "organizer.gallery",
                    event_id=event.id
                )
            )


        upload_folder = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)
            ),
            "static",
            "uploads",
            "events"
        )


        os.makedirs(
            upload_folder,
            exist_ok=True
        )


        uploaded = 0


        for file in files:

            if not file:
                continue


            original_name = secure_filename(
                file.filename
            )


            if not original_name:
                continue


            if not allowed_image(
                original_name
            ):

                flash(
                    (
                        f"{original_name} "
                        "is not a supported image."
                    ),
                    "error"
                )

                continue


            extension = (
                original_name
                .rsplit(".", 1)[1]
                .lower()
            )


            unique_filename = (
                f"event_{event.id}_"
                f"{uuid.uuid4().hex}."
                f"{extension}"
            )


            file.save(
                os.path.join(
                    upload_folder,
                    unique_filename
                )
            )


            gallery_item = EventGallery(

                event_id=event.id,

                filename=unique_filename,

                original_filename=original_name

            )


            db.session.add(
                gallery_item
            )


            uploaded += 1


        db.session.commit()


        if uploaded:

            flash(
                (
                    f"{uploaded} photo"
                    f"{'s' if uploaded != 1 else ''} "
                    "uploaded successfully."
                ),
                "success"
            )


        return redirect(
            url_for(
                "organizer.gallery",
                event_id=event.id
            )
        )


    photos = EventGallery.query.filter_by(
        event_id=event.id
    ).order_by(
        EventGallery.uploaded_at.desc()
    ).all()


    return render_template(
        "organizer/gallery.html",
        event=event,
        photos=photos
    )


# =========================================================
# DELETE GALLERY PHOTO
# =========================================================

@organizer_bp.route(
    "/events/<int:event_id>/gallery/<int:photo_id>/delete",
    methods=["POST"]
)
@login_required
def delete_gallery_photo(
    event_id,
    photo_id
):

    if not organizer_required():
        return "Access denied", 403


    event = Event.query.filter_by(
        id=event_id,
        organizer_id=current_user.id
    ).first_or_404()


    photo = EventGallery.query.filter_by(
        id=photo_id,
        event_id=event.id
    ).first_or_404()


    upload_folder = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)
        ),
        "static",
        "uploads",
        "events"
    )


    file_path = os.path.join(
        upload_folder,
        photo.filename
    )


    if os.path.exists(file_path):

        os.remove(file_path)


    db.session.delete(
        photo
    )

    db.session.commit()


    flash(
        "Photo removed from the event gallery.",
        "success"
    )


    return redirect(
        url_for(
            "organizer.gallery",
            event_id=event.id
        )
    )
# =========================================================
# EVENT REVIEWS
# =========================================================

@organizer_bp.route(
    "/events/<int:event_id>/reviews"
)
@login_required
def event_reviews(event_id):

    if not organizer_required():
        return "Access denied", 403


    event = Event.query.filter_by(
        id=event_id,
        organizer_id=current_user.id
    ).first_or_404()


    reviews = Review.query.filter_by(
        event_id=event.id
    ).order_by(
        Review.created_at.desc()
    ).all()


    if reviews:

        average_rating = round(
            sum(
                review.rating
                for review in reviews
            )
            /
            len(reviews),
            1
        )

    else:

        average_rating = 0


    return render_template(
        "organizer/reviews.html",
        event=event,
        reviews=reviews,
        average_rating=average_rating
    )



# =========================================================
# ORGANIZER ANALYTICS
# =========================================================

@organizer_bp.route(
    "/analytics"
)
@login_required
def analytics():

    if not organizer_required():
        return "Access denied", 403


    events = Event.query.filter_by(
        organizer_id=current_user.id
    ).order_by(
        Event.id.desc()
    ).all()


    total_events = len(events)

    approved_events = sum(
        1
        for event in events
        if event.status == "approved"
    )

    pending_events = sum(
        1
        for event in events
        if event.status == "pending"
    )

    rejected_events = sum(
        1
        for event in events
        if event.status == "rejected"
    )


    total_registrations = 0

    total_checkins = 0


    event_analytics = []


    for event in events:

        registrations = Registration.query.filter_by(
            event_id=event.id
        ).all()


        registrations_count = len(
            registrations
        )


        checkins_count = sum(
            1
            for registration in registrations
            if registration.checked_in
        )


        if registrations_count > 0:

            attendance_rate = round(
                (
                    checkins_count
                    /
                    registrations_count
                )
                * 100,
                1
            )

        else:

            attendance_rate = 0


        reviews = Review.query.filter_by(
            event_id=event.id
        ).all()


        if reviews:

            average_rating = round(
                sum(
                    review.rating
                    for review in reviews
                )
                /
                len(reviews),
                1
            )

        else:

            average_rating = 0


        volunteer_count = VolunteerApplication.query.filter_by(
            event_id=event.id
        ).count()


        total_registrations += (
            registrations_count
        )

        total_checkins += (
            checkins_count
        )


        event_analytics.append({

            "event": event,

            "registrations":
                registrations_count,

            "checkins":
                checkins_count,

            "attendance_rate":
                attendance_rate,

            "average_rating":
                average_rating,

            "volunteers":
                volunteer_count

        })


    if total_registrations > 0:

        overall_attendance = round(
            (
                total_checkins
                /
                total_registrations
            )
            * 100,
            1
        )

    else:

        overall_attendance = 0


    total_volunteers = VolunteerApplication.query.join(
        Event,
        VolunteerApplication.event_id == Event.id
    ).filter(
        Event.organizer_id == current_user.id
    ).count()


    approved_volunteers = VolunteerApplication.query.join(
        Event,
        VolunteerApplication.event_id == Event.id
    ).filter(
        Event.organizer_id == current_user.id,
        VolunteerApplication.status == "approved"
    ).count()


    reviews = Review.query.join(
        Event,
        Review.event_id == Event.id
    ).filter(
        Event.organizer_id == current_user.id
    ).all()


    if reviews:

        overall_rating = round(
            sum(
                review.rating
                for review in reviews
            )
            /
            len(reviews),
            1
        )

    else:

        overall_rating = 0


    return render_template(

        "organizer/analytics.html",

        events=events,

        event_analytics=
            event_analytics,

        total_events=
            total_events,

        approved_events=
            approved_events,

        pending_events=
            pending_events,

        rejected_events=
            rejected_events,

        total_registrations=
            total_registrations,

        total_checkins=
            total_checkins,

        overall_attendance=
            overall_attendance,

        total_volunteers=
            total_volunteers,

        approved_volunteers=
            approved_volunteers,

        overall_rating=
            overall_rating

    )


# =========================================================
# ORGANIZER CERTIFICATE MANAGEMENT
# =========================================================

@organizer_bp.route(
    "/certificates"
)
@login_required
def certificate_management():

    if not organizer_required():
        return "Access denied", 403


    events = Event.query.filter_by(
        organizer_id=current_user.id
    ).order_by(
        Event.id.desc()
    ).all()


    certificate_events = []


    total_registered = 0
    total_checked_in = 0
    total_certificates = 0


    for event in events:

        registrations = Registration.query.filter_by(
            event_id=event.id
        ).all()


        registered_count = len(
            registrations
        )


        checked_in_count = sum(
            1
            for registration in registrations
            if registration.checked_in
        )


        certificate_count = Certificate.query.filter_by(
            event_id=event.id
        ).count()


        total_registered += (
            registered_count
        )

        total_checked_in += (
            checked_in_count
        )

        total_certificates += (
            certificate_count
        )


        certificate_events.append({

            "event": event,

            "registered":
                registered_count,

            "checked_in":
                checked_in_count,

            "certificates":
                certificate_count

        })


    return render_template(

        "organizer/certificates.html",

        certificate_events=
            certificate_events,

        total_registered=
            total_registered,

        total_checked_in=
            total_checked_in,

        total_certificates=
            total_certificates

    )

