import cv2
import logging
from config import Config

logger = logging.getLogger(__name__)

# CLAHE is created once and reused so training and live recognition apply the
# exact same illumination normalization to every face crop.
_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)) if Config.FACE_PREPROCESS_CLAHE else None


def preprocess_face_crop(gray_crop):
    """Canonical face-crop preprocessing shared by training and live recognition.

    Input:  grayscale face crop (uint8, any size / aspect ratio).
    Output: uint8 grayscale (RECOGNITION_IMAGE_SIZE) ready for the LBPH recognizer.

    Because both the training pipeline and the live camera loop call this exact
    function, the two inputs fed to the LBPH matcher are guaranteed to go through
    identical steps: resize to 100x100, then optional CLAHE contrast equalization.
    """
    if gray_crop is None or gray_crop.size == 0:
        return None

    target_w, target_h = Config.RECOGNITION_IMAGE_SIZE
    src_h, src_w = gray_crop.shape[:2]
    if src_h > target_h or src_w > target_w:
        interp = cv2.INTER_AREA
    else:
        interp = cv2.INTER_LINEAR

    roi = cv2.resize(gray_crop, (target_w, target_h), interpolation=interp)
    if _clahe is not None:
        roi = _clahe.apply(roi)
    return roi