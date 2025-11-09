"""Main FastAPI application for the note-taking app."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from auth import (
    get_google_auth_url,
    exchange_code_for_token,
    get_user_info,
    create_session_cookie,
    require_auth,
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Notes App")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Ensure required directories exist
Path("notes/personal").mkdir(parents=True, exist_ok=True)
Path("notes/work").mkdir(parents=True, exist_ok=True)
Path("notes/reference").mkdir(parents=True, exist_ok=True)
Path(".indexes").mkdir(exist_ok=True)


@app.get("/")
async def index(request: Request, user: str = Depends(require_auth)):
    """Main app page - requires authentication."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": user, "notes": []}
    )


@app.get("/login")
async def login_page(request: Request):
    """Show login page with Google OAuth button."""
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.get("/auth/google")
async def auth_google():
    """Redirect to Google OAuth consent screen."""
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def auth_callback(code: str, response: Response):
    """
    Handle Google OAuth callback.
    Exchange code for token, get user info, create session.
    """
    try:
        # Exchange authorization code for access token
        token_data = await exchange_code_for_token(code)
        access_token = token_data["access_token"]

        # Get user information
        user_info = await get_user_info(access_token)
        user_email = user_info["email"]

        # Create session cookie
        session_cookie = create_session_cookie(user_email)

        # Set cookie and redirect to main app
        response = RedirectResponse("/")
        response.set_cookie(
            key="session",
            value=session_cookie,
            httponly=True,
            secure=os.getenv("DEBUG") != "True",  # HTTPS only in production
            samesite="lax",
            max_age=604800,  # 1 week
        )
        return response

    except Exception as e:
        # If OAuth fails, redirect back to login
        print(f"OAuth error: {e}")
        return RedirectResponse("/login?error=auth_failed")


@app.post("/auth/logout")
async def logout(response: Response):
    """Destroy session and redirect to login."""
    response = RedirectResponse("/login")
    response.delete_cookie("session")
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
