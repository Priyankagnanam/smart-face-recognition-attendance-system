import logging
import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from models.database import db
from models.user import User
from utils.security import limiter

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter username and password.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            logger.info(f'User {username} logged in successfully')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            logger.warning(f'Failed login attempt for username: {username}')
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    logger.info(f'User {username} logged out')
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/check-session')
def check_session():
    return jsonify({'authenticated': current_user.is_authenticated}), 200


def create_default_admin():
    """Create the initial admin user if none exists.

    Credentials are read from environment variables:
      ADMIN_USERNAME (default: admin)
      ADMIN_PASSWORD

    If ADMIN_PASSWORD is not set, a strong random password is generated and
    printed once to the log/console. There is no fixed default password.
    """
    username = os.environ.get('ADMIN_USERNAME', 'admin').strip() or 'admin'
    admin = User.query.filter_by(username=username).first()
    if admin:
        return

    password = os.environ.get('ADMIN_PASSWORD')
    generated = False
    if not password:
        password = secrets.token_urlsafe(12)
        generated = True

    admin = User(
        username=username,
        role='admin'
    )
    admin.set_password(password)
    db.session.add(admin)
    try:
        db.session.commit()
    except IntegrityError:
        # Multiple gunicorn workers boot simultaneously; another worker
        # already created the admin user. That is fine - roll back and continue.
        db.session.rollback()
        logger.info('Admin user "%s" already created by another worker.', username)
        return

    if generated:
        logger.warning(
            'No ADMIN_PASSWORD environment variable set. '
            'Created admin user "%s" with a generated password: %s  '
            '(change it after first login and set ADMIN_PASSWORD for future installs).',
            username, password,
        )
    else:
        logger.info('Admin user "%s" created from environment configuration.', username)
