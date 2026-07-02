# Smart Face Recognition Attendance System

An AI-powered attendance management system that automatically recognizes students using facial recognition technology and marks attendance securely. Built with Flask, OpenCV, InsightFace, and modern web technologies.

---

## Features

- **Face Recognition** - Real-time face detection and recognition using InsightFace
- **Automated Attendance** - Mark attendance automatically when faces are recognized
- **Student Management** - Register, update, and manage student records
- **Live Camera Feed** - Real-time video stream with face detection overlay
- **Dashboard** - Interactive dashboard with attendance statistics
- **Reports** - Generate daily, weekly, monthly, and department-wise reports
- **Export** - Export reports to CSV and Excel formats
- **Analytics** - Visual charts for attendance trends and accuracy
- **Dark/Light Mode** - Toggle between dark and light themes
- **Responsive Design** - Works on desktop and mobile devices

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, Flask |
| Database | SQLite, SQLAlchemy ORM |
| Face Recognition | InsightFace, OpenCV |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Charts | Chart.js |
| Icons | Font Awesome |
| Authentication | Flask-Login |

---

## Project Structure

```
SmartFaceRecognitionAttendance/
├── app.py                          # Application entry point
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── database/                       # SQLite database files
├── models/                         # SQLAlchemy ORM models
│   ├── database.py                 # Database initialization
│   ├── user.py                     # User model
│   ├── student.py                  # Student model
│   └── attendance.py              # Attendance model
├── routes/                         # Flask blueprints (routes)
│   ├── auth.py                     # Authentication routes
│   ├── dashboard.py                # Dashboard routes
│   ├── student.py                  # Student management routes
│   ├── attendance.py               # Attendance routes
│   ├── reports.py                  # Report generation routes
│   ├── analytics.py                # Analytics routes
│   ├── settings.py                 # Settings routes
│   └── recognition_routes.py       # Recognition API endpoints
├── recognition/                    # Face recognition modules
│   ├── camera.py                   # Camera management
│   ├── trainer.py                  # Model training
│   └── recognizer.py              # Real-time recognition
├── templates/                      # HTML templates
├── static/                         # Static assets (CSS, JS)
├── dataset/                        # Student face images
├── trained_models/                 # Trained face encodings
├── exports/                        # Exported reports
├── logs/                           # Application logs
└── utils/                          # Utility functions
```

---

## Installation

### Prerequisites

- Python 3.12 or higher
- Webcam (for face capture and recognition)
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/SmartFaceRecognitionAttendance.git
cd SmartFaceRecognitionAttendance
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

### Step 5: Access the Application

Open your web browser and go to:

```
http://127.0.0.1:5000
```

---

## Default Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |

---

## Usage Guide

### 1. Register Students
- Navigate to **Register Student**
- Fill in student details
- Click **Capture Face** to capture 40 face images
- Click **Save Student**

### 2. Train Model
- Go to **Settings**
- Click **Train Model** to generate face embeddings
- Wait for training to complete

### 3. Take Attendance
- Go to **Take Attendance**
- Click **Start Camera**
- Faces are recognized in real-time
- Attendance is marked automatically

### 4. View Reports
- Go to **Reports**
- Select report type (Daily/Weekly/Monthly)
- Export to CSV or Excel

### 5. Analytics
- Go to **Analytics**
- View attendance trends and statistics
- Interactive charts

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | GET/POST | User login |
| `/auth/logout` | GET | User logout |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/students/api/list` | GET | List students |
| `/students/api/add` | POST | Add student |
| `/students/api/update` | POST | Update student |
| `/students/api/delete/<id>` | DELETE | Delete student |
| `/attendance/api/today` | GET | Today's attendance |
| `/attendance/api/mark` | POST | Mark attendance |
| `/attendance/api/history` | GET | Attendance history |
| `/reports/api/data` | GET | Report data |
| `/reports/api/export/csv` | GET | Export CSV |
| `/reports/api/export/excel` | GET | Export Excel |
| `/analytics/api/overview` | GET | Analytics overview |
| `/recognition/start` | POST | Start recognition |
| `/recognition/stop` | POST | Stop recognition |
| `/recognition/train` | POST | Train model |

---

## Screenshots

*[Screenshots coming soon]*

---

## Security

- Passwords hashed using Werkzeug
- SQLAlchemy ORM prevents SQL injection
- Flask-Login for session management
- CSRF protection enabled
- Input validation on all forms
- Role-based access control

---

---

## Fixes Applied (v2.0.1)

| Issue | Fix |
|-------|-----|
| Broken `fa-analytics` icon in sidebar | Changed to `fa-chart-pie` |
| Hardcoded secret key fallback | Changed to `os.urandom(32).hex()` |
| Missing `.gitkeep` in empty directories | Added `.gitkeep` to dataset, trained_models, exports, logs, uploads |
| No `.env.example` for env configuration | Created `.env.example` with instructions |
| Duplicate event listeners in attendance history | Fixed: `input` event only on search, `change` on filters |

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Production setup with Gunicorn + Nginx
- Systemd service configuration
- Security checklist
- Git push commands

---

## Test Report

See [TEST_REPORT.md](TEST_REPORT.md) for complete test results (52/52 tests passed).

---

## Future Enhancements

- [ ] Multiple camera support
- [ ] Email notifications for absent students
- [ ] Cloud backup integration
- [ ] Mobile app (React Native)
- [ ] Multi-factor authentication
- [ ] Real-time notifications via WebSocket
- [ ] Integration with LMS platforms
- [ ] Advanced reporting with PDF export

---

## License

MIT License

Copyright (c) 2024 SmartVision Technologies

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...

---

