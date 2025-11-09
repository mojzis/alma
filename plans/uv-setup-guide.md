# UV Project Setup Guide

## About This Project

This is a **UV-managed Python project**. UV is a modern, fast Python package installer and resolver. Use `uv` commands instead of `pip` for all dependency management.

## Initial Setup

### 1. Initialize Project (if not already done)
```bash
# Project should already be initialized
# But if starting fresh:
uv init
```

### 2. Add Core Dependencies

**Phase 1: Authentication**
```bash
uv add fastapi
uv add uvicorn
uv add jinja2
uv add python-dotenv
uv add httpx
uv add itsdangerous
```

**Phase 2: Core CRUD**
```bash
uv add python-frontmatter
uv add python-slugify
```

**Phase 3: Organization**
```bash
# No additional dependencies - uses stdlib json
```

**Phase 4: Intelligence (Optional)**
```bash
# Only add if you want these features:
uv add chromadb          # For embeddings
uv add sentence-transformers  # For embeddings
uv add ollama            # For LLM classification
```

**Phase 5: Polish**
```bash
# No additional Python dependencies
# Frontend libraries loaded via CDN
```

## Running the Application

### Development Server
```bash
# UV automatically manages the virtual environment
uv run uvicorn main:app --reload
```

### Run Scripts
```bash
# Regenerate indexes
uv run python regenerate.py
```

### Run Tests (when implemented)
```bash
uv run pytest
```

## Project Structure

```
alma/
├── pyproject.toml          # UV project configuration (replaces requirements.txt)
├── .python-version         # Python version specification
├── uv.lock                # Locked dependencies (like package-lock.json)
├── .env                   # Environment variables (gitignored)
├── main.py                # FastAPI application
├── auth.py                # Authentication logic
├── notes.py               # Note CRUD operations
├── indexes.py             # Index management
├── regenerate.py          # Manual index regeneration
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   └── partials/
├── static/                # Static assets
│   ├── css/
│   └── js/
├── notes/                 # User's markdown files
│   ├── personal/
│   ├── work/
│   └── reference/
├── .indexes/              # Generated indexes (gitignored)
│   ├── projects.json
│   ├── tags.json
│   ├── wiki-links.json
│   └── metadata.json
└── .intelligence/         # AI-generated data (gitignored)
    ├── embeddings/
    └── suggestions/
```

## Environment Configuration

Create `.env` file:
```bash
# Required
SECRET_KEY=<generate-with-python-c-import-secrets-print-secrets-token-hex-32>
GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Optional
DEBUG=True
ENABLE_EMBEDDINGS=false
ENABLE_LLM_CLASSIFICATION=false
ENABLE_GIT_AUTOCOMMIT=false
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/auth/callback`
5. Copy Client ID and Client Secret to `.env`

## Git Configuration

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/

# UV
.venv/
.python-version

# Environment
.env

# Application data
.indexes/
.intelligence/
notes/  # Optional: commit or ignore based on preference

# Exports
exports/
```

## Development Workflow

### Phase-by-Phase Implementation

Follow the detailed phase plans:
1. `plans/phase1-authentication.md` - Start here
2. `plans/phase2-core-crud.md` - Basic functionality
3. `plans/phase3-organization.md` - Filtering and search
4. `plans/phase4-intelligence.md` - Optional AI features
5. `plans/phase5-polish.md` - UX improvements

### Adding New Dependencies

**DO:**
```bash
uv add package-name        # Add latest version
uv add package-name==1.2.3 # Add specific version (if needed)
```

**DON'T:**
```bash
pip install package-name   # Don't use pip in UV projects
```

### Updating Dependencies

```bash
uv sync           # Sync dependencies with lock file
uv lock --upgrade # Update all dependencies
```

## Running Tests

Each phase plan includes manual tests. For automated tests:

```bash
# Add pytest
uv add pytest pytest-asyncio httpx

# Create tests/
mkdir tests

# Run tests
uv run pytest
```

**Example test structure:**
```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_unauthenticated_redirect():
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["location"]
```

## Production Deployment

### 1. Environment Setup
```bash
# On production server
export DEBUG=false
export GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback
# ... other production settings
```

### 2. Run with Production Server
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Use Process Manager (systemd, supervisor, or pm2)

**systemd example:**
```ini
[Unit]
Description=Notes App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/notes
Environment="PATH=/var/www/notes/.venv/bin"
ExecStart=/usr/local/bin/uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

### 4. Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /var/www/notes/static;
    }
}
```

## Minimal Implementation Guide

**Phase 1 Minimal (Authentication):**
- Set up FastAPI project
- Google OAuth login/logout
- Session management
- Protected routes
- **Estimated:** 2-3 hours

**Phase 2 Minimal (CRUD):**
- Create note (markdown file)
- List notes (read from files)
- Delete note
- Skip: Edit functionality (can add later)
- **Estimated:** 2-3 hours

**Phase 3 Minimal (Organization):**
- Manual regeneration script
- Basic project filter (3 hardcoded projects)
- Skip: Tags, search (can add later)
- **Estimated:** 1-2 hours

**Phase 4 & 5: Skip for MVP**

**Total MVP: 5-8 hours**

## Troubleshooting

### UV not found
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies not syncing
```bash
uv sync --refresh
```

### Python version mismatch
```bash
# Specify Python version
uv python install 3.11
uv python pin 3.11
```

### Module not found
```bash
# Make sure dependencies are installed
uv sync

# Run commands with uv run
uv run python main.py
```

## Best Practices

1. **Always use `uv add`** - Don't manually edit pyproject.toml for dependencies
2. **Commit uv.lock** - Ensures reproducible builds
3. **Use `uv run`** - Ensures correct virtual environment
4. **Keep .env out of git** - Never commit secrets
5. **Regenerate indexes after git pull** - If notes are version controlled

## Quick Start Commands

```bash
# Clone repo (or start fresh)
cd alma

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your Google OAuth credentials

# Create directories
mkdir -p notes/{personal,work,reference} .indexes .intelligence static/{css,js} templates/partials

# Run development server
uv run uvicorn main:app --reload

# In another terminal: regenerate indexes
uv run python regenerate.py
```

## Next Steps

1. Read `plans/implementation.md` for full architecture overview
2. Start with `plans/phase1-authentication.md`
3. Implement phase by phase, testing as you go
4. Use the tests in each phase plan to verify functionality
5. Keep it minimal - implement only what you need

## Resources

- [UV Documentation](https://github.com/astral-sh/uv)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [HTMX Documentation](https://htmx.org/)
- [Alpine.js Documentation](https://alpinejs.dev/)
