import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from config import Config
from models.database import init_db, db
from models.user import User
from models.student import Student
from models.attendance import Attendance
from routes.auth import auth_bp, create_default_admin
from routes.dashboard import dashboard_bp
from routes.student import student_bp
from routes.attendance import attendance_bp
from routes.reports import reports_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp
from routes.recognition_routes import recognition_bp, init_recognizer
from utils.helpers import setup_logging
from flask_login import LoginManager
from sqlalchemy import event


logger = setup_logging()


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)

    with app.app_context():
        @event.listens_for(db.engine, 'connect')
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA busy_timeout=30000')
            cursor.execute('PRAGMA synchronous=NORMAL')
            cursor.close()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(recognition_bp)
    init_recognizer(app)

    with app.app_context():
        create_default_admin()

    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('500.html'), 500

    logger.info('Smart Face Recognition Attendance System started')
    return app


app = create_app()

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=False,
        threaded=True,
    )
