import logging
import os
import threading
from flask import Blueprint, request, jsonify, Response
from flask_login import login_required
from config import Config
from recognition.camera import CameraManager
from recognition.trainer import FaceTrainer
from recognition.recognizer import FaceRecognizer
from models.database import db
from models.student import Student

logger = logging.getLogger(__name__)
recognition_bp = Blueprint('recognition', __name__, url_prefix='/recognition')

face_recognizer = None
trainer = FaceTrainer()
training_lock = threading.Lock()
training_in_progress = False
training_progress_current = 0
training_total_students = 0


def init_recognizer(app):
    global face_recognizer
    face_recognizer = FaceRecognizer(app=app)
    logger.info('Face recognizer initialized with Flask app context')


@recognition_bp.route('/capture', methods=['POST'])
@login_required
def capture_faces():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided.'}), 400

    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()

    if not student_id or not name:
        return jsonify({'success': False, 'message': 'Student ID and name required.'}), 400

    student_dir = os.path.join(Config.DATASET_DIR, student_id)
    os.makedirs(student_dir, exist_ok=True)

    camera = CameraManager()
    try:
        captured_files = camera.capture_faces_for_registration(
            student_id, num_images=Config.REQUIRED_IMAGES_FOR_REGISTRATION
        )
        if captured_files:
            _auto_train_async()
            return jsonify({
                'success': True,
                'count': len(captured_files),
                'message': f'Successfully captured {len(captured_files)} face images. Model auto-training started.',
            })
        else:
            return jsonify({'success': False, 'message': 'No faces detected or capture failed.'}), 400
    except Exception as e:
        logger.error(f'Face capture error: {e}')
        return jsonify({'success': False, 'message': f'Camera error: {str(e)}'}), 500
    finally:
        camera.release_camera()


def _auto_train_async():
    """Trigger automatic model training in background after face capture."""
    if training_in_progress or training_lock.locked():
        logger.info('Training already in progress, skipping auto-train')
        return

    def auto_training_task():
        global training_in_progress, training_progress_current
        training_in_progress = True
        training_progress_current = 0
        with training_lock:
            try:
                def cb(progress, sid):
                    global training_progress_current
                    training_progress_current = progress
                count, total = trainer.train_model(progress_callback=cb)
                training_progress_current = 100
                logger.info(f'Auto-training complete: {count}/{total} students')
            except Exception as e:
                logger.error(f'Auto-training error: {e}')
            finally:
                training_in_progress = False

    thread = threading.Thread(target=auto_training_task, daemon=True)
    thread.start()
    logger.info('Auto-training triggered after face capture')


@recognition_bp.route('/train', methods=['POST'])
@login_required
def train_model():
    global training_in_progress, training_progress_current, training_total_students
    if training_in_progress or training_lock.locked():
        return jsonify({'success': False, 'message': 'Training already in progress.'}), 400

    training_in_progress = True
    training_progress_current = 0

    def training_task():
        global training_in_progress, training_progress_current, training_total_students
        with training_lock:
            try:
                def progress_callback(progress, student_id):
                    global training_progress_current
                    training_progress_current = progress
                    logger.info(f'Training progress: {progress}% - {student_id}')

                count, total = trainer.train_model(progress_callback=progress_callback)
                training_progress_current = 100
                training_total_students = total
                logger.info(f'Training complete: {count}/{total} students')
            except Exception as e:
                logger.error(f'Training error: {e}')
            finally:
                training_in_progress = False

    thread = threading.Thread(target=training_task, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Training started successfully.',
    })


@recognition_bp.route('/training-status')
@login_required
def training_status():
    global training_in_progress, training_progress_current
    status = trainer.get_training_status()
    status['training_in_progress'] = training_in_progress
    status['training_progress'] = training_progress_current
    return jsonify(status)


@recognition_bp.route('/start', methods=['POST'])
@login_required
def start_recognition():
    if face_recognizer is None:
        return jsonify({'success': False, 'message': 'Recognizer not initialized.'}), 500
    success = face_recognizer.start_recognition()
    if success:
        return jsonify({'success': True, 'message': 'Recognition started.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to start. Ensure model is trained.'}), 400


@recognition_bp.route('/stop', methods=['POST'])
@login_required
def stop_recognition():
    if face_recognizer:
        face_recognizer.stop_recognition()
    return jsonify({'success': True, 'message': 'Recognition stopped.'})


@recognition_bp.route('/video_feed')
@login_required
def video_feed():
    if face_recognizer is None:
        return Response(b'', mimetype='image/jpeg')
    frame_data = face_recognizer.get_frame()
    if frame_data is None:
        return Response(b'', mimetype='image/jpeg')
    return Response(frame_data, mimetype='image/jpeg')


@recognition_bp.route('/recognized')
@login_required
def recognized_faces():
    if face_recognizer is None:
        return jsonify([])
    faces = face_recognizer.get_recognized_faces()
    return jsonify(faces)
