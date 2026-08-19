# Gunicorn configuration for Smart Face Recognition Attendance System
#
# LAN deployment notes:
#   - This application performs OpenCV face recognition and owns a single
#     webcam inside a background thread. Use ONE worker process so that only
#     one recognizer/camera instance exists.
#   - Threads within that single worker handle concurrent HTTP requests
#     (video feed polling, recognition status, etc.) while the recognition
#     loop runs in its own background thread.
#   - Do NOT increase `workers` for this application.
#
# Run:
#   gunicorn -c gunicorn.conf.py app:app

bind = "0.0.0.0:8000"

# Single process: one webcam, one OpenCV recognizer, one SQLite writer.
workers = 1

# Gthread worker so concurrent requests (video feed + polls) do not block.
worker_class = "gthread"
threads = 4

# Requests that trigger model training / recognition startup can take time.
# Keep the sync timeout generous for camera/recognition requests.
timeout = 120
graceful_timeout = 30

# Access + error logging.
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"
capture_output = True