import cv2
import os
import time
import threading
import logging
import numpy as np
from config import Config
from recognition.cascades import load_face_cascade

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages webcam operations for face capture and recognition."""

    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap = None

    def open_camera(self) -> bool:
        """Open the webcam."""
        if self.cap is not None:
            self.release_camera()
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            logger.error(f'Failed to open camera {self.camera_id}')
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        logger.info(f'Camera {self.camera_id} opened successfully')
        return True

    def release_camera(self):
        """Release the webcam."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info('Camera released')

    def capture_frame(self):
        """Capture a single frame from the webcam with timeout."""
        if self.cap is None:
            if not self.open_camera():
                return None
        result = [None]
        def _read():
            try:
                ret, frame = self.cap.read()
                if ret:
                    result[0] = frame
            except:
                pass
        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout=1)
        if result[0] is None:
            return None
        return result[0]

    def capture_faces_for_registration(self, student_id: str, num_images: int = 40):
        """Capture multiple face images for student registration."""
        student_dir = os.path.join(Config.DATASET_DIR, student_id)
        os.makedirs(student_dir, exist_ok=True)

        try:
            face_cascade = load_face_cascade()
        except (FileNotFoundError, RuntimeError) as e:
            logger.error('Face cascade unavailable: %s', e)
            return []

        if not self.open_camera():
            return []

        captured = 0
        captured_files = []
        last_saved_gray = None
        start_time = time.time()
        max_duration = 20

        while captured < num_images:
            if time.time() - start_time > max_duration:
                logger.info('Capture timed out')
                break

            frame = self.capture_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
            )

            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face_img = frame[y:y + h, x:x + w]
                face_img = cv2.resize(face_img, Config.TRAINING_IMAGE_SIZE)

                # Save the grayscale crop so training and live recognition use
                # the exact same single-channel representation.
                face_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)

                # Skip near-duplicate frames so training data is diverse.
                if last_saved_gray is not None:
                    diff = cv2.absdiff(face_gray, last_saved_gray)
                    mean_diff = float(np.mean(diff))
                    if mean_diff < 6.0:
                        time.sleep(0.1)
                        continue
                last_saved_gray = face_gray

                filename = f'{student_id}_{captured:03d}.jpg'
                filepath = os.path.join(student_dir, filename)
                cv2.imwrite(filepath, face_gray)
                captured_files.append(filepath)
                captured += 1
                time.sleep(0.12)

        self.release_camera()

        logger.info(f'Captured {len(captured_files)} face images for student {student_id}')
        return captured_files

    def get_available_cameras(self, max_cameras: int = 5) -> list:
        """Detect available camera indices."""
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
