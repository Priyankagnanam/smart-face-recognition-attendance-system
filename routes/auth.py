import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.database import db
from models.user import User

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
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
    """Create default admin user if none exists."""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logger.info('Default admin user created (admin/admin123)')
