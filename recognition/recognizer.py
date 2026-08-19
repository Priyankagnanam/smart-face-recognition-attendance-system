import cv2
import numpy as np
import logging
import threading
import time
from datetime import datetime
from config import Config
from recognition.trainer import FaceTrainer
from recognition.cascades import load_face_cascade
from recognition.preprocess import preprocess_face_crop
from models.database import db
from models.student import Student
from models.attendance import Attendance

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """Real-time face recognition with attendance marking using OpenCV LBPH."""

    def __init__(self, app=None):
        self.trainer = FaceTrainer()
        self.model_data = {}
        self.model_loaded = False
        self.is_running = False
        self.cap = None
        try:
            self.face_cascade = load_face_cascade()
        except (FileNotFoundError, RuntimeError) as e:
            logger.error('Face cascade unavailable: %s', e)
            self.face_cascade = None
        self.current_frame = None
        self.recognized_faces = []
        self.last_recognition = None
        self.last_frame_faces = 0
        self._lock = threading.Lock()
        self.lbph_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.label_map = {}
        self._app = app
        self._consecutive = {}

    def _build_recognizer(self, model_data: dict):
        """Build an LBPH recognizer from a model_data dict.

        Returns (recognizer, label_map) or (None, {}) when there is nothing
        trainable. label_map maps LBPH label id -> student_id.
        """
        faces = []
        labels = []
        label_map = {}
        current_label = 0

        for student_id, student_faces in model_data.items():
            for face in student_faces:
                faces.append(face)
                labels.append(current_label)
            label_map[current_label] = student_id
            current_label += 1

        if not faces:
            return None, {}

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces, np.array(labels))
        return recognizer, label_map

    def load_model(self) -> bool:
        """Load the trained face data and train LBPH recognizer."""
        self.model_data = self.trainer.load_model()
        if not self.model_data:
            self.model_loaded = False
            return False

        recognizer, label_map = self._build_recognizer(self.model_data)
        if recognizer is None:
            self.model_loaded = False
            self.label_map = {}
            return False

        self.lbph_recognizer = recognizer
        self.label_map = label_map
        self.model_loaded = True
        logger.info(
            f'LBPH recognizer trained with {len(self.model_data)} students '
            f'({sum(len(f) for f in self.model_data.values())} faces)'
        )
        return True

    def reload_model(self) -> bool:
        """Rebuild the in-memory LBPH recognizer from the freshest pickle on disk.

        Called after 'Settings -> Train Model' or face-capture auto-training so
        recognition immediately uses the newly generated model instead of a stale
        one. Safe to call while the recognition loop is running: a brand-new
        recognizer is trained and swapped in atomically.
        """
        model_data = self.trainer.load_model()
        if not model_data:
            self.model_loaded = False
            self.label_map = {}
            return False

        recognizer, label_map = self._build_recognizer(model_data)
        if recognizer is None:
            self.model_loaded = False
            self.label_map = {}
            return False

        with self._lock:
            self.lbph_recognizer = recognizer
            self.label_map = label_map
            self.model_data = model_data
            self.model_loaded = True
        logger.info(
            f'LBPH recognizer RELOADED from {self.trainer.model_path} '
            f'({len(model_data)} students, '
            f'{sum(len(f) for f in model_data.values())} faces)'
        )
        return True

    def start_recognition(self):
        """Start the real-time face recognition loop.
        Camera starts regardless of model; recognition only when model is loaded.
        """
        if self.face_cascade is None:
            logger.error('Face cascade unavailable - cannot start recognition')
            return False

        # If a loop is already running, stop it first so we never stack loops
        # or hold the camera twice.
        if self.is_running:
            self.stop_recognition()

        if not self.load_model():
            logger.warning('No trained model available - camera will start without recognition')

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logger.error('Failed to open camera')
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.is_running = True
        self.recognized_faces = []
        self.last_recognition = None
        self.last_frame_faces = 0
        self._consecutive = {}
        self._frame_timeout = 1.0

        thread = threading.Thread(target=self._recognition_loop, daemon=True)
        thread.start()
        logger.info('Face recognition started')
        return True

    def _mark_attendance(self, student_id, confidence_val, today):
        """Mark attendance within a Flask app context."""
        ctx = self._app.app_context() if self._app else None
        if ctx:
            ctx.push()
        try:
            student = Student.query.get(student_id)
            if not student:
                return None

            existing = Attendance.query.filter_by(
                student_id=student_id,
                attendance_date=today
            ).first()
            if existing:
                return None

            now = datetime.now()
            confidence_score = max(0.0, 1.0 - confidence_val / 100.0)
            attendance = Attendance(
                student_id=student_id,
                attendance_date=today,
                check_in_time=now.time(),
                status='Present',
                confidence_score=float(confidence_score),
            )
            db.session.add(attendance)
            db.session.commit()
            logger.info(f'Auto-marked attendance: {student.name} ({confidence_score:.2f})')
            return student
        except Exception as e:
            logger.error(f'Failed to mark attendance: {e}')
            return None
        finally:
            if ctx:
                ctx.pop()

    def _update_temporal_counts(self, recognized_ids):
        """Track how many consecutive frames each student has been recognized on.

        A student's counter resets whenever they are missing from a frame, so a
        single unstable/random frame cannot mark attendance. Returns the current
        consecutive-frame count for every recognized student.
        """
        for sid in list(self._consecutive.keys()):
            if sid not in recognized_ids:
                del self._consecutive[sid]
        for sid in recognized_ids:
            self._consecutive[sid] = self._consecutive.get(sid, 0) + 1
        return {sid: self._consecutive[sid] for sid in recognized_ids}

    def _recognition_loop(self):
        """Main recognition loop running in a separate thread."""
        recognized_students_today = set()
        today = datetime.now().date()

        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.03)
                    continue
            except:
                time.sleep(0.03)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
            )
            # Prefer the largest face so we never recognize random small regions
            # of the frame as a face.
            faces = sorted(faces, key=lambda b: b[2] * b[3], reverse=True)

            face_results = []
            recognized_this_frame = set()

            for (x, y, w, h) in faces:
                # SAME preprocessing as training (see preprocess_face_crop).
                face_roi = preprocess_face_crop(gray[y:y + h, x:x + w])

                student_id = None
                confidence_val = Config.LBPH_CONFIDENCE_THRESHOLD + 1

                if self.model_loaded:
                    try:
                        label_id, confidence = self.lbph_recognizer.predict(face_roi)
                        candidate_id = self.label_map.get(label_id, None)
                        logger.debug(
                            'Detected face: x=%d y=%d w=%d h=%d | live face shape: %s | '
                            'predicted student: %s | best distance: %.1f | recognition threshold: %.1f | status: %s',
                            x, y, w, h, face_roi.shape, candidate_id, confidence,
                            Config.LBPH_CONFIDENCE_THRESHOLD,
                            'MATCH' if candidate_id is not None and confidence < Config.LBPH_CONFIDENCE_THRESHOLD else 'UNKNOWN'
                        )
                        if candidate_id is not None and confidence < Config.LBPH_CONFIDENCE_THRESHOLD:
                            student_id = candidate_id
                            confidence_val = confidence
                    except Exception as e:
                        logger.debug('Recognition prediction error: %s', e)

                if student_id is not None:
                    recognized_this_frame.add(student_id)
                face_results.append(((x, y, w, h), student_id, confidence_val))

            # Temporal confirmation: a student is only trusted after being
            # recognized on several consecutive valid frames.
            counts = self._update_temporal_counts(recognized_this_frame)

            current_recognitions = []

            for (box, student_id, confidence_val) in face_results:
                x, y, w, h = box
                stable_frames = counts.get(student_id, 0) if student_id else 0
                is_confirmed = student_id is not None and stable_frames >= Config.RECOGNITION_CONSECUTIVE_FRAMES

                if is_confirmed:
                    student = None
                    already_marked = False
                    if student_id not in recognized_students_today:
                        student = self._mark_attendance(student_id, confidence_val, today)
                        if student:
                            recognized_students_today.add(student_id)
                            logger.info(
                                'Attendance confirmed for %s after %d consecutive frames (distance=%.1f)',
                                student.name, stable_frames, confidence_val,
                            )
                    else:
                        already_marked = True
                        if self._app:
                            ctx2 = self._app.app_context()
                            ctx2.push()
                            try:
                                student = Student.query.get(student_id)
                            except:
                                student = None
                            finally:
                                ctx2.pop()

                    if student:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (34, 197, 94), 2)
                        label = f'{student.name} ({100 - confidence_val:.1f}%)'
                        cv2.putText(frame, label, (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (34, 197, 94), 2)
                        current_recognitions.append({
                            'student_id': student_id,
                            'name': student.name,
                            'confidence': max(0.0, 1.0 - confidence_val / 100.0),
                            'attendance_marked': student_id in recognized_students_today,
                        })
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (239, 68, 68), 2)
                        cv2.putText(frame, 'Unknown', (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (239, 68, 68), 2)
                elif student_id is not None:
                    # Recognized on this frame but not yet stable -> keep verifying.
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (245, 158, 11), 2)
                    cv2.putText(frame, 'Verifying...', (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (245, 158, 11), 2)
                else:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (239, 68, 68), 2)
                    cv2.putText(frame, 'Unknown', (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (239, 68, 68), 2)

            model_status = 'Model: Active' if self.model_loaded else 'Model: Not Trained'
            info_text = f'Faces: {len(faces)} | Recognized: {len(current_recognitions)} | {model_status}'
            cv2.putText(frame, info_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            with self._lock:
                self.current_frame = frame
                self.recognized_faces = current_recognitions
                self.last_frame_faces = len(faces)
                if current_recognitions:
                    self.last_recognition = current_recognitions[0]

            time.sleep(0.03)

    def stop_recognition(self):
        """Stop the recognition loop and release camera."""
        self.is_running = False
        time.sleep(0.1)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        with self._lock:
            self.recognized_faces = []
            self.last_recognition = None
            self.last_frame_faces = 0
        logger.info('Face recognition stopped')

    def get_frame(self):
        """Get the current video frame with recognition overlay."""
        with self._lock:
            if self.current_frame is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.current_frame)
            if not ret:
                return None
            return jpeg.tobytes()

    def get_recognized_faces(self) -> list:
        """Get list of currently recognized faces."""
        with self._lock:
            return list(self.recognized_faces)

    def get_recognition_status(self) -> dict:
        """Get the recognition state the live-attendance UI needs.

        Returns the currently recognized faces, falling back to the most recent
        confirmed recognition (so the UI keeps showing a student who was marked
        even if recognition briefly drops on individual frames), plus whether a
        face is currently detected. The UI never infers recognition itself.
        """
        with self._lock:
            recognized = list(self.recognized_faces)
            if not recognized and self.is_running and self.last_recognition:
                recognized = [dict(self.last_recognition)]
            return {
                'running': self.is_running,
                'faces_detected': self.last_frame_faces > 0,
                'recognized': recognized,
            }
