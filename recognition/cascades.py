import os
import logging
import cv2
from config import Config

logger = logging.getLogger(__name__)

FACE_CASCADE_FILENAME = 'haarcascade_frontalface_default.xml'
FACE_CASCADE_PATH = os.path.join(
    Config.BASE_DIR, 'recognition', 'cascades', FACE_CASCADE_FILENAME
)


def load_face_cascade():
    """Load the Haar cascade from the project-local cascades directory.

    The cascade file is shipped inside this repository (recognition/cascades/)
    so face detection never depends on OpenCV's bundled data files, which are
    not present in every OpenCV distribution.

    Raises:
        FileNotFoundError: if the cascade file is missing from the project.
        RuntimeError: if OpenCV cannot parse/load the cascade file.
    """
    if not os.path.exists(FACE_CASCADE_PATH):
        logger.error('Face cascade file not found at %s', FACE_CASCADE_PATH)
        raise FileNotFoundError(
            f'Haar cascade file not found: {FACE_CASCADE_PATH}. '
            'Ensure recognition/cascades/haarcascade_frontalface_default.xml '
            'is present in the repository.'
        )

    cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    if cascade.empty():
        logger.error('Failed to load Haar cascade from %s', FACE_CASCADE_PATH)
        raise RuntimeError(f'Failed to load Haar cascade: {FACE_CASCADE_PATH}')

    logger.debug('Loaded Haar cascade from %s', FACE_CASCADE_PATH)
    return cascade
