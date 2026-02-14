"""
Core application state and shared utilities.
This module is imported by route blueprints to avoid circular imports.
Supports multi-user mode: each user has their own credentials and settings.
"""

import os
import re
import sys
import json
import time
import uuid
import threading
import logging
from functools import wraps
from datetime import datetime

from flask import session, redirect, url_for, g, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))

# Load .env (for backward compat and initial admin seeding)
load_dotenv(os.path.join(PROJECT_ROOT, 'config', '.env'))

# Import automation classes
from main_automation import (
    GoogleSheetsManager,
    AIResearchEngine,
    EmailPersonalizationEngine,
    EmailTracker,
    AutoReplyEngine,
    PIPELINE_STAGES as DEFAULT_PIPELINE_STAGES
)
from automated_workflow import CustomerSegmentationEngine

# Load pipeline config
config_path = os.path.join(PROJECT_ROOT, 'config', 'pipeline_config.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        PIPELINE_STAGES = json.load(f)
        PIPELINE_STAGES = {int(k): v for k, v in PIPELINE_STAGES.items()}
else:
    PIPELINE_STAGES = DEFAULT_PIPELINE_STAGES

# ── Legacy globals (kept for backward compat with CLI scripts) ────
APP_USERNAME = os.getenv('APP_USERNAME', 'admin')
APP_PASSWORD = os.getenv('APP_PASSWORD', 'quartz2024')
GMAIL_CREDS = os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json')

SPAM_DOMAINS = [d.strip().lower() for d in os.getenv('SPAM_DOMAINS',
    '@accounts.google.com,@indeed.com,@pinterest.com,@discover.pinterest.com,@email.shopify.com,@englishgrammar.org,@360alumni.com,@inspire.pinterest.com,mailer-daemon@,noreply@,no-reply@,@shutterstock.com,@coursera.org,@discord.com,@malwarebytes.com,@dropbox.com'
).split(',')]

# ── Logging ────────────────────────────────────────────
log_dir = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'web_app.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('quartz_web')

# ── Engagement colors ──────────────────────────────────
ENGAGEMENT_COLORS = {
    'HOT': {'bg': 'danger', 'icon': 'fire'},
    'WARM': {'bg': 'warning text-dark', 'icon': 'thermometer-half'},
    'INTERESTED': {'bg': 'info', 'icon': 'eye'},
    'COLD': {'bg': 'secondary', 'icon': 'snow'},
    'UNRESPONSIVE': {'bg': 'dark', 'icon': 'x-circle'},
}

# ══════════════════════════════════════════════════════════
# PER-USER CONFIG SYSTEM
# ══════════════════════════════════════════════════════════

def get_current_user():
    """Get the current user from session. Returns User or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    # Cache in request context
    if not hasattr(g, '_current_user') or g._current_user is None:
        from models import User
        g._current_user = User.get_by_id(user_id)
    return g._current_user


def get_user_config(key, default=None):
    """Get a config value for the current user."""
    user = get_current_user()
    if not user:
        return default
    val = getattr(user, key, default)
    return val if val is not None else default


def get_api_key():
    """Get the Anthropic API key for the current user."""
    user = get_current_user()
    if not user:
        return os.getenv('ANTHROPIC_API_KEY', '')
    key = user.get_credential('anthropic_api_key')
    return key or os.getenv('ANTHROPIC_API_KEY', '')


def get_sender_info():
    """Return dict of sender info for the current user."""
    user = get_current_user()
    if not user:
        return {
            'sender_name': os.getenv('SENDER_NAME', ''),
            'sender_email': os.getenv('SENDER_EMAIL', ''),
            'sender_title': os.getenv('SENDER_TITLE', ''),
            'company_name': os.getenv('COMPANY_NAME', ''),
            'company_phone': os.getenv('COMPANY_PHONE', ''),
            'company_website': os.getenv('COMPANY_WEBSITE', ''),
            'company_address': os.getenv('COMPANY_ADDRESS', ''),
        }
    return {
        'sender_name': user.sender_name or '',
        'sender_email': user.sender_email or '',
        'sender_title': user.sender_title or '',
        'company_name': user.company_name or '',
        'company_phone': user.company_phone or '',
        'company_website': user.company_website or '',
        'company_address': user.company_address or '',
    }


# ── Per-user Sheets service ──────────────────────────────
def get_sheets():
    """Get GoogleSheetsManager for the current user."""
    user = get_current_user()
    if not user:
        raise RuntimeError("No authenticated user")

    cache_key = f'_sheets_{user.id}'
    if hasattr(g, cache_key):
        return getattr(g, cache_key)

    sheets_id = user.google_sheets_id
    if not sheets_id:
        raise RuntimeError("Google Sheets not configured. Please complete setup.")

    sa_json = user.get_credential('service_account')
    if not sa_json:
        raise RuntimeError("Service account not configured. Please complete setup.")

    mgr = GoogleSheetsManager(sheets_id)
    mgr.authenticate_from_json(sa_json)
    setattr(g, cache_key, mgr)
    return mgr


def get_segmentation_engine():
    """Get AI segmentation engine for current user."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Anthropic API key not configured.")
    return CustomerSegmentationEngine(api_key)


