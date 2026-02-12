"""Pytest fixtures for Quartz Email System tests."""

import os
import sys
import pytest

# Set up paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
os.chdir(PROJECT_ROOT)


@pytest.fixture
def app():
    """Create Flask test app."""
    from web_app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client, app):
    """Test client with active login session."""
    with client.session_transaction() as sess:
        sess['authenticated'] = True
        sess['username'] = 'admin'
    return client
