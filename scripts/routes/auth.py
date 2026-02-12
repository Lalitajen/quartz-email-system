"""Authentication routes."""

import time
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger('quartz_web')

# Brute force protection: track failed attempts per IP
_failed_attempts = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes


def _check_lockout(ip):
    """Return True if IP is locked out."""
    if ip in _failed_attempts:
        attempts, lockout_time = _failed_attempts[ip]
        if attempts >= MAX_FAILED_ATTEMPTS:
            if time.time() - lockout_time < LOCKOUT_SECONDS:
                return True
            # Lockout expired, reset
            del _failed_attempts[ip]
    return False


def _record_failed(ip):
    """Record a failed login attempt."""
    if ip in _failed_attempts:
        attempts, _ = _failed_attempts[ip]
        _failed_attempts[ip] = (attempts + 1, time.time())
    else:
        _failed_attempts[ip] = (1, time.time())


def _clear_failed(ip):
    """Clear failed attempts on successful login."""
    _failed_attempts.pop(ip, None)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        client_ip = request.remote_addr

        # Check brute force lockout
        if _check_lockout(client_ip):
            logger.warning(f"Login blocked - IP locked out: {client_ip}")
            flash('Too many failed attempts. Please try again later.', 'danger')
            return render_template('login.html'), 429

        username = request.form.get('username', '')
        password = request.form.get('password', '')
        stored_password = current_app.config['APP_PASSWORD']

        # Support both hashed and plaintext passwords for backward compatibility
        if username == current_app.config['APP_USERNAME']:
            password_ok = False
            if stored_password.startswith(('pbkdf2:', 'scrypt:')):
                password_ok = check_password_hash(stored_password, password)
            else:
                password_ok = (password == stored_password)

            if password_ok:
                _clear_failed(client_ip)
                session.permanent = True
                session['authenticated'] = True
                logger.info(f"Login successful: user={username} ip={client_ip}")
                flash('Welcome back!', 'success')
                return redirect(url_for('dashboard.dashboard'))

        # Failed login
        _record_failed(client_ip)
        logger.warning(f"Login failed: user={username} ip={client_ip}")
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    logger.info(f"Logout: ip={request.remote_addr}")
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
