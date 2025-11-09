# TipTap Implementation Guide for Claude Code

## Project Context

You are implementing a WYSIWYG markdown editor for a note-taking application with these architectural constraints:

- **Backend**: FastAPI + Jinja2 templates
- **Frontend**: HTMX + Alpine.js (minimal JavaScript)
- **Storage**: Markdown files with YAML frontmatter (filesystem-based)
- **Editor**: TipTap with markdown extension
- **Build**: Vite (bundler for TipTap)

## What We're Building (Scope)

### In Scope for This Implementation
1. TipTap editor initialization with markdown support
2. Load markdown from FastAPI backend into editor
3. Save editor content as markdown to FastAPI backend
4. HTMX integration for form submission
5. Basic markdown features: headings, bold, italic, lists, links, code
6. Auto-save functionality
7. Proper Vite build configuration

### Explicitly Out of Scope (For Later)
- Wiki-link autocomplete (`[[page-name]]` syntax)
- Tag management
- Full-text search
- AI features
- Git integration

**Critical**: Design the editor initialization to make wiki-links easy to add later via TipTap's custom extension system.

---

## Architecture Overview

```
User writes in TipTap WYSIWYG
         ↓
Content stored as ProseMirror JSON (in-memory only)
         ↓
On save: JSON → Markdown conversion
         ↓
HTMX POST to FastAPI
         ↓
FastAPI writes markdown file
         ↓
Frontmatter + content stored in filesystem
```

**Key Insight**: Markdown is ONLY for storage. TipTap uses JSON internally. This is intentional and correct.

---

## Implementation Steps

### Step 1: Project Setup and Dependencies

**Install TipTap packages:**

```bash
npm install @tiptap/core @tiptap/starter-kit @tiptap/extension-markdown marked
```

**Install build tools:**

```bash
npm install --save-dev vite
```

**Python dependencies (add to requirements.txt):**

```
fastapi
jinja2
python-frontmatter
pyyaml
aiofiles
```

### Step 2: Vite Configuration

**Create `vite.config.js` in project root:**

```javascript
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: 'static/dist',
    rollupOptions: {
      input: {
        editor: 'static/js/editor.js'
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    }
  },
  optimizeDeps: {
    exclude: [
      '@codemirror/state',
      '@codemirror/view'
    ]
  }
})
```

**Why this config**:
- Outputs to `static/dist/` where FastAPI serves static files
- Predictable filenames for template references
- Excludes problematic dependencies

### Step 3: FastAPI Backend Structure

**File: `app/main.py` (or your main FastAPI file)**

```python
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import frontmatter
from pathlib import Path
from datetime import datetime
import uuid

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

NOTES_DIR = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with editor"""
    return templates.TemplateResponse("editor.html", {
        "request": request
    })

@app.get("/notes/{note_id}", response_class=HTMLResponse)
async def get_note(note_id: str):
    """Load a note's markdown content"""
    note_path = NOTES_DIR / f"{note_id}.md"
    
    if not note_path.exists():
        raise HTTPException(status_code=404, detail="Note not found")
    
    post = frontmatter.load(note_path)
    
    # Return just the markdown content (no frontmatter)
    # TipTap will convert this to its internal JSON
    return HTMLResponse(content=post.content)

@app.post("/notes/{note_id}")
async def save_note(note_id: str, content: str = Form(...)):
    """Save markdown content to file"""
    note_path = NOTES_DIR / f"{note_id}.md"
    
    if note_path.exists():
        # Load existing frontmatter
        post = frontmatter.load(note_path)
        post.content = content
        post['modified'] = datetime.now().isoformat()
    else:
        # Create new note with frontmatter
        post = frontmatter.Post(content)
        post['id'] = note_id
        post['created'] = datetime.now().isoformat()
        post['modified'] = datetime.now().isoformat()
        post['project'] = 'default'
        post['type'] = 'note'
        post['tags'] = []
    
    # Write file
    with open(note_path, 'w') as f:
        f.write(frontmatter.dumps(post))
    
    return {"success": True, "note_id": note_id}

@app.post("/notes")
async def create_note(content: str = Form(...)):
    """Create a new note"""
    note_id = str(uuid.uuid4())
    await save_note(note_id, content)
    return {"success": True, "note_id": note_id}
```

