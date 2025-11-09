# Phase 5: Polish & User Experience

## Goal
Enhance user experience with keyboard shortcuts, mobile responsiveness, dark mode, export functionality, and performance optimizations.

## Prerequisites
- Phases 1-4 completed
- Core functionality working

## Tasks

### 5.1 Keyboard Shortcuts

**File: `static/js/keyboard.js`**
```javascript
// Minimal vanilla JS for keyboard shortcuts
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', (e) => {
        // Cmd/Ctrl + K: Focus search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            document.querySelector('input[name="q"]')?.focus();
        }

        // Cmd/Ctrl + N: Focus new note form
        if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
            e.preventDefault();
            document.querySelector('textarea[name="content"]')?.focus();
        }

        // Escape: Clear search or close modals
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        }
    });
});
```

**Update `templates/base.html`:**
```html
<script src="/static/js/keyboard.js"></script>
```

### 5.2 Mobile Responsive Design

**File: `static/css/responsive.css`**
```css
/* Mobile-first responsive design */
@media (max-width: 768px) {
    /* Stack form and notes vertically on mobile */
    .main-grid {
        grid-template-columns: 1fr !important;
    }

    /* Make form sticky on mobile */
    .note-form-container {
        position: sticky;
        top: 0;
        background: white;
        z-index: 100;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    }

    /* Reduce padding on mobile */
    body {
        padding: 10px !important;
    }

    /* Make buttons touch-friendly */
    button {
        min-height: 44px;
        font-size: 16px;
    }

    /* Stack filter buttons vertically */
    .filter-buttons {
        flex-direction: column !important;
    }

    /* Make note items more compact */
    .note {
        padding: 10px !important;
    }
}
```

**Update `templates/index.html`:**
```html
<link rel="stylesheet" href="/static/css/responsive.css">

<div class="main-grid" style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px;">
    <!-- existing content -->
</div>
```

### 5.3 Dark Mode

**File: `static/css/dark-mode.css`**
```css
/* Dark mode using CSS variables */
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --text-primary: #000000;
    --text-secondary: #666666;
    --border-color: #dddddd;
    --accent-color: #0066cc;
    --note-bg: #ffffff;
}

[data-theme="dark"] {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --text-primary: #ffffff;
    --text-secondary: #aaaaaa;
    --border-color: #444444;
    --accent-color: #4d9fff;
    --note-bg: #252525;
}

body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.note {
    background-color: var(--note-bg);
    border-color: var(--border-color);
}

input, textarea, select {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border-color: var(--border-color);
}

button {
    background-color: var(--accent-color);
}
```

**File: `templates/partials/theme-toggle.html`**
```html
<div x-data="{
    dark: localStorage.getItem('theme') === 'dark',
    toggle() {
        this.dark = !this.dark;
        localStorage.setItem('theme', this.dark ? 'dark' : 'light');
        document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
    }
}" x-init="document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')">
    <button @click="toggle()" type="button">
        <span x-show="!dark">🌙</span>
        <span x-show="dark">☀️</span>
    </button>
</div>
```

### 5.4 Export Functionality

**File: `export.py`**
```python
import zipfile
from pathlib import Path
from datetime import datetime
import json

def export_all_notes(output_format: str = "zip") -> Path:
    """Export all notes as zip archive"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    export_file = Path(f"exports/notes-export-{timestamp}.zip")
    export_file.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all markdown files
        for md_file in Path("notes").rglob("*.md"):
            zipf.write(md_file, md_file)

        # Add indexes
        for index_file in Path(".indexes").glob("*.json"):
            zipf.write(index_file, f".indexes/{index_file.name}")

    return export_file

def export_project(project: str) -> Path:
    """Export single project as zip"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    export_file = Path(f"exports/{project}-export-{timestamp}.zip")
    export_file.parent.mkdir(exist_ok=True)

    project_dir = Path("notes") / project
    if not project_dir.exists():
        raise ValueError(f"Project {project} not found")

    with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for md_file in project_dir.glob("*.md"):
            zipf.write(md_file, f"{project}/{md_file.name}")

    return export_file

def export_as_json() -> dict:
    """Export all notes as JSON"""
    import notes
    import indexes

    all_metadata = indexes.get_all_metadata(limit=10000)
    export_data = []

    for meta in all_metadata:
        note = notes.get_note(meta["id"])
        if note:
            export_data.append(note)

    return {
        "exported_at": datetime.now().isoformat(),
        "note_count": len(export_data),
        "notes": export_data
    }
```

