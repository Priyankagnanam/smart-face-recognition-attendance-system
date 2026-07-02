import logging
import os
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from config import Config

logger = logging.getLogger(__name__)
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/')
@login_required
def index():
    return render_template('settings.html')


@settings_bp.route('/api/info')
@login_required
def api_info():
    dataset_count = 0
    dataset_dir = Config.DATASET_DIR
    if os.path.exists(dataset_dir):
        for root, dirs, files in os.walk(dataset_dir):
            dataset_count += len([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    model_file = os.path.join(Config.TRAINED_MODELS_DIR, 'face_encodings.pkl')
    model_exists = os.path.exists(model_file)

    db_file = os.path.join(Config.DATABASE_DIR, 'attendance.db')
    db_size = 0
    if os.path.exists(db_file):
        db_size = round(os.path.getsize(db_file) / 1024, 1)

    return jsonify({
        'app_name': Config.APP_NAME,
        'app_version': Config.APP_VERSION,
        'app_description': Config.APP_DESCRIPTION,
        'company_name': Config.COMPANY_NAME,
        'support_email': Config.SUPPORT_EMAIL,
        'dataset_count': dataset_count,
        'model_exists': model_exists,
        'db_size': db_size,
        'python_version': __import__('sys').version,
        'flask_version': __import__('flask').__version__,
        'opencv_version': __import__('cv2').__version__,
    })
