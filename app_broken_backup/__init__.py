
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "campushub-secret-key"

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///campushub.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(
            User,
            int(user_id)
        )

    from app.routes.auth import auth_bp
    from app.routes.organizer import organizer_bp
    from app.routes.admin import admin_bp
    from app.routes.events import events_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/auth"
    )

    app.register_blueprint(
        organizer_bp,
        url_prefix="/organizer"
    )

    app.register_blueprint(
        admin_bp,
        url_prefix="/admin"
    )

    app.register_blueprint(
        events_bp,
        url_prefix="/events"
    )

    @app.route("/")
    def home():

        from flask_login import current_user

        if current_user.is_authenticated:

            if current_user.role == "organizer":
                return '<script>location.href="/organizer/dashboard"</script>'

            if current_user.role == "admin":
                return '<script>location.href="/admin/dashboard"</script>'

            return '<script>location.href="/events/"</script>'

        return '<script>location.href="/auth/login"</script>'

    with app.app_context():

        db.create_all()

        create_demo_users()

    return app


def create_demo_users():

    from app.models import User

    demo_users = [

        (
            "Demo Student",
            "student@campus.com",
            "student"
        ),

        (
            "Demo Organizer",
            "organizer@campus.com",
            "organizer"
        ),

        (
            "College Administrator",
            "admin@campus.com",
            "admin"
        ),

        (
            "Demo Volunteer",
            "volunteer@campus.com",
            "volunteer"
        )

    ]

    for name, email, role in demo_users:

        user = User.query.filter_by(
            email=email
        ).first()

        if user is None:

            user = User(
                name=name,
                email=email,
                role=role
            )

            user.set_password("123456")

            db.session.add(user)

    db.session.commit()
