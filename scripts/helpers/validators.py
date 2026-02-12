"""Input validation helpers."""

SETTINGS_VALIDATORS = {
    'MAX_EMAILS_PER_DAY': lambda v: v.isdigit() and 1 <= int(v) <= 500,
    'RESEARCH_DELAY_SECONDS': lambda v: v.isdigit() and 1 <= int(v) <= 60,
    'MAX_RESEARCH_PER_RUN': lambda v: v.isdigit() and 1 <= int(v) <= 50,
    'EMAIL_CHECK_INTERVAL_HOURS': lambda v: v.isdigit() and 1 <= int(v) <= 168,
    'AUTO_REPLY_CONFIDENCE_THRESHOLD': lambda v: v.replace('.', '', 1).isdigit() and 0 <= float(v) <= 1,
    'SENDER_EMAIL': lambda v: '@' in v and '.' in v.split('@')[1] if v else True,
}


def validate_setting(key, value):
    """Validate a setting value. Returns (is_valid, error_message)."""
    value = value.strip().replace('\n', '').replace('\r', '')
    validator = SETTINGS_VALIDATORS.get(key)
    if validator:
        try:
            if not validator(value):
                return False, f'Invalid value for {key}: {value}'
        except (ValueError, IndexError):
            return False, f'Invalid value for {key}: {value}'
    return True, None
