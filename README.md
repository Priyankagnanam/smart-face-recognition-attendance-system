# Smart Face Recognition Attendance System

An AI-powered attendance management system that automatically recognizes students using facial recognition technology and marks attendance securely. Built with Flask, OpenCV (LBPH), and modern web technologies.

---

## Features

- **Face Recognition** - Real-time face detection and recognition using OpenCV LBPH + Haar cascades
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
| Face Recognition | OpenCV LBPH + Haar cascades |
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
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── TEST_REPORT.md                  # Test results
├── DEPLOYMENT.md                   # Deployment guide
├── database/                       # SQLite database
│   ├── attendance.db
│   └── .gitkeep
├── models/                         # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── database.py                 # Database initialization
│   ├── user.py                     # User model
│   ├── student.py                  # Student model
│   ├── attendance.py              # Attendance model
│   └── face_encoding              # Legacy column (unused)
├── recognition/                    # Face recognition modules
│   ├── __init__.py
│   ├── camera.py                   # Camera management
│   ├── trainer.py                  # Model training
│   ├── recognizer.py              # Real-time recognition
│   ├── preprocess.py               # Face preprocessing (shared by training & live)
│   └── cascades.py                 # Haar cascade file location
├── routes/                         # Flask blueprints (routes)
│   ├── __init__.py
│   ├── auth.py                     # Authentication routes
│   ├── dashboard.py                # Dashboard routes
│   ├── student.py                  # Student management routes
│   ├── attendance.py               # Attendance routes
│   ├── reports.py                  # Report generation routes
│   ├── analytics.py                # Analytics routes
│   ├── settings.py                 # Settings routes
│   └── recognition_routes.py       # Recognition API endpoints
├── templates/                      # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html
│   ├── register_student.html
│   ├── attendance.html
│   ├── live_attendance.html
│   ├── attendance_history.html
│   ├── reports.html
│   ├── analytics.html
│   ├── settings.html
│   ├── 404.html
│   └── 500.html
├── static/                         # Static assets
│   ├── css/style.css
│   ├── js/app.js
│   ├── icons/
│   └── images/
├── dataset/                        # Student face images
│   └── .gitkeep
├── trained_models/                 # Trained face encodings
│   └── .gitkeep
├── exports/                        # Exported reports
│   └── .gitkeep
├── logs/                           # Application logs
│   └── .gitkeep
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── helpers.py                  # File validation & confidence formatting
│   └── security.py                 # Rate limiter & student-id validation
└── gunicorn.conf.py                # Gunicorn production configuration
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

## Initial Admin Login

The first time the application starts, an admin account is created from the
`ADMIN_USERNAME` / `ADMIN_PASSWORD` environment variables (see `.env.example`).

- If `ADMIN_PASSWORD` is **set**: the admin account uses that password.
- If `ADMIN_PASSWORD` is **not set**: a strong random password is generated and
  printed once to the application log/console. Change it after your first login.

There is **no** fixed default password.

---

## Usage Guide

### 1. Register Students
- Navigate to **Register Student**
- Fill in student details
- Click **Save Student**
- Click **Capture Face** to capture 40 face images

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

## Fixes Applied (v2.1.0)

| Issue | Fix |
|-------|-----|
| Broken `fa-analytics` icon in sidebar | Changed to `fa-chart-pie` |
| Hardcoded secret key fallback | Changed to env-based SECRET_KEY with persistent dev fallback (no hard-coded secret) |
| Missing `.gitkeep` in empty directories | Added `.gitkeep` to dataset, trained_models, exports, logs, uploads |
| No `.env.example` for env configuration | Created `.env.example` with instructions |
| Duplicate event listeners in attendance history | Fixed: `input` event only on search, `change` on filters |

---

## Deployment

### LAN Deployment (Gunicorn, single worker)

> **Webcam architecture:** recognition is server-side. The webcam must stay
> physically connected to the computer running the Flask/Gunicorn application.
> Other computers on the LAN only view the server-provided video feed.

```bash
# 1. INSTALL
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. SET SECRET KEY (required for production)
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

# 3. RUN (binds 0.0.0.0:8000, logs to logs/)
gunicorn -c gunicorn.conf.py app:app

# 4. FIND SERVER IP
ip addr

# 5. ACCESS FROM LAN (on the server machine or another computer)
#    Server machine:  http://0.0.0.0:8000
#    Other computer:  http://SERVER_LAN_IP:8000   (NOT 127.0.0.1)
```

Allow port 8000 through the firewall if needed: `sudo ufw allow 8000/tcp`.

Local development still works as before with `python app.py`
(`http://127.0.0.1:5000`).

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Webcam architecture notes (server-side recognition, camera on the server)
- Gunicorn + systemd service configuration
- Nginx reverse proxy (optional, for HTTPS/domain)
- Security checklist
- Git push commands

---

## Test Report

See [TEST_REPORT.md](TEST_REPORT.md) for complete test results (current suite).

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

