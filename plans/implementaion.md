# Personal Note-Taking App - Implementation Plan

## Core Philosophy
Build a markdown-based note-taking system with **authentication-first security** (Google OAuth), **minimal JavaScript** (HTMX + Alpine.js), and **file-based storage** with intelligent regeneration. All content is private by default - no authentication = no access to anything.

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **Jinja2** - Server-side HTML templating
- **python-frontmatter** - YAML frontmatter parsing/writing

### Frontend
- **HTMX** - Dynamic interactions without writing JavaScript
- **Alpine.js** - Client-side UI state (dropdowns, modals, form validation)
- **Tailwind CSS** - Utility-first styling

### Authentication
- **Google OAuth 2.0** - Single authentication provider
- **httpx** - For OAuth token validation
- **Session cookies** - HttpOnly, Secure, SameSite=Lax

### Data Storage
- Markdown files with YAML frontmatter (organized by project)
- File structure: `notes/{project}/{timestamp}-{slug}.md`

---

## Architecture Overview

### Authentication Flow
1. **Landing page** - Only shows "Sign in with Google" button
2. **OAuth redirect** - User authenticates with Google
3. **Session creation** - Validate token, create secure session cookie
4. **Protected routes** - ALL routes require valid session (except OAuth callback)
5. **No authentication = 404/redirect** - Zero information leakage

### Request Flow with HTMX
```
Browser → HTMX request → FastAPI endpoint → 
  → Check session → Process → Return HTML fragment → 
  → HTMX swaps into page
```

### File Generation Flow
```
Form submission → FastAPI processes → 
  → Extract metadata (project, type, tags) →
  → Generate frontmatter →
  → Write markdown file →
  → Update indexes synchronously (project list, tags, wiki-links) →
  → Optional: git commit (background task) →
  → Return updated view
```

**For external edits:** Run manual regeneration command to rebuild all indexes from files.

---

## Key Components

### 1. Authentication System

**Google OAuth Integration:**
- Configure Google Cloud Console for OAuth credentials
- Redirect URI: `https://yourdomain.com/auth/callback`
- Scopes: `openid`, `email`, `profile`
- Store only necessary user info (email, name, google_id)

**Session Management:**
- Use `fastapi-sessions` or similar
- Session storage: Redis (production) or in-memory (development)
- Cookie config:
  - `secure=True` (HTTPS only)
  - `httponly=True` (no JS access)
  - `samesite="lax"` (CSRF protection)
  - `max_age=86400*7` (1 week expiry)

**Route Protection:**
- Dependency injection pattern: `Depends(require_auth)`
- All routes except `/auth/*` require valid session
- Invalid session → redirect to login
- No partial content exposure before auth

### 2. Form Interface

**Always-Visible Form:**
Located in persistent header/sidebar with:

**Form Fields:**
```html
<form hx-post="/notes" hx-target="#notes-list" hx-swap="afterbegin">
  <!-- Project dropdown (Alpine.js) -->
  <select name="project" x-data alpine>
    <option>Work</option>
    <option>Personal</option>
    <!-- Dynamic from existing projects -->
  </select>
  
  <!-- Content type dropdown -->
  <select name="content_type">
    <option>Note</option>
    <option>Idea</option>
    <option>Task</option>
    <option>Reference</option>
  </select>
  
  <!-- Tags input -->
  <input type="text" name="tags" placeholder="tag1, tag2, tag3">
  
  <!-- Main content (textarea or rich editor) -->
  <textarea name="content" required></textarea>
  
  <!-- Submit triggers HTMX request -->
  <button type="submit">Add Note</button>
</form>
```

**Alpine.js Enhancements:**
- Dropdown state management (open/close)
- Tag input with autocomplete from existing tags
- Character count for content
- Form validation before submission
- Loading states during submission

**HTMX Behavior:**
- `hx-post="/notes"` - Submits form via Ajax
- `hx-target="#notes-list"` - Updates notes list
- `hx-swap="afterbegin"` - Prepends new note
- `hx-indicator` - Shows loading spinner
- Success → clears form, shows new note
- Error → displays error message inline

### 3. FastAPI Backend Structure

**Core Endpoints:**

