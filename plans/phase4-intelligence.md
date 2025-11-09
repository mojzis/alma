# Phase 4: Intelligence Features

## Goal
Add wiki-link parsing, semantic similarity search, and optional LLM-based classification as **non-blocking background tasks**. The app works perfectly without these features - they're enhancements.

## Prerequisites
- Phase 3 (Organization) completed
- Basic filtering and search working

## Philosophy
All intelligence features run as background tasks. They enhance the experience but never block user interactions. If they fail, the app continues working.

## Tasks

### 4.1 Wiki-Link Parsing and Indexing

**File: `wiki_links.py`**
```python
import re
from pathlib import Path
from typing import List, Set
import indexes

WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
WIKI_LINKS_INDEX = indexes.INDEXES_DIR / "wiki-links.json"

def extract_wiki_links(content: str) -> Set[str]:
    """Extract wiki-style links [[link]] from content"""
    return set(WIKI_LINK_PATTERN.findall(content))

def add_wiki_links_to_index(note_id: str, links: Set[str]):
    """Store wiki links for a note"""
    index = indexes.load_index(WIKI_LINKS_INDEX)
    index[note_id] = list(links)
    indexes.save_index(WIKI_LINKS_INDEX, index)

def get_backlinks(note_title: str) -> List[str]:
    """Find all notes that link to this note"""
    index = indexes.load_index(WIKI_LINKS_INDEX)
    backlinks = []
    for note_id, links in index.items():
        if note_title in links:
            backlinks.append(note_id)
    return backlinks

def resolve_wiki_link(link_text: str) -> str | None:
    """Find note ID by title (fuzzy match)"""
    all_metadata = indexes.get_all_metadata(limit=1000)
    link_lower = link_text.lower()

    for meta in all_metadata:
        if meta["title"].lower() == link_lower:
            return meta["id"]

    return None
```

**Update `notes.py` to extract wiki-links:**
```python
import wiki_links

def create_note(content: str, project: str, content_type: str, tags: List[str], user: str) -> dict:
    """Create note and update indexes"""
    # ... existing code ...

    # Extract and index wiki-links synchronously (fast regex)
    links = wiki_links.extract_wiki_links(content)
    wiki_links.add_wiki_links_to_index(note_id, links)

    return note_dict
```

### 4.2 Wiki-Link Rendering

**File: `templates/partials/note-item.html`** (update)
```html
<div class="note" id="note-{{ note.id }}">
    <div>
        <strong>{{ note.title }}</strong>
        <span style="color: #666; font-size: 0.9em;">
            {{ note.created }} | {{ note.project }} | {{ note.type }}
        </span>
    </div>
    <div style="margin: 10px 0;">{{ note.content_html | safe }}</div>
    <div style="color: #666; font-size: 0.9em;">
        {% if note.tags %}
            Tags: {{ note.tags|join(', ') }}
        {% endif %}
    </div>
    {% if note.backlinks %}
    <div style="margin-top: 10px; color: #666; font-size: 0.9em;">
        Backlinks:
        {% for backlink_id in note.backlinks %}
            <a href="#note-{{ backlink_id }}">{{ backlink_id[:8] }}</a>
        {% endfor %}
    </div>
    {% endif %}
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

**File: `markdown_renderer.py`**
```python
import re
import wiki_links

def render_wiki_links(content: str) -> str:
    """Convert [[wiki links]] to HTML links"""
    def replace_link(match):
        link_text = match.group(1)
        note_id = wiki_links.resolve_wiki_link(link_text)

        if note_id:
            return f'<a href="#note-{note_id}" style="color: #0066cc; text-decoration: underline;">[[{link_text}]]</a>'
        else:
            return f'<span style="color: #999;">[[{link_text}]]</span>'

    return re.sub(wiki_links.WIKI_LINK_PATTERN, replace_link, content)
```

### 4.3 Background Task System

**Add dependency:**
```
# requirements.txt
fastapi==0.104.1
...existing...
```

FastAPI has built-in background tasks - no external library needed.

**File: `background.py`**
```python
from fastapi import BackgroundTasks
import logging

logger = logging.getLogger(__name__)

async def log_background_task(task_name: str, note_id: str):
    """Simple background task logger"""
    logger.info(f"Background task '{task_name}' started for note {note_id}")

# Placeholder for future intelligence features
async def generate_embeddings(note_id: str, content: str):
    """Generate embeddings for semantic search (Phase 4.4)"""
    pass

async def classify_note(note_id: str, content: str):
    """LLM-based classification (Phase 4.5)"""
    pass

async def git_commit(note_id: str, action: str, title: str):
    """Git auto-commit (Phase 4.6)"""
    pass
