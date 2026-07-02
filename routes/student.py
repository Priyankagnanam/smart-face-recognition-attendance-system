import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from models.database import db
from models.student import Student
from sqlalchemy import or_

logger = logging.getLogger(__name__)
student_bp = Blueprint('student', __name__, url_prefix='/students')


@student_bp.route('/')
@login_required
def list_students():
    return render_template('students.html')


@student_bp.route('/register')
@login_required
def register():
    return render_template('register_student.html')


@student_bp.route('/api/list')
@login_required
def api_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()

    query = Student.query
    if search:
        query = query.filter(
            or_(
                Student.student_id.ilike(f'%{search}%'),
                Student.name.ilike(f'%{search}%'),
                Student.department.ilike(f'%{search}%'),
                Student.email.ilike(f'%{search}%'),
            )
        )

    total = query.count()
    students = query.order_by(Student.name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'students': [s.to_dict() for s in students.items],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })


@student_bp.route('/api/add', methods=['POST'])
@login_required
def api_add():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided.'}), 400

    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    year = data.get('year', '').strip()
    section = data.get('section', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()

    errors = []
    if not student_id:
        errors.append('Student ID is required.')
    if not name:
        errors.append('Name is required.')
    if not department:
        errors.append('Department is required.')
    if not year:
        errors.append('Year is required.')
    if not section:
        errors.append('Section is required.')
    if not email:
        errors.append('Email is required.')

    if errors:
        return jsonify({'success': False, 'message': ' '.join(errors)}), 400

    if Student.query.get(student_id):
        return jsonify({'success': False, 'message': 'Student ID already exists.'}), 400

    if Student.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered.'}), 400

    student = Student(
        student_id=student_id,
        name=name,
        department=department,
        year=year,
        section=section,
        email=email,
        phone=phone,
    )
    db.session.add(student)
    db.session.commit()
    logger.info(f'Student registered: {student_id} - {name}')
    return jsonify({'success': True, 'message': 'Student registered successfully!'})


@student_bp.route('/api/update', methods=['POST'])
@login_required
def api_update():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided.'}), 400

    student_id = data.get('student_id', '').strip()
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found.'}), 404

    student.name = data.get('name', student.name).strip()
    student.department = data.get('department', student.department).strip()
    student.year = data.get('year', student.year).strip()
    student.section = data.get('section', student.section).strip()
    student.email = data.get('email', student.email).strip()
    student.phone = data.get('phone', student.phone).strip()

    db.session.commit()
    logger.info(f'Student updated: {student_id}')
    return jsonify({'success': True, 'message': 'Student updated successfully!'})


@student_bp.route('/api/delete/<student_id>', methods=['DELETE'])
@login_required
def api_delete(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found.'}), 404

    db.session.delete(student)
    db.session.commit()
    logger.info(f'Student deleted: {student_id}')
    return jsonify({'success': True, 'message': 'Student deleted successfully!'})


@student_bp.route('/api/get/<student_id>')
@login_required
def api_get(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found.'}), 404
    return jsonify({'success': True, 'student': student.to_dict()})


@student_bp.route('/api/departments')
@login_required
def api_departments():
    departments = db.session.query(Student.department).distinct().all()
    return jsonify({
        'departments': [d[0] for d in departments if d[0]]
    })


@student_bp.route('/api/all')
@login_required
def api_all():
    students = Student.query.order_by(Student.name).all()
    return jsonify({'students': [s.to_dict() for s in students]})
