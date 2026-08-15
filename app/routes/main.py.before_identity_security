from flask import Blueprint, render_template, redirect, url_for

from flask_login import login_required, current_user

from app.models import Event, Registration


main_bp = Blueprint(
    "main",
    __name__
)


@main_bp.route("/")
def index():

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    return redirect(
        url_for("auth.register")
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "admin":
        return redirect(
            url_for("admin.dashboard")
        )

    if current_user.role == "organizer":
        return redirect(
            url_for("organizer.dashboard")
        )

    if current_user.role == "volunteer":
        return redirect(
            url_for("volunteer.dashboard")
        )

    upcoming_events = Event.query.filter_by(
        status="approved"
    ).order_by(
        Event.date.asc(),
        Event.start_time.asc()
    ).limit(4).all()

    registrations = Registration.query.filter_by(
        student_id=current_user.id
    ).order_by(
        Registration.created_at.desc()
    ).all()

    attended_count = sum(
        1
        for registration in registrations
        if registration.checked_in
    )

    review_count = len(
        current_user.reviews
    )

    return render_template(
        "dashboard/student.html",
        upcoming_events=upcoming_events,
        registrations=registrations,
        attended_count=attended_count,
        review_count=review_count
    )


@main_bp.route("/profile")
@login_required
def profile():

    registrations = Registration.query.filter_by(
        student_id=current_user.id
    ).order_by(
        Registration.created_at.desc()
    ).all()

    attended_count = sum(
        1
        for registration in registrations
        if registration.checked_in
    )

    review_count = len(
        current_user.reviews
    )

    return render_template(
        "dashboard/profile.html",
        registrations=registrations,
        attended_count=attended_count,
        review_count=review_count
    )

# =========================================================
# HALL OF FAME
# =========================================================

@main_bp.route("/hall-of-fame")
@login_required
def hall_of_fame():

    events = Event.query.filter_by(
        status="approved"
    ).all()


    ranked_events = []


    for event in events:

        reviews = getattr(
            event,
            "reviews",
            []
        )


        if not reviews:
            continue


        average_rating = round(
            sum(
                review.rating
                for review in reviews
            )
            / len(reviews),
            1
        )


        ranked_events.append({
            "event": event,
            "rating": average_rating,
            "review_count": len(reviews)
        })


    ranked_events.sort(
        key=lambda item: (
            item["rating"],
            item["review_count"]
        ),
        reverse=True
    )


    ranked_events = ranked_events[:10]


    return render_template(
        "hall_of_fame.html",
        ranked_events=ranked_events
    )

