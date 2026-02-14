"""OAuth 2.0 authorization flow for Gmail API."""

import os
import json
import secrets
from flask import Blueprint, request, redirect, url_for, flash, session
from google_auth_oauthlib.flow import Flow
from app_core import login_required, get_current_user, logger, PROJECT_ROOT

# Allow HTTP for local development (required for OAuth on localhost)
if os.getenv('FLASK_ENV', 'development') != 'production':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

oauth_bp = Blueprint('oauth', __name__)

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]


def _get_oauth_flow():
    """Create OAuth flow from gmail_credentials.json or env vars."""
    # Try environment variables first (for production)
    client_id = os.getenv('GMAIL_CLIENT_ID')
    client_secret = os.getenv('GMAIL_CLIENT_SECRET')

    if client_id and client_secret:
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [url_for('oauth.oauth_callback', _external=True)]
            }
        }
    else:
        # Fall back to credentials file
        creds_path = os.path.join(PROJECT_ROOT, 'gmail_credentials.json')
        if not os.path.exists(creds_path):
            raise FileNotFoundError("Gmail credentials not configured")

        with open(creds_path, 'r') as f:
            creds_data = json.load(f)

        # Convert "installed" type to "web" type
        if 'installed' in creds_data:
            client_config = {
                "web": {
                    "client_id": creds_data['installed']['client_id'],
                    "client_secret": creds_data['installed']['client_secret'],
                    "auth_uri": creds_data['installed']['auth_uri'],
                    "token_uri": creds_data['installed']['token_uri'],
                    "redirect_uris": [url_for('oauth.oauth_callback', _external=True)]
                }
            }
        else:
            client_config = creds_data

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=url_for('oauth.oauth_callback', _external=True)
    )
    return flow


@oauth_bp.route('/oauth/authorize')
@login_required
def oauth_authorize():
    """Redirect user to Google OAuth consent screen."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in.', 'warning')
        return redirect(url_for('auth.login'))

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    session['oauth_user_id'] = user.id

    try:
        flow = _get_oauth_flow()
        authorization_url, _ = flow.authorization_url(
            access_type='offline',  # Request refresh token
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent to get refresh token
        )

        logger.info(f"OAuth: Redirecting user {user.email} to Google consent")
        return redirect(authorization_url)

    except Exception as e:
        logger.error(f"OAuth authorization error: {e}")
        flash('Failed to initialize Gmail authorization. Please contact support.', 'danger')
        return redirect(url_for('setup.setup_step', step=4))


@oauth_bp.route('/oauth/callback')
@login_required
def oauth_callback():
    """Handle OAuth callback from Google."""
    user = get_current_user()
    if not user:
        flash('Session expired. Please log in.', 'warning')
        return redirect(url_for('auth.login'))

    # Verify state parameter (CSRF protection)
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        logger.warning(f"OAuth: State mismatch for user {user.email}")
        flash('Invalid OAuth state. Please try again.', 'danger')
        return redirect(url_for('setup.setup_step', step=4))

    # Check for errors
    if 'error' in request.args:
        error = request.args.get('error')
        logger.warning(f"OAuth: User {user.email} denied consent: {error}")
        flash('Gmail authorization was cancelled.', 'warning')
        return redirect(url_for('setup.setup_step', step=4))

    # Exchange authorization code for tokens
    try:
        flow = _get_oauth_flow()
        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials

        # Convert to JSON format for storage
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes),
        }

        # Save to encrypted database
        user.set_credential('gmail_token', json.dumps(token_data))

        # Clear session state
        session.pop('oauth_state', None)
        session.pop('oauth_user_id', None)

        logger.info(f"OAuth: Successfully authorized Gmail for user {user.email}")
        flash('Gmail authorized successfully!', 'success')
        return redirect(url_for('setup.setup_step', step=5))

    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        flash('Failed to complete Gmail authorization. Please try again.', 'danger')
        return redirect(url_for('setup.setup_step', step=4))
