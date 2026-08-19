from datetime import date
from models.database import db


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(
        db.String(20),
        db.ForeignKey('students.student_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    attendance_date = db.Column(db.Date, nullable=False, default=date.today)
    check_in_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Present')
    confidence_score = db.Column(db.Float, nullable=True)

    __table_args__ = (
        db.UniqueConstraint(
            'student_id', 'attendance_date',
            name='unique_attendance_per_day'
        ),
        db.Index('idx_attendance_date', 'attendance_date'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'student_id': self.student_id,
            'attendance_date': self.attendance_date.isoformat() if self.attendance_date else None,
            'check_in_time': self.check_in_time.strftime('%H:%M:%S') if self.check_in_time else None,
            'status': self.status,
            'confidence_score': self.confidence_score,
        }

    def __repr__(self) -> str:
        return f'<Attendance {self.student_id} on {self.attendance_date}>'
