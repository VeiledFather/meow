from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()
login_manager = LoginManager()


def create_app():

    app = Flask(__name__)


    # =====================================================
    # CONFIGURATION
    # =====================================================

    app.config["SECRET_KEY"] = "campushub-secret-key"

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///campushub.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


    # =====================================================
    # INITIALIZE EXTENSIONS
    # =====================================================

    db.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"


    # =====================================================
    # USER LOADER
    # =====================================================

    from app.models import User


    @login_manager.user_loader
    def load_user(user_id):

        return User.query.get(
            int(user_id)
        )


    # =====================================================
    # BLUEPRINT IMPORTS
    # =====================================================

    from app.routes.main import main_bp

    from app.routes.auth import auth_bp

    from app.routes.events import events_bp

    from app.routes.admin import admin_bp

    from app.routes.organizer import organizer_bp

    from app.routes.volunteer import volunteer_bp

    from app.routes.ai import ai_bp

    from app.routes.certificates import certificate_bp

    from app.routes.notifications import notification_bp


    # =====================================================
    # REGISTER BLUEPRINTS
    # =====================================================

    app.register_blueprint(
        main_bp
    )


    app.register_blueprint(
        auth_bp,
        url_prefix="/auth"
    )


    app.register_blueprint(
        events_bp,
        url_prefix="/events"
    )


    app.register_blueprint(
        admin_bp,
        url_prefix="/admin"
    )


    app.register_blueprint(
        organizer_bp,
        url_prefix="/organizer"
    )


    app.register_blueprint(
        volunteer_bp,
        url_prefix="/volunteer"
    )


    app.register_blueprint(
        ai_bp
    )


    app.register_blueprint(
        certificate_bp,
        url_prefix="/certificates"
    )


    app.register_blueprint(
        notification_bp
    )


    # =====================================================
    # DATABASE
    # =====================================================

    with app.app_context():

        db.create_all()


    return app
