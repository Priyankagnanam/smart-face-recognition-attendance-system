from datetime import datetime, timezone
from models.database import db


class Student(db.Model):
    __tablename__ = 'students'

    student_id = db.Column(db.String(20), primary_key=True, nullable=False)
    name = db.Column(db.String(120), nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    registered_on = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    face_encoding = db.Column(db.Text, nullable=True)

    attendances = db.relationship(
        'Attendance', backref='student', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def full_name(self) -> str:
        return self.name

    def to_dict(self) -> dict:
        return {
            'student_id': self.student_id,
            'name': self.name,
            'department': self.department,
            'year': self.year,
            'section': self.section,
            'email': self.email,
            'phone': self.phone,
            'registered_on': self.registered_on.isoformat() if self.registered_on else None,
        }

    def __repr__(self) -> str:
        return f'<Student {self.student_id}: {self.name}>'
