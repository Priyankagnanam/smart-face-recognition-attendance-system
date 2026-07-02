import os
import logging
from datetime import datetime
from config import Config


def setup_logging():
    """Configure application logging."""
    log_file = os.path.join(Config.LOGS_DIR, f'app_{datetime.now().strftime("%Y%m%d")}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger(__name__)


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if a file has an allowed extension."""
    if allowed_extensions is None:
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


def format_confidence(confidence: float) -> str:
    """Format confidence score as percentage string."""
    return f'{confidence * 100:.1f}%'
