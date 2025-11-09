# Phase 3: Organization & Indexing

## Goal
Implement project filtering, tag-based navigation, basic search, and synchronous index management with manual regeneration capability.

## Prerequisites
- Phase 2 (Core CRUD) completed
- Notes can be created, read, updated, deleted

## Tasks

### 3.1 Index Management System

**File: `indexes.py`**
```python
import json
from pathlib import Path
from typing import Dict, List, Set
import frontmatter

INDEXES_DIR = Path(".indexes")
INDEXES_DIR.mkdir(exist_ok=True)

# Index file paths
PROJECTS_INDEX = INDEXES_DIR / "projects.json"
TAGS_INDEX = INDEXES_DIR / "tags.json"
METADATA_INDEX = INDEXES_DIR / "metadata.json"

def load_index(index_path: Path) -> dict:
    """Load index from JSON file"""
    if not index_path.exists():
        return {}
    return json.loads(index_path.read_text())

def save_index(index_path: Path, data: dict):
    """Save index to JSON file"""
    index_path.write_text(json.dumps(data, indent=2))

# Projects Index
def add_to_project_index(project: str, note_id: str):
    """Add note to project index"""

def remove_from_project_index(project: str, note_id: str):
    """Remove note from project index"""

def get_notes_by_project(project: str) -> List[str]:
    """Get all note IDs for a project"""

# Tags Index
def add_to_tags_index(tags: List[str], note_id: str):
    """Add note to tag indexes"""

def remove_from_tags_index(tags: List[str], note_id: str):
    """Remove note from tag indexes"""

def update_tags_index(old_tags: List[str], new_tags: List[str], note_id: str):
    """Update tags when note is modified"""

def get_notes_by_tag(tag: str) -> List[str]:
    """Get all note IDs for a tag"""

def get_all_tags() -> List[str]:
    """Get list of all tags"""

# Metadata Index
def add_to_metadata_index(note_id: str, title: str, created: str, modified: str, file_path: str, project: str):
    """Add note metadata to index"""

def update_metadata_index(note_id: str, modified: str):
    """Update modification time"""

def remove_from_metadata_index(note_id: str):
    """Remove note from metadata index"""

def get_note_metadata(note_id: str) -> dict | None:
    """Get metadata for a note"""

def get_all_metadata(limit: int = 100, offset: int = 0) -> List[dict]:
    """Get all note metadata, sorted by created date"""
```

### 3.2 Integrate Indexes with CRUD Operations

**Update `notes.py`:**
```python
import indexes

def create_note(content: str, project: str, content_type: str, tags: List[str], user: str) -> dict:
    """Create note and update indexes"""
    # ... existing file creation code ...

    # Update indexes synchronously
    indexes.add_to_project_index(project, note_id)
    indexes.add_to_tags_index(tags, note_id)
    indexes.add_to_metadata_index(note_id, title, created, modified, file_path, project)

    return note_dict

def update_note(note_id: str, content: str, tags: List[str]) -> dict:
    """Update note and indexes"""
    # Load old note to compare
    old_note = get_note(note_id)

    # ... existing file update code ...

    # Update indexes for changed tags
    old_tags = old_note.get("tags", [])
    if set(old_tags) != set(tags):
        indexes.update_tags_index(old_tags, tags, note_id)

    # Update modification time
    indexes.update_metadata_index(note_id, modified)

    return note_dict

def delete_note(note_id: str) -> bool:
    """Delete note and remove from indexes"""
    note = get_note(note_id)
    if not note:
        return False

    # Remove from indexes
    indexes.remove_from_project_index(note["project"], note_id)
    indexes.remove_from_tags_index(note.get("tags", []), note_id)
    indexes.remove_from_metadata_index(note_id)

    # Delete file
    # ... existing deletion code ...
```

### 3.3 Manual Regeneration Endpoint

**File: `regenerate.py`**
```python
from pathlib import Path
import frontmatter
import indexes

NOTES_DIR = Path("notes")

def regenerate_all_indexes():
    """Rebuild all indexes from markdown files"""
    # Clear existing indexes
    for index_file in indexes.INDEXES_DIR.glob("*.json"):
        index_file.write_text("{}")

    count = 0
    for md_file in NOTES_DIR.rglob("*.md"):
        note = frontmatter.load(md_file)
        metadata = note.metadata

        note_id = metadata.get("id")
        if not note_id:
            continue

        # Rebuild indexes
        indexes.add_to_project_index(metadata.get("project"), note_id)
        indexes.add_to_tags_index(metadata.get("tags", []), note_id)
        indexes.add_to_metadata_index(
            note_id,
            metadata.get("title"),
            metadata.get("created"),
            metadata.get("modified"),
            str(md_file),
            metadata.get("project")
        )
        count += 1

    return count

if __name__ == "__main__":
    count = regenerate_all_indexes()
    print(f"Regenerated indexes for {count} notes")
```

**Add to `main.py`:**
```python
from regenerate import regenerate_all_indexes

@app.post("/admin/regenerate")
async def regenerate_indexes(user: str = Depends(require_auth)):
    """Manually trigger index regeneration"""
    count = regenerate_all_indexes()
    return {"status": "success", "notes_indexed": count}
```

### 3.4 Project Filter Interface

**File: `templates/partials/project-filter.html`**
```html
<div style="margin-bottom: 20px;">
    <label>Filter by Project:</label>
    <div style="display: flex; gap: 10px; margin-top: 5px;">
        <button
            hx-get="/notes?project=all"
            hx-target="#notes-list"
            hx-swap="innerHTML"
        >All</button>
        <button
            hx-get="/notes?project=personal"
            hx-target="#notes-list"
            hx-swap="innerHTML"
        >Personal</button>
        <button
            hx-get="/notes?project=work"
            hx-target="#notes-list"
            hx-swap="innerHTML"
        >Work</button>
        <button
            hx-get="/notes?project=reference"
            hx-target="#notes-list"
            hx-swap="innerHTML"
        >Reference</button>
    </div>
</div>
```

### 3.5 Tag Cloud and Filter

**File: `templates/partials/tag-cloud.html`**
```html
<div style="margin-bottom: 20px;">
    <label>Filter by Tag:</label>
    <div style="margin-top: 5px;">
        {% for tag in tags %}
        <button
            hx-get="/notes?tag={{ tag }}"
            hx-target="#notes-list"
            hx-swap="innerHTML"
            style="margin: 2px; padding: 5px 10px; font-size: 0.9em;"
        >{{ tag }}</button>
        {% endfor %}
    </div>
</div>
```

### 3.6 Search Interface

**File: `templates/partials/search-bar.html`**
```html
<div style="margin-bottom: 20px;">
    <input
        type="search"
        name="q"
        placeholder="Search notes..."
        hx-get="/search"
        hx-trigger="keyup changed delay:300ms"
        hx-target="#notes-list"
        hx-swap="innerHTML"
        style="width: 100%; padding: 10px;"
    >
</div>
```

**File: `search.py`**
```python
from typing import List
import indexes

def search_notes(query: str) -> List[str]:
    """Simple full-text search in note content"""
    if not query:
        return []

    query_lower = query.lower()
    results = []

    # Search in metadata (titles)
    all_metadata = indexes.get_all_metadata(limit=1000)
    for meta in all_metadata:
        if query_lower in meta.get("title", "").lower():
            results.append(meta["id"])

    # TODO: Could also search in file content

    return results
```

### 3.7 Update Main Page with Filters

**Update `templates/index.html`:**
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
        <h2>Notes</h2>
        {% include "partials/search-bar.html" %}
        {% include "partials/project-filter.html" %}
        {% include "partials/tag-cloud.html" %}

        <div id="notes-list">
            {% for note in notes %}
                {% include "partials/note-item.html" %}
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
```

### 3.8 Filter and Search Endpoints

**Update `main.py`:**
```python
from search import search_notes
import indexes

@app.get("/")
async def index(request: Request, user: str = Depends(require_auth)):
    """Main app page"""
    notes_list = notes.list_notes(limit=20)
    all_tags = indexes.get_all_tags()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "notes": notes_list,
        "tags": all_tags
    })

@app.get("/notes")
async def filter_notes(
    request: Request,
    project: str | None = None,
    tag: str | None = None,
    user: str = Depends(require_auth)
):
    """Filter notes by project or tag, return HTML fragment"""
    if project and project != "all":
        note_ids = indexes.get_notes_by_project(project)
    elif tag:
        note_ids = indexes.get_notes_by_tag(tag)
    else:
        # Get all
        metadata = indexes.get_all_metadata(limit=50)
        note_ids = [m["id"] for m in metadata]

    # Load full notes
    notes_list = [notes.get_note(nid) for nid in note_ids if notes.get_note(nid)]

    return templates.TemplateResponse("partials/note-list-only.html", {
        "request": request,
        "notes": notes_list
    })

@app.get("/search")
async def search(
    request: Request,
    q: str,
    user: str = Depends(require_auth)
):
    """Search notes, return HTML fragment"""
    note_ids = search_notes(q)
    notes_list = [notes.get_note(nid) for nid in note_ids if notes.get_note(nid)]

    return templates.TemplateResponse("partials/note-list-only.html", {
        "request": request,
        "notes": notes_list
    })

@app.get("/api/tags")
async def api_tags(user: str = Depends(require_auth)):
    """Get all tags as JSON (for autocomplete)"""
    return {"tags": indexes.get_all_tags()}
```

**File: `templates/partials/note-list-only.html`**
```html
{% for note in notes %}
    {% include "partials/note-item.html" %}
{% endfor %}
{% if not notes %}
    <p style="color: #666;">No notes found.</p>
{% endif %}
```

## Tests

### Test 1: Project Index Creation
**Objective:** Verify indexes update when notes are created

**Steps:**
1. Create note in "Personal" project
2. Check `.indexes/projects.json`
3. **Expected:** File exists with structure: `{"personal": ["note-id"]}`
4. Create another note in "Personal"
5. Check index again
6. **Expected:** `{"personal": ["note-id-1", "note-id-2"]}`

**Pass Criteria:** Projects index updates correctly

### Test 2: Tags Index Creation
**Objective:** Verify tag indexes are maintained

**Steps:**
1. Create note with tags: python, fastapi
2. Check `.indexes/tags.json`
3. **Expected:** `{"python": ["note-id"], "fastapi": ["note-id"]}`
4. Create note with tag: python
5. **Expected:** `{"python": ["note-id-1", "note-id-2"], "fastapi": ["note-id-1"]}`

**Pass Criteria:** Tags index tracks all tag associations

### Test 3: Metadata Index
**Objective:** Verify metadata index maintains note info

**Steps:**
1. Create note
2. Check `.indexes/metadata.json`
3. **Expected:** Contains note with id, title, created, modified, file_path, project

**Pass Criteria:** Metadata index complete and accurate

### Test 4: Project Filtering
**Objective:** Verify project filter works

**Steps:**
1. Create 2 notes in "Personal", 1 note in "Work"
2. Click "Personal" filter button
3. **Expected:** Only 2 Personal notes shown
4. Click "Work" filter button
5. **Expected:** Only 1 Work note shown
6. Click "All" filter button
7. **Expected:** All 3 notes shown

**Pass Criteria:** Filter updates note list via HTMX

### Test 5: Tag Filtering
**Objective:** Verify tag filter works

**Steps:**
1. Create note with tags: python, web
2. Create note with tags: python, cli
3. Create note with tags: web, frontend
4. **Expected:** Tag cloud shows: python, web, cli, frontend
5. Click "python" tag
6. **Expected:** Shows 2 notes with python tag
7. Click "web" tag
8. **Expected:** Shows 2 notes with web tag

**Pass Criteria:** Tag filtering works correctly

### Test 6: Search Functionality
**Objective:** Verify search finds notes

**Steps:**
1. Create note with title containing "FastAPI tutorial"
2. Create note with title "Python tips"
3. Type "fastapi" in search box
4. Wait 300ms (debounce)
5. **Expected:** Only FastAPI note shown
6. Clear search
7. **Expected:** All notes shown again

**Pass Criteria:** Search is debounced and filters correctly

### Test 7: Manual Regeneration
**Objective:** Verify manual regeneration rebuilds indexes

**Steps:**
1. Create 3 notes normally
2. Delete `.indexes/` directory
3. Run: `python regenerate.py`
4. **Expected:** Output: "Regenerated indexes for 3 notes"
5. Check `.indexes/` directory
6. **Expected:** All index files recreated
7. Reload app
8. **Expected:** All notes still appear correctly

**Pass Criteria:** Regeneration recreates indexes from files

### Test 8: Index Update on Note Edit
**Objective:** Verify indexes update when tags change

**Steps:**
1. Create note with tags: old, test
2. Check `.indexes/tags.json`
3. **Expected:** Contains mappings for "old" and "test"
4. Edit note to tags: new, test
5. Check index again
6. **Expected:** "old" no longer contains note ID
7. **Expected:** "new" contains note ID
8. **Expected:** "test" still contains note ID

**Pass Criteria:** Tag index updates correctly on edit

### Test 9: Index Cleanup on Delete
**Objective:** Verify indexes cleaned up when note deleted

**Steps:**
1. Create note with tags: delete, me
2. Check all index files contain note ID
3. Delete the note
4. Check all index files
5. **Expected:** Note ID removed from all indexes

**Pass Criteria:** All indexes cleaned up on deletion

### Test 10: External Edit + Regeneration
**Objective:** Verify regeneration handles external edits

**Steps:**
1. Create 2 notes via app
2. Manually create a note file in `notes/personal/` with valid frontmatter
3. Run: `python regenerate.py`
4. Reload app
5. **Expected:** All 3 notes appear (including manual one)
6. **Expected:** Indexes include all 3 notes

**Pass Criteria:** Manual regeneration picks up external changes

### Test 11: Tag Autocomplete API
**Objective:** Verify tags API endpoint works

**Steps:**
1. Create notes with tags: python, javascript, java
2. Visit `/api/tags` endpoint
3. **Expected:** Returns JSON: `{"tags": ["python", "javascript", "java"]}`

**Pass Criteria:** API returns all unique tags

## Files Created/Modified
- `indexes.py` - Index management functions
- `regenerate.py` - Manual regeneration script
- `search.py` - Search functionality
- `templates/partials/project-filter.html` - Project filter UI
- `templates/partials/tag-cloud.html` - Tag cloud UI
- `templates/partials/search-bar.html` - Search input
- `templates/partials/note-list-only.html` - Notes list fragment
- `templates/index.html` - Updated with filters
- `main.py` - Filter/search endpoints
- `notes.py` - Integrated with indexes
- `.indexes/` - Directory for index files (gitignored)

## Phase Completion Criteria
- [ ] All tests pass
- [ ] Indexes update synchronously with CRUD operations
- [ ] Manual regeneration works for external edits
- [ ] Project filtering works
- [ ] Tag filtering works
- [ ] Search works with debouncing
- [ ] Tag autocomplete API available
- [ ] Ready for Phase 4 (intelligence features)
