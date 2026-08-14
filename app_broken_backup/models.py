
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="student")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    description = db.Column(db.Text, nullable=False)

    event_type = db.Column(db.String(50), nullable=False)

    date = db.Column(db.String(20), nullable=False)

    start_time = db.Column(db.String(10), nullable=False)

    end_time = db.Column(db.String(10), nullable=False)

    venue = db.Column(db.String(150), nullable=False)

    expected_attendees = db.Column(db.Integer, default=0)

    budget = db.Column(db.Float, default=0)

    food_requirements = db.Column(
        db.Text,
        default=""
    )

    equipment_requirements = db.Column(
        db.Text,
        default=""
    )

    status = db.Column(
        db.String(30),
        default="pending"
    )

    organizer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
