"""
Quartz Email Outreach System - Web Interface v3.0
Refactored Flask app with proper templates, security, and modular routes.
"""

import os
import sys
import time
from datetime import timedelta

# Ensure project root and scripts directory are on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))

from flask import Flask, render_template, request as flask_request
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import app core (shared state, config, helpers)
from app_core import (
    PROJECT_ROOT, APP_USERNAME, APP_PASSWORD,
    engagement_badge, stage_badge, SENDER_NAME, logger
)

# Import route blueprints
from routes import ALL_BLUEPRINTS

# Global CSRF and rate limiter (initialized in create_app)
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])


def create_app():
    """Application factory."""
    app = Flask(__name__,
                template_folder=os.path.join(PROJECT_ROOT, 'templates'),
                static_folder=os.path.join(PROJECT_ROOT, 'static'))

    # Use a stable secret key from env or generate once and save to file
    secret_key_file = os.path.join(PROJECT_ROOT, 'config', '.flask_secret')
    if os.getenv('FLASK_SECRET_KEY'):
        app.secret_key = os.getenv('FLASK_SECRET_KEY')
    elif os.path.exists(secret_key_file):
        with open(secret_key_file, 'rb') as f:
            app.secret_key = f.read()
    else:
        key = os.urandom(32)
        os.makedirs(os.path.dirname(secret_key_file), exist_ok=True)
        with open(secret_key_file, 'wb') as f:
            f.write(key)
        os.chmod(secret_key_file, 0o600)
        app.secret_key = key
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
    app.config['APP_USERNAME'] = APP_USERNAME
    app.config['APP_PASSWORD'] = APP_PASSWORD
    app.config['SENDER_NAME'] = SENDER_NAME

    # ── Session Security (A07) ────────────────────────────
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

    # ── CSRF Protection (A01) ─────────────────────────────
    csrf.init_app(app)

    # ── Rate Limiting (A04) ───────────────────────────────
    limiter.init_app(app)

    # Register Jinja2 global functions
    app.jinja_env.globals['engagement_badge'] = engagement_badge
    app.jinja_env.globals['stage_badge'] = stage_badge
    app.jinja_env.globals['config'] = app.config

    # Custom Jinja2 filter for splitting attachment strings
    app.jinja_env.filters['split_semi'] = lambda s: [x.strip() for x in str(s).split(';') if x.strip()]
    app.jinja_env.filters['split_comma'] = lambda s: [x.strip() for x in str(s).split(',') if x.strip()]

    # Register all blueprints
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    # Request logging
    @app.before_request
    def log_request_start():
        flask_request._start_time = time.time()

    # ── Security Headers (A05) ────────────────────────────
    @app.after_request
    def set_security_headers(response):
        duration = time.time() - getattr(flask_request, '_start_time', time.time())
        if not flask_request.path.startswith('/static'):
            logger.info(f"{flask_request.method} {flask_request.path} {response.status_code} {duration:.2f}s")
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        if os.getenv('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Error handlers - generic messages to avoid info leakage (A09)
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html', active_page=''), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"500 error: {e}")
        return render_template('500.html', active_page=''), 500

    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, request
        flash('File too large. Maximum upload size is 16 MB.', 'danger')
        return redirect(request.referrer or '/'), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        from flask import flash, redirect, request
        flash('Too many requests. Please slow down.', 'warning')
        return redirect(request.referrer or '/'), 429

    return app


if __name__ == '__main__':
    print("=" * 55)
    print("  Quartz Email Outreach System - Web Interface v3.0")
    print("  Refactored: Modular Routes + Jinja2 Templates")
    print("=" * 55)
    print(f"  Templates: {os.path.join(PROJECT_ROOT, 'templates')}")
    print(f"  Static:    {os.path.join(PROJECT_ROOT, 'static')}")
    print(f"  Logs:      {os.path.join(PROJECT_ROOT, 'logs')}")
    print("=" * 55)
    print("  Login credentials configured via config/.env")
    print("  (APP_USERNAME, APP_PASSWORD)")
    print("=" * 55)

    app = create_app()
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    host = '127.0.0.1' if debug else '0.0.0.0'
    app.run(debug=debug, host=host, port=5000)
