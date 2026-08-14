from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from app import db

from app.models import (
    Notification,
    Registration
)

from datetime import datetime, timedelta


notification_bp = Blueprint(
    "notification",
    __name__,
    url_prefix="/notifications"
)


# =========================================================
# NOTIFICATION CENTER
# =========================================================

@notification_bp.route("/")
@login_required
def center():

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()


    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()


    return render_template(
        "notifications/center.html",
        notifications=notifications,
        unread_count=unread_count
    )


# =========================================================
# MARK ONE NOTIFICATION AS READ
# =========================================================

@notification_bp.route(
    "/<int:notification_id>/read",
    methods=["POST"]
)
@login_required
def mark_read(notification_id):

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()


    notification.is_read = True

    db.session.commit()


    if notification.event_id:

        return redirect(
            url_for(
                "events.details",
                event_id=notification.event_id
            )
        )


    return redirect(
        url_for(
            "notification.center"
        )
    )


# =========================================================
# MARK ALL AS READ
# =========================================================

@notification_bp.route(
    "/read-all",
    methods=["POST"]
)
@login_required
def mark_all_read():

    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update(
        {
            "is_read": True
        }
    )


    db.session.commit()


    flash(
        "All notifications marked as read.",
        "success"
    )


    return redirect(
        url_for(
            "notification.center"
        )
    )


# =========================================================
# CREATE NOTIFICATION
# =========================================================

def create_notification(
    user_id,
    title,
    message,
    notification_type="general",
    event_id=None
):

    notification = Notification(

        user_id=user_id,

        title=title,

        message=message,

        notification_type=
            notification_type,

        event_id=event_id,

        is_read=False

    )


    db.session.add(
        notification
    )


    return notification


# =========================================================
# GENERATE SMART EVENT REMINDERS
# =========================================================

@notification_bp.route(
    "/generate-reminders",
    methods=["POST"]
)
@login_required
def generate_reminders():

    if current_user.role != "student":

        return "Access denied", 403


    registrations = Registration.query.filter_by(
        student_id=current_user.id,
        status="registered"
    ).all()


    created = 0


    today = datetime.now().date()


    for registration in registrations:

        event = registration.event


        if not event:

            continue


        try:

            event_date = datetime.strptime(
                event.date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            continue


        days_until = (
            event_date - today
        ).days


        # -------------------------------------------------
        # EVENT TOMORROW
        # -------------------------------------------------

        if days_until == 1:

            existing = Notification.query.filter_by(

                user_id=current_user.id,

                event_id=event.id,

                notification_type=
                    "event_reminder"

            ).first()


            if not existing:

                create_notification(

                    user_id=current_user.id,

                    title="Your event is tomorrow",

                    message=(
                        f"{event.title} is happening "
                        f"tomorrow at {event.start_time} "
                        f"at {event.venue}."
                    ),

                    notification_type=
                        "event_reminder",

                    event_id=event.id

                )

                created += 1


        # -------------------------------------------------
        # EVENT TODAY
        # -------------------------------------------------

        elif days_until == 0:

            existing = Notification.query.filter_by(

                user_id=current_user.id,

                event_id=event.id,

                notification_type=
                    "event_today"

            ).first()


            if not existing:

                create_notification(

                    user_id=current_user.id,

                    title="Your event is today",

                    message=(
                        f"{event.title} starts at "
                        f"{event.start_time}. "
                        f"Venue: {event.venue}. "
                        "Don't forget your digital ticket."
                    ),

                    notification_type=
                        "event_today",

                    event_id=event.id

                )

                created += 1


    db.session.commit()


    if created:

        flash(
            f"{created} smart notification(s) created.",
            "success"
        )

    else:

        flash(
            "No new reminders are needed right now.",
            "info"
        )


    return redirect(
        url_for(
            "notification.center"
        )
    )
