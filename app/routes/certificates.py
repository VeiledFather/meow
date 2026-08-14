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
    Certificate,
    Registration,
    Event
)

import secrets


certificate_bp = Blueprint(
    "certificate",
    __name__
)


# =========================================================
# MY CERTIFICATES
# =========================================================

@certificate_bp.route("/")
@login_required
def my_certificates():

    if current_user.role != "student":

        return "Access denied", 403


    certificates = Certificate.query.filter_by(
        student_id=current_user.id
    ).order_by(
        Certificate.issued_at.desc()
    ).all()


    return render_template(
        "certificates/my_certificates.html",
        certificates=certificates
    )


# =========================================================
# GENERATE CERTIFICATE
# =========================================================

@certificate_bp.route(
    "/generate/<int:event_id>",
    methods=["POST"]
)
@login_required
def generate(event_id):

    if current_user.role != "student":

        return "Access denied", 403


    event = Event.query.get_or_404(
        event_id
    )


    # -----------------------------------------------------
    # Student must have registered
    # -----------------------------------------------------

    registration = Registration.query.filter_by(
        student_id=current_user.id,
        event_id=event.id
    ).first()


    if not registration:

        flash(
            "You were not registered for this event.",
            "error"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    # -----------------------------------------------------
    # Student must actually have attended
    # -----------------------------------------------------

    if not registration.checked_in:

        flash(
            "Your certificate will become available after you attend the event.",
            "info"
        )

        return redirect(
            url_for(
                "events.details",
                event_id=event.id
            )
        )


    # -----------------------------------------------------
    # Don't create duplicate certificates
    # -----------------------------------------------------

    existing = Certificate.query.filter_by(
        student_id=current_user.id,
        event_id=event.id
    ).first()


    if existing:

        return redirect(
            url_for(
                "certificate.view",
                certificate_id=existing.id
            )
        )


    # -----------------------------------------------------
    # Generate unique certificate code
    # -----------------------------------------------------

    certificate_code = (
        "CERT-"
        + secrets.token_hex(8).upper()
    )


    certificate = Certificate(

        student_id=current_user.id,

        event_id=event.id,

        certificate_code=
            certificate_code

    )


    db.session.add(
        certificate
    )

    db.session.commit()


    flash(
        "Your digital certificate has been issued.",
        "success"
    )


    return redirect(
        url_for(
            "certificate.view",
            certificate_id=certificate.id
        )
    )


# =========================================================
# VIEW CERTIFICATE
# =========================================================

@certificate_bp.route(
    "/<int:certificate_id>"
)
@login_required
def view(certificate_id):

    certificate = Certificate.query.get_or_404(
        certificate_id
    )


    # Students can only view their own certificates.
    if current_user.role == "student":

        if certificate.student_id != current_user.id:

            return "Access denied", 403


    return render_template(
        "certificates/certificate.html",
        certificate=certificate
    )


# =========================================================
# VERIFY CERTIFICATE
# =========================================================

@certificate_bp.route(
    "/verify/<certificate_code>"
)
def verify(certificate_code):

    certificate = Certificate.query.filter_by(
        certificate_code=certificate_code
    ).first()


    if not certificate:

        return render_template(
            "certificates/verify.html",
            certificate=None
        )


    return render_template(
        "certificates/verify.html",
        certificate=certificate
    )
