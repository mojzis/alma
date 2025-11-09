# Phase 2: Core CRUD Operations

## Goal
Implement basic note creation, reading, updating, and deletion with HTMX for dynamic updates and Alpine.js for UI interactions. Markdown files with YAML frontmatter as storage.

## Prerequisites
- Phase 1 (Authentication) completed
- User can log in and session works

## Tasks

### 2.1 Add Dependencies

**Update `requirements.txt`:**
```
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
python-dotenv==1.0.0
httpx==0.25.1
itsdangerous==2.1.2
python-frontmatter==1.0.0
python-slugify==8.0.1
```

### 2.2 Notes Module

**File: `notes.py`**
```python
import frontmatter
from datetime import datetime
from pathlib import Path
from slugify import slugify
import uuid

NOTES_DIR = Path("notes")

def create_note(content: str, project: str, content_type: str, tags: list[str], user: str) -> dict:
    """Create markdown file with frontmatter, return note metadata"""
    # 1. Generate metadata
    # 2. Create frontmatter
    # 3. Write file
    # 4. Return note dict

def get_note(note_id: str) -> dict | None:
    """Load note from file by ID"""

def list_notes(project: str | None = None, limit: int = 50) -> list[dict]:
    """List notes, optionally filtered by project"""

def update_note(note_id: str, content: str, tags: list[str]) -> dict:
    """Update existing note"""

def delete_note(note_id: str) -> bool:
    """Delete note file"""

def _generate_filename(title: str) -> str:
    """Generate filename: YYYYMMDD-HHMMSS-slug.md"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(title, max_length=50)
    return f"{timestamp}-{slug}.md"

def _find_file_by_id(note_id: str) -> Path | None:
    """Find note file by ID in frontmatter"""
```

### 2.3 HTMX and Alpine.js Setup

**File: `templates/base.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Notes{% endblock %}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js" defer></script>
    <style>
        body { font-family: system-ui; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .note { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
        button { padding: 10px 20px; background: #0066cc; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background: #0052a3; }
        .htmx-indicator { display: none; }
        .htmx-request .htmx-indicator { display: inline; }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    {% block body %}{% endblock %}
</body>
</html>
```

### 2.4 Note Creation Form

**File: `templates/partials/note-form.html`**
```html
<form
    hx-post="/notes"
    hx-target="#notes-list"
    hx-swap="afterbegin"
    hx-on::after-request="this.reset()"
    x-data="{ content: '', valid: false }"
    x-init="$watch('content', val => valid = val.length > 0)"
>
    <div class="form-group">
        <label>Project</label>
        <select name="project" required>
            <option value="personal">Personal</option>
            <option value="work">Work</option>
            <option value="reference">Reference</option>
        </select>
    </div>

    <div class="form-group">
        <label>Type</label>
        <select name="content_type" required>
            <option value="note">Note</option>
            <option value="idea">Idea</option>
            <option value="task">Task</option>
            <option value="reference">Reference</option>
        </select>
    </div>

    <div class="form-group">
        <label>Tags (comma-separated)</label>
        <input type="text" name="tags" placeholder="python, fastapi, notes">
    </div>

    <div class="form-group">
        <label>Content</label>
        <textarea name="content" rows="6" required x-model="content"></textarea>
    </div>

    <button type="submit" :disabled="!valid">
        <span class="htmx-indicator">Saving...</span>
        <span>Add Note</span>
    </button>
</form>
```

### 2.5 Note Display Templates

**File: `templates/partials/note-item.html`**
```html
<div class="note" id="note-{{ note.id }}">
    <div>
        <strong>{{ note.title }}</strong>
        <span style="color: #666; font-size: 0.9em;">
            {{ note.created }} | {{ note.project }} | {{ note.type }}
        </span>
    </div>
    <div style="margin: 10px 0;">{{ note.content }}</div>
    <div style="color: #666; font-size: 0.9em;">
        {% if note.tags %}
            Tags: {{ note.tags|join(', ') }}
        {% endif %}
    </div>
    <div style="margin-top: 10px;">
        <button
            hx-get="/notes/{{ note.id }}/edit"
            hx-target="#note-{{ note.id }}"
            hx-swap="outerHTML"
        >Edit</button>
        <button
            hx-delete="/notes/{{ note.id }}"
            hx-target="#note-{{ note.id }}"
            hx-swap="outerHTML swap:300ms"
            hx-confirm="Delete this note?"
        >Delete</button>
    </div>
</div>
```