**Add to `main.py`:**
```python
from fastapi.responses import FileResponse, JSONResponse
import export

@app.get("/export/all")
async def export_all(user: str = Depends(require_auth)):
    """Export all notes as zip"""
    export_file = export.export_all_notes()
    return FileResponse(
        export_file,
        media_type="application/zip",
        filename=export_file.name
    )

@app.get("/export/project/{project}")
async def export_project(project: str, user: str = Depends(require_auth)):
    """Export single project as zip"""
    export_file = export.export_project(project)
    return FileResponse(
        export_file,
        media_type="application/zip",
        filename=export_file.name
    )

@app.get("/export/json")
async def export_json(user: str = Depends(require_auth)):
    """Export all notes as JSON"""
    data = export.export_as_json()
    return JSONResponse(data)
```

**Add to `templates/index.html`:**
```html
<div style="margin-bottom: 20px;">
    <details>
        <summary>Export</summary>
        <a href="/export/all" download>Export All (ZIP)</a> |
        <a href="/export/json" download>Export All (JSON)</a>
    </details>
</div>
```

### 5.5 Performance Optimizations

**File: `caching.py`**
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache for frequently accessed data
_cache = {}
_cache_timeout = timedelta(minutes=5)

def cache_get(key: str):
    """Get from cache if not expired"""
    if key in _cache:
        value, timestamp = _cache[key]
        if datetime.now() - timestamp < _cache_timeout:
            return value
    return None

def cache_set(key: str, value):
    """Set cache value"""
    _cache[key] = (value, datetime.now())

def cache_invalidate(key: str):
    """Invalidate cache entry"""
    if key in _cache:
        del _cache[key]

@lru_cache(maxsize=1000)
def get_note_cached(note_id: str):
    """Cached note retrieval"""
    import notes
    return notes.get_note(note_id)
```

**Optimization: Lazy Load Notes**

Update templates to load initial notes, then load more on scroll:

**File: `templates/partials/load-more.html`:**
```html
<div
    hx-get="/notes?offset={{ offset }}&limit=20"
    hx-trigger="revealed"
    hx-swap="afterend"
    style="padding: 20px; text-align: center; color: #666;"
>
    Loading more notes...
</div>
```

### 5.6 UI/UX Improvements

**Better Loading States:**
```html
<!-- Add to base.html -->
<style>
.htmx-request .loading-overlay {
    display: block;
}
.loading-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #0066cc, #4d9fff);
    animation: loading 1s infinite;
    z-index: 9999;
}
@keyframes loading {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}
</style>
<div class="loading-overlay"></div>
```

**Toast Notifications:**
```html
<!-- Alpine.js toast component -->
<div x-data="toasts" @toast.window="add($event.detail)" style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
    <template x-for="toast in items" :key="toast.id">
        <div x-show="toast.visible" x-transition style="background: #0066cc; color: white; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
            <span x-text="toast.message"></span>
        </div>
    </template>
</div>

<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('toasts', () => ({
        items: [],
        add(message) {
            const id = Date.now();
            this.items.push({ id, message, visible: true });
            setTimeout(() => {
                const toast = this.items.find(t => t.id === id);
                if (toast) toast.visible = false;
                setTimeout(() => {
                    this.items = this.items.filter(t => t.id !== id);
                }, 300);
            }, 3000);
        }
    }));
});
</script>
```

### 5.7 Accessibility Improvements

**Add ARIA labels and semantic HTML:**
```html
<!-- Update templates with proper ARIA -->
<nav aria-label="Project filters">
    <button aria-label="Filter by all projects">All</button>
    <button aria-label="Filter by personal projects">Personal</button>
</nav>

<main role="main" aria-label="Notes list">
    <!-- notes -->
</main>

<form aria-label="Create new note">
    <!-- form fields -->