def get_gmail_service_for_user():
    """Get Gmail API service for the current user."""
    from services.email_service import get_gmail_service
    user = get_current_user()
    if not user:
        raise RuntimeError("No authenticated user")
    token_json = user.get_credential('gmail_token')
    if not token_json:
        raise RuntimeError("Gmail not configured. Please complete setup.")
    result = get_gmail_service(token_json_str=token_json)
    if isinstance(result, tuple):
        service, updated_creds = result
        if updated_creds and hasattr(updated_creds, 'token') and updated_creds.token:
            updated_token = json.dumps({
                'token': updated_creds.token,
                'refresh_token': updated_creds.refresh_token,
                'token_uri': updated_creds.token_uri,
                'client_id': updated_creds.client_id,
                'client_secret': updated_creds.client_secret,
                'scopes': list(updated_creds.scopes) if updated_creds.scopes else [],
            })
            user.set_credential('gmail_token', updated_token)
        return service
    return result


# ── Simple cache (per-user) ───────────────────────────
_cache = {}
CACHE_TTL = 60

def cached_get_customers():
    user_id = session.get('user_id', 'default')
    key = f'customers_{user_id}'
    if key in _cache and time.time() - _cache[key]['time'] < CACHE_TTL:
        return _cache[key]['data']
    data = get_sheets().get_customers()
    _cache[key] = {'data': data, 'time': time.time()}
    return data

def invalidate_cache():
    user_id = session.get('user_id', 'default')
    keys_to_remove = [k for k in _cache if k.endswith(f'_{user_id}')]
    for k in keys_to_remove:
        del _cache[k]

# ── Workflow state (per-user, thread-safe) ─────────────
workflow_lock = threading.Lock()
_workflow_states = {}

def get_workflow_status():
    """Get workflow status for current user."""
    user_id = session.get('user_id', 'default')
    if user_id not in _workflow_states:
        _workflow_states[user_id] = {
            'running': False, 'log': [], 'completed': False, 'error': None
        }
    return _workflow_states[user_id]

# Keep backward compat reference
workflow_status = get_workflow_status

# ── Auth decorators ───────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated') or not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated') or session.get('user_role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated

# ── Path safety ────────────────────────────────────────
def safe_attachment_path(filename):
    """Return safe path for attachment filename, or None."""
    filename = secure_filename(filename)
    if not filename:
        return None
    attachments_dir = os.path.join(PROJECT_ROOT, 'attachments')
    file_path = os.path.join(attachments_dir, filename)
    if not os.path.realpath(file_path).startswith(os.path.realpath(attachments_dir)):
        return None
    return file_path

# ── Badge helpers (registered as Jinja2 globals) ───────
from markupsafe import Markup

def engagement_badge(level):
    level = str(level).upper() if level else ''
    info = ENGAGEMENT_COLORS.get(level, {'bg': 'light text-dark', 'icon': 'question-circle'})
    if not level:
        return Markup('<span class="badge bg-light text-muted">N/A</span>')
    return Markup(f'<span class="badge bg-{info["bg"]}"><i class="bi bi-{info["icon"]} me-1"></i>{level}</span>')

