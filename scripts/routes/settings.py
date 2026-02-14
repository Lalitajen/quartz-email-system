"""Settings routes - Per-user settings stored in SQLite."""

import json
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

    # Check credential status
    credentials_status = {
        'anthropic_api_key': user.has_credential('anthropic_api_key'),
        'service_account': user.has_credential('service_account'),
        'gmail_token': user.has_credential('gmail_token'),
        'google_sheets_id': bool(user.google_sheets_id),
    }

    return render_template('settings.html',
        active_page='settings',
        settings=current_settings,
        user=user,
        credentials_status=credentials_status,
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


@settings_bp.route('/settings/update-api-key', methods=['POST'])
@login_required
def update_api_key():
    """Update Anthropic API key."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        api_key = request.form.get('anthropic_api_key', '').strip()

        if not api_key:
            flash('Please enter an API key.', 'danger')
            return redirect(url_for('settings.settings_page'))

        if not api_key.startswith('sk-ant-'):
            flash('Invalid API key format. It should start with "sk-ant-".', 'warning')

        # Save encrypted
        user.set_credential('anthropic_api_key', api_key)
        logger.info(f"API key updated for user {user.email}")
        flash('Anthropic API key updated successfully!', 'success')

    except Exception as e:
        logger.error(f"API key update failed: {e}")
        safe_flash_error(e, 'Update API key')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/update-sheets-id', methods=['POST'])
@login_required
def update_sheets_id():
    """Update Google Sheets ID."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        sheets_id = request.form.get('google_sheets_id', '').strip()

        if not sheets_id:
            flash('Please enter a Google Sheets ID.', 'danger')
            return redirect(url_for('settings.settings_page'))

        # Validate format (Google Sheets IDs are typically 44 characters)
        if len(sheets_id) < 20:
            flash('Invalid Google Sheets ID format. Please check the ID.', 'warning')

        user.set_setting('google_sheets_id', sheets_id)
        logger.info(f"Google Sheets ID updated for user {user.email}")
        flash('Google Sheets ID updated successfully!', 'success')

    except Exception as e:
        logger.error(f"Sheets ID update failed: {e}")
        safe_flash_error(e, 'Update Sheets ID')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/update-service-account', methods=['POST'])
@login_required
def update_service_account():
    """Update Google Service Account JSON."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        service_account_json = request.form.get('service_account_json', '').strip()

        if not service_account_json:
            flash('Please provide the service account JSON.', 'danger')
            return redirect(url_for('settings.settings_page'))

        # Validate JSON
        try:
            sa_data = json.loads(service_account_json)
            if 'type' not in sa_data or sa_data.get('type') != 'service_account':
                flash('Invalid service account JSON. Please check the file.', 'danger')
                return redirect(url_for('settings.settings_page'))
        except json.JSONDecodeError:
            flash('Invalid JSON format. Please paste the entire contents of your service_account.json file.', 'danger')
            return redirect(url_for('settings.settings_page'))

        # Save encrypted
        user.set_credential('service_account', service_account_json)
        logger.info(f"Service account updated for user {user.email}")
        flash('Google Service Account updated successfully!', 'success')

    except Exception as e:
        logger.error(f"Service account update failed: {e}")
        safe_flash_error(e, 'Update service account')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/test-api-key', methods=['POST'])
@login_required
def test_api_key():
    """Test Anthropic API key connection."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        api_key = user.get_credential('anthropic_api_key')
        if not api_key:
            flash('No API key configured. Please add your Anthropic API key first.', 'warning')
            return redirect(url_for('settings.settings_page'))

        # Test API connection
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}]
        )

        if message.content:
            flash('✅ API key is valid! Connection successful.', 'success')
            logger.info(f"API key test successful for user {user.email}")
        else:
            flash('API key test returned no response.', 'warning')

    except Exception as e:
        logger.error(f"API key test failed: {e}")
        flash(f'❌ API key test failed: {str(e)}', 'danger')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/test-sheets', methods=['POST'])
@login_required
def test_sheets():
    """Test Google Sheets connection."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        sheets_id = user.google_sheets_id
        if not sheets_id:
            flash('No Google Sheets ID configured. Please add your Sheets ID first.', 'warning')
            return redirect(url_for('settings.settings_page'))

        service_account = user.get_credential('service_account')
        if not service_account:
            flash('No service account configured. Please add your service account first.', 'warning')
            return redirect(url_for('settings.settings_page'))

        # Test connection
        from app_core import get_sheets
        sheets = get_sheets()

        # Try to get the Customers sheet
        sheet = sheets.get_worksheet('Customers')
        headers = sheet.row_values(1)

        if headers:
            flash(f'✅ Google Sheets connection successful! Found {len(headers)} columns.', 'success')
            logger.info(f"Sheets test successful for user {user.email}")
        else:
            flash('Google Sheets connected but no headers found. Sheet might be empty.', 'warning')

    except Exception as e:
        logger.error(f"Sheets test failed: {e}")
        flash(f'❌ Google Sheets test failed: {str(e)}', 'danger')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/test-gmail', methods=['POST'])
@login_required
def test_gmail():
    """Test Gmail OAuth connection."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        gmail_token = user.get_credential('gmail_token')
        if not gmail_token:
            flash('No Gmail token configured. Please authorize Gmail first.', 'warning')
            return redirect(url_for('settings.settings_page'))

        # Test connection
        from app_core import get_gmail_service_for_user
        service = get_gmail_service_for_user(user)

        # Try to get user profile
        profile = service.users().getProfile(userId='me').execute()

        if profile:
            email = profile.get('emailAddress', 'Unknown')
            flash(f'✅ Gmail connection successful! Connected as: {email}', 'success')
            logger.info(f"Gmail test successful for user {user.email}")
        else:
            flash('Gmail connected but could not get profile.', 'warning')

    except Exception as e:
        logger.error(f"Gmail test failed: {e}")
        flash(f'❌ Gmail test failed: {str(e)}. You may need to re-authorize.', 'danger')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/auto-create-sheet', methods=['POST'])
@login_required
def auto_create_sheet():
    """Auto-create a new Google Sheet for the user."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        service_account = user.get_credential('service_account')
        if not service_account:
            flash('No service account configured. Please add your service account first.', 'warning')
            return redirect(url_for('settings.settings_page'))

        from app_core import create_user_sheet_template
        sheets_id = create_user_sheet_template(user)

        user.set_setting('google_sheets_id', sheets_id)
        flash(f'✅ Google Sheet created successfully! ID: {sheets_id}', 'success')
        logger.info(f"Auto-created sheet for user {user.email}: {sheets_id}")

    except Exception as e:
        logger.error(f"Auto-create sheet failed: {e}")
        flash(f'❌ Failed to create sheet: {str(e)}', 'danger')

    return redirect(url_for('settings.settings_page'))