```

### 4.4 Semantic Similarity (Optional Enhancement)

**Add dependencies:**
```
# requirements.txt (optional)
chromadb==0.4.18
sentence-transformers==2.2.2
```

**File: `embeddings.py`**
```python
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

INTELLIGENCE_DIR = Path(".intelligence")
INTELLIGENCE_DIR.mkdir(exist_ok=True)

# Lazy load model (only when first used)
_model = None
_chroma_client = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast model
    return _model

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(INTELLIGENCE_DIR / "chroma"))
    return _chroma_client

async def generate_embedding(note_id: str, content: str):
    """Generate and store embedding (background task)"""
    try:
        model = get_model()
        embedding = model.encode(content).tolist()

        client = get_chroma_client()
        collection = client.get_or_create_collection("notes")

        collection.upsert(
            ids=[note_id],
            embeddings=[embedding],
            documents=[content]
        )
    except Exception as e:
        # Log error but don't fail - this is optional enhancement
        print(f"Embedding generation failed: {e}")

def semantic_search(query: str, limit: int = 10) -> List[str]:
    """Find similar notes using embeddings"""
    try:
        model = get_model()
        query_embedding = model.encode(query).tolist()

        client = get_chroma_client()
        collection = client.get_collection("notes")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )

        return results['ids'][0] if results['ids'] else []
    except Exception as e:
        print(f"Semantic search failed: {e}")
        return []
```

**Update `main.py` to queue embeddings:**
```python
from fastapi import BackgroundTasks
import embeddings

@app.post("/notes")
async def create_note(
    request: Request,
    background_tasks: BackgroundTasks,
    project: Annotated[str, Form()],
    content_type: Annotated[str, Form()],
    tags: Annotated[str, Form()],
    content: Annotated[str, Form()],
    user: str = Depends(require_auth)
):
    """Create new note, queue background tasks"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    note = notes.create_note(content, project, content_type, tag_list, user)

    # Queue background task (non-blocking)
    background_tasks.add_task(embeddings.generate_embedding, note["id"], content)

    return templates.TemplateResponse("partials/note-item.html", {
        "request": request,
        "note": note
    })
```

### 4.5 LLM Classification (Optional Enhancement)

**Add dependency:**
```
# requirements.txt (optional)
ollama==0.1.6
```

**File: `classification.py`**
```python
import ollama
import json

async def classify_note_with_llm(note_id: str, content: str) -> dict:
    """Use local LLM to suggest tags/category (background task)"""
    try:
        prompt = f"""Analyze this note and suggest:
1. Additional tags (max 3)
2. Content type (note/idea/task/reference)

Note content:
{content}

