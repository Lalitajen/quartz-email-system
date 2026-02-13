"""
SQLite-backed User model with encrypted credential storage.
Supports multi-user system where each user brings their own API keys.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager

from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger('quartz_web')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'quartz.db')

# Lazy-loaded Fernet cipher
_fernet = None


def _get_fernet():
    """Get Fernet cipher for encrypting/decrypting credentials."""
    global _fernet
    if _fernet is None:
        from cryptography.fernet import Fernet
        import base64
        import hashlib
        key_source = os.getenv('CREDENTIAL_ENCRYPTION_KEY', '')
        if not key_source:
            # Fall back to Flask secret key
            secret_file = os.path.join(PROJECT_ROOT, 'config', '.flask_secret')
            if os.path.exists(secret_file):
                with open(secret_file, 'rb') as f:
                    key_source = f.read().hex()
            else:
                key_source = os.getenv('FLASK_SECRET_KEY', 'default-dev-key-change-me')
        # Derive a proper 32-byte Fernet key
        key_bytes = hashlib.sha256(key_source.encode() if isinstance(key_source, str) else key_source).digest()
        _fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    return _fernet


def encrypt_value(plaintext):
    """Encrypt a string value."""
    if not plaintext:
        return None
    return _get_fernet().encrypt(plaintext.encode('utf-8'))


def decrypt_value(encrypted_bytes):
    """Decrypt an encrypted value."""
    if not encrypted_bytes:
        return None
    try:
        return _get_fernet().decrypt(encrypted_bytes).decode('utf-8')
    except Exception:
        logger.error("Failed to decrypt credential")
        return None


@contextmanager
def get_db():
    """Get a database connection with WAL mode for concurrent access."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(app=None):
    """Create tables if they don't exist and seed admin user."""
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_login TEXT,

                google_sheets_id TEXT DEFAULT '',
                service_account_enc BLOB DEFAULT NULL,
                gmail_token_enc BLOB DEFAULT NULL,
                gmail_credentials_enc BLOB DEFAULT NULL,
                anthropic_api_key_enc BLOB DEFAULT NULL,

                sender_name TEXT DEFAULT '',
                sender_email TEXT DEFAULT '',
                sender_title TEXT DEFAULT '',
                company_name TEXT DEFAULT '',
                company_phone TEXT DEFAULT '',
                company_website TEXT DEFAULT '',
                company_address TEXT DEFAULT '',
                max_emails_per_day INTEGER DEFAULT 50,
                research_delay_seconds INTEGER DEFAULT 2,
                max_research_per_run INTEGER DEFAULT 5,
                followup_days INTEGER DEFAULT 3,
                auto_reply_confidence REAL DEFAULT 0.8,

                setup_complete INTEGER NOT NULL DEFAULT 0
            );
        ''')

    # Seed admin from env vars if no users exist
    _seed_admin()


def _seed_admin():
    """Create admin user from environment variables if no users exist."""
    import base64

    with get_db() as db:
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return

    admin_email = os.getenv('ADMIN_EMAIL', '')
    admin_username = os.getenv('APP_USERNAME', 'admin')
    admin_password = os.getenv('APP_PASSWORD', 'quartz2024')

    if not admin_email:
        sender_email = os.getenv('SENDER_EMAIL', '')
        admin_email = sender_email if sender_email else f"{admin_username}@localhost"

    user = User.create(
        email=admin_email,
        password=admin_password,
        display_name=admin_username,
        role='admin'
    )
    if not user:
        return

    # Migrate existing credentials from env vars
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    if api_key:
        user.set_credential('anthropic_api_key', api_key)

    sheets_id = os.getenv('GOOGLE_SHEETS_ID', '')
    if sheets_id:
        user.update_field('google_sheets_id', sheets_id)

    # Migrate base64-encoded credentials
    sa_b64 = os.getenv('SERVICE_ACCOUNT_B64', '')
    if sa_b64:
        try:
            sa_json = base64.b64decode(sa_b64).decode('utf-8')
            user.set_credential('service_account', sa_json)
        except Exception as e:
            logger.error(f"Failed to migrate service account: {e}")

    gmail_b64 = os.getenv('GMAIL_TOKEN_B64', '')
    if gmail_b64:
        try:
            token_json = base64.b64decode(gmail_b64).decode('utf-8')
            user.set_credential('gmail_token', token_json)
        except Exception as e:
            logger.error(f"Failed to migrate Gmail token: {e}")

    # Also try file-based credentials
    if not sa_b64:
        sa_path = os.path.join(PROJECT_ROOT, 'service_account.json')
        if os.path.exists(sa_path):
            with open(sa_path, 'r') as f:
                user.set_credential('service_account', f.read())

    if not gmail_b64:
        token_path = os.path.join(PROJECT_ROOT, 'token.json')
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                user.set_credential('gmail_token', f.read())

    # Migrate sender settings
    settings = {
        'sender_name': os.getenv('SENDER_NAME', ''),
        'sender_email': os.getenv('SENDER_EMAIL', ''),
        'sender_title': os.getenv('SENDER_TITLE', ''),
        'company_name': os.getenv('COMPANY_NAME', ''),
        'company_phone': os.getenv('COMPANY_PHONE', ''),
        'company_website': os.getenv('COMPANY_WEBSITE', ''),
        'company_address': os.getenv('COMPANY_ADDRESS', ''),
    }
    for key, val in settings.items():
        if val:
            user.update_field(key, val)

    user.update_field('setup_complete', 1)
    logger.info(f"Admin user seeded: {admin_email}")


class User:
    """User model backed by SQLite."""

    def __init__(self, row):
        """Initialize from a sqlite3.Row."""
        for key in row.keys():
            setattr(self, key, row[key])

    @staticmethod
    def create(email, password, display_name='', role='user'):
        """Create a new user. Returns User or None if email exists."""
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (email, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
                    (email.lower().strip(), generate_password_hash(password), display_name, role)
                )
                user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            return User.get_by_id(user_id)
        except sqlite3.IntegrityError:
            return None

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        with get_db() as db:
            row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User(row) if row else None

    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        with get_db() as db:
            row = db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        return User(row) if row else None

    @staticmethod
    def get_all():
        """Get all users."""
        with get_db() as db:
            rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [User(r) for r in rows]

    def verify_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last_login timestamp."""
        with get_db() as db:
            db.execute("UPDATE users SET last_login = ? WHERE id = ?",
                       (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.id))

    def update_field(self, field, value):
        """Update a single field."""
        allowed = {
            'google_sheets_id', 'sender_name', 'sender_email', 'sender_title',
            'company_name', 'company_phone', 'company_website', 'company_address',
            'max_emails_per_day', 'research_delay_seconds', 'max_research_per_run',
            'followup_days', 'auto_reply_confidence', 'setup_complete',
            'display_name', 'is_active', 'role',
        }
        if field not in allowed:
            raise ValueError(f"Cannot update field: {field}")
        with get_db() as db:
            db.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, self.id))
        setattr(self, field, value)

    def update_settings(self, form_data):
        """Update multiple settings from form data."""
        field_map = {
            'SENDER_NAME': 'sender_name',
            'SENDER_EMAIL': 'sender_email',
            'SENDER_TITLE': 'sender_title',
            'COMPANY_NAME': 'company_name',
            'COMPANY_PHONE': 'company_phone',
            'COMPANY_WEBSITE': 'company_website',
            'COMPANY_ADDRESS': 'company_address',
            'MAX_EMAILS_PER_DAY': 'max_emails_per_day',
            'RESEARCH_DELAY_SECONDS': 'research_delay_seconds',
            'MAX_RESEARCH_PER_RUN': 'max_research_per_run',
            'FOLLOWUP_DAYS': 'followup_days',
            'AUTO_REPLY_CONFIDENCE_THRESHOLD': 'auto_reply_confidence',
            'GOOGLE_SHEETS_ID': 'google_sheets_id',
        }
        for form_key, db_field in field_map.items():
            val = form_data.get(form_key)
            if val is not None:
                val = val.strip()
                if db_field in ('max_emails_per_day', 'research_delay_seconds',
                                'max_research_per_run', 'followup_days'):
                    val = int(val) if val.isdigit() else getattr(self, db_field)
                elif db_field == 'auto_reply_confidence':
                    try:
                        val = float(val)
                    except ValueError:
                        val = getattr(self, db_field)
                self.update_field(db_field, val)

    def set_credential(self, cred_type, value):
        """Encrypt and store a credential."""
        col_map = {
            'service_account': 'service_account_enc',
            'gmail_token': 'gmail_token_enc',
            'gmail_credentials': 'gmail_credentials_enc',
            'anthropic_api_key': 'anthropic_api_key_enc',
        }
        col = col_map.get(cred_type)
        if not col:
            raise ValueError(f"Unknown credential type: {cred_type}")
        encrypted = encrypt_value(value)
        with get_db() as db:
            db.execute(f"UPDATE users SET {col} = ? WHERE id = ?", (encrypted, self.id))

    def get_credential(self, cred_type):
        """Decrypt and return a credential."""
        col_map = {
            'service_account': 'service_account_enc',
            'gmail_token': 'gmail_token_enc',
            'gmail_credentials': 'gmail_credentials_enc',
            'anthropic_api_key': 'anthropic_api_key_enc',
        }
        col = col_map.get(cred_type)
        if not col:
            return None
        # Re-fetch from DB to get latest
        with get_db() as db:
            row = db.execute(f"SELECT {col} FROM users WHERE id = ?", (self.id,)).fetchone()
        if not row:
            return None
        return decrypt_value(row[0])

    def has_credential(self, cred_type):
        """Check if a credential is set (without decrypting)."""
        col_map = {
            'service_account': 'service_account_enc',
            'gmail_token': 'gmail_token_enc',
            'gmail_credentials': 'gmail_credentials_enc',
            'anthropic_api_key': 'anthropic_api_key_enc',
        }
        col = col_map.get(cred_type)
        if not col:
            return False
        with get_db() as db:
            row = db.execute(f"SELECT {col} FROM users WHERE id = ?", (self.id,)).fetchone()
        return row and row[0] is not None

    def change_password(self, new_password):
        """Change user password."""
        with get_db() as db:
            db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                       (generate_password_hash(new_password), self.id))
