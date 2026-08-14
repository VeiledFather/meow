from app.models import (
    Event,
    Registration,
    Certificate,
    Review,
    VolunteerApplication,
)


def get_user_context(user):

    role = user.role

    lines = [
        f"Current user: {user.name}",
        f"Current role: {role}",
        "",
    ]


    # =====================================================
    # STUDENT CONTEXT
    # =====================================================

    if role == "student":

        registrations = (
            Registration.query
            .filter_by(student_id=user.id)
            .all()
        )


        if registrations:

            lines.append("STUDENT REGISTRATIONS:")

            for registration in registrations:

                event = registration.event

                if not event:
                    continue

                lines.append(
                    f"- {event.title} | "
                    f"{event.event_type} | "
                    f"{event.date} | "
                    f"{event.start_time}-{event.end_time} | "
                    f"Venue: {event.venue} | "
                    f"Status: {registration.status} | "
                    f"Checked in: "
                    f"{'Yes' if registration.checked_in else 'No'}"
                )

        else:

            lines.append(
                "STUDENT REGISTRATIONS: None"
            )


        certificates = (
            Certificate.query
            .filter_by(student_id=user.id)
            .all()
        )


        if certificates:

            lines.append("")
            lines.append("STUDENT CERTIFICATES:")

            for certificate in certificates:

                event = certificate.event

                if event:

                    lines.append(
                        f"- {event.title} | "
                        f"Certificate: "
                        f"{certificate.certificate_code} | "
                        f"Issued: "
                        f"{certificate.issued_at}"
                    )

        else:

            lines.append(
                "STUDENT CERTIFICATES: None"
            )


        reviews = (
            Review.query
            .filter_by(student_id=user.id)
            .all()
        )


        if reviews:

            lines.append("")
            lines.append("STUDENT REVIEWS:")

            for review in reviews:

                event = review.event

                if event:

                    lines.append(
                        f"- {event.title} | "
                        f"Rating: {review.rating}/5 | "
                        f"Comment: "
                        f"{review.comment or 'No comment'}"
                    )


        upcoming_events = (
            Event.query
            .filter_by(status="approved")
            .order_by(Event.date.asc())
            .limit(30)
            .all()
        )


        if upcoming_events:

            lines.append("")
            lines.append("AVAILABLE CAMPUS EVENTS:")

            for event in upcoming_events:

                lines.append(
                    f"- {event.title} | "
                    f"{event.event_type} | "
                    f"{event.date} | "
                    f"{event.start_time}-{event.end_time} | "
                    f"Venue: {event.venue}"
                )


    # =====================================================
    # ORGANIZER CONTEXT
    # =====================================================

    elif role == "organizer":

        events = (
            Event.query
            .filter_by(
                organizer_id=user.id
            )
            .order_by(Event.date.desc())
            .all()
        )


        if events:

            lines.append(
                "ORGANIZER EVENTS:"
            )

            for event in events:

                lines.append(
                    f"- {event.title} | "
                    f"{event.event_type} | "
                    f"{event.date} | "
                    f"{event.start_time}-{event.end_time} | "
                    f"Venue: {event.venue} | "
                    f"Status: {event.status} | "
                    f"Expected attendees: "
                    f"{event.expected_attendees}"
                )

        else:

            lines.append(
                "ORGANIZER EVENTS: None"
            )


    # =====================================================
    # VOLUNTEER CONTEXT
    # =====================================================

    elif role == "volunteer":

        applications = (
            VolunteerApplication.query
            .filter_by(
                volunteer_id=user.id
            )
            .all()
        )


        if applications:

            lines.append(
                "VOLUNTEER ASSIGNMENTS:"
            )

            for application in applications:

                event = application.event

                if not event:
                    continue

                lines.append(
                    f"- {event.title} | "
                    f"{event.date} | "
                    f"{event.start_time}-{event.end_time} | "
                    f"Venue: {event.venue} | "
                    f"Assignment status: "
                    f"{application.status}"
                )

        else:

            lines.append(
                "VOLUNTEER ASSIGNMENTS: None"
            )


    # =====================================================
    # ADMIN
    # =====================================================

    elif role == "admin":

        event_count = Event.query.count()

        approved_count = Event.query.filter_by(
            status="approved"
        ).count()

        pending_count = Event.query.filter_by(
            status="pending"
        ).count()

        registration_count = Registration.query.count()

        lines.extend([
            "ADMIN CAMPUS OVERVIEW:",
            f"- Total events: {event_count}",
            f"- Approved events: {approved_count}",
            f"- Pending events: {pending_count}",
            f"- Total registrations: {registration_count}",
        ])


    return "\n".join(lines)
