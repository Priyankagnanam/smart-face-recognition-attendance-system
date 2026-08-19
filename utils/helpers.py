import os
import re
import logging
from datetime import datetime
from config import Config

# Student IDs become dataset directory names and DB primary keys. Restrict to
# alphanumeric plus dash/underscore so they can never traverse directories or
# collide with path separators.
STUDENT_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')


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


def is_valid_student_id(student_id: str) -> bool:
    """Return True when a student ID is safe to use as a dataset directory.

    Student IDs are embedded in filesystem paths (dataset/<student_id> and
    dataset/<student_id>/<student_id>_NNN.jpg), so they must not contain path
    separators or traversal sequences. Alphanumeric plus '-'/'_' only.
    """
    return bool(STUDENT_ID_RE.match(student_id or ''))