**Boundaries**:
- FastAPI handles ONLY file I/O and frontmatter
- No markdown parsing/rendering on backend
- Frontmatter is separate from content
- Notes stored as `{uuid}.md` files

### Step 4: Frontend JavaScript (TipTap)

**File: `static/js/editor.js`**

```javascript
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/extension-markdown'

class NoteEditor {
  constructor(element, noteId = null) {
    this.element = element
    this.noteId = noteId
    this.editor = null
    this.autoSaveTimeout = null
    
    this.initEditor()
    if (noteId) {
      this.loadNote(noteId)
    }
  }

  initEditor() {
    this.editor = new Editor({
      element: this.element,
      extensions: [
        StarterKit,
        Markdown.configure({
          // This config makes wiki-links possible later
          // by keeping the parser extensible
          transformPastedText: true,
          transformCopiedText: true
        })
      ],
      content: '',
      contentType: 'markdown',
      onUpdate: ({ editor }) => {
        this.scheduleAutoSave()
      }
    })
  }

  async loadNote(noteId) {
    try {
      const response = await fetch(`/notes/${noteId}`)
      if (!response.ok) throw new Error('Failed to load note')
      
      const markdown = await response.text()
      
      // Load markdown into editor
      // TipTap converts to JSON internally
      this.editor.commands.setContent(markdown, {
        contentType: 'markdown'
      })
      
      this.noteId = noteId
    } catch (error) {
      console.error('Error loading note:', error)
      // Show error to user (implement UI for this)
    }
  }

  async saveNote() {
    if (!this.noteId) {
      // Create new note
      return this.createNote()
    }

    // Get markdown from editor
    // This converts internal JSON back to markdown
    const markdown = this.editor.storage.markdown.getMarkdown()
    
    // Prepare form data for HTMX
    const formData = new FormData()
    formData.append('content', markdown)

    try {
      const response = await fetch(`/notes/${this.noteId}`, {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) throw new Error('Save failed')
      
      this.showSaveIndicator('saved')
      return await response.json()
    } catch (error) {
      console.error('Error saving note:', error)
      this.showSaveIndicator('error')
    }
  }

  async createNote() {
    const markdown = this.editor.storage.markdown.getMarkdown()
    const formData = new FormData()
    formData.append('content', markdown)

    try {
      const response = await fetch('/notes', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) throw new Error('Create failed')
      
      const data = await response.json()
      this.noteId = data.note_id
      
      // Update URL without reload
      window.history.pushState({}, '', `/notes/${this.noteId}`)
      
      this.showSaveIndicator('saved')
      return data
    } catch (error) {
      console.error('Error creating note:', error)
      this.showSaveIndicator('error')
    }
  }

  scheduleAutoSave() {
    // Debounce auto-save
    clearTimeout(this.autoSaveTimeout)
    this.autoSaveTimeout = setTimeout(() => {
      this.saveNote()
    }, 2000) // Save 2 seconds after last edit
  }

  showSaveIndicator(status) {
    // Implement visual feedback
    const indicator = document.getElementById('save-indicator')
    if (!indicator) return
    
    indicator.textContent = {
      'saved': '✓ Saved',
      'saving': '⋯ Saving',
      'error': '✗ Error'
    }[status] || ''
    
    indicator.className = `save-indicator save-indicator--${status}`
  }

  getMarkdown() {
    return this.editor.storage.markdown.getMarkdown()
  }

  destroy() {
    if (this.editor) {
      this.editor.destroy()
    }
  }
}

// Initialize editor when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const editorElement = document.getElementById('editor')
  if (!editorElement) return

  // Get note ID from URL if present
  const pathMatch = window.location.pathname.match(/\/notes\/([^/]+)/)
  const noteId = pathMatch ? pathMatch[1] : null

  // Create global editor instance
  window.noteEditor = new NoteEditor(editorElement, noteId)
})

// Expose for HTMX integration
window.saveCurrentNote = () => {
  if (window.noteEditor) {
    return window.noteEditor.saveNote()
  }
}
```

