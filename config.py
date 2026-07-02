import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
    TRAINED_MODELS_DIR = os.path.join(BASE_DIR, 'trained_models')
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    UPLOADS_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
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
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Face recognition settings
    CONFIDENCE_THRESHOLD = 0.5
    LBPH_CONFIDENCE_THRESHOLD = 80
    REQUIRED_IMAGES_FOR_REGISTRATION = 40
    TRAINING_IMAGE_SIZE = (160, 160)

    # Attendance settings
    DAILY_CHECK_IN_START = '06:00'
    DAILY_CHECK_IN_END = '10:00'
    ATTENDANCE_AUTO_MARK = True

    # Application info
    APP_NAME = 'Smart Face Recognition Attendance System'
    APP_VERSION = '2.0.0'
    APP_DESCRIPTION = 'AI-Powered Attendance Management System'
    COMPANY_NAME = 'SmartVision Technologies'
    SUPPORT_EMAIL = 'support@smartvision.tech'


def create_directories():
    for directory in [Config.DATABASE_DIR, Config.DATASET_DIR, Config.TRAINED_MODELS_DIR,
                      Config.EXPORTS_DIR, Config.LOGS_DIR, Config.UPLOADS_DIR]:
        os.makedirs(directory, exist_ok=True)


create_directories()
