
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from app import db
from app.models import Event


organizer_bp = Blueprint(
    "organizer",
    __name__
)


@organizer_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "organizer":
        return "Access denied", 403

    events = Event.query.filter_by(
        organizer_id=current_user.id
    ).order_by(
        Event.id.desc()
    ).all()

    return render_template(
        "organizer/dashboard.html",
        events=events
    )


@organizer_bp.route(
    "/create",
    methods=["GET", "POST"]
)
@login_required
def create_event():

    if current_user.role != "organizer":
        return "Access denied", 403

    if request.method == "POST":

        try:

            start = request.form["start_time"]
            end = request.form["end_time"]

            if start >= end:

                flash(
                    "End time must be after start time.",
                    "error"
                )

                return render_template(
                    "organizer/create_event.html"
                )

            event = Event(

                title=request.form[
                    "title"
                ].strip(),

                description=request.form[
                    "description"
                ].strip(),

                event_type=request.form[
                    "event_type"
                ],

                date=request.form[
                    "date"
                ],

                start_time=start,

                end_time=end,

                venue=request.form[
                    "venue"
                ].strip(),

                expected_attendees=int(
                    request.form[
                        "expected_attendees"
                    ]
                ),

                budget=float(
                    request.form[
                        "budget"
                    ]
                ),

                food_requirements=request.form.get(
                    "food_requirements",
                    ""
                ).strip(),

                equipment_requirements=request.form.get(
                    "equipment_requirements",
                    ""
                ).strip(),

                organizer_id=current_user.id,

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
