"""Onboarding wizard for new users to set up their credentials."""

import json
import base64
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app_core import login_required, get_current_user, logger, safe_flash_error

setup_bp = Blueprint('setup', __name__)


@setup_bp.route('/setup')
@login_required
def setup_redirect():
    """Redirect to step 1 of setup."""
    return redirect(url_for('setup.setup_step', step=1))


@setup_bp.route('/setup/step/<int:step>')
@login_required
def setup_step(step):
    """Multi-step onboarding wizard."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    if step < 1 or step > 5:
        return redirect(url_for('setup.setup_step', step=1))

    # Check if already setup
    if user.setup_complete and step == 1:
        flash('Your account is already set up! You can update settings here.', 'info')
        return redirect(url_for('settings.settings_page'))

    # Get current progress
    credentials = {
        'anthropic_api_key': user.has_credential('anthropic_api_key'),
        'service_account': user.has_credential('service_account'),
        'gmail_token': user.has_credential('gmail_token'),
        'google_sheets_id': user.has_credential('google_sheets_id'),
    }

    return render_template('setup.html',
        active_page='setup',
        step=step,
        user=user,
        credentials=credentials,
    )


@setup_bp.route('/setup/save/<int:step>', methods=['POST'])
@login_required
def save_step(step):
    """Save a setup step."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        if step == 1:
            # Welcome - just continue
            flash('Welcome! Let\'s set up your account.', 'success')
            return redirect(url_for('setup.setup_step', step=2))

        elif step == 2:
            # Anthropic API Key
            api_key = request.form.get('anthropic_api_key', '').strip()
            if not api_key:
                flash('Please enter your Anthropic API key.', 'danger')
                return redirect(url_for('setup.setup_step', step=2))

            if not api_key.startswith('sk-ant-'):
                flash('Invalid API key format. It should start with "sk-ant-".', 'warning')

            user.set_credential('anthropic_api_key', api_key)
            flash('Anthropic API key saved!', 'success')
            return redirect(url_for('setup.setup_step', step=3))

        elif step == 3:
            # Google Sheets Service Account
            service_account_json = request.form.get('service_account_json', '').strip()
            google_sheets_id = request.form.get('google_sheets_id', '').strip()

            if not service_account_json:
                flash('Please provide the service account JSON.', 'danger')
                return redirect(url_for('setup.setup_step', step=3))

            # Validate JSON
            try:
                sa_data = json.loads(service_account_json)
                if 'type' not in sa_data or sa_data.get('type') != 'service_account':
                    flash('Invalid service account JSON. Please check the file.', 'danger')
                    return redirect(url_for('setup.setup_step', step=3))
            except json.JSONDecodeError:
                flash('Invalid JSON format. Please paste the entire contents of your service_account.json file.', 'danger')
                return redirect(url_for('setup.setup_step', step=3))

            # Save service account
            user.set_credential('service_account', service_account_json)

            # Auto-create Google Sheet if ID not provided
            if not google_sheets_id:
                try:
                    from app_core import create_user_sheet_template
                    google_sheets_id = create_user_sheet_template(user)
                    flash('Google Sheet created automatically with all required columns!', 'success')
                except Exception as e:
                    logger.error(f"Failed to auto-create sheet for {user.email}: {e}")
                    flash('Could not auto-create sheet. Please provide a Google Sheets ID or try again.', 'danger')
                    return redirect(url_for('setup.setup_step', step=3))

            user.set_setting('google_sheets_id', google_sheets_id)
            flash('Google Sheets configured successfully!', 'success')
            return redirect(url_for('setup.setup_step', step=4))

        elif step == 4:
            # Gmail OAuth - handled by /oauth/authorize route
            # This step is informational/button-based, no form submission needed
            # Users click "Authorize Gmail" button which redirects to OAuth flow
            flash('Click "Authorize Gmail" to connect your account.', 'info')
            return redirect(url_for('setup.setup_step', step=4))

        elif step == 5:
            # Sender Information & Company Details
            sender_name = request.form.get('sender_name', '').strip()
            sender_email = request.form.get('sender_email', '').strip()
            sender_title = request.form.get('sender_title', '').strip()
            company_name = request.form.get('company_name', '').strip()
            company_phone = request.form.get('company_phone', '').strip()
            company_website = request.form.get('company_website', '').strip()
            company_address = request.form.get('company_address', '').strip()

            from app_core import is_valid_email
            if sender_email and not is_valid_email(sender_email):
                flash('Invalid sender email address.', 'danger')
                return redirect(url_for('setup.setup_step', step=5))

            # Save all settings
            if sender_name:
                user.set_setting('sender_name', sender_name)
            if sender_email:
                user.set_setting('sender_email', sender_email)
            if sender_title:
                user.set_setting('sender_title', sender_title)
            if company_name:
                user.set_setting('company_name', company_name)
            if company_phone:
                user.set_setting('company_phone', company_phone)
            if company_website:
                user.set_setting('company_website', company_website)
            if company_address:
                user.set_setting('company_address', company_address)

            # Mark setup as complete
            from models import get_db
            with get_db() as db:
                db.execute('UPDATE users SET setup_complete = 1 WHERE id = ?', (user.id,))

            logger.info(f"Setup completed for user {user.email}")
            flash('Setup complete! Welcome to Quartz Email System.', 'success')
            return redirect(url_for('dashboard.dashboard'))

    except Exception as e:
        logger.error(f"Setup step {step} failed for user {user.email}: {e}")
        safe_flash_error(e, 'Setup')
        return redirect(url_for('setup.setup_step', step=step))

    return redirect(url_for('setup.setup_step', step=step))


@setup_bp.route('/setup/skip', methods=['POST'])
@login_required
def skip_setup():
    """Skip setup wizard (for testing or if user wants to configure later)."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    from models import get_db
    with get_db() as db:
        db.execute('UPDATE users SET setup_complete = 1 WHERE id = ?', (user.id,))

    flash('Setup skipped. You can configure your credentials in Settings.', 'info')
    return redirect(url_for('dashboard.dashboard'))