**File: `templates/partials/note-edit.html`**
```html
<div class="note" id="note-{{ note.id }}">
    <form
        hx-put="/notes/{{ note.id }}"
        hx-target="#note-{{ note.id }}"
        hx-swap="outerHTML"
    >
        <div class="form-group">
            <label>Tags (comma-separated)</label>
            <input type="text" name="tags" value="{{ note.tags|join(', ') }}">
        </div>

        <div class="form-group">
            <label>Content</label>
            <textarea name="content" rows="6" required>{{ note.content }}</textarea>
        </div>

        <button type="submit">Save</button>
        <button
            type="button"
            hx-get="/notes/{{ note.id }}"
            hx-target="#note-{{ note.id }}"
            hx-swap="outerHTML"
        >Cancel</button>
    </form>
</div>
```

### 2.6 Main App Page

**File: `templates/index.html`**
```html
{% extends "base.html" %}

{% block body %}
<header style="margin-bottom: 30px; border-bottom: 2px solid #ddd; padding-bottom: 10px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h1>Notes</h1>
        <div>
            <span>{{ user }}</span>
            <form method="post" action="/auth/logout" style="display: inline;">
                <button type="submit">Logout</button>
            </form>
        </div>
    </div>
</header>

<div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px;">
    <div>
        <h2>Add Note</h2>
        {% include "partials/note-form.html" %}
    </div>

    <div>
        <h2>Recent Notes</h2>
        <div id="notes-list">
            {% for note in notes %}
                {% include "partials/note-item.html" %}
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
```

### 2.7 CRUD Endpoints

**File: `main.py`** (update)
```python
from fastapi import Form
from typing import Annotated

@app.get("/")
async def index(request: Request, user: str = Depends(require_auth)):
    """Main app page"""
    notes_list = notes.list_notes(limit=20)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "notes": notes_list
    })

@app.post("/notes")
async def create_note(
    request: Request,
    project: Annotated[str, Form()],
    content_type: Annotated[str, Form()],
    tags: Annotated[str, Form()],
    content: Annotated[str, Form()],
    user: str = Depends(require_auth)
):
    """Create new note, return HTML fragment"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    note = notes.create_note(content, project, content_type, tag_list, user)
    return templates.TemplateResponse("partials/note-item.html", {
        "request": request,
        "note": note
    })

@app.get("/notes/{note_id}")
async def get_note(
    request: Request,
    note_id: str,
    user: str = Depends(require_auth)
):
    """Get single note, return HTML fragment"""
    note = notes.get_note(note_id)
    if not note:
        raise HTTPException(404)
    return templates.TemplateResponse("partials/note-item.html", {
        "request": request,
        "note": note
    })

@app.get("/notes/{note_id}/edit")
async def edit_note(
    request: Request,
    note_id: str,
    user: str = Depends(require_auth)
):
    """Get edit form, return HTML fragment"""
    note = notes.get_note(note_id)
    if not note:
        raise HTTPException(404)
    return templates.TemplateResponse("partials/note-edit.html", {
        "request": request,
        "note": note
    })

@app.put("/notes/{note_id}")
async def update_note(
    request: Request,
    note_id: str,
    tags: Annotated[str, Form()],
    content: Annotated[str, Form()],
    user: str = Depends(require_auth)
):
    """Update note, return HTML fragment"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    note = notes.update_note(note_id, content, tag_list)
    return templates.TemplateResponse("partials/note-item.html", {
        "request": request,
        "note": note
    })

@app.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    user: str = Depends(require_auth)
):
    """Delete note, return empty response"""
    notes.delete_note(note_id)
    return ""
```

### 2.8 Create Notes Directory Structure

```bash
mkdir -p notes/personal notes/work notes/reference
```

## Tests

### Test 1: Create Note
**Objective:** Verify note creation works end-to-end

**Steps:**
1. Log in to app
2. Fill out note form:
   - Project: Personal
   - Type: Note
   - Tags: test, phase2
   - Content: This is my first note
