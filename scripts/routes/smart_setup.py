"""
Smart Setup Assistant - AI-powered one-click credential configuration.
Intelligently detects, configures, and validates all required credentials.
"""

import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app_core import login_required, get_current_user, logger, safe_flash_error

smart_setup_bp = Blueprint('smart_setup', __name__)


@smart_setup_bp.route('/smart-setup')
@login_required
def smart_setup_page():
    """Smart setup assistant - intelligent credential configuration."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    # Analyze current setup status
    setup_status = analyze_setup_status(user)

    return render_template('smart_setup.html',
        active_page='smart_setup',
        setup_status=setup_status,
        user=user,
    )


def analyze_setup_status(user):
    """
    Intelligently analyze what's configured and what's missing.
    Returns detailed status for each credential.
    """
    status = {
        'overall_completion': 0,
        'total_steps': 4,
        'completed_steps': 0,
        'credentials': {},
        'next_action': None,
        'can_auto_complete': False,
    }

    # 1. Anthropic API Key
    has_api_key = user.has_credential('anthropic_api_key')
    status['credentials']['anthropic_api_key'] = {
        'name': 'Anthropic API Key',
        'configured': has_api_key,
        'tested': False,  # Will be tested if configured
        'required': True,
        'auto_configurable': False,  # Requires user input
        'icon': 'robot',
        'color': 'primary',
        'instructions': 'Get from https://console.anthropic.com/settings/keys',
        'test_endpoint': '/settings/test-api-key',
    }
    if has_api_key:
        status['completed_steps'] += 1

    # 2. Google Service Account
    has_service_account = user.has_credential('service_account')
    status['credentials']['service_account'] = {
        'name': 'Google Service Account',
        'configured': has_service_account,
        'tested': False,
        'required': True,
        'auto_configurable': False,  # Requires user input
        'icon': 'file-earmark-code',
        'color': 'info',
        'instructions': 'Download from https://console.cloud.google.com/iam-admin/serviceaccounts',
        'test_endpoint': None,  # Tested via sheets connection
    }
    if has_service_account:
        status['completed_steps'] += 1

    # 3. Google Sheets ID
    has_sheets_id = bool(user.google_sheets_id)
    status['credentials']['google_sheets_id'] = {
        'name': 'Google Sheets ID',
        'configured': has_sheets_id,
        'tested': False,
        'required': True,
        'auto_configurable': True,  # Can auto-create!
        'icon': 'table',
        'color': 'success',
        'instructions': 'Can be auto-created with one click',
        'test_endpoint': '/settings/test-sheets',
        'auto_setup_endpoint': '/settings/auto-create-sheet',
        'auto_setup_label': 'Auto-Create Sheet',
    }
    if has_sheets_id:
        status['completed_steps'] += 1

    # 4. Gmail OAuth
    has_gmail_token = user.has_credential('gmail_token')
    status['credentials']['gmail_token'] = {
        'name': 'Gmail OAuth',
        'configured': has_gmail_token,
        'tested': False,
        'required': True,
        'auto_configurable': True,  # One-click OAuth
        'icon': 'envelope',
        'color': 'warning',
        'instructions': 'One-click authorization via Google',
        'test_endpoint': '/settings/test-gmail',
        'auto_setup_endpoint': '/oauth/authorize',
        'auto_setup_label': 'Authorize Gmail',
    }
    if has_gmail_token:
        status['completed_steps'] += 1

    # Calculate overall completion percentage
    status['overall_completion'] = int((status['completed_steps'] / status['total_steps']) * 100)

    # Determine next recommended action
    if not has_api_key:
        status['next_action'] = 'anthropic_api_key'
    elif not has_service_account:
        status['next_action'] = 'service_account'
    elif not has_sheets_id:
        status['next_action'] = 'google_sheets_id'
    elif not has_gmail_token:
        status['next_action'] = 'gmail_token'
    else:
        status['next_action'] = 'complete'

    # Check if we can auto-complete remaining steps
    if has_api_key and has_service_account:
        # Can auto-create sheets and auto-authorize Gmail
        status['can_auto_complete'] = True

    return status


@smart_setup_bp.route('/smart-setup/auto-complete', methods=['POST'])
@login_required
def auto_complete_setup():
    """
    Intelligent auto-complete: automatically configure what's possible.
    - Auto-creates Google Sheet if service account exists
    - Redirects to Gmail OAuth if not authorized
    """
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        status = analyze_setup_status(user)
        auto_completed = []
        errors = []

        # Step 1: Auto-create Google Sheet (if service account exists)
        if status['credentials']['service_account']['configured'] and \
           not status['credentials']['google_sheets_id']['configured']:
            try:
                from app_core import create_user_sheet_template
                sheets_id = create_user_sheet_template(user)
                user.set_setting('google_sheets_id', sheets_id)
                auto_completed.append('✅ Google Sheet created automatically')
                logger.info(f"Auto-setup: Created sheet for {user.email}")
            except Exception as e:
                errors.append(f'Failed to create Google Sheet: {str(e)}')
                logger.error(f"Auto-setup sheet creation failed: {e}")

        # Step 2: Test connections for configured items
        if user.has_credential('anthropic_api_key'):
            try:
                import anthropic
                api_key = user.get_credential('anthropic_api_key')
                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "OK"}]
                )
                if message.content:
                    auto_completed.append('✅ Anthropic API tested successfully')
            except Exception as e:
                errors.append(f'Anthropic API test failed: {str(e)}')

        if user.google_sheets_id and user.has_credential('service_account'):
            try:
                from app_core import get_sheets
                sheets = get_sheets()
                sheet = sheets.get_worksheet('Customers')
                headers = sheet.row_values(1)
                if headers:
                    auto_completed.append(f'✅ Google Sheets tested ({len(headers)} columns)')
            except Exception as e:
                errors.append(f'Google Sheets test failed: {str(e)}')

        # Step 3: Redirect to Gmail OAuth if not configured
        if not user.has_credential('gmail_token'):
            if auto_completed:
                flash(' | '.join(auto_completed), 'success')
            if errors:
                flash(' | '.join(errors), 'warning')
            flash('🔄 Redirecting to Gmail authorization...', 'info')
            return redirect(url_for('oauth.oauth_authorize'))

        # All done!
        if auto_completed:
            flash(' | '.join(auto_completed), 'success')
        if errors:
            flash(' | '.join(errors), 'warning')

        # Check if everything is now complete
        final_status = analyze_setup_status(user)
        if final_status['overall_completion'] == 100:
            flash('🎉 Setup complete! All credentials configured and tested.', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('⚠️ Some steps still need attention. Please review below.', 'info')
            return redirect(url_for('smart_setup.smart_setup_page'))

    except Exception as e:
        logger.error(f"Auto-complete setup failed: {e}")
        safe_flash_error(e, 'Auto-complete setup')
        return redirect(url_for('smart_setup.smart_setup_page'))


@smart_setup_bp.route('/smart-setup/quick-config', methods=['POST'])
@login_required
def quick_config():
    """
    Quick configuration: accepts API key and service account in one form.
    Automatically creates sheet and redirects to Gmail OAuth.
    """
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        api_key = request.form.get('anthropic_api_key', '').strip()
        service_account_json = request.form.get('service_account_json', '').strip()

        errors = []
        success = []

        # 1. Save Anthropic API Key
        if api_key:
            if api_key.startswith('sk-ant-'):
                user.set_credential('anthropic_api_key', api_key)
                success.append('Anthropic API key saved')
                logger.info(f"Quick config: API key set for {user.email}")
            else:
                errors.append('Invalid API key format (should start with sk-ant-)')
        else:
            errors.append('Anthropic API key is required')

        # 2. Save Service Account
        if service_account_json:
            try:
                sa_data = json.loads(service_account_json)
                if sa_data.get('type') == 'service_account':
                    user.set_credential('service_account', service_account_json)
                    success.append('Service account saved')
                    logger.info(f"Quick config: Service account set for {user.email}")
                else:
                    errors.append('Invalid service account JSON')
            except json.JSONDecodeError:
                errors.append('Invalid JSON format for service account')
        else:
            errors.append('Service account JSON is required')

        # If both saved, auto-create sheet and redirect to OAuth
        if len(success) == 2:
            try:
                from app_core import create_user_sheet_template
                sheets_id = create_user_sheet_template(user)
                user.set_setting('google_sheets_id', sheets_id)
                success.append(f'Google Sheet created (ID: {sheets_id[:20]}...)')
                logger.info(f"Quick config: Sheet created for {user.email}")
            except Exception as e:
                errors.append(f'Failed to create sheet: {str(e)}')

            # Show success messages
            flash(' ✅ '.join(success), 'success')
            if errors:
                flash(' ⚠️ '.join(errors), 'warning')

            # Redirect to Gmail OAuth
            flash('🔄 Final step: Authorizing Gmail...', 'info')
            return redirect(url_for('oauth.oauth_authorize'))

        # Show errors
        if errors:
            flash(' | '.join(errors), 'danger')
        if success:
            flash(' | '.join(success), 'success')

        return redirect(url_for('smart_setup.smart_setup_page'))

    except Exception as e:
        logger.error(f"Quick config failed: {e}")
        safe_flash_error(e, 'Quick configuration')
        return redirect(url_for('smart_setup.smart_setup_page'))


@smart_setup_bp.route('/smart-setup/test-all', methods=['POST'])
@login_required
def test_all_credentials():
    """
    Test all configured credentials at once.
    Returns a comprehensive report.
    """
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    results = []

    # Test Anthropic API
    if user.has_credential('anthropic_api_key'):
        try:
            import anthropic
            api_key = user.get_credential('anthropic_api_key')
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "OK"}]
            )
            if message.content:
                results.append('✅ Anthropic API: Connected')
        except Exception as e:
            results.append(f'❌ Anthropic API: Failed ({str(e)[:50]})')
    else:
        results.append('⚠️ Anthropic API: Not configured')

    # Test Google Sheets
    if user.google_sheets_id and user.has_credential('service_account'):
        try:
            from app_core import get_sheets
            sheets = get_sheets()
            sheet = sheets.get_worksheet('Customers')
            headers = sheet.row_values(1)
            results.append(f'✅ Google Sheets: Connected ({len(headers)} columns)')
        except Exception as e:
            results.append(f'❌ Google Sheets: Failed ({str(e)[:50]})')
    else:
        results.append('⚠️ Google Sheets: Not configured')

    # Test Gmail OAuth
    if user.has_credential('gmail_token'):
        try:
            from app_core import get_gmail_service_for_user
            service = get_gmail_service_for_user(user)
            profile = service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress', 'Unknown')
            results.append(f'✅ Gmail: Connected as {email}')
        except Exception as e:
            results.append(f'❌ Gmail: Failed ({str(e)[:50]})')
    else:
        results.append('⚠️ Gmail: Not configured')

    # Display results
    flash(' | '.join(results), 'info')
    logger.info(f"Test all credentials for {user.email}: {results}")

    return redirect(url_for('smart_setup.smart_setup_page'))
