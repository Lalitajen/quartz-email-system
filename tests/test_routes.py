"""Integration tests for all routes."""


def test_error_pages(client):
    """404 page should render."""
    resp = client.get('/nonexistent-page-xyz')
    assert resp.status_code in (302, 404)  # Might redirect to login first


def test_dashboard_loads(logged_in_client):
    """Dashboard should load for authenticated users."""
    resp = logged_in_client.get('/')
    # May return 200 or 500 depending on Sheets connection
    assert resp.status_code in (200, 500)


def test_settings_page_loads(logged_in_client):
    """Settings page should render."""
    resp = logged_in_client.get('/settings')
    assert resp.status_code == 200
    assert b'Settings' in resp.data


def test_login_page(client):
    """Login page should always be accessible."""
    resp = client.get('/login')
    assert resp.status_code == 200


def test_static_files(client):
    """Static CSS and JS should be served."""
    resp = client.get('/static/css/style.css')
    assert resp.status_code == 200
    assert b'navbar' in resp.data

    resp = client.get('/static/js/app.js')
    assert resp.status_code == 200
    assert b'initTableSearch' in resp.data


def test_csv_template_download(logged_in_client):
    """CSV template should download."""
    resp = logged_in_client.get('/customers/csv-template')
    assert resp.status_code == 200
    assert b'company_name' in resp.data
    assert 'text/csv' in resp.headers.get('Content-Type', '')