**Critical design decisions**:
1. **Markdown is contentType**: TipTap handles conversion
2. **Auto-save debounced**: 2 seconds after last edit
3. **Class-based**: Easy to extend with wiki-links later
4. **Global instance**: `window.noteEditor` for HTMX access
5. **Markdown config preserved**: Ready for custom extensions

### Step 5: Jinja2 Template

**File: `templates/editor.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Note Editor</title>
  
  <!-- HTMX -->
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  
  <!-- Alpine.js (if needed for UI) -->
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
  
  <!-- Tailwind CSS (or your CSS) -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- TipTap Editor (Vite build output) -->
  <script type="module" src="{{ url_for('static', path='dist/editor.js') }}"></script>
  
  <style>
    /* TipTap editor styles */
    .ProseMirror {
      min-height: 400px;
      padding: 1rem;
      border: 1px solid #e5e7eb;
      border-radius: 0.5rem;
      outline: none;
    }
    
    .ProseMirror:focus {
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Markdown styling in editor */
    .ProseMirror h1 { font-size: 2em; font-weight: bold; margin: 0.5em 0; }
    .ProseMirror h2 { font-size: 1.5em; font-weight: bold; margin: 0.5em 0; }
    .ProseMirror h3 { font-size: 1.25em; font-weight: bold; margin: 0.5em 0; }
    .ProseMirror strong { font-weight: bold; }
    .ProseMirror em { font-style: italic; }
    .ProseMirror code { background: #f3f4f6; padding: 0.2em 0.4em; border-radius: 0.25rem; font-family: monospace; }
    .ProseMirror pre { background: #1f2937; color: #f9fafb; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; }
    .ProseMirror pre code { background: transparent; padding: 0; }
    .ProseMirror ul, .ProseMirror ol { padding-left: 2rem; margin: 0.5em 0; }
    .ProseMirror blockquote { border-left: 3px solid #e5e7eb; padding-left: 1rem; color: #6b7280; }
    
    /* Save indicator */
    .save-indicator {
      position: fixed;
      top: 1rem;
      right: 1rem;
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      font-size: 0.875rem;
      transition: opacity 0.3s;
    }
    .save-indicator--saved { background: #d1fae5; color: #065f46; }
    .save-indicator--saving { background: #fef3c7; color: #92400e; }
    .save-indicator--error { background: #fee2e2; color: #991b1b; }
  </style>
</head>
<body class="bg-gray-50">
  <div class="max-w-4xl mx-auto py-8 px-4">
    <!-- Header -->
    <div class="mb-6 flex justify-between items-center">
      <h1 class="text-3xl font-bold text-gray-900">Note Editor</h1>
      <div id="save-indicator" class="save-indicator"></div>
    </div>
    
    <!-- Toolbar (optional - add formatting buttons here) -->
    <div class="mb-4 flex gap-2 p-2 bg-white rounded-lg shadow-sm" x-data="toolbar">
      <button 
        @click="$dispatch('format-heading', { level: 1 })"
        class="px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
      >
        H1
      </button>
      <button 
        @click="$dispatch('format-heading', { level: 2 })"
        class="px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
      >
        H2
      </button>
      <div class="border-l border-gray-300"></div>
      <button 
        @click="$dispatch('format-bold')"
        class="px-3 py-1 text-sm font-bold text-gray-700 hover:bg-gray-100 rounded"
      >
        B
      </button>
      <button 
        @click="$dispatch('format-italic')"
        class="px-3 py-1 text-sm italic text-gray-700 hover:bg-gray-100 rounded"
      >
        I
      </button>
      <button 
        @click="$dispatch('format-code')"
        class="px-3 py-1 text-sm font-mono text-gray-700 hover:bg-gray-100 rounded"
      >
        Code
      </button>
    </div>
    
    <!-- Editor -->
    <div class="bg-white rounded-lg shadow-sm">
      <div id="editor"></div>
    </div>
    
    <!-- Manual save button (optional with auto-save) -->
    <div class="mt-4 flex justify-end gap-2">
      <button 
        onclick="window.saveCurrentNote()"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Save Note
      </button>
    </div>
  </div>

  <script>
    // Toolbar functionality with Alpine.js
    document.addEventListener('alpine:init', () => {
      Alpine.data('toolbar', () => ({
        init() {
          this.$el.addEventListener('format-heading', (e) => {
            if (window.noteEditor?.editor) {
              window.noteEditor.editor.chain().focus()
                .toggleHeading({ level: e.detail.level }).run()
            }
          })
          
          this.$el.addEventListener('format-bold', () => {
            if (window.noteEditor?.editor) {
              window.noteEditor.editor.chain().focus().toggleBold().run()
            }
          })
          
          this.$el.addEventListener('format-italic', () => {
            if (window.noteEditor?.editor) {
              window.noteEditor.editor.chain().focus().toggleItalic().run()
            }
          })
          
          this.$el.addEventListener('format-code', () => {
            if (window.noteEditor?.editor) {
              window.noteEditor.editor.chain().focus().toggleCode().run()
            }
          })
        }
      }))
    })
  </script>
</body>
</html>
```

