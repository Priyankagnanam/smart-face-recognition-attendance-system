import os
import secrets
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_secret_key() -> str:
    """Resolve the Flask secret key.

    Priority:
      1. SECRET_KEY environment variable (required for production).
      2. A persistent random key stored in instance/secret.key (dev fallback so
         sessions survive restarts). Never a hard-coded value.
    """
    key = os.environ.get('SECRET_KEY')
    if key:
        return key

    key_file = Path(os.path.abspath(os.path.dirname(__file__))) / 'instance' / 'secret.key'
    if key_file.exists():
        stored = key_file.read_text().strip()
        if stored:
            return stored

    generated = secrets.token_hex(32)
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(generated)
    key_file.chmod(0o600)
    logger.warning(
        'SECRET_KEY environment variable is not set. '
        'Generated a persistent development key at %s. '
        'Set SECRET_KEY in your environment for production.',
        key_file,
    )
    return generated


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
    TRAINED_MODELS_DIR = os.path.join(BASE_DIR, 'trained_models')
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    UPLOADS_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
    SECRET_KEY = _resolve_secret_key()
    _db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'attendance.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{_db_path}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'timeout': 30,
            'check_same_thread': False,
        },
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Session hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'

    # Face recognition settings
    CONFIDENCE_THRESHOLD = 0.5
    # LBPH distance below which a prediction is accepted. Calibrated on the
    # live model: genuine matches under realistic lighting/pose reach p90=88,
    # p99=117 (measured with brightness/contrast/box augmentation over the
    # actual dataset), while unknown/noise subjects sit at 145+. Temporal
    # confirmation (RECOGNITION_CONSECUTIVE_FRAMES) guards false accepts.
    LBPH_CONFIDENCE_THRESHOLD = 120
    REQUIRED_IMAGES_FOR_REGISTRATION = 40
    TRAINING_IMAGE_SIZE = (160, 160)
    RECOGNITION_IMAGE_SIZE = (100, 100)
    FACE_PREPROCESS_CLAHE = True
    RECOGNITION_CONSECUTIVE_FRAMES = 3

    # Attendance settings
    DAILY_CHECK_IN_START = '06:00'
    DAILY_CHECK_IN_END = '10:00'
    ATTENDANCE_AUTO_MARK = True

    # Application info
    APP_NAME = 'Smart Face Recognition Attendance System'
    APP_VERSION = '2.1.0'
    APP_DESCRIPTION = 'AI-Powered Attendance Management System'
    COMPANY_NAME = 'SmartVision Technologies'
    SUPPORT_EMAIL = 'support@smartvision.tech'


def create_directories():
    for directory in [Config.DATABASE_DIR, Config.DATASET_DIR, Config.TRAINED_MODELS_DIR,
                      Config.EXPORTS_DIR, Config.LOGS_DIR, Config.UPLOADS_DIR]:
        os.makedirs(directory, exist_ok=True)


create_directories()
