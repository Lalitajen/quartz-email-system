"""Settings routes."""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app_core import (login_required, PROJECT_ROOT, SETTINGS_VALIDATORS, reload_config, logger,
                      safe_flash_error)

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
@login_required
def settings_page():
    env_path = os.path.join(PROJECT_ROOT, 'config', '.env')
    current_settings = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    current_settings[key.strip()] = val.strip()
    except Exception:
        pass

    return render_template('settings.html',
        active_page='settings',
        settings=current_settings,
    )


@settings_bp.route('/settings/save', methods=['POST'])
@login_required
def save_settings():
    env_path = os.path.join(PROJECT_ROOT, 'config', '.env')

    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()

        updatable = ['SENDER_NAME', 'SENDER_EMAIL', 'SENDER_TITLE',
                     'COMPANY_NAME', 'COMPANY_PHONE', 'COMPANY_WEBSITE',
                     'COMPANY_ADDRESS',
                     'MAX_EMAILS_PER_DAY', 'RESEARCH_DELAY_SECONDS',
                     'MAX_RESEARCH_PER_RUN', 'EMAIL_CHECK_INTERVAL_HOURS',
                     'AUTO_REPLY_CONFIDENCE_THRESHOLD',
                     'FOLLOWUP_DAYS']

        errors = []
        for key in updatable:
            new_val = request.form.get(key, '')
            if not new_val:
                continue

            # Sanitize: strip newlines and carriage returns
            new_val = new_val.strip().replace('\n', '').replace('\r', '')

            # Validate
            validator = SETTINGS_VALIDATORS.get(key)
            if validator:
                try:
                    if not validator(new_val):
                        errors.append(f'Invalid value for {key}: {new_val}')
                        continue
                except (ValueError, IndexError):
                    errors.append(f'Invalid value for {key}: {new_val}')
                    continue

            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{key}='):
                    lines[i] = f'{key}={new_val}\n'
                    found = True
                    break
            if not found:
                lines.append(f'{key}={new_val}\n')

        if errors:
            for err in errors:
                flash(err, 'warning')
        else:
            with open(env_path, 'w') as f:
                f.writelines(lines)

            reload_config()
            logger.info("Settings saved successfully")
            flash('Settings saved successfully!', 'success')

    except Exception as e:
        logger.error(f"Settings save failed: {e}")
        safe_flash_error(e, 'Save settings')

    return redirect(url_for('settings.settings_page'))