**Boundaries**:
- Template handles ONLY presentation
- Editor initialization via script
- Toolbar uses Alpine.js for reactivity
- No inline JavaScript logic (keep it in editor.js)

### Step 6: Build Process

**Add to `package.json`:**

```json
{
  "name": "note-editor",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tiptap/core": "^2.10.0",
    "@tiptap/starter-kit": "^2.10.0",
    "@tiptap/extension-markdown": "^2.10.0",
    "marked": "^11.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

**Development workflow:**

```bash
# Terminal 1: Vite dev server (for JS hot-reload)
npm run dev

# Terminal 2: FastAPI server
uvicorn app.main:app --reload

# Production build:
npm run build  # Outputs to static/dist/
```

---

## Integration Points for Future Features

### Wiki-Links (Future Extension)

The current setup is ready for wiki-links. Here's where you'll add them:

**1. Create TipTap custom extension** (`static/js/extensions/wiki-link.js`):

```javascript
// Placeholder for future implementation
import { Node } from '@tiptap/core'

export const WikiLink = Node.create({
  name: 'wikiLink',
  
  addAttributes() {
    return {
      page: { default: null }
    }
  },
  
  parseHTML() {
    return [
      { tag: 'a[data-wiki-link]' }
    ]
  },
  
  renderHTML({ HTMLAttributes }) {
    return ['a', { 
      ...HTMLAttributes, 
      'data-wiki-link': '',
      href: `/notes/${HTMLAttributes.page}`
    }, 0]
  },
  
  // Input rule for [[page-name]] syntax
  addInputRules() {
    // Will implement autocomplete here
  }
})
```

**2. Modify editor initialization**:

```javascript
import { WikiLink } from './extensions/wiki-link.js'

this.editor = new Editor({
  extensions: [
    StarterKit,
    Markdown,
    WikiLink  // Add when ready
  ]
})
```

**3. Backend endpoint for page list**:

```python
@app.get("/api/pages")
async def get_pages():
    """Return list of all note titles for autocomplete"""
    pages = []
    for note_path in NOTES_DIR.glob("*.md"):
        post = frontmatter.load(note_path)
        pages.append({
            "id": note_path.stem,
            "title": post.get('title', 'Untitled'),
            "preview": post.content[:100]
        })
    return pages
