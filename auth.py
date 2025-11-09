"""Authentication module with Google OAuth 2.0 and session management."""

import os
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import Cookie, HTTPException
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Load configuration from environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

# OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Session settings
SESSION_MAX_AGE = 604800  # 1 week in seconds


def get_google_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_user_info(access_token: str) -> dict:
    """Get user information from Google using access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


def create_session_cookie(user_email: str) -> str:
    """Create signed session cookie containing user email."""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(user_email, salt="session")


def verify_session_cookie(cookie: str) -> str | None:
    """Verify session cookie and return user email, or None if invalid."""
    if not cookie:
        return None

    try:
        serializer = URLSafeTimedSerializer(SECRET_KEY)
        user_email = serializer.loads(
            cookie, salt="session", max_age=SESSION_MAX_AGE
        )
        return user_email
    except (BadSignature, SignatureExpired):
        return None


async def require_auth(
    session: Annotated[str | None, Cookie()] = None
) -> str:
    """
    FastAPI dependency that requires valid authentication.
    Returns user email if authenticated, otherwise raises HTTPException.
    """
    if not session:
        raise HTTPException(
            status_code=302,
            headers={"Location": "/login"}
        )

    user_email = verify_session_cookie(session)
    if not user_email:
        raise HTTPException(
            status_code=302,
            headers={"Location": "/login"}
        )

    return user_email
