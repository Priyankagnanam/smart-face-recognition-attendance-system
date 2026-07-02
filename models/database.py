from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def create_database():
    """Create all database tables."""
    db.create_all()


def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    with app.app_context():
        create_database()