3. Click "Add Note"
4. **Expected:** Note appears at top of list immediately (HTMX swap)
5. **Expected:** Form clears automatically
6. Check `notes/personal/` directory
7. **Expected:** Markdown file created with correct frontmatter

**Pass Criteria:**
- Note appears in UI immediately
- File created with valid frontmatter
- Form resets after submission

### Test 2: List Notes
**Objective:** Verify notes display correctly

**Steps:**
1. Create 3 notes with different content
2. Refresh page
3. **Expected:** All 3 notes display
4. **Expected:** Most recent note appears first
5. **Expected:** Each note shows title, content, tags, metadata

**Pass Criteria:** All notes load and display correctly

### Test 3: Edit Note
**Objective:** Verify note editing works

**Steps:**
1. Create a note
2. Click "Edit" button
3. **Expected:** Note transforms into edit form (HTMX swap)
4. Change content and tags
5. Click "Save"
6. **Expected:** Note updates in UI (HTMX swap)
7. Check file on disk
8. **Expected:** File updated with new content
9. **Expected:** `modified` timestamp updated in frontmatter

**Pass Criteria:**
- Edit form loads inline
- Changes save successfully
- File reflects changes

### Test 4: Cancel Edit
**Objective:** Verify cancel discards changes

**Steps:**
1. Create a note
2. Click "Edit"
3. Change content
4. Click "Cancel"
5. **Expected:** Note reverts to original display (no changes saved)

**Pass Criteria:** Cancel reverts to view mode without saving

### Test 5: Delete Note
**Objective:** Verify note deletion works

**Steps:**
1. Create a note
2. Click "Delete"
3. **Expected:** Confirmation dialog appears
4. Confirm deletion
5. **Expected:** Note removed from UI with animation (HTMX swap)
6. Check `notes/` directory
7. **Expected:** File deleted

**Pass Criteria:**
- Confirmation required
- Note removed from UI
- File deleted from disk

### Test 6: Frontmatter Parsing
**Objective:** Verify frontmatter is correctly written and read

**Steps:**
1. Create a note with tags: python, fastapi
2. Open created file in text editor
3. **Expected:** Valid YAML frontmatter with:
   - `id` (UUID)
   - `title` (first line of content)
   - `created` (ISO timestamp)
   - `modified` (ISO timestamp)
   - `project` (selected project)
   - `type` (selected type)
   - `tags` (list)
   - `user` (email)
4. **Expected:** Content appears after `---` separator

**Pass Criteria:** Frontmatter is valid YAML and contains all required fields

### Test 7: Multiple Projects
**Objective:** Verify notes are organized by project

**Steps:**
1. Create note in "Personal" project
2. Create note in "Work" project
3. Check directory structure
4. **Expected:** `notes/personal/` contains first note
5. **Expected:** `notes/work/` contains second note

**Pass Criteria:** Notes stored in correct project directories

### Test 8: Form Validation
**Objective:** Verify Alpine.js validation works

**Steps:**
1. Open app
2. Leave content empty
3. **Expected:** Submit button is disabled
4. Type content
5. **Expected:** Submit button becomes enabled

**Pass Criteria:** Form validation prevents empty submissions

### Test 9: HTMX Loading Indicator
**Objective:** Verify loading indicator appears during submission

**Steps:**
1. Fill out note form
2. Click "Add Note"
3. **Expected:** Button text changes to "Saving..." during request
4. **Expected:** Button reverts to "Add Note" after completion

**Pass Criteria:** Loading state visible during async request

## Files Created/Modified
- `notes.py` - Note CRUD operations
- `templates/base.html` - Base template with HTMX/Alpine.js
- `templates/index.html` - Main app page
- `templates/partials/note-form.html` - Creation form
- `templates/partials/note-item.html` - Note display
- `templates/partials/note-edit.html` - Edit form
- `main.py` - CRUD endpoints
- `notes/` - Directory structure

## Phase Completion Criteria
- [ ] All tests pass
- [ ] Can create, read, update, delete notes
- [ ] HTMX updates UI without page refresh
- [ ] Alpine.js form validation works
- [ ] Markdown files created with valid frontmatter
- [ ] Notes organized by project directory
- [ ] Ready for Phase 3 (organization features)
