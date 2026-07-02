import os
import pickle
import logging
import numpy as np
import cv2
from config import Config
from models.database import db
from models.student import Student

logger = logging.getLogger(__name__)


class FaceTrainer:
    """Handles training of face recognition models using OpenCV LBPH."""

    def __init__(self):
        self.model_path = os.path.join(Config.TRAINED_MODELS_DIR, 'face_encodings.pkl')
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def extract_face(self, image_path: str):
        """Detect and extract face from an image, return grayscale face ROI."""
        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        if len(faces) == 0:
            return None
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y + h, x:x + w]
        face_roi = cv2.resize(face_roi, (100, 100))
        return face_roi

    def extract_embeddings_batch(self, student_id: str):
        """Extract face images for a student from dataset folder."""
        student_dir = os.path.join(Config.DATASET_DIR, student_id)
        if not os.path.exists(student_dir):
            logger.error(f'Dataset directory not found for {student_id}')
            return []

        faces = []
        image_files = sorted([
            f for f in os.listdir(student_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])

        for img_file in image_files:
            img_path = os.path.join(student_dir, img_file)
            face = self.extract_face(img_path)
            if face is not None:
                faces.append(face)
            else:
                logger.warning(f'No face found in {img_path}')

        logger.info(f'Extracted {len(faces)} face images for {student_id}')
        return faces

    def train_model(self, progress_callback=None):
        """Train the LBPH face recognizer on all students in the dataset."""
        all_faces = {}
        student_dirs = [
            d for d in os.listdir(Config.DATASET_DIR)
            if os.path.isdir(os.path.join(Config.DATASET_DIR, d))
        ]

        total = len(student_dirs)
        logger.info(f'Starting training for {total} students')

        for idx, student_id in enumerate(student_dirs):
            faces = self.extract_embeddings_batch(student_id)
            if faces:
                all_faces[student_id] = faces

            if progress_callback:
                progress = int(((idx + 1) / total) * 100)
                progress_callback(progress, student_id)

        self._save_model(all_faces)

        trained_count = len(all_faces)
        logger.info(f'Training complete. {trained_count}/{total} students trained.')
        return trained_count, total

    def _save_model(self, data: dict):
        """Save the trained face data to disk."""
        os.makedirs(Config.TRAINED_MODELS_DIR, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f'Face data saved to {self.model_path}')

    def load_model(self) -> dict:
        """Load the trained face data from disk."""
        if not os.path.exists(self.model_path):
            logger.warning(f'No trained model found at {self.model_path}')
            return {}
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)
        logger.info(f'Face data loaded with {len(data)} students')
        return data

    def get_training_status(self) -> dict:
        """Get current training status information."""
        model_exists = os.path.exists(self.model_path)
        student_dirs = [
            d for d in os.listdir(Config.DATASET_DIR)
            if os.path.isdir(os.path.join(Config.DATASET_DIR, d))
        ]

        total_images = 0
        for sid in student_dirs:
            sdir = os.path.join(Config.DATASET_DIR, sid)
            total_images += len([
                f for f in os.listdir(sdir)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ])

        return {
            'model_exists': model_exists,
            'total_students_in_dataset': len(student_dirs),
            'total_images': total_images,
        }