</form>
```

**Add focus indicators:**
```css
/* Better focus indicators for keyboard navigation */
*:focus-visible {
    outline: 2px solid var(--accent-color);
    outline-offset: 2px;
}
```

## Tests

### Test 1: Keyboard Shortcuts
**Objective:** Verify keyboard shortcuts work

**Steps:**
1. Open app
2. Press Cmd/Ctrl + K
3. **Expected:** Search input focused
4. Press Cmd/Ctrl + N
5. **Expected:** Content textarea focused
6. Type in search
7. Press Escape
8. **Expected:** Search cleared

**Pass Criteria:** All keyboard shortcuts work

### Test 2: Mobile Responsiveness
**Objective:** Verify app works on mobile

**Steps:**
1. Open app in mobile viewport (375px width)
2. **Expected:** Form and notes stacked vertically
3. **Expected:** Buttons are touch-friendly (44px min height)
4. Try creating a note
5. **Expected:** All functionality works on mobile

**Pass Criteria:** App usable on mobile devices

### Test 3: Dark Mode Toggle
**Objective:** Verify dark mode works and persists

**Steps:**
1. Click dark mode toggle
2. **Expected:** Theme changes to dark
3. Refresh page
4. **Expected:** Dark mode persists (localStorage)
5. Toggle again
6. **Expected:** Theme changes to light

**Pass Criteria:** Dark mode toggles and persists

### Test 4: Export All Notes
**Objective:** Verify export functionality works

**Steps:**
1. Create 3 notes
2. Click "Export All (ZIP)"
3. **Expected:** ZIP file downloads
4. Open ZIP file
5. **Expected:** Contains all markdown files
6. **Expected:** Contains .indexes folder

**Pass Criteria:** Export creates valid ZIP

### Test 5: Export Project
**Objective:** Verify project export works

**Steps:**
1. Create 2 notes in "Personal", 1 in "Work"
2. Export "Personal" project
3. **Expected:** ZIP contains only Personal notes

**Pass Criteria:** Project export filters correctly

### Test 6: JSON Export
**Objective:** Verify JSON export works

**Steps:**
1. Create notes
2. Click "Export All (JSON)"
3. **Expected:** JSON file downloads
4. Open JSON
5. **Expected:** Contains array of notes with all metadata

**Pass Criteria:** JSON export is valid and complete

### Test 7: Infinite Scroll
**Objective:** Verify lazy loading works

**Steps:**
1. Create 30 notes
2. Initial load shows 20
3. Scroll to bottom
4. **Expected:** "Loading more notes..." appears
5. **Expected:** Next 10 notes load automatically

**Pass Criteria:** Infinite scroll loads more notes

### Test 8: Loading Indicators
**Objective:** Verify loading states are visible

**Steps:**
1. Create note
2. **Expected:** Loading bar appears at top during request
3. **Expected:** Loading bar disappears after completion

**Pass Criteria:** Loading states provide feedback

### Test 9: Toast Notifications
**Objective:** Verify toast notifications appear

**Steps:**
1. Trigger toast (e.g., note created successfully)
2. **Expected:** Toast appears in top-right
3. Wait 3 seconds
4. **Expected:** Toast fades out and disappears

**Pass Criteria:** Toasts appear and auto-dismiss

### Test 10: Accessibility
**Objective:** Verify accessibility features work

**Steps:**
1. Navigate app using only keyboard (Tab key)
2. **Expected:** Can reach all interactive elements
3. **Expected:** Focus indicators visible
4. Use screen reader
5. **Expected:** ARIA labels are read correctly

**Pass Criteria:** App is keyboard and screen reader accessible

## Files Created/Modified
- `static/js/keyboard.js` - Keyboard shortcuts
- `static/css/responsive.css` - Mobile styles
- `static/css/dark-mode.css` - Dark mode theme
- `templates/partials/theme-toggle.html` - Dark mode toggle
- `templates/partials/load-more.html` - Infinite scroll
- `export.py` - Export functionality
- `caching.py` - Performance caching
- `main.py` - Export endpoints
- `templates/base.html` - Loading indicators, toasts, ARIA
- `templates/index.html` - Export UI, accessibility improvements

## Phase Completion Criteria
- [ ] All tests pass
- [ ] Keyboard shortcuts implemented
- [ ] Mobile responsive design works
- [ ] Dark mode toggles and persists
- [ ] Export functionality works (ZIP, JSON)
- [ ] Infinite scroll loads more notes
- [ ] Loading states visible
- [ ] Toast notifications work
- [ ] Accessibility features implemented
- [ ] App is production-ready

## Optional Enhancements
- [ ] PWA support (offline mode)
- [ ] Markdown preview while typing
- [ ] Drag-and-drop file attachments
- [ ] Note templates
- [ ] Bulk operations (delete, tag, export)
- [ ] Note versioning/history
- [ ] Collaborative editing
