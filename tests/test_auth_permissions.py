"""Tests for authentication, role-based permissions, and password reset."""
import pytest
from app import create_app, db
from app.models import User, CustomerProfile


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, email='u@test.com', role_after=None):
    client.post('/auth/register', data={
        'email': email, 'password': 'pass1234',
        'confirm_password': 'pass1234',
        'first_name': 'Test', 'last_name': 'User',
    })


def _login(client, email='u@test.com'):
    return client.post('/auth/login', data={
        'email': email, 'password': 'pass1234',
    }, follow_redirects=True)


# ── access control ─────────────────────────────────────────────────────────────

def test_customer_cannot_access_admin(client):
    _register(client)
    _login(client)
    resp = client.get('/admin/dashboard', follow_redirects=True)
    assert b'Access denied' in resp.data or resp.status_code in (302, 403)


def test_anonymous_cannot_access_customer_dashboard(client):
    resp = client.get('/customer/dashboard', follow_redirects=True)
    assert b'log in' in resp.data.lower() or resp.status_code in (302, 401)


def test_admin_cannot_access_customer_routes(app, client):
    with app.app_context():
        admin = User(email='admin@test.com', role='admin')
        admin.set_password('pass1234')
        db.session.add(admin)
        db.session.commit()

    client.post('/auth/login', data={'email': 'admin@test.com', 'password': 'pass1234'})
    resp = client.get('/customer/dashboard', follow_redirects=True)
    assert b'Access denied' in resp.data


def test_inactive_user_cannot_login(app, client):
    _register(client, 'inactive@test.com')
    with app.app_context():
        user = User.query.filter_by(email='inactive@test.com').first()
        user.is_active = False
        db.session.commit()

    resp = client.post('/auth/login', data={
        'email': 'inactive@test.com', 'password': 'pass1234',
    }, follow_redirects=True)
    assert b'Invalid email or password' in resp.data


# ── password reset ─────────────────────────────────────────────────────────────

def test_forgot_password_returns_token_in_dev(client):
    _register(client, 'reset@test.com')
    resp = client.post('/auth/forgot-password', data={'email': 'reset@test.com'},
                       follow_redirects=True)
    assert resp.status_code == 200
    # In dev mode the reset link is rendered on the page
    assert b'reset-password' in resp.data


def test_reset_password_with_valid_token(app, client):
    _register(client, 'reset2@test.com')

    # Request reset
    resp = client.post('/auth/forgot-password', data={'email': 'reset2@test.com'},
                       follow_redirects=True)

    # Extract token from DB
    with app.app_context():
        from app.models import PasswordResetToken
        token = PasswordResetToken.query.first()
        assert token is not None
        token_value = token.token

    # Use token to set new password
    resp2 = client.post(f'/auth/reset-password/{token_value}', data={
        'password': 'newpass99', 'confirm_password': 'newpass99',
    }, follow_redirects=True)
    assert b'Password updated successfully' in resp2.data

    # Login with new password
    resp3 = client.post('/auth/login', data={
        'email': 'reset2@test.com', 'password': 'newpass99',
    }, follow_redirects=True)
    assert b'Customer Dashboard' in resp3.data


def test_reset_token_cannot_be_reused(app, client):
    _register(client, 'reset3@test.com')
    client.post('/auth/forgot-password', data={'email': 'reset3@test.com'},
                follow_redirects=True)

    with app.app_context():
        from app.models import PasswordResetToken
        token_value = PasswordResetToken.query.first().token

    # Use it once
    client.post(f'/auth/reset-password/{token_value}', data={
        'password': 'newpass99', 'confirm_password': 'newpass99',
    }, follow_redirects=True)

    # Try to use it again
    resp = client.post(f'/auth/reset-password/{token_value}', data={
        'password': 'anotherpass', 'confirm_password': 'anotherpass',
    }, follow_redirects=True)
    assert b'invalid or has expired' in resp.data


def test_logout_redirects_to_home(client):
    _register(client)
    _login(client)
    resp = client.get('/auth/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b'logged out' in resp.data
