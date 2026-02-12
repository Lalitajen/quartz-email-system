"""Gmail sending service."""

import os
import re
import json
import time
import base64
import pickle
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

logger = logging.getLogger('quartz_web')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_credentials():
    """Load OAuth credentials from JSON (preferred) or legacy pickle."""
    from google.oauth2.credentials import Credentials

    # Prefer JSON token file
    json_token_path = os.path.join(PROJECT_ROOT, 'token.json')
    if os.path.exists(json_token_path):
        with open(json_token_path, 'r') as f:
            token_data = json.load(f)
        return Credentials.from_authorized_user_info(token_data)

    # Fallback to legacy pickle (read-only, will migrate to JSON on refresh)
    pickle_token_path = os.path.join(PROJECT_ROOT, 'token.pickle')
    if os.path.exists(pickle_token_path):
        with open(pickle_token_path, 'rb') as f:
            return pickle.load(f)

    return None


def _save_credentials(creds):
    """Save credentials as JSON (secure, no code execution risk)."""
    json_token_path = os.path.join(PROJECT_ROOT, 'token.json')
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes) if creds.scopes else [],
    }
    with open(json_token_path, 'w') as f:
        json.dump(token_data, f)
    os.chmod(json_token_path, 0o600)


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = _load_credentials()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_credentials(creds)
        else:
            return None
    return build('gmail', 'v1', credentials=creds)


def send_email_via_gmail(to_email, subject, body, attachment_filenames=None,
                          sender_name='', sender_email=''):
    """Send email with attachments via Gmail API. Returns (msg_id, error)."""
    if not to_email or not EMAIL_REGEX.match(to_email.strip()):
        return None, f"Invalid email address: '{to_email}'"

    to_email = to_email.strip()

    service = get_gmail_service()
    if not service:
        return None, "Gmail not authenticated. Run authenticate_gmail.py first."

    msg = MIMEMultipart()
    msg['To'] = to_email
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_filenames:
        from werkzeug.utils import secure_filename
        attachments_dir = os.path.join(PROJECT_ROOT, 'attachments')
        for filename in attachment_filenames:
            safe_name = secure_filename(filename)
            if not safe_name:
                continue
            filepath = os.path.join(attachments_dir, safe_name)
            if not os.path.realpath(filepath).startswith(os.path.realpath(attachments_dir)):
                continue
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={safe_name}')
                    msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    # Retry once on transient errors
    last_error = None
    for attempt in range(2):
        try:
            sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
            logger.info(f"Email sent to {to_email}: {sent['id']}")
            return sent['id'], None
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # Don't retry on permanent errors (invalid address, auth, etc.)
            if any(perm in error_str for perm in ['invalid', 'unauthorized', 'forbidden', 'not found']):
                break
            if attempt == 0:
                logger.warning(f"Transient error sending to {to_email}, retrying in 2s: {e}")
                time.sleep(2)

    logger.error(f"Failed to send email to {to_email}: {last_error}")
    return None, str(last_error)
