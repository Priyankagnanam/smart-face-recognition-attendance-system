"""Seed the database with sample demo data.

Called once on fresh startup (when no students exist) so that the live
cloud demo always looks populated with realistic data.
"""

import logging
import random
from datetime import datetime, date, time, timedelta, timezone

from models.database import db
from models.student import Student
from models.attendance import Attendance

logger = logging.getLogger(__name__)

SAMPLE_STUDENTS = [
    {
        'student_id': 'CSE2024001',
        'name': 'Arjun Reddy',
        'department': 'Computer Science',
        'year': '3rd Year',
        'section': 'A',
        'email': 'arjun.reddy@university.edu',
        'phone': '9876543210',
    },
    {
        'student_id': 'CSE2024002',
        'name': 'Sneha Patel',
        'department': 'Computer Science',
        'year': '3rd Year',
        'section': 'A',
        'email': 'sneha.patel@university.edu',
        'phone': '9876543211',
    },
    {
        'student_id': 'CSE2024003',
        'name': 'Rahul Sharma',
        'department': 'Computer Science',
        'year': '3rd Year',
        'section': 'B',
        'email': 'rahul.sharma@university.edu',
        'phone': '9876543212',
    },
    {
        'student_id': 'ECE2024001',
        'name': 'Divya Krishnan',
        'department': 'Electronics',
        'year': '2nd Year',
        'section': 'A',
        'email': 'divya.k@university.edu',
        'phone': '9876543213',
    },
    {
        'student_id': 'ECE2024002',
        'name': 'Vikram Singh',
        'department': 'Electronics',
        'year': '2nd Year',
        'section': 'A',
        'email': 'vikram.singh@university.edu',
        'phone': '9876543214',
    },
    {
        'student_id': 'CSE2024004',
        'name': 'Ananya Gupta',
        'department': 'Computer Science',
        'year': '4th Year',
        'section': 'A',
        'email': 'ananya.gupta@university.edu',
        'phone': '9876543215',
    },
]


def seed_demo_data():
    """Populate the database with sample students and attendance records.

    Only runs when the students table is empty (fresh database).
    """
    if Student.query.first() is not None:
        return

    logger.info('Seeding demo data for live portfolio demo...')

    # Add students
    for s in SAMPLE_STUDENTS:
        student = Student(**s)
        db.session.add(student)

    db.session.commit()
    logger.info('Added %d sample students', len(SAMPLE_STUDENTS))

    # Generate attendance for the last 14 days
    today = date.today()
    attendance_count = 0

    for day_offset in range(14, 0, -1):
        att_date = today - timedelta(days=day_offset)

        # Skip weekends
        if att_date.weekday() >= 5:
            continue

        for s in SAMPLE_STUDENTS:
            # 85% attendance rate — realistic
            if random.random() < 0.15:
                continue

            # Random check-in between 8:30 and 9:30 AM
            hour = 8 if random.random() < 0.3 else 9
            minute = random.randint(0, 59)
            check_in = time(hour, minute)

            # Confidence score between 0.75 and 0.98
            confidence = round(random.uniform(0.75, 0.98), 2)

            attendance = Attendance(
                student_id=s['student_id'],
                attendance_date=att_date,
                check_in_time=check_in,
                status='Present',
                confidence_score=confidence,
            )
            db.session.add(attendance)
            attendance_count += 1

    db.session.commit()
    logger.info('Added %d attendance records across 14 days', attendance_count)
    logger.info('Demo data seeding complete!')
