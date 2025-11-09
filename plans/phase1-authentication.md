# Phase 1: Authentication

## Goal
Implement secure Google OAuth authentication with session management. Zero information leakage - no content without authentication.

## Tasks

### 1.1 Project Setup
- Create FastAPI project structure
  - `main.py` - Application entry point
  - `auth.py` - Authentication logic
  - `.env` - Environment variables (gitignored)
  - `requirements.txt` - Dependencies
  - `templates/` - Jinja2 templates directory
  - `static/` - CSS/JS assets directory

**Dependencies:**
```
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
python-dotenv==1.0.0
httpx==0.25.1
itsdangerous==2.1.2
```

### 1.2 Environment Configuration
Create `.env` file with:
```bash
SECRET_KEY=<generate-strong-random-key>
GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
```

### 1.3 Google OAuth Flow Implementation

**File: `auth.py`**
```python
import httpx
from fastapi import HTTPException, Response, Request
from itsdangerous import URLSafeTimedSerializer
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

def get_google_auth_url() -> str:
    """Generate Google OAuth URL"""

def exchange_code_for_token(code: str) -> dict:
    """Exchange auth code for access token"""

def verify_google_token(token: str) -> dict:
    """Verify token and get user info"""

def create_session_cookie(user_email: str) -> str:
    """Create signed session cookie"""

def verify_session_cookie(cookie: str) -> str | None:
    """Verify session cookie, return email or None"""
```

### 1.4 Session Management

**Implementation:**
- Use `itsdangerous.URLSafeTimedSerializer` for signed cookies
- Cookie settings:
  - `httponly=True` - No JS access
  - `secure=True` - HTTPS only (False in dev)
  - `samesite="lax"` - CSRF protection
  - `max_age=604800` - 1 week expiry

### 1.5 Protected Route Decorator

**File: `auth.py`**
```python
from fastapi import Depends, Cookie
from typing import Annotated

async def require_auth(
    session: Annotated[str | None, Cookie()] = None
) -> str:
    """Dependency that requires valid session cookie"""
    if not session:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

    user_email = verify_session_cookie(session)
    if not user_email:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

    return user_email
```

### 1.6 Authentication Routes

**File: `main.py`**
```python
@app.get("/")
async def index(user: str = Depends(require_auth)):
    """Main app - requires authentication"""
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login")
async def login_page():
    """Show login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/auth/google")
async def auth_google():
    """Redirect to Google OAuth"""
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)

@app.get("/auth/callback")
async def auth_callback(code: str, response: Response):
    """Handle Google OAuth callback"""
    # 1. Exchange code for token
    # 2. Verify token and get user info
    # 3. Create session cookie
    # 4. Redirect to main app

@app.post("/auth/logout")
async def logout(response: Response):
    """Destroy session"""
    response.delete_cookie("session")
    return RedirectResponse("/login")
```

### 1.7 Templates

**File: `templates/login.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Login - Notes</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <h1>Notes App</h1>
    <a href="/auth/google">Sign in with Google</a>
</body>
</html>
```

**File: `templates/index.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Notes</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <h1>Welcome, {{ user }}</h1>
    <form method="post" action="/auth/logout">
        <button type="submit">Logout</button>
    </form>
</body>
</html>
```

## Tests

### Test 1: Unauthenticated Access
**Objective:** Verify no content is accessible without authentication

**Steps:**
1. Start app: `uvicorn main:app --reload`
2. Visit `http://localhost:8000/` without session cookie
3. **Expected:** Redirect to `/login`
4. Visit any other route without session cookie
5. **Expected:** Redirect to `/login`

**Pass Criteria:** No protected content is visible without authentication

### Test 2: Google OAuth Flow
**Objective:** Verify complete authentication flow works

**Steps:**
1. Visit `http://localhost:8000/login`
2. Click "Sign in with Google"
3. **Expected:** Redirect to Google OAuth consent screen
4. Grant permissions
5. **Expected:** Redirect back to app with session cookie set
6. **Expected:** See main app page with user email

**Pass Criteria:** Successfully authenticated and session created

### Test 3: Session Persistence
**Objective:** Verify session cookie works across requests

**Steps:**
1. Authenticate successfully
2. Navigate to `http://localhost:8000/`
3. **Expected:** Still authenticated, see main page
4. Refresh page
5. **Expected:** Still authenticated

**Pass Criteria:** Session persists across multiple requests

### Test 4: Session Expiry
**Objective:** Verify expired sessions are rejected

**Steps:**
1. Set `max_age=1` in session cookie for testing
2. Authenticate successfully
3. Wait 2 seconds
4. Refresh page
5. **Expected:** Redirect to `/login`

**Pass Criteria:** Expired sessions are properly rejected

### Test 5: Logout
**Objective:** Verify logout destroys session

**Steps:**
1. Authenticate successfully
2. Click "Logout" button
3. **Expected:** Redirect to `/login` with session cookie deleted
4. Try to visit `http://localhost:8000/`
5. **Expected:** Redirect to `/login`

**Pass Criteria:** Session is destroyed and user must re-authenticate

### Test 6: Invalid Session Cookie
**Objective:** Verify tampered cookies are rejected

**Steps:**
1. Authenticate successfully
2. Manually edit session cookie value in browser dev tools
3. Refresh page
4. **Expected:** Redirect to `/login`

**Pass Criteria:** Invalid/tampered cookies are rejected

## Security Checklist
- [ ] Session secret is strong (32+ random bytes)
- [ ] Session secret is in `.env`, not committed to git
- [ ] Cookies use `httponly=True`
- [ ] Cookies use `secure=True` in production
- [ ] Cookies use `samesite="lax"`
- [ ] All routes except auth endpoints use `Depends(require_auth)`
- [ ] No user data exposed on login page
- [ ] HTTPS enforced in production

## Files Created
- `main.py` - FastAPI app with auth routes
- `auth.py` - Authentication logic
- `.env` - Environment configuration (gitignored)
- `requirements.txt` - Python dependencies
- `templates/login.html` - Login page
- `templates/index.html` - Main app page (placeholder)

## Phase Completion Criteria
- [ ] All tests pass
- [ ] Security checklist complete
- [ ] No content accessible without authentication
- [ ] Google OAuth flow works end-to-end
- [ ] Sessions persist and expire correctly
- [ ] Ready to build CRUD functionality in Phase 2