```
GET  /              → Main app (requires auth)
GET  /auth/login    → Redirect to Google OAuth
GET  /auth/callback → Handle OAuth, create session
POST /auth/logout   → Destroy session, redirect

POST /notes         → Create new note (returns HTML fragment)
GET  /notes/{id}    → View single note (returns HTML fragment)
PUT  /notes/{id}    → Update note (returns HTML fragment)
DELETE /notes/{id}  → Delete note (returns success/redirect)

GET  /api/projects  → List projects (JSON for Alpine.js)
GET  /api/tags      → List existing tags (JSON for autocomplete)

POST /admin/regenerate → Rebuild all indexes from files (manual trigger)
```

**Note Creation Handler:**
```python
@app.post("/notes")
async def create_note(
    project: str,
    content_type: str, 
    tags: str,
    content: str,
    user: User = Depends(require_auth)
):
    # 1. Parse and validate input
    # 2. Generate frontmatter
    # 3. Create markdown file
    # 4. Update indexes synchronously (fast - just JSON updates)
    # 5. Optional: Queue background tasks (embeddings, git commit)
    # 6. Return HTML fragment of new note
```

### 4. Markdown File Structure

**Frontmatter Format:**
```yaml
---
id: uuid-generated-once
title: First line of content or explicit
created: 2025-11-02T14:30:00Z
modified: 2025-11-02T14:30:00Z
project: Work
type: Note
tags:
  - python
  - fastapi
  - notes
user: user@example.com
---

Actual markdown content goes here...
```

**File Organization:**
```
notes/
├── work/
│   ├── 20251102-143000-meeting-notes.md
│   ├── 20251102-150000-api-design.md
├── personal/
│   ├── 20251102-160000-book-notes.md
└── reference/
    ├── 20251102-170000-python-tips.md
```

**File Naming Convention:**
- `{timestamp}-{slugified-title}.md`
- Timestamp: `YYYYMMDD-HHMMSS`
- Slug: Lowercase, hyphens, max 50 chars
- Ensures unique, sortable filenames

### 5. Index Generation Strategy

**Synchronous Updates (App-Initiated Changes):**
When the app creates/modifies/deletes notes, it updates indexes immediately in the same request:

**On New Note:**
```python
def create_note(content, project, tags, ...):
    # 1. Write markdown file with frontmatter
    file_path = write_note_file(...)
    
    # 2. Update indexes immediately
    update_project_index(project, note_id)
    update_tags_index(tags, note_id)
    extract_and_index_wiki_links(content, note_id)
    update_metadata_index(note_id, title, created, modified)
    
    # 3. Optional: Queue background tasks (non-blocking)
    #    - Generate embeddings
    #    - LLM classification
    #    - Git commit
    
    return note_html
```

**On Modified Note:**
```python
def update_note(note_id, new_content, new_tags, ...):
    # Load old note to see what changed
    old_note = load_note(note_id)
    
    # Write updated file
    write_note_file(...)
    
    # Update only what changed
    if tags_changed:
        update_tags_index(old_tags, new_tags, note_id)
    if links_changed:
        reindex_wiki_links(note_id, new_content)
    
    update_metadata_index(note_id, modified=now())
    
    return updated_note_html
```

**On Deleted Note:**
```python
def delete_note(note_id):
    note = load_note(note_id)
    
    # Remove from all indexes
    remove_from_project_index(note.project, note_id)
    remove_from_tags_index(note.tags, note_id)
    remove_wiki_links(note_id)
    remove_from_metadata_index(note_id)
    
    # Delete file
    os.remove(note.file_path)
    
    return success_response
```

**Manual Regeneration (External Edits):**
Provide a command/endpoint to rebuild all indexes from scratch by scanning files:

```python
# CLI: python regenerate.py
# Or endpoint: POST /admin/regenerate (admin only)

def regenerate_all_indexes():
    """Scan all markdown files and rebuild indexes from scratch"""
    # Clear existing indexes
    clear_all_indexes()
    
    # Scan notes directory
    for file_path in glob("notes/**/*.md", recursive=True):
        note = parse_markdown_file(file_path)
        
        # Rebuild all indexes
        update_project_index(note.project, note.id)
        update_tags_index(note.tags, note.id)
        extract_and_index_wiki_links(note.content, note.id)
        update_metadata_index(note.id, note.title, note.created, note.modified)
    
    return f"Regenerated indexes for {count} notes"
```

**When to regenerate manually:**
- After `git pull` that brings in external changes
- After editing files directly in an editor
- After fixing corrupted index files
- On initial setup to build indexes from existing notes

