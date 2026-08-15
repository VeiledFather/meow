from flask import Blueprint, render_template, redirect, url_for, session

from flask_login import login_required, current_user

from app import db

from app.models import (
    Event,
    Registration,
    CampusIdentity
)


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

    # =====================================================
    # ACTIVE CAMPUSHUB IDENTITY
    # =====================================================

    active_identity_id = session.get(
        "active_identity_id"
    )

    identity = None

    if active_identity_id:
        identity = db.session.get(
            CampusIdentity,
            active_identity_id
        )

    # If no valid active identity exists, choose from
    # currently active identities.
    if (
        identity is None
        or identity.user_id != current_user.id
        or identity.status != "active"
    ):

        identities = (
            CampusIdentity.query
            .filter_by(
                user_id=current_user.id,
                status="active"
            )
            .order_by(
                CampusIdentity.id.asc()
            )
            .all()
        )

        if not identities:
            return "No active CampusHub identity is available.", 403

        if len(identities) > 1:
            return redirect(
                url_for("auth.login")
            )

        identity = identities[0]

        session["active_identity_id"] = identity.id
        session["active_identity_type"] = identity.identity_type

    identity_type = identity.identity_type

    # =====================================================
    # PORTAL ROUTING
    # =====================================================

    if identity_type == "admin":
        return redirect(
            url_for("admin.dashboard")
        )

    if identity_type == "organizer":
        return redirect(
            url_for("organizer.dashboard")
        )

    if identity_type == "volunteer":
        return redirect(
            url_for("volunteer.dashboard")
        )

    # =====================================================
    # STUDENT DASHBOARD
    # =====================================================

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