```

**The architecture is already ready**:
- Markdown extension is extensible
- Custom nodes can be added
- Parser/serializer hooks are available
- Backend structure supports metadata

---

## Testing Checklist

Before considering this complete, verify:

1. **Basic functionality**:
   - [ ] Create new note saves to filesystem
   - [ ] Load existing note shows content in editor
   - [ ] Edit and save updates markdown file
   - [ ] Frontmatter is preserved

2. **Markdown conversion**:
   - [ ] Headings (H1-H6) work
   - [ ] Bold and italic work
   - [ ] Lists (ordered and unordered) work
   - [ ] Code blocks and inline code work
   - [ ] Links work
   - [ ] Blockquotes work

3. **Integration**:
   - [ ] Auto-save triggers after 2 seconds
   - [ ] Save indicator updates correctly
   - [ ] Vite build completes without errors
   - [ ] Static files served correctly by FastAPI
   - [ ] HTMX is available but not used yet (for future forms)

4. **File system**:
   - [ ] Notes directory created automatically
   - [ ] Files have correct frontmatter structure
   - [ ] File names are valid UUIDs
   - [ ] Content separate from metadata

---

## Common Issues and Solutions

### Issue: Editor doesn't initialize
**Solution**: Check browser console. Likely causes:
- Vite build didn't complete
- Script path in template incorrect
- Module import syntax browser incompatibility

### Issue: Markdown doesn't save correctly
**Solution**: 
- Verify `@tiptap/extension-markdown` is installed
- Check `editor.storage.markdown.getMarkdown()` returns string
- Confirm FastAPI receives content in form data

### Issue: Content looks different after reload
**Solution**: 
- This is expected! ProseMirror JSON → Markdown is lossy
- Document this to users
- Consider storing JSON alongside markdown for critical data

### Issue: Vite build fails with "Cannot find module"
**Solution**:
- Run `npm install` again
- Clear node_modules and reinstall
- Check Vite config excludes problematic packages

---

## Architecture Boundaries (Critical)

**Frontend (TipTap):**
- Handles ONLY editor state and UI
- Converts markdown ↔ JSON internally
- No business logic
- No file system access
- No frontmatter parsing

**Backend (FastAPI):**
- Handles ONLY file I/O
- Manages frontmatter
- No markdown parsing/rendering
- No editor logic
- Returns raw markdown strings

**Storage (Filesystem):**
- Markdown files are source of truth
- Frontmatter is metadata layer
- Content is separate from metadata
- Files are independent (no database)

**Build (Vite):**
- Bundles ONLY TipTap and dependencies
- Outputs to static/dist/
- No backend code in bundle
- Dev server for hot-reload only

---

## Next Steps After Basic Implementation

Once this works:

1. **Add toolbar functionality** (complete the Alpine.js buttons)
2. **Implement wiki-link extension** (see placeholder above)
3. **Add tag management UI** (separate from editor)
4. **Create note browser** (list view with HTMX)
5. **Add search** (backend endpoint + frontend UI)

But first: **Get the basic editor working end-to-end**.

---

## Summary

You're building a TipTap WYSIWYG editor that:
- Stores markdown files (not JSON)
- Uses ProseMirror JSON internally (this is correct)
- Integrates with FastAPI via fetch API
- Auto-saves every 2 seconds
- Preserves frontmatter metadata
- Is ready for wiki-link extensions

**Critical understanding**: The "internal format" concern is not a problem. All ProseMirror editors (TipTap, Milkdown, etc.) use JSON internally. You store markdown, that's what matters. The conversion is handled by TipTap's markdown extension, and GitLab proves this works at scale.

Start with Step 1 (dependencies) and work sequentially. Each step builds on the previous one.
