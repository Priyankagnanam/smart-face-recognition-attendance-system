import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func, extract
from models.database import db
from models.student import Student
from models.attendance import Attendance

logger = logging.getLogger(__name__)
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/')
@login_required
def index():
    return render_template('analytics.html')


@analytics_bp.route('/api/overview')
@login_required
def api_overview():
    today = date.today()
    total_students = Student.query.count()

    today_count = Attendance.query.filter(
        Attendance.attendance_date == today
    ).count()

    avg_confidence = db.session.query(
        func.avg(Attendance.confidence_score)
    ).filter(
        Attendance.attendance_date == today
    ).scalar() or 0

    weekly_count = Attendance.query.filter(
        Attendance.attendance_date >= today - timedelta(days=7)
    ).count()

    monthly_count = Attendance.query.filter(
        extract('month', Attendance.attendance_date) == today.month,
        extract('year', Attendance.attendance_date) == today.year,
    ).count()

    return jsonify({
        'total_students': total_students,
        'today_attendance': today_count,
        'avg_confidence': round(float(avg_confidence) * 100, 1),
        'weekly_count': weekly_count,
        'monthly_count': monthly_count,
    })


@analytics_bp.route('/api/monthly-trend')
@login_required
def monthly_trend():
    today = date.today()
    months = []
    present_data = []
    absent_data = []

    total_students = max(Student.query.count(), 1)

    for i in range(6):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        month_name = datetime(y, m, 1).strftime('%b %Y')
        months.insert(0, month_name)

        total_days = Attendance.query.filter(
            extract('month', Attendance.attendance_date) == m,
            extract('year', Attendance.attendance_date) == y,
        ).count()

        unique_students = db.session.query(
            Attendance.student_id
        ).filter(
            extract('month', Attendance.attendance_date) == m,
            extract('year', Attendance.attendance_date) == y,
        ).distinct().count()

        present_data.insert(0, unique_students)
        absent_data.insert(0, max(0, total_students - unique_students))

    return jsonify({
        'labels': months,
        'present': present_data,
        'absent': absent_data,
    })


@analytics_bp.route('/api/department-stats')
@login_required
def department_stats():
    departments = db.session.query(Student.department).distinct().all()
    today = date.today()
    result = []

    for (dept,) in departments:
        if not dept:
            continue
        total = Student.query.filter_by(department=dept).count()
        present = db.session.query(Attendance).join(
            Student, Attendance.student_id == Student.student_id
        ).filter(
            Student.department == dept,
            Attendance.attendance_date == today,
        ).count()

        pct = round((present / total) * 100, 1) if total > 0 else 0
        result.append({
            'department': dept,
            'total': total,
            'present': present,
            'percentage': pct,
        })

    result.sort(key=lambda x: x['percentage'], reverse=True)
    return jsonify({'departments': result})


@analytics_bp.route('/api/daily-trend')
@login_required
def daily_trend():
    today = date.today()
    days = []
    counts = []

    for i in range(14, -1, -1):
        d = today - timedelta(days=i)
        days.append(d.strftime('%d %b'))
        count = Attendance.query.filter(
            Attendance.attendance_date == d
        ).count()
        counts.append(count)

    return jsonify({
        'labels': days,
        'counts': counts,
    })


@analytics_bp.route('/api/accuracy-trend')
@login_required
def accuracy_trend():
    today = date.today()
    days = []
    accuracy_data = []

    for i in range(7, -1, -1):
        d = today - timedelta(days=i)
        days.append(d.strftime('%a'))
        avg_conf = db.session.query(
            func.avg(Attendance.confidence_score)
        ).filter(
            Attendance.attendance_date == d
        ).scalar() or 0

        accuracy_data.append(round(float(avg_conf) * 100, 1))

    return jsonify({
        'labels': days,
        'accuracy': accuracy_data,
    })
