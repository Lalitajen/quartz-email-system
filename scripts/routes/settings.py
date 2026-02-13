"""Settings routes - Per-user settings stored in SQLite."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app_core import login_required, get_current_user, logger, safe_flash_error

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
@login_required
def settings_page():
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    current_settings = user.get_all_settings()

    return render_template('settings.html',
        active_page='settings',
        settings=current_settings,
        user=user,
    )


@settings_bp.route('/settings/save', methods=['POST'])
@login_required
def save_settings():
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        updatable_fields = {
            'sender_name': str,
            'sender_email': str,
            'sender_title': str,
            'company_name': str,
            'company_phone': str,
            'company_website': str,
            'company_address': str,
            'max_emails_per_day': int,
            'research_delay_seconds': int,
            'max_research_per_run': int,
            'email_check_interval_hours': int,
            'auto_reply_confidence_threshold': float,
            'followup_days': int,
        }

        errors = []
        for field, field_type in updatable_fields.items():
            new_val = request.form.get(field, '').strip()
            if not new_val:
                continue

            new_val = new_val.replace('\n', '').replace('\r', '')

            try:
                if field_type == int:
                    typed_val = int(new_val)
                    if typed_val < 0:
                        errors.append(f'{field} must be non-negative')
                        continue
                elif field_type == float:
                    typed_val = float(new_val)
                    if typed_val < 0 or typed_val > 1:
                        errors.append(f'{field} must be between 0 and 1')
                        continue
                else:
                    typed_val = new_val

                if field == 'sender_email' or field == 'company_email':
                    from app_core import is_valid_email
                    if not is_valid_email(str(typed_val)):
                        errors.append(f'Invalid email address: {typed_val}')
                        continue

                user.set_setting(field, str(typed_val))

            except (ValueError, TypeError) as e:
                errors.append(f'Invalid value for {field}: {new_val}')
                continue

        if errors:
            for err in errors:
                flash(err, 'warning')
        else:
            logger.info(f"Settings saved for user {user.email}")
            flash('Settings saved successfully!', 'success')

    except Exception as e:
        logger.error(f"Settings save failed: {e}")
        safe_flash_error(e, 'Save settings')

    return redirect(url_for('settings.settings_page'))
