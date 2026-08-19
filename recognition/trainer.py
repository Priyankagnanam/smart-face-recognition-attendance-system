import os
import pickle
import logging
import cv2
from config import Config
from recognition.cascades import load_face_cascade
from recognition.preprocess import preprocess_face_crop

logger = logging.getLogger(__name__)


class FaceTrainer:
    """Handles training of face recognition models using OpenCV LBPH."""

    def __init__(self):
        self.model_path = os.path.join(Config.TRAINED_MODELS_DIR, 'face_encodings.pkl')
        try:
            self.face_cascade = load_face_cascade()
        except (FileNotFoundError, RuntimeError) as e:
            logger.error('Face cascade unavailable: %s', e)
            self.face_cascade = None

    def extract_face(self, image_path: str):
        """Load a saved face crop and normalize it for training.

        Saved dataset images are already tight face crops produced by capture,
        so we do NOT re-run Haar detection on them. Re-detecting inside an
        already-cropped face is unreliable (it often finds a different, smaller
        sub-region or nothing at all) and would make the training samples
        structurally different from the live camera crops. Instead we apply the
        SAME preprocessing used by live recognition (grayscale -> resize to
        100x100 -> optional CLAHE), so training and live inputs match.
        """
        img = cv2.imread(image_path)
        if img is None:
            return None
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        return preprocess_face_crop(gray)

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

    @staticmethod
    def _dir_has_images(dir_path: str) -> bool:
        return any(
            f.lower().endswith(('.jpg', '.jpeg', '.png'))
            for f in os.listdir(dir_path)
        )

    def train_model(self, progress_callback=None):
        """Train the LBPH face recognizer on ALL students in the dataset.

        Training ALWAYS rebuilds the model from the current dataset directory,
        so the persisted model can never go stale while images exist on disk.
        Empty directories are ignored (they contain no face samples).
        """
        all_faces = {}
        student_dirs = [
            d for d in os.listdir(Config.DATASET_DIR)
            if os.path.isdir(os.path.join(Config.DATASET_DIR, d))
            and self._dir_has_images(os.path.join(Config.DATASET_DIR, d))
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
            and self._dir_has_images(os.path.join(Config.DATASET_DIR, d))
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
