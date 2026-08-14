
from flask import (
    Blueprint,
    render_template
)

from flask_login import (
    login_required,
    current_user
)

from app.models import Event


events_bp = Blueprint(
    "events",
    __name__
)


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


@events_bp.route(
    "/<int:event_id>"
)
@login_required
def details(event_id):

    event = Event.query.get_or_404(
        event_id
    )

    return render_template(
        "events/detail.html",
        event=event
    )