Respond with JSON: {{"tags": [], "type": ""}}
"""

        response = ollama.chat(
            model='llama2',  # Or any local model
            messages=[{'role': 'user', 'content': prompt}]
        )

        result = json.loads(response['message']['content'])

        # Store suggestions in .intelligence/
        suggestions_file = Path(f".intelligence/suggestions/{note_id}.json")
        suggestions_file.parent.mkdir(exist_ok=True, parents=True)
        suggestions_file.write_text(json.dumps(result, indent=2))

        return result
    except Exception as e:
        print(f"LLM classification failed: {e}")
        return {}
```

### 4.6 Git Auto-Commit (Optional Enhancement)

**File: `git_integration.py`**
```python
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

async def auto_commit_note(note_id: str, action: str, note_title: str):
    """Auto-commit changes to git (background task)"""
    try:
        # Check if in git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return  # Not a git repo, skip

        # Add changes
        subprocess.run(["git", "add", "notes/"], check=True)

        # Commit
        commit_msg = f"{action}: {note_title[:50]}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True
        )

        logger.info(f"Auto-committed: {commit_msg}")

        # Optional: auto-push
        # subprocess.run(["git", "push"], check=False)

    except subprocess.CalledProcessError as e:
        logger.warning(f"Git commit failed: {e}")
    except Exception as e:
        logger.error(f"Git integration error: {e}")
```

## Tests

### Test 1: Wiki-Link Extraction
**Objective:** Verify wiki-links are extracted from content

**Steps:**
1. Create note with content: "Check out [[FastAPI Guide]] and [[Python Tips]]"
2. Check `.indexes/wiki-links.json`
3. **Expected:** `{"note-id": ["FastAPI Guide", "Python Tips"]}`

**Pass Criteria:** Wiki-links extracted and indexed

### Test 2: Wiki-Link Rendering
**Objective:** Verify wiki-links render as HTML links

**Steps:**
1. Create note titled "FastAPI Guide"
2. Create note with content: "Read [[FastAPI Guide]]"
3. View second note in UI
4. **Expected:** "FastAPI Guide" is clickable link
5. **Expected:** Link has href="#note-{id}"

**Pass Criteria:** Wiki-links render as HTML

### Test 3: Backlinks
**Objective:** Verify backlinks are shown

**Steps:**
1. Create note titled "Python"
2. Create note with content: "[[Python]] is great"
3. Create note with content: "I love [[Python]]"
4. View first note ("Python")
5. **Expected:** Shows 2 backlinks

**Pass Criteria:** Backlinks displayed correctly

### Test 4: Broken Wiki-Links
**Objective:** Verify unresolved links are styled differently

**Steps:**
1. Create note with content: "[[NonExistent Note]]"
2. View note
3. **Expected:** Link is grayed out (color: #999)
4. **Expected:** Not clickable

**Pass Criteria:** Broken links visually distinct

### Test 5: Background Task Execution
**Objective:** Verify background tasks don't block response

**Steps:**
1. Create note
2. **Expected:** Note appears immediately in UI
3. **Expected:** No delay waiting for background tasks
4. Check logs
5. **Expected:** Background task logged as started

**Pass Criteria:** Response immediate, tasks run asynchronously

### Test 6: Embedding Generation (Optional)
**Objective:** Verify embeddings are generated if enabled

**Prerequisites:** ChromaDB and sentence-transformers installed

**Steps:**
1. Create note with content: "FastAPI is a web framework"
2. Wait a few seconds for background task
3. Check `.intelligence/chroma/` directory
4. **Expected:** ChromaDB data files exist
5. Create note with content: "Python web development"
6. Perform semantic search for "web frameworks"
7. **Expected:** Both notes returned as similar

**Pass Criteria:** Embeddings generated and searchable

### Test 7: LLM Classification (Optional)
**Objective:** Verify LLM suggestions work if enabled

**Prerequisites:** Ollama installed with llama2 model

**Steps:**
1. Create note with content: "TODO: Finish the API endpoints"
2. Wait a few seconds
3. Check `.intelligence/suggestions/{note-id}.json`
4. **Expected:** File exists with suggested tags and type
5. **Expected:** Type likely suggests "task"

**Pass Criteria:** LLM generates reasonable suggestions

### Test 8: Git Auto-Commit (Optional)
**Objective:** Verify git commits work if enabled

**Prerequisites:** Notes directory is a git repo

**Steps:**
1. Initialize git: `cd notes && git init`
2. Create note
3. Wait a few seconds
4. Run: `git log`
5. **Expected:** Auto-commit created with message like "create: Note Title"

**Pass Criteria:** Git commit created automatically

### Test 9: Graceful Failure
**Objective:** Verify app works when optional features fail

**Steps:**
1. Don't install ChromaDB or Ollama
2. Create notes normally
3. **Expected:** Notes created successfully
4. **Expected:** No errors shown to user
5. Check logs
6. **Expected:** Errors logged but not raised

**Pass Criteria:** App continues working despite feature failures

### Test 10: Manual Regeneration with Wiki-Links
**Objective:** Verify regeneration rebuilds wiki-link index

**Steps:**
1. Create note with wiki-links
2. Delete `.indexes/wiki-links.json`
3. Run: `python regenerate.py`
4. Check wiki-links index
5. **Expected:** Index rebuilt with wiki-links

**Pass Criteria:** Regeneration includes wiki-links

## Configuration

**File: `.env`** (update)
```bash
# Existing config...

# Intelligence Features (Optional)
ENABLE_EMBEDDINGS=false
ENABLE_LLM_CLASSIFICATION=false
ENABLE_GIT_AUTOCOMMIT=false

# LLM Config
OLLAMA_MODEL=llama2
```

## Files Created/Modified
- `wiki_links.py` - Wiki-link parsing and indexing
- `markdown_renderer.py` - Wiki-link rendering
- `background.py` - Background task utilities
- `embeddings.py` - Semantic search (optional)
- `classification.py` - LLM classification (optional)
- `git_integration.py` - Git auto-commit (optional)
- `templates/partials/note-item.html` - Show backlinks
- `main.py` - Queue background tasks
- `regenerate.py` - Include wiki-links in regeneration
- `.intelligence/` - Directory for AI-generated data (gitignored)

## Phase Completion Criteria
- [ ] All tests pass
- [ ] Wiki-links parsed and indexed
- [ ] Wiki-links rendered as HTML
- [ ] Backlinks displayed
- [ ] Background tasks don't block responses
- [ ] Optional features fail gracefully
- [ ] Embeddings work if enabled (optional)
- [ ] LLM classification works if enabled (optional)
- [ ] Git auto-commit works if enabled (optional)
- [ ] Ready for Phase 5 (polish)

## Notes
- All intelligence features are **optional enhancements**
- The app works perfectly without them
- They run as background tasks and never block user interactions
- Failures are logged but don't break the app
- Users can enable/disable via environment variables
