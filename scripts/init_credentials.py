"""
Initialize credential files from base64-encoded environment variables.
Used in production (Render/Docker) where files can't be committed to git.
"""

import os
import base64
import logging

logger = logging.getLogger('quartz_web')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_credentials():
    """Decode base64 env vars and write credential files if they don't already exist."""
    credentials = {
        'SERVICE_ACCOUNT_B64': os.path.join(PROJECT_ROOT, 'service_account.json'),
        'GMAIL_TOKEN_B64': os.path.join(PROJECT_ROOT, 'token.json'),
        'GMAIL_CREDENTIALS_B64': os.path.join(PROJECT_ROOT, 'gmail_credentials.json'),
    }

    for env_var, file_path in credentials.items():
        # Skip if file already exists (local development)
        if os.path.exists(file_path):
            continue

        b64_value = os.getenv(env_var, '')
        if not b64_value:
            continue

        try:
            decoded = base64.b64decode(b64_value)
            with open(file_path, 'wb') as f:
                f.write(decoded)
            os.chmod(file_path, 0o600)
            logger.info(f"Initialized {os.path.basename(file_path)} from {env_var}")
        except Exception as e:
            logger.error(f"Failed to decode {env_var}: {e}")
