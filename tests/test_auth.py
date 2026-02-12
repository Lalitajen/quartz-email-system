"""Tests for authentication."""


def test_login_page_loads(client):
    """Login page should be accessible without auth."""
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'Login' in resp.data


def test_protected_routes_redirect(client):
    """Protected routes should redirect to login when not authenticated."""
    protected = ['/', '/customers', '/compose', '/tracking', '/batch_send',
                 '/settings', '/workflow', '/attachments', '/research']
    for route in protected:
        resp = client.get(route)
        assert resp.status_code == 302, f"{route} should redirect, got {resp.status_code}"
        assert '/login' in resp.headers.get('Location', ''), f"{route} should redirect to /login"


def test_login_success(client, app):
    """Valid credentials should log in."""
    resp = client.post('/login', data={
        'username': app.config['APP_USERNAME'],
        'password': app.config['APP_PASSWORD'],
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert '/' == resp.headers.get('Location', '') or '/login' not in resp.headers.get('Location', '')


def test_login_failure(client):
    """Invalid credentials should show error."""
    resp = client.post('/login', data={
        'username': 'wrong',
        'password': 'wrong',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Invalid' in resp.data or b'login' in resp.data.lower()


def test_logout(logged_in_client):
    """Logout should clear session and redirect to login."""
    resp = logged_in_client.get('/logout', follow_redirects=False)
    assert resp.status_code == 302
    # After logout, should redirect to login
    resp2 = logged_in_client.get('/')
    assert resp2.status_code == 302  # Redirected to login
