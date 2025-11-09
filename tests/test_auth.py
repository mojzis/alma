"""Tests for authentication functionality."""

import pytest
from alma.auth import create_session_cookie, verify_session_cookie


def test_unauthenticated_access(client):
    """Test that unauthenticated users are redirected to login."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]


def test_login_page_accessible(client):
    """Test that login page is accessible without authentication."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Google" in response.content or b"Sign in" in response.content


def test_session_cookie_creation():
    """Test session cookie creation and verification."""
    email = "test@example.com"
    cookie = create_session_cookie(email)

    assert cookie is not None
    assert isinstance(cookie, str)

    # Verify the cookie
    verified_email = verify_session_cookie(cookie)
    assert verified_email == email


def test_invalid_session_cookie():
    """Test that invalid session cookies are rejected."""
    invalid_cookie = "invalid-cookie-value"
    verified_email = verify_session_cookie(invalid_cookie)
    assert verified_email is None


def test_authenticated_access(authenticated_client):
    """Test that authenticated users can access the main app."""
    response = authenticated_client.get("/")
    assert response.status_code == 200
    assert b"Notes" in response.content


def test_logout(authenticated_client):
    """Test that logout destroys the session."""
    response = authenticated_client.post("/auth/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]

    # Verify cookie is deleted
    assert "session" not in response.cookies or response.cookies["session"] == ""
