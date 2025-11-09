# Alma

A minimal, file-first note-taking app with Google OAuth authentication, HTMX for dynamic interactions, and markdown file storage.

## Features

- Secure Authentication - Google OAuth 2.0 with session management
- Simple Note Management - Create, edit, and delete notes with a clean interface
- Project Organization - Organize notes into Personal, Work, and Reference projects
- Tagging System - Add tags to notes for easy categorization
- Markdown Storage - All notes stored as plain markdown files with YAML frontmatter
- Dynamic UI - HTMX-powered interface with no page refreshes
- Clean Design - Minimal, distraction-free interface

## Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager
- Google OAuth credentials ([Get them here](https://console.cloud.google.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd alma
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

4. **Configure .env file**

   Edit `.env` and add your credentials:
   ```bash
   # Generate a secret key
   SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

   # Add your Google OAuth credentials
   GOOGLE_CLIENT_ID=your-client-id-here
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

   # Optional settings
   DEBUG=True
   ```

### Running the App

Start the development server:

```bash
uv run uvicorn alma.main:app --reload
```

Or use the shorthand:

```bash
uv run alma
```

The app will be available at **http://localhost:8000**

## Google OAuth Setup

### Step-by-Step Configuration

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**

2. **Create a new project** (or select existing)
   - Click "Select a project" > "New Project"
   - Give it a name like "Alma Notes"

3. **Configure OAuth consent screen**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" (unless you have a Google Workspace account)
   - Fill in app name: "Alma" (or your preferred name)
   - Add your email as support email
   - Click "Save and Continue"
   - Skip scopes (click "Save and Continue")
   - Add yourself as a test user
   - Click "Save and Continue"

4. **Create OAuth credentials**
   - Go to "Credentials" > "Create Credentials" > "OAuth 2.0 Client ID"
   - Application type: **Web application**
   - Name: "Alma Web Client"
   - **Authorized redirect URIs**: `http://localhost:8000/auth/callback`
     - **IMPORTANT**: Must be exactly this URL
     - No trailing slash
     - Must match `GOOGLE_REDIRECT_URI` in your `.env`

5. **Copy credentials to .env**
   - Click "Download JSON" or copy the Client ID and Client Secret
   - Update your `.env` file:
     ```bash
     GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
     GOOGLE_CLIENT_SECRET=your-actual-client-secret-here
     ```

### Troubleshooting OAuth Errors

**"400. That's an error. The server cannot process the request..."**
- Check that your `.env` file exists and has the correct credentials
- Verify `GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback` (no trailing slash)
- Ensure the redirect URI in Google Cloud Console matches exactly
- Run `uv run alma` and check for the "✓ Configuration validated" message

**"redirect_uri_mismatch" error:**
- The redirect URI in Google Cloud Console must exactly match the one in `.env`
- Check for trailing slashes, http vs https, localhost vs 127.0.0.1

**App still says "This app isn't verified":**
- This is normal for apps in testing mode
- Click "Advanced" > "Go to Alma (unsafe)" to proceed
- Add yourself as a test user in the OAuth consent screen

## Project Structure

```
alma/
├── alma/                      # Application code
│   ├── main.py               # FastAPI app and routes
│   ├── auth.py               # Google OAuth & session management
│   ├── notes.py              # Note CRUD operations
│   ├── templates/            # Jinja2 templates
│   │   ├── base.html         # Base template with HTMX/Alpine.js
│   │   ├── index.html        # Main app interface
│   │   ├── login.html        # Login page
│   │   └── partials/         # HTMX partial templates
│   └── static/               # CSS and JavaScript
├── notes/                    # Your markdown notes (gitignored)
│   ├── personal/
│   ├── work/
│   └── reference/
├── .indexes/                 # Fast lookup indexes (gitignored)
├── pyproject.toml            # Project configuration
├── .env                      # Environment variables (gitignored)
└── README.md                 # This file
```

## How It Works

### Note Storage

Notes are stored as markdown files with YAML frontmatter:

```markdown
---
id: 123e4567-e89b-12d3-a456-426614174000
title: My First Note
created: 2025-11-09T12:00:00
modified: 2025-11-09T12:00:00
project: personal
type: note
tags:
  - python
  - fastapi
user: you@example.com
---

Your note content goes here...
```

### Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: HTMX 1.9, Alpine.js 3.13
- **Auth**: Google OAuth 2.0, itsdangerous (session cookies)
- **Storage**: Markdown files with python-frontmatter
- **Templating**: Jinja2

## Usage

1. **Login** - Visit http://localhost:8000 and sign in with Google
2. **Create a Note** - Fill out the form on the left and click "Add Note"
3. **Edit a Note** - Click "Edit" to modify content inline
4. **Delete a Note** - Click "Delete" (with confirmation)
5. **Organize** - Use projects and tags to keep notes organized

## Development

### Install dev dependencies
```bash
uv sync --extra dev
```

### Run tests
```bash
uv run pytest
```

### Project Commands
```bash
# Start development server
uv run uvicorn alma.main:app --reload

# Or use the shorthand
uv run alma

# Run with custom host/port
uv run uvicorn alma.main:app --host 0.0.0.0 --port 8080 --reload

# Install new dependency
uv add <package-name>

# Update dependencies
uv lock --upgrade
```

## Roadmap

### Completed (Phase 1 & 2)
- [x] Google OAuth authentication
- [x] Session management
- [x] Note CRUD operations
- [x] HTMX dynamic updates
- [x] Markdown file storage
- [x] Project organization
- [x] Tagging system

### Coming Soon (Phase 3)
- [ ] Fast JSON indexing
- [ ] Project filtering UI
- [ ] Tag cloud and filtering
- [ ] Search functionality
- [ ] Manual index regeneration

### Future (Phase 4 & 5)
- [ ] Wiki-style links `[[link]]`
- [ ] Semantic search (embeddings)
- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Export functionality
- [ ] Mobile responsive design

See [plans/](plans/) directory for detailed implementation plans.

## Security Features

- HttpOnly cookies (no JavaScript access)
- Secure cookies (HTTPS only in production)
- SameSite=Lax (CSRF protection)
- Signed session cookies
- Session expiry (1 week)
- All routes require authentication

## Contributing

This is a personal project, but suggestions and improvements are welcome! See the detailed phase plans in the `plans/` directory for implementation guidance.

## License

MIT License - feel free to use this project however you like.

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [HTMX](https://htmx.org/) - Dynamic HTML without JavaScript
- [Alpine.js](https://alpinejs.dev/) - Minimal JavaScript framework
- [UV](https://github.com/astral-sh/uv) - Fast Python package manager

---

Made with care using minimal code and maximum simplicity
