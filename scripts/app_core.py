"""
Core application state and shared utilities.
This module is imported by route blueprints to avoid circular imports.
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

from flask import session, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))

# Load .env
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

# ── Configuration ──────────────────────────────────────
SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '')
API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
GMAIL_CREDS = os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json')
SENDER_NAME = os.getenv('SENDER_NAME', 'Quartz Export')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
SENDER_TITLE = os.getenv('SENDER_TITLE', '')
COMPANY_NAME = os.getenv('COMPANY_NAME', 'Lorh La Seng Commercial')
COMPANY_PHONE = os.getenv('COMPANY_PHONE', '')
COMPANY_WEBSITE = os.getenv('COMPANY_WEBSITE', '')
COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', '')
MAX_EMAILS_PER_DAY = int(os.getenv('MAX_EMAILS_PER_DAY', '50'))
RESEARCH_DELAY = int(os.getenv('RESEARCH_DELAY_SECONDS', '2'))
MAX_RESEARCH_PER_RUN = int(os.getenv('MAX_RESEARCH_PER_RUN', '5'))
FOLLOWUP_DAYS = int(os.getenv('FOLLOWUP_DAYS', '3'))
APP_USERNAME = os.getenv('APP_USERNAME', 'admin')
APP_PASSWORD = os.getenv('APP_PASSWORD', 'quartz2024')

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

# ── Sheets service (lazy-init) ─────────────────────────
_sheets = None

def get_sheets():
    global _sheets
    if _sheets is None:
        _sheets = GoogleSheetsManager(SHEETS_ID)
        _sheets.authenticate()
    return _sheets

# ── AI Segmentation engine (lazy-init) ────────────────
_segmentation_engine = None

def get_segmentation_engine():
    global _segmentation_engine
    if _segmentation_engine is None:
        _segmentation_engine = CustomerSegmentationEngine(API_KEY)
    return _segmentation_engine

# ── Simple cache ───────────────────────────────────────
_cache = {}
CACHE_TTL = 60

def cached_get_customers():
    key = 'customers'
    if key in _cache and time.time() - _cache[key]['time'] < CACHE_TTL:
        return _cache[key]['data']
    data = get_sheets().get_customers()
    _cache[key] = {'data': data, 'time': time.time()}
    return data

def invalidate_cache():
    _cache.clear()

# ── Workflow state (thread-safe) ───────────────────────
workflow_lock = threading.Lock()
workflow_status = {
    'running': False,
    'log': [],
    'completed': False,
    'error': None
}

# ── Auth decorator ─────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth.login'))
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

# ── Safe error flash (A09 - no internal details to users) ─────
def safe_flash_error(error, context='Operation'):
    """Log full error internally, show generic message to user."""
    from flask import flash
    logger.error(f"{context}: {error}", exc_info=True)
    flash(f'{context} failed. Please try again or contact support.', 'danger')


# ── Email validation ──────────────────────────────────
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

def is_valid_email(email):
    """Check if email address has valid format."""
    return bool(email and EMAIL_REGEX.match(email.strip()))

# ── Reply classification ─────────────────────────────
# Pre-compiled patterns for word-boundary matching (avoids false positives like "cif" in "specifications")
_REPLY_RULES = [
    # Check negative/decline FIRST (e.g. "not interested" before "interested")
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
    """Classify a customer reply by type and detect pipeline stage.
    Returns (request_type, detected_stage) tuple.
    Uses word-boundary regex for short keywords to avoid false positives.
    """
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

def reload_config():
    """Reload configuration from .env file."""
    global SENDER_NAME, SENDER_EMAIL, SENDER_TITLE, COMPANY_NAME, COMPANY_PHONE, COMPANY_WEBSITE, COMPANY_ADDRESS, FOLLOWUP_DAYS
    env_path = os.path.join(PROJECT_ROOT, 'config', '.env')
    load_dotenv(env_path, override=True)
    SENDER_NAME = os.getenv('SENDER_NAME', 'Quartz Export')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
    SENDER_TITLE = os.getenv('SENDER_TITLE', '')
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Lorh La Seng Commercial')
    COMPANY_PHONE = os.getenv('COMPANY_PHONE', '')
    COMPANY_WEBSITE = os.getenv('COMPANY_WEBSITE', '')
    COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', '')
    FOLLOWUP_DAYS = int(os.getenv('FOLLOWUP_DAYS', '3'))
