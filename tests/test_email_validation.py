"""Tests for email validation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from app_core import is_valid_email


def test_valid_emails():
    """Valid email formats should pass."""
    valid = [
        'user@example.com',
        'first.last@company.co.uk',
        'user+tag@domain.org',
        'user123@test.io',
        'a@b.cd',
    ]
    for email in valid:
        assert is_valid_email(email), f"Should be valid: {email}"


def test_invalid_emails():
    """Invalid email formats should fail."""
    invalid = [
        '',
        'not-an-email',
        '@domain.com',
        'user@',
        'user@.com',
        'user name@domain.com',
        'user@domain',
        None,
    ]
    for email in invalid:
        assert not is_valid_email(email), f"Should be invalid: {email}"


def test_whitespace_handling():
    """Emails with leading/trailing whitespace should be accepted after strip."""
    assert is_valid_email('  user@example.com  ')
    assert is_valid_email('\tuser@example.com\n')


def test_settings_validators():
    """Settings validators should work correctly."""
    from app_core import SETTINGS_VALIDATORS

    # MAX_EMAILS_PER_DAY
    assert SETTINGS_VALIDATORS['MAX_EMAILS_PER_DAY']('50')
    assert not SETTINGS_VALIDATORS['MAX_EMAILS_PER_DAY']('0')
    assert not SETTINGS_VALIDATORS['MAX_EMAILS_PER_DAY']('abc')
    assert not SETTINGS_VALIDATORS['MAX_EMAILS_PER_DAY']('999')

    # SENDER_EMAIL
    assert SETTINGS_VALIDATORS['SENDER_EMAIL']('test@example.com')
    assert not SETTINGS_VALIDATORS['SENDER_EMAIL']('not-email')

    # FOLLOWUP_DAYS
    assert SETTINGS_VALIDATORS['FOLLOWUP_DAYS']('3')
    assert not SETTINGS_VALIDATORS['FOLLOWUP_DAYS']('0')
    assert not SETTINGS_VALIDATORS['FOLLOWUP_DAYS']('50')