def stage_badge(stage):
    stage_str = str(stage)
    name = PIPELINE_STAGES.get(int(stage_str), {}).get('name', stage_str) if stage_str.isdigit() else stage_str
    colors = {'1': 'primary', '2': 'info', '3': 'warning', '4': 'success', '5': 'danger', '6': 'dark', '7': 'secondary'}
    color = colors.get(stage_str, 'secondary')
    return Markup(f'<span class="badge bg-{color} badge-stage">{stage_str} - {name}</span>')

# ── Email log helper ───────────────────────────────────
def create_email_log(customer_id, customer, subject, body, stage,
                     attachments='', status='queued', email_type='outreach',
                     reviewed_by='approved', gmail_msg_id='', confidence=''):
    return {
        'email_id': f"EMAIL{int(time.time())}_{uuid.uuid4().hex[:6]}",
        'customer_id': customer_id,
        'company_name': customer.get('company_name', '') if customer else '',
        'contact_email': customer.get('contact_email', '') if customer else '',
        'subject': subject,
        'sent_date': datetime.now().strftime('%Y-%m-%d'),
        'sent_time': datetime.now().strftime('%H:%M:%S') if status == 'sent' else '',
        'pipeline_stage': str(stage),
        'email_type': email_type,
        'attachments': attachments,
        'status': status,
        'opened': 'no',
        'replied': 'no',
        'reply_date': '',
        'reply_content_summary': '',
        'next_action': '',
        'ai_confidence': str(confidence),
        'reviewed_by': reviewed_by,
        'gmail_msg_id': gmail_msg_id,
    }

# ── Safe error flash ──────────────────────────────────
def safe_flash_error(error, context='Operation'):
    """Log full error internally, show generic message to user."""
    logger.error(f"{context}: {error}", exc_info=True)
    flash(f'{context} failed. Please try again or contact support.', 'danger')

# ── Email validation ──────────────────────────────────
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

def is_valid_email(email):
    """Check if email address has valid format."""
    return bool(email and EMAIL_REGEX.match(email.strip()))

# ── Reply classification ─────────────────────────────
_REPLY_RULES = [
    ('Declined', 10, ['not interested', 'unsubscribe', 'remove me', 'stop email',
                       'no thank', 'no thanks', 'pass on', r'\bdecline\b']),
    ('Quotation Request', 5, ['price', 'quote', 'quotation', r'\bcost\b', r'\bfob\b',
                               r'\bcif\b', 'pricing']),
    ('Sample Request', 4, ['sample', 'trial', r'\btest\b', r'\blab\b', '2-5kg', 'testing']),
    ('Technical Info Request', 3, ['specification', 'technical', 'data sheet', 'purity',
                                    r'\bsio2\b', 'boron', 'analysis', r'\bicp\b']),
    ('Contract Request', 6, ['contract', 'agreement', r'\bterms\b', 'payment']),
    ('Repeat Order', 9, ['repeat', 'reorder', 'bulk order', 'container']),
    ('Shipping Inquiry', 7, ['delivery', 'shipping', 'invoice', r'\bcoa\b']),
    ('Info Request', 2, ['interested', 'more info', 'tell me more', 'brochure']),
]

def classify_reply(reply_body):
    """Classify a customer reply by type and detect pipeline stage (keyword-based)."""
    text = reply_body.lower()
    for label, stage, patterns in _REPLY_RULES:
        for p in patterns:
            if p.startswith(r'\b'):
                if re.search(p, text):
                    return label, stage
            else:
                if p in text:
                    return label, stage
    return 'General Reply', None


def classify_reply_smart(
    reply_body,
    subject="",
    current_stage=1,
    email_history=None,
    customer_context=None,
    use_ai=True
):
    """
    Smart reply classification with AI fallback for higher accuracy.

    Args:
        reply_body: Email body text
        subject: Email subject line
        current_stage: Current pipeline stage
        email_history: Previous emails in thread
        customer_context: Additional context (company_name, industry, etc.)
        use_ai: Whether to use AI for classification (default True)

    Returns:
        dict: {
            'intent': str,           # Primary intent label
            'stage': int or None,    # Recommended pipeline stage
            'confidence': float,     # Confidence score 0.0-1.0
            'multiple_intents': bool,  # True if multiple intents detected
            'secondary_intents': list,
            'urgency_level': str,    # high/medium/low
            'sentiment': str,        # positive/neutral/negative
            'buying_signals': list,
            'objections': list,
            'reasoning': str,
            'ai_used': bool          # True if AI was used
        }
    """
    # Try keyword matching first (fast, free)
    keyword_result, keyword_stage = classify_reply(reply_body)

    # Count how many keyword rules matched
    text = reply_body.lower()
    matches = []
    for label, stage, patterns in _REPLY_RULES:
        for p in patterns:
            if p.startswith(r'\b'):
                if re.search(p, text):
                    matches.append((label, stage))
                    break
            else:
                if p in text:
                    matches.append((label, stage))
                    break

    # Decide whether to use AI:
    # - Multiple keyword matches (ambiguous)
    # - No keyword match (General Reply)
    # - Complex email (>100 words suggests complexity)
    word_count = len(reply_body.split())
    needs_ai = (
        len(matches) > 1 or
        keyword_result == 'General Reply' or
        word_count > 100
    )

    # If AI not needed or not available, return keyword result
    if not use_ai or not needs_ai:
        return {
            'intent': keyword_result,
            'stage': keyword_stage,
            'confidence': 0.7 if keyword_result != 'General Reply' else 0.3,
            'multiple_intents': len(matches) > 1,
            'secondary_intents': [],
            'urgency_level': 'medium',
            'sentiment': 'neutral',
            'buying_signals': [],
            'objections': [],
            'reasoning': f'Keyword match: {keyword_result}',
            'ai_used': False
        }

    # Use AI for analysis
    try:
        from ai_engines import SmartIntentDetectionEngine
        api_key = get_api_key()

        if not api_key:
            logger.warning("No API key available for AI classification")
            return {
                'intent': keyword_result,
                'stage': keyword_stage,
                'confidence': 0.5,
                'multiple_intents': False,
                'secondary_intents': [],
                'urgency_level': 'medium',
                'sentiment': 'neutral',
                'buying_signals': [],
                'objections': [],
                'reasoning': 'API key not available, using keyword fallback',
                'ai_used': False
            }

        engine = SmartIntentDetectionEngine(api_key)
        ai_result = engine.analyze_email_intent(
            email_body=reply_body,
            subject=subject,
            current_stage=current_stage,
            email_history=email_history,
            customer_context=customer_context
        )

        # Map AI intent to readable label
        intent_label_map = {
            'info_request': 'Info Request',
            'technical_info_request': 'Technical Info Request',
            'sample_request': 'Sample Request',
            'quotation_request': 'Quotation Request',
            'contract_request': 'Contract Request',
            'shipping_inquiry': 'Shipping Inquiry',
            'repeat_order': 'Repeat Order',
            'declined': 'Declined',
            'general_reply': 'General Reply',
        }

        primary_intent = intent_label_map.get(
            ai_result.get('primary_intent', 'general_reply'),
            ai_result.get('primary_intent', 'General Reply')
        )

        # Use AI result if confidence is high (>0.75), otherwise blend with keyword result
        if ai_result.get('confidence_score', 0) >= 0.75:
            final_intent = primary_intent
            final_stage = ai_result.get('recommended_stage')
        else:
            # Low AI confidence, use keyword result but keep AI metadata
            final_intent = keyword_result
            final_stage = keyword_stage

        return {
            'intent': final_intent,
            'stage': final_stage,
            'confidence': ai_result.get('confidence_score', 0.5),
            'multiple_intents': len(ai_result.get('secondary_intents', [])) > 0,
            'secondary_intents': ai_result.get('secondary_intents', []),
            'urgency_level': ai_result.get('urgency_level', 'medium'),
            'sentiment': ai_result.get('sentiment', 'neutral'),
            'buying_signals': ai_result.get('buying_signals', []),
            'objections': ai_result.get('objections', []),
            'reasoning': ai_result.get('reasoning', 'AI analysis completed'),
            'ai_used': True
        }

    except Exception as e:
        logger.error(f"AI classification failed: {e}", exc_info=True)
        # Fallback to keyword result
        return {
            'intent': keyword_result,
            'stage': keyword_stage,
            'confidence': 0.6,
            'multiple_intents': False,
            'secondary_intents': [],
            'urgency_level': 'medium',
            'sentiment': 'neutral',
            'buying_signals': [],
            'objections': [],
            'reasoning': f'AI failed, keyword fallback: {str(e)[:100]}',
            'ai_used': False
        }

# ── Settings validators ───────────────────────────────
SETTINGS_VALIDATORS = {
    'MAX_EMAILS_PER_DAY': lambda v: v.isdigit() and 1 <= int(v) <= 500,
    'RESEARCH_DELAY_SECONDS': lambda v: v.isdigit() and 1 <= int(v) <= 60,
    'MAX_RESEARCH_PER_RUN': lambda v: v.isdigit() and 1 <= int(v) <= 50,
    'EMAIL_CHECK_INTERVAL_HOURS': lambda v: v.isdigit() and 1 <= int(v) <= 168,
    'FOLLOWUP_DAYS': lambda v: v.isdigit() and 1 <= int(v) <= 30,
    'AUTO_REPLY_CONFIDENCE_THRESHOLD': lambda v: v.replace('.', '', 1).isdigit() and 0 <= float(v) <= 1,
    'SENDER_EMAIL': lambda v: '@' in v and '.' in v.split('@')[1] if v else True,
}

# Legacy compat
SENDER_NAME = os.getenv('SENDER_NAME', 'Quartz Export')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
SENDER_TITLE = os.getenv('SENDER_TITLE', '')
COMPANY_NAME = os.getenv('COMPANY_NAME', 'Lorh La Seng Commercial')
COMPANY_PHONE = os.getenv('COMPANY_PHONE', '')
COMPANY_WEBSITE = os.getenv('COMPANY_WEBSITE', '')
COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', '')
SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '')
API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
MAX_EMAILS_PER_DAY = int(os.getenv('MAX_EMAILS_PER_DAY', '50'))
RESEARCH_DELAY = int(os.getenv('RESEARCH_DELAY_SECONDS', '2'))
MAX_RESEARCH_PER_RUN = int(os.getenv('MAX_RESEARCH_PER_RUN', '5'))
FOLLOWUP_DAYS = int(os.getenv('FOLLOWUP_DAYS', '3'))

def reload_config():
    """No-op in multi-user mode. Settings are per-user in SQLite."""
    pass


def create_user_sheet_template(user):
    """
    Auto-create a Google Sheets template for new user with pre-configured columns.

    Args:
        user: User object with service account credential

    Returns:
        str: The created Google Sheets ID

    Raises:
        ValueError: If service account not configured
        Exception: If sheet creation fails
    """
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    import json

    # Get user's service account
    sa_json = user.get_credential('service_account')
    if not sa_json:
        raise ValueError("Service account not configured")

    sa_data = json.loads(sa_json)
    credentials = Credentials.from_service_account_info(
        sa_data,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    # Create Sheets API service
    service = build('sheets', 'v4', credentials=credentials)

    # Create spreadsheet with formatted header row
    spreadsheet = {
        'properties': {
            'title': f'Quartz Outreach - {user.display_name or user.email}',
            'locale': 'en_US',
            'timeZone': 'America/New_York',
        },
        'sheets': [{
            'properties': {
                'title': 'Customers',
                'gridProperties': {
                    'frozenRowCount': 1,  # Freeze header row
                    'frozenColumnCount': 0,
                },
            },
            'data': [{
                'startRow': 0,
                'startColumn': 0,
                'rowData': [{
                    'values': [
                        {
                            'userEnteredValue': {'stringValue': 'Company'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                        {
                            'userEnteredValue': {'stringValue': 'Email'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                        {
                            'userEnteredValue': {'stringValue': 'Contact Name'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                        {
                            'userEnteredValue': {'stringValue': 'Stage'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                        {
                            'userEnteredValue': {'stringValue': 'Last Contact'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                        {
                            'userEnteredValue': {'stringValue': 'Engagement'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                        {
                            'userEnteredValue': {'stringValue': 'Status'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                        {
                            'userEnteredValue': {'stringValue': 'Notes'},
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                            }
                        },
                    ]
                }]
            }]
        }]
    }

    result = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    sheet_id = result['spreadsheetId']

    logger.info(f"Created Google Sheet {sheet_id} for user {user.email}")
    return sheet_id
