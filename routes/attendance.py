import logging
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.database import db
from models.student import Student
from models.attendance import Attendance

logger = logging.getLogger(__name__)
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/')
@login_required
def index():
    return render_template('attendance.html')


@attendance_bp.route('/live')
@login_required
def live():
    return render_template('live_attendance.html')


@attendance_bp.route('/history')
@login_required
def history():
    return render_template('attendance_history.html')


@attendance_bp.route('/api/today')
@login_required
def api_today():
    today = date.today()
    records = (
        Attendance.query
        .filter(Attendance.attendance_date == today)
        .order_by(Attendance.check_in_time.desc())
        .all()
    )
    result = []
    for rec in records:
        student = Student.query.get(rec.student_id)
        result.append({
            'id': rec.id,
            'student_id': rec.student_id,
            'name': student.name if student else 'Unknown',
            'department': student.department if student else '',
            'time': rec.check_in_time.strftime('%H:%M:%S'),
            'status': rec.status,
            'confidence': round(rec.confidence_score * 100, 1) if rec.confidence_score else 0,
        })
    return jsonify({'records': result, 'date': today.isoformat()})


@attendance_bp.route('/api/mark', methods=['POST'])
@login_required
def api_mark():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided.'}), 400

    student_id = data.get('student_id', '').strip()
    confidence = data.get('confidence', 0.0)

    if not student_id:
        return jsonify({'success': False, 'message': 'Student ID required.'}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found.'}), 404

    today = date.today()
    existing = Attendance.query.filter_by(
        student_id=student_id,
        attendance_date=today
    ).first()

    if existing:
        return jsonify({
            'success': True,
            'message': f'{student.name} already marked present today.',
            'already_marked': True,
            'record': {
                'student_id': student_id,
                'name': student.name,
                'time': existing.check_in_time.strftime('%H:%M:%S'),
                'confidence': round(existing.confidence_score * 100, 1) if existing.confidence_score else 0,
            }
        })

    now = datetime.now()
    attendance = Attendance(
        student_id=student_id,
        attendance_date=today,
        check_in_time=now.time(),
        status='Present',
        confidence_score=confidence,
    )
    db.session.add(attendance)
    db.session.commit()
    logger.info(f'Attendance marked: {student_id} - {student.name} ({confidence:.2f})')

    return jsonify({
        'success': True,
        'message': f'Attendance marked for {student.name}!',
        'record': {
            'student_id': student_id,
            'name': student.name,
            'department': student.department,
            'time': now.strftime('%H:%M:%S'),
            'confidence': round(confidence * 100, 1),
        }
    })


@attendance_bp.route('/api/history')
@login_required
def api_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    department = request.args.get('department', '')
    search = request.args.get('search', '').strip()

    query = Attendance.query.join(Student, Attendance.student_id == Student.student_id)

    if date_from:
        try:
            query = query.filter(Attendance.attendance_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Attendance.attendance_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass
    if department:
        query = query.filter(Student.department == department)
    if search:
        query = query.filter(
            db.or_(
                Student.student_id.ilike(f'%{search}%'),
                Student.name.ilike(f'%{search}%'),
            )
        )

    total = query.count()
    records = query.order_by(
        Attendance.attendance_date.desc(),
        Attendance.check_in_time.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    result = []
    for rec in records.items:
        student = Student.query.get(rec.student_id)
        result.append({
            'id': rec.id,
            'student_id': rec.student_id,
            'name': student.name if student else 'Unknown',
            'department': student.department if student else '',
            'year': student.year if student else '',
            'section': student.section if student else '',
            'date': rec.attendance_date.isoformat(),
            'time': rec.check_in_time.strftime('%H:%M:%S'),
            'status': rec.status,
            'confidence': round(rec.confidence_score * 100, 1) if rec.confidence_score else 0,
        })

    return jsonify({
        'records': result,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })
