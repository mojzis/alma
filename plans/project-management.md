# Project Management Implementation Plan

## Current State Analysis

### What Exists
Currently, the application has **hardcoded projects** in multiple locations:
- `main.py:38-40` - Creates three fixed directories: `personal`, `work`, `reference`
- `notes.py:126-130` - Hardcoded list when filtering notes
- `templates/partials/projects-list.html:11-34` - Static HTML for each project
- `templates/partials/note-form.html:29-33` - Hardcoded dropdown options

### What's Missing
❌ No ability to add new projects
❌ No ability to delete projects
❌ No ability to rename projects
❌ No project metadata (colors, descriptions, icons)
❌ No project management UI

---

## Goals

### Primary Objectives
1. ✅ **Create Projects** - Users can add new projects dynamically
2. ✅ **Delete Projects** - Users can remove projects (with safeguards)
3. ✅ **Edit Projects** - Users can rename and customize projects
4. ✅ **Project Metadata** - Support colors, descriptions, and visual customization
5. ✅ **Dynamic UI** - All project lists update automatically

### User Experience Goals
- Simple, intuitive project management
- Visual project organization (colors/icons)
- Safe deletion with warnings
- No breaking changes to existing notes

---

## Implementation Phases

### Phase 1: Backend - Project Configuration System

**New File:** `alma/projects.py`

```python
"""Project management module."""

import json
from pathlib import Path
from typing import List, Dict

INDEXES_DIR = Path(".indexes")
PROJECTS_CONFIG = INDEXES_DIR / "projects_config.json"

# Default projects that ship with the app
DEFAULT_PROJECTS = [
    {"id": "personal", "name": "Personal", "color": "blue", "description": "Personal notes"},
    {"id": "work", "name": "Work", "color": "green", "description": "Work-related notes"},
    {"id": "reference", "name": "Reference", "color": "purple", "description": "Reference materials"},
]

def load_projects_config() -> List[Dict]:
    """Load projects configuration from JSON."""

def save_projects_config(projects: List[Dict]):
    """Save projects configuration to JSON."""

def get_all_projects() -> List[Dict]:
    """Get all projects (defaults + custom)."""

def create_project(project_id: str, name: str, color: str = "gray", description: str = "") -> Dict:
    """Create a new project."""

def update_project(project_id: str, name: str = None, color: str = None, description: str = None) -> Dict:
    """Update project metadata."""

def delete_project(project_id: str) -> bool:
    """Delete a project (must be empty)."""

def get_project(project_id: str) -> Dict | None:
    """Get single project by ID."""

def project_exists(project_id: str) -> bool:
    """Check if project exists."""
```

**Key Features:**
- JSON-based configuration storage
- Default projects always available
- Color coding support
- Validation (unique IDs, valid colors)

---

### Phase 2: Backend - API Endpoints

**File:** `alma/main.py`

New endpoints to add:

```python
# ============================================================================
# Project Management Endpoints
# ============================================================================

@app.get("/api/projects")
async def list_projects(user: str = Depends(require_auth)):
    """Get all projects with metadata."""

@app.post("/api/projects")
async def create_project_endpoint(
    request: Request,
    name: Annotated[str, Form()],
    color: Annotated[str, Form()] = "gray",
    description: Annotated[str, Form()] = "",
    user: str = Depends(require_auth)
):
    """Create new project, return HTML fragment."""

@app.put("/api/projects/{project_id}")
async def update_project_endpoint(
    request: Request,
    project_id: str,
    name: Annotated[str, Form()],
    color: Annotated[str, Form()] = None,
    description: Annotated[str, Form()] = None,
    user: str = Depends(require_auth)
):
    """Update project metadata, return HTML fragment."""

@app.delete("/api/projects/{project_id}")
async def delete_project_endpoint(
    project_id: str,
    user: str = Depends(require_auth)
):
    """Delete project (only if empty), return empty response."""
```

**Validation Rules:**
- Project names must be unique
- Project IDs must be valid slugs (no spaces, special chars)
- Cannot delete projects with notes
- Cannot delete default projects

---

### Phase 3: Frontend - Dynamic Project List

**File:** `alma/templates/partials/projects-list.html`

Transform from static to dynamic:

```html
<div class="section-header" style="display: flex; justify-content: space-between; align-items: center;">
    <span>Projects</span>
    <button
        class="icon-button"
        title="Add Project"
        hx-get="/projects/new"
        hx-target="#project-modal"
        hx-swap="innerHTML">
        +
    </button>
</div>

<ul class="project-list">
    <!-- All Notes (Special Item) -->
    <li class="project-item active"
        hx-get="/notes?filter=all"
        hx-target="#notes-list"
        hx-swap="innerHTML">
        <div class="project-dot default"></div>
        <span class="project-name">All Notes</span>
        <span class="project-count">{{ total_count|default(0) }}</span>
    </li>

    <!-- Dynamic Projects -->
    {% for project in projects_list %}
    <li class="project-item"
        hx-get="/notes?project={{ project.id }}"
        hx-target="#notes-list"
        hx-swap="innerHTML">
        <div class="project-dot {{ project.color }}"></div>
        <span class="project-name">{{ project.name }}</span>
        <span class="project-count">{{ project.note_count }}</span>

        <!-- Edit/Delete Buttons (on hover) -->
        <div class="project-actions">
            <button class="icon-button-small"
                hx-get="/projects/{{ project.id }}/edit"
                hx-target="#project-modal">
                ✎
            </button>
            <button class="icon-button-small danger"
                hx-delete="/api/projects/{{ project.id }}"
                hx-confirm="Delete '{{ project.name }}'? All notes must be moved first.">
                ×
            </button>
        </div>
    </li>
    {% endfor %}
</ul>
```

**Changes Required:**
1. Update `main.py:index()` to pass `projects_list` with full metadata
2. Add CSS for `.project-actions` (show on hover)
3. Add CSS for color variants (`.project-dot.blue`, `.project-dot.green`, etc.)

---

### Phase 4: Frontend - Project Management UI

**New Files:**

#### 4.1 Project Creation Modal

**File:** `alma/templates/partials/project-create-modal.html`

```html
<div class="modal-overlay" x-data="{ color: 'gray' }">
    <div class="modal-content">
        <h2>New Project</h2>

        <form hx-post="/api/projects" hx-target="#projects-list" hx-swap="innerHTML">
            <div class="form-group">
                <label>Project Name</label>
                <input type="text" name="name" required placeholder="e.g., Client Work" />
            </div>

            <div class="form-group">
                <label>Color</label>
                <div class="color-picker">
                    <button type="button" @click="color='blue'" :class="{'selected': color==='blue'}" style="background: var(--color-blue)"></button>
                    <button type="button" @click="color='green'" :class="{'selected': color==='green'}" style="background: var(--color-green)"></button>
                    <button type="button" @click="color='purple'" :class="{'selected': color==='purple'}" style="background: var(--color-purple)"></button>
                    <button type="button" @click="color='orange'" :class="{'selected': color==='orange'}" style="background: var(--color-orange)"></button>
                    <button type="button" @click="color='red'" :class="{'selected': color==='red'}" style="background: var(--color-red)"></button>
                    <button type="button" @click="color='gray'" :class="{'selected': color==='gray'}" style="background: var(--color-gray)"></button>
                </div>
                <input type="hidden" name="color" x-model="color" />
            </div>

            <div class="form-group">
                <label>Description (Optional)</label>
                <textarea name="description" placeholder="What this project is for..."></textarea>
            </div>

            <div class="modal-actions">
                <button type="button" class="secondary" @click="$el.closest('.modal-overlay').remove()">Cancel</button>
                <button type="submit">Create Project</button>
            </div>
        </form>
    </div>
</div>
```

#### 4.2 Update Note Form

**File:** `alma/templates/partials/note-form.html:29-33`

Replace hardcoded dropdown with:

```html
<select name="project" required style="padding: 8px 12px; font-size: 13px;">
    {% for project in projects_list %}
    <option value="{{ project.id }}">{{ project.name }}</option>
    {% endfor %}
</select>
```

---

### Phase 5: Migration & Cleanup

**Tasks:**

1. **Initialize Default Projects**
   - Create `projects_config.json` on first run
   - Populate with default projects
   - Ensure backward compatibility

2. **Remove Hardcoded References**
   - ✅ Remove hardcoded directories from `main.py:38-40`
   - ✅ Remove hardcoded list from `notes.py:126-130`
   - ✅ Update all templates to use dynamic data

3. **Data Migration**
   - Scan existing `notes/` directory for project folders
   - Add any discovered projects to config
   - No data loss for existing notes

4. **Testing Checklist**
   - [ ] Create new project
   - [ ] Delete empty project
   - [ ] Attempt to delete project with notes (should fail)
   - [ ] Rename project
   - [ ] Change project color
   - [ ] Filter notes by custom project
   - [ ] Create note in custom project
   - [ ] Default projects still work

---

## Database Schema

### Projects Configuration (`projects_config.json`)

```json
{
  "projects": [
    {
      "id": "personal",
      "name": "Personal",
      "color": "blue",
      "description": "Personal notes and thoughts",
      "is_default": true,
      "created": "2025-01-09T10:00:00",
      "note_count": 15
    },
    {
      "id": "client-work-acme",
      "name": "Client: ACME Corp",
      "color": "orange",
      "description": "All work for ACME Corp client",
      "is_default": false,
      "created": "2025-01-09T14:30:00",
      "note_count": 8
    }
  ]
}
```

---

## UI/UX Considerations

### Project List Enhancements
- **Hover Effects:** Show edit/delete buttons on hover
- **Color Dots:** Visual project identification
- **Count Badges:** Show number of notes per project
- **Drag-to-Reorder:** Future enhancement for custom ordering

### Project Creation Flow
1. Click "+" button in sidebar
2. Modal appears with form
3. Enter name, select color
4. Create → Project appears in list immediately
5. Can immediately create notes in new project

### Project Deletion Safety
- Cannot delete if notes exist
- Show warning: "Move all notes first"
- Link to project filter to see all notes
- Future: Offer "Move notes to..." before delete

### Color Palette
Default colors to support:
- `blue` - #3b82f6
- `green` - #10b981
- `purple` - #8b5cf6
- `orange` - #f97316
- `red` - #ef4444
- `gray` - #6b7280
- `pink` - #ec4899
- `yellow` - #f59e0b

---

## Technical Decisions

### Why JSON Configuration?
- ✅ Simple, human-readable
- ✅ No database required
- ✅ Easy backup/version control
- ✅ Fast read/write for small datasets
- ❌ Not suitable for 1000+ projects (but fine for typical use)

### Why Separate `projects.py` Module?
- ✅ Separation of concerns
- ✅ Easier testing
- ✅ Follows existing pattern (`notes.py`, `indexes.py`, `auth.py`)
- ✅ Reusable across endpoints

### Why Not Allow Deleting Default Projects?
- ✅ Prevents accidental data loss
- ✅ Maintains app consistency
- ✅ Users can hide them instead (future feature)

---

## Future Enhancements

### Phase 2 (Later)
- Project archiving (hide without deleting)
- Project templates (predefined tags, structure)
- Project icons (emoji or icon library)
- Sub-projects / project hierarchy
- Project sharing (multi-user)
- Project export/import

### Phase 3 (Much Later)
- Project analytics (note count trends, activity)
- Project goals/milestones
- Project-level settings (default tags, auto-archive rules)

---

## Rollout Plan

### Step 1: Backend Foundation
- Implement `projects.py` module
- Add migration script to create initial config
- Test CRUD operations

### Step 2: API Layer
- Add all API endpoints
- Add validation and error handling
- Test with curl/Postman

### Step 3: Frontend Integration
- Update templates to use dynamic data
- Add project management UI
- Test user flows

### Step 4: Polish & Testing
- Add CSS animations
- Improve error messages
- Cross-browser testing
- Mobile responsiveness

### Step 5: Documentation
- Update README with project management guide
- Add screenshots
- Document API endpoints

---

## Success Metrics

- ✅ Users can create projects without touching code
- ✅ No hardcoded projects in codebase
- ✅ All existing notes continue working
- ✅ UI feels responsive and intuitive
- ✅ No data loss during migration
- ✅ Project colors visible at a glance

---

## Questions to Resolve

1. **Project ID Generation:** Auto-generate from name (slug) or let user choose?
   - Recommendation: Auto-generate, ensure uniqueness

2. **Max Projects Limit:** Should we limit number of custom projects?
   - Recommendation: Start with no limit, add if performance issues

3. **Project Ordering:** Alphabetical, by creation date, or custom?
   - Recommendation: Custom drag-to-reorder, default to alphabetical

4. **Keyboard Shortcuts:** Add shortcuts for creating projects?
   - Recommendation: Later enhancement (⌘⇧P for new project)

---

## Implementation Priority

**High Priority (MVP)**
- ✅ `projects.py` module
- ✅ CRUD API endpoints
- ✅ Dynamic project list rendering
- ✅ Project creation UI
- ✅ Migration script

**Medium Priority (Polish)**
- Project editing UI
- Project deletion with validation
- Color picker component
- Hover interactions

**Low Priority (Nice-to-Have)**
- Project descriptions
- Project reordering
- Project archiving
- Keyboard shortcuts

---

## Estimated Timeline

- **Phase 1-2 (Backend):** 4-6 hours
- **Phase 3 (Dynamic UI):** 2-3 hours
- **Phase 4 (Management UI):** 3-4 hours
- **Phase 5 (Migration & Testing):** 2-3 hours

**Total:** ~12-16 hours of focused development

---

## Notes

- This plan maintains backward compatibility with existing notes
- All changes are additive, not breaking
- Default projects ensure new users have a starting point
- JSON config can be version-controlled with notes
