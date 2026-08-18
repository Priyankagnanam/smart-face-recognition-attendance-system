import os
import cv2
import numpy as np
import logging
import threading
import time
from datetime import datetime
from config import Config
from recognition.trainer import FaceTrainer
from recognition.cascades import load_face_cascade
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
        self._lock = threading.Lock()
        self.lbph_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.label_map = {}
        self._app = app

    def load_model(self) -> bool:
        """Load the trained face data and train LBPH recognizer."""
        self.model_data = self.trainer.load_model()
        if not self.model_data:
            self.model_loaded = False
            return False

        faces = []
        labels = []
        self.label_map = {}
        current_label = 0

        for student_id, student_faces in self.model_data.items():
            for face in student_faces:
                faces.append(face)
                labels.append(current_label)
            self.label_map[current_label] = student_id
            current_label += 1

        if faces:
            self.lbph_recognizer.train(faces, np.array(labels))
            self.model_loaded = True
            logger.info(f'LBPH recognizer trained with {len(faces)} faces across {len(self.label_map)} students')
            return True

        self.model_loaded = False
        return False

    def start_recognition(self):
        """Start the real-time face recognition loop.
        Camera starts regardless of model; recognition only when model is loaded.
        """
        if self.face_cascade is None:
            logger.error('Face cascade unavailable - cannot start recognition')
            return False

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

            current_recognitions = []

            for (x, y, w, h) in faces:
                face_roi = gray[y:y + h, x:x + w]
                face_roi = cv2.resize(face_roi, (100, 100))

                student_id = None
                confidence_val = 100

                if self.model_loaded:
                    try:
                        label_id, confidence = self.lbph_recognizer.predict(face_roi)
                        student_id = self.label_map.get(label_id, None)
                        confidence_val = confidence
                    except Exception as e:
                        student_id = None
                        confidence_val = 100

                from config import Config as AppConfig
                if student_id and confidence_val < AppConfig.LBPH_CONFIDENCE_THRESHOLD:
                    student = None
                    already_marked = False
                    if student_id not in recognized_students_today:
                        student = self._mark_attendance(student_id, confidence_val, today)
                        if student:
                            recognized_students_today.add(student_id)
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
                            'attendance_marked': not already_marked,
                        })
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (239, 68, 68), 2)
                        cv2.putText(frame, 'Unknown', (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (239, 68, 68), 2)
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

            time.sleep(0.03)

    def stop_recognition(self):
        """Stop the recognition loop and release camera."""
        self.is_running = False
        time.sleep(0.1)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
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
