"""Tests for email service."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from services.email_service import send_email_via_gmail, EMAIL_REGEX


def test_email_regex():
    """Email regex should match valid addresses."""
    assert EMAIL_REGEX.match('user@example.com')
    assert EMAIL_REGEX.match('first.last@company.co.uk')
    assert not EMAIL_REGEX.match('invalid')
    assert not EMAIL_REGEX.match('@domain.com')
    assert not EMAIL_REGEX.match('')


def test_send_rejects_invalid_email():
    """send_email_via_gmail should reject invalid emails before connecting."""
    msg_id, error = send_email_via_gmail('', 'Subject', 'Body')
    assert msg_id is None
    assert 'Invalid email' in error

    msg_id, error = send_email_via_gmail('not-an-email', 'Subject', 'Body')
    assert msg_id is None
    assert 'Invalid email' in error

    msg_id, error = send_email_via_gmail('user@', 'Subject', 'Body')
    assert msg_id is None
    assert 'Invalid email' in error


def test_send_rejects_none_email():
    """send_email_via_gmail should handle None email."""
    msg_id, error = send_email_via_gmail(None, 'Subject', 'Body')
    assert msg_id is None
    assert 'Invalid email' in error