**Index Storage:**
Store indexes as JSON files for fast reads:
```
.indexes/
├── projects.json       # {project: [note_ids]}
├── tags.json          # {tag: [note_ids]}
├── wiki-links.json    # {note_id: [linked_note_ids]}
└── metadata.json      # {note_id: {title, created, modified, file_path}}
```

**Git Integration (Optional Background Task):**
```python
import subprocess

async def auto_commit_changes(note_id, action, note_title):
    """Queue git commit as background task - doesn't block response"""
    try:
        # Add the specific note file
        subprocess.run(["git", "add", f"notes/**/*{note_id}*.md"], check=True)
        
        # Commit with descriptive message
        subprocess.run(
            ["git", "commit", "-m", f"{action}: {note_title}"],
            check=True
        )
        
        # Optional: auto-push to remote
        # subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        # Log error but don't fail the request
        logger.error(f"Git commit failed: {e}")
```

**Clever Machinery (Phase 2):**
When ready to add intelligence, queue background tasks that don't block:
- Generate embeddings with local model → Store in `.intelligence/embeddings/`
- Run LLM classification for auto-tagging → Store in `.intelligence/classifications/`
- These are "nice-to-have" enhancements that happen asynchronously
- The app works perfectly fine without them

---

## HTMX Integration Patterns

### Pattern 1: Form Submission
```html
<form hx-post="/notes" hx-target="#result" hx-swap="innerHTML">
  <!-- form fields -->
</form>
```
FastAPI returns HTML fragment, HTMX swaps it in.

### Pattern 2: Live Search
```html
<input 
  type="search" 
  name="q"
  hx-get="/search" 
  hx-trigger="keyup changed delay:300ms"
  hx-target="#search-results"
>
```
Debounced search as user types.

### Pattern 3: Delete with Confirmation
```html
<button 
  hx-delete="/notes/{id}"
  hx-confirm="Delete this note?"
  hx-target="closest .note-item"
  hx-swap="outerHTML swap:1s"
>Delete</button>
```
Confirm dialog, then remove element with animation.

### Pattern 4: Infinite Scroll
```html
<div hx-get="/notes?page=2" hx-trigger="revealed" hx-swap="afterend">
  Loading more...
</div>
```
Load next page when element scrolls into view.

### FastAPI HTMX Response Helper
Detect HTMX requests and return appropriate response:
```python
from fastapi import Request

def render_template(request: Request, template: str, context: dict):
    if request.headers.get("HX-Request"):
        # Return just the fragment for HTMX
        return templates.TemplateResponse(
            f"partials/{template}", 
            context
        )
    else:
        # Return full page for direct navigation
        return templates.TemplateResponse(
            f"pages/{template}",
            context
        )
```

---

## Alpine.js Integration Patterns

### Pattern 1: Dropdown State
```html
<div x-data="{ open: false }">
  <button @click="open = !open">Select Project</button>
  <div x-show="open" @click.away="open = false">
    <!-- dropdown options -->
  </div>
</div>
```

### Pattern 2: Tag Autocomplete
```html
<div x-data="{ 
  tags: [],
  suggestions: [],
  query: ''
}" x-init="fetch('/api/tags').then(r => r.json()).then(d => tags = d)">
  <input 
    x-model="query"
    @input="suggestions = tags.filter(t => t.includes(query))"
  >
  <template x-for="tag in suggestions">
    <div @click="addTag(tag)" x-text="tag"></div>
  </template>
</div>
```

### Pattern 3: Form Validation
```html
<form x-data="{ 
  content: '',
  valid: false 
}" x-init="$watch('content', value => valid = value.length > 10)">
  <textarea x-model="content"></textarea>
  <button :disabled="!valid">Submit</button>
</form>
```

---

## Security Checklist

### Authentication
- [ ] Google OAuth properly configured
- [ ] Sessions use secure, httpOnly cookies
- [ ] Session secret is strong, from environment variable
- [ ] All routes except auth callbacks require authentication
- [ ] No content served to unauthenticated users

### Input Validation
- [ ] All form inputs validated server-side
- [ ] Markdown content sanitized (if rendering user HTML)
- [ ] File paths sanitized to prevent directory traversal
- [ ] Tag names validated (alphanumeric, hyphens, underscores only)

### File System
- [ ] Notes directory has proper permissions (not web-accessible)
- [ ] Filename generation prevents path injection
- [ ] File writes are atomic (write to temp, then rename)

### Headers
- [ ] Strict-Transport-Security (HSTS)
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Content-Security-Policy configured

---

## Development Workflow

