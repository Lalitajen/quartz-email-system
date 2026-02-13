"""Authentication routes with multi-user registration and login."""

import time
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app_core import is_valid_email

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
    if session.get('authenticated'):
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        client_ip = request.remote_addr

        if _check_lockout(client_ip):
            logger.warning(f"Login blocked - IP locked out: {client_ip}")
            flash('Too many failed attempts. Please try again later.', 'danger')
            return render_template('login.html'), 429

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        from models import User
        user = User.get_by_email(email)

        if user and user.is_active and user.verify_password(password):
            _clear_failed(client_ip)
            session.permanent = True
            session['authenticated'] = True
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_display_name'] = user.display_name or email
            user.update_last_login()
            logger.info(f"Login successful: user={email} ip={client_ip}")
            flash(f'Welcome back, {user.display_name or email}!', 'success')
            return redirect(url_for('dashboard.dashboard'))

        _record_failed(client_ip)
        logger.warning(f"Login failed: email={email} ip={client_ip}")
        flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('authenticated'):
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        display_name = request.form.get('display_name', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Validate
        if not email or not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html')

        if not display_name:
            flash('Please enter your name.', 'danger')
            return render_template('register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        from models import User
        user = User.create(email=email, password=password, display_name=display_name)

        if not user:
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html')

        # Auto-login after registration
        session.permanent = True
        session['authenticated'] = True
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_display_name'] = user.display_name
        logger.info(f"New user registered: {email}")
        flash('Account created! Let\'s set up your credentials.', 'success')
        return redirect(url_for('setup.setup_step', step=1))

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    logger.info(f"Logout: user_id={session.get('user_id')} ip={request.remote_addr}")
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
