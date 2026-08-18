from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Shared limiter instance. Bound to the Flask app in app.py via limiter.init_app().
# Uses the client IP as the rate-limit key. Behind a reverse proxy, set
# BEHIND_PROXY=1 so ProxyFix rewrites remote_addr from X-Forwarded-For.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