### Phase 1: Authentication (Week 1)
1. Set up FastAPI project structure
2. Implement Google OAuth flow
3. Create session management
4. Build protected route decorator
5. Test: No content accessible without auth

### Phase 2: Core CRUD (Week 1-2)
1. Build note creation form (HTMX + Alpine.js)
2. Implement markdown file writing with frontmatter
3. Create note listing view
4. Add edit and delete functionality
5. Test: Full note lifecycle works

### Phase 3: Organization (Week 2)
1. Implement project-based organization
2. Add tag filtering
3. Build search interface (basic)
4. Create synchronous index update system
5. Add manual regeneration endpoint
6. Test: Can organize and find notes

### Phase 4: Intelligence (Week 3+)
1. Add wiki-link parsing and indexing
2. Implement semantic similarity (ChromaDB)
3. Integrate LLM classification (Ollama) as background tasks
4. Add git auto-commit (optional)
5. Test: Smart features work without blocking

### Phase 5: Polish (Ongoing)
1. Keyboard shortcuts
2. Mobile responsive design
3. Dark mode
4. Export functionality
5. Performance optimization

---

## File Structure

```
project/
├── main.py                 # FastAPI app
├── requirements.txt        # Dependencies
├── .env                   # Environment variables
├── templates/
│   ├── base.html          # Base layout
│   ├── pages/
│   │   ├── index.html     # Main app page
│   │   └── login.html     # Login page
│   └── partials/
│       ├── note-form.html # Form fragment
│       ├── note-item.html # Single note
│       └── note-list.html # List of notes
├── static/
│   ├── css/
│   │   └── styles.css     # Tailwind or custom CSS
│   └── js/
│       └── app.js         # Minimal JS if needed
├── notes/                 # User's markdown files
│   ├── work/
│   ├── personal/
│   └── reference/
├── .indexes/              # Generated indexes (gitignored)
│   ├── projects.json
│   ├── tags.json
│   └── wiki-links.json
└── .intelligence/         # AI-generated data (gitignored)
    ├── embeddings/
    └── classifications/
```

---

## Key Messages for Implementation

### 1. FastAPI as Template Engine
Use FastAPI primarily to serve HTML, not JSON. Most endpoints return Jinja2 templates (full pages) or template fragments (for HTMX). The app feels fast because HTMX updates page sections without full reloads.

### 2. Progressive Enhancement
Start with working HTML forms that submit normally. Layer on HTMX for Ajax behavior. Add Alpine.js for interactive UI elements. The app works (degraded) even if JavaScript fails.

### 3. File-First Architecture
Markdown files are the source of truth. Everything else (indexes, embeddings, classifications) can be regenerated from files. Users can edit files directly if needed. The app mediates access but doesn't lock in data.

### 4. Security By Default
Authentication happens first, before anything else. No information leakage to unauthenticated users. Every route checks authentication. Session management is secure by default.

### 5. Synchronous Index Updates
The app knows exactly what changed because it made the change. Update indexes immediately when writing files - it's fast because indexes are just JSON files. No background monitoring needed. For external edits (git pull, direct file editing), users run a manual regeneration command.

### 6. Alpine.js for State, HTMX for Server Communication
Use Alpine.js for purely client-side concerns (dropdown open/closed, form validation, loading states). Use HTMX for all server communication (form submissions, loading content, search). They complement each other perfectly.

---

## Environment Variables

```bash
# .env file
SECRET_KEY=your-session-secret-key
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback

# Paths
NOTES_DIR=./notes
INDEXES_DIR=./.indexes
INTELLIGENCE_DIR=./.intelligence

# Session
SESSION_MAX_AGE=604800  # 1 week in seconds

# Development
DEBUG=True
```

---

## Next Steps for Claude Code

1. **Start with authentication** - Nothing else matters if this isn't solid
2. **Build the simplest CRUD** - Form submission that writes files and updates indexes
3. **Add HTMX incrementally** - Start with one interaction, expand from there
4. **Layer in Alpine.js for UI** - Add interactivity where it helps
5. **Implement manual regeneration** - For when files are edited externally (git pull, etc.)
6. **Add smart features later** - Embeddings, LLM classification are optional enhancements

The goal is a **secure, fast, file-based note-taking system** that feels like a modern web app but remains fundamentally simple. Markdown files you can edit with any tool (just run regeneration after), version controlled with git, enhanced with modern web capabilities through HTMX and Alpine.js, protected by solid authentication, and enriched with optional AI features that don't get in the way.
