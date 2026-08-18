# Deployment Guide - Smart Face Recognition Attendance System

## Prerequisites

- Python 3.12+
- Webcam (for face capture/recognition)
- 1GB+ RAM
- 500MB+ free disk space

---

## Commands to Run the Project

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/SmartFaceRecognitionAttendance.git
cd SmartFaceRecognitionAttendance

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export SECRET_KEY="your-super-secret-key"          # REQUIRED in production
export ADMIN_USERNAME="admin"                      # initial admin (optional)
export ADMIN_PASSWORD="a-strong-password"          # initial admin password (optional; random if unset)

# 5. Run the application
python app.py

# 6. Access the application
# Open browser to: http://127.0.0.1:5000
# Login using the admin credentials configured above (or the generated password from the log).
```

---

## Production Deployment

### Option 1: Gunicorn (Linux)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Option 2: Gunicorn with systemd service

Create `/etc/systemd/system/face-attendance.service`:

```ini
[Unit]
Description=Smart Face Recognition Attendance System
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/SmartFaceRecognitionAttendance
Environment="SECRET_KEY=your-production-secret-key"
Environment="ADMIN_USERNAME=admin"
Environment="ADMIN_PASSWORD=your-strong-password"
ExecStart=/opt/SmartFaceRecognitionAttendance/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable face-attendance
sudo systemctl start face-attendance
```

### Option 3: Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/SmartFaceRecognitionAttendance/static/;
        expires 30d;
    }
}
```

---

## Production Checklist

- [ ] Set a strong `SECRET_KEY` environment variable
- [ ] Change default admin password after first login
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Use Gunicorn + Nginx instead of Flask dev server
- [ ] Set `debug=False` in app.py for production
- [ ] Configure firewall (allow only port 80/443 and SSH)
- [ ] Regular database backups (`cp database/attendance.db backups/`)
- [ ] Monitor logs in `logs/` directory
- [ ] Set up log rotation
- [ ] Configure systemd auto-restart on crash
- [ ] Use environment variables for all secrets
- [ ] Set up monitoring/alerting
- [ ] Regular security updates

---

## Requirements for Deployment

| Software | Version |
|----------|---------|
| Python | 3.12+ |
| Flask | 3.0+ |
| OpenCV | 4.5+ |
| SQLite | 3.x |
| Gunicorn | 21.x (production) |
| Nginx | Latest (production) |

Python packages listed in `requirements.txt`

---

## Folder Cleanup Suggestions

Before deployment:
- Remove `__pycache__/` directories: `find . -type d -name __pycache__ -exec rm -rf {} +`
- Remove `.gitkeep` from dataset/trained_models if deploying fresh
- Clear old logs: `rm -f logs/*.log`
- Clear old exports: `rm -f exports/*`
- Reset database if needed: `rm -f database/attendance.db*`

---

## Final Project Structure

```
SmartFaceRecognitionAttendance/
├── app.py                          # Application entry point
├── config.py                       # Configuration (secret key, paths)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── TEST_REPORT.md                  # Test results
├── DEPLOYMENT.md                   # Deployment guide
├── database/                       # SQLite database
│   ├── .gitkeep
│   └── attendance.db
├── dataset/                        # Student face images
│   └── .gitkeep
├── exports/                        # Exported reports
│   └── .gitkeep
├── logs/                           # Application logs
│   └── .gitkeep
├── models/                         # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── database.py
│   ├── user.py
│   ├── student.py
│   └── attendance.py
├── recognition/                    # Face recognition modules
│   ├── __init__.py
│   ├── camera.py
│   ├── trainer.py
│   └── recognizer.py
├── routes/                         # Flask blueprints
│   ├── __init__.py
│   ├── auth.py
│   ├── dashboard.py
│   ├── student.py
│   ├── attendance.py
│   ├── reports.py
│   ├── analytics.py
│   ├── settings.py
│   └── recognition_routes.py
├── static/                         # Static assets
│   ├── css/style.css
│   ├── js/app.js
│   ├── icons/
│   ├── images/
│   └── uploads/.gitkeep
├── templates/                      # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── register_student.html
│   ├── students.html
│   ├── attendance.html
│   ├── attendance_history.html
│   ├── live_attendance.html
│   ├── reports.html
│   ├── analytics.html
│   ├── settings.html
│   ├── 404.html
│   └── 500.html
├── trained_models/                 # Trained face encodings
│   └── .gitkeep
└── utils/                          # Utilities
    ├── __init__.py
    └── helpers.py
```

---

## Git Commands to Push to GitHub

```bash
# Initialize if not already done
git init
git add .
git commit -m "Initial commit: Smart Face Recognition Attendance System v2.0"

# Add remote and push
git remote add origin https://github.com/yourusername/SmartFaceRecognitionAttendance.git
git push -u origin main

# Or if using a different branch
git branch -M main
git push -u origin main
```
