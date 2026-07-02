import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from models.database import db
from models.student import Student
from models.attendance import Attendance
import numpy as np

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    today = date.today()

    total_students = Student.query.count()

    today_attendances = Attendance.query.filter(
        Attendance.attendance_date == today
    ).all()
    present_today = len(today_attendances)
    absent_today = max(0, total_students - present_today)

    attendance_percentage = 0.0
    if total_students > 0:
        attendance_percentage = round((present_today / total_students) * 100, 1)

    confidence_scores = [a.confidence_score for a in today_attendances if a.confidence_score is not None]
    avg_accuracy = 0.0
    if confidence_scores:
        avg_accuracy = round(float(np.mean(confidence_scores)) * 100, 1)

    recent_attendance = (
        Attendance.query
        .order_by(Attendance.attendance_date.desc(), Attendance.check_in_time.desc())
        .limit(10)
        .all()
    )

    recent_list = []
    for att in recent_attendance:
        student = Student.query.get(att.student_id)
        if student:
            recent_list.append({
                'student_id': att.student_id,
                'name': student.name,
                'department': student.department,
                'date': att.attendance_date.isoformat(),
                'time': att.check_in_time.strftime('%H:%M:%S'),
                'status': att.status,
                'confidence': round(att.confidence_score * 100, 1) if att.confidence_score else 0,
            })

    return jsonify({
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'attendance_percentage': attendance_percentage,
        'avg_accuracy': avg_accuracy,
        'recent_attendance': recent_list,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })


@dashboard_bp.route('/api/dashboard/weekly-trend')
@login_required
def weekly_trend():
    today = date.today()
    week_ago = today - timedelta(days=7)
    dates = []
    present_counts = []

    for i in range(7):
        d = week_ago + timedelta(days=i)
        if d > today:
            break
        dates.append(d.strftime('%a'))
        count = Attendance.query.filter(
            Attendance.attendance_date == d
        ).count()
        present_counts.append(count)

    return jsonify({
        'labels': dates,
        'present': present_counts,
    })
