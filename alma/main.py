"""Main FastAPI application for the note-taking app."""

import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import (
    get_google_auth_url,
    exchange_code_for_token,
    get_user_info,
    create_session_cookie,
    require_auth,
    validate_config,
)
from . import notes, indexes, projects

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Notes App")

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Ensure required directories exist
Path("notes").mkdir(parents=True, exist_ok=True)
Path(".indexes").mkdir(exist_ok=True)

# Initialize default project on first run
default_project_dir = Path("notes/default")
default_project_dir.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    try:
        validate_config()
        print("✓ Configuration validated successfully")
    except ValueError as e:
        print(f"\n❌ Configuration Error:\n{e}\n")
        raise


@app.get("/")
async def index(request: Request, user: str = Depends(require_auth)):
    """Main app page - requires authentication."""
    notes_list = notes.list_notes(limit=20)
    all_tags = indexes.get_all_tags()

    # Get all projects with counts
    projects_list = projects.get_all_projects()
    total_count = sum(p.get("note_count", 0) for p in projects_list)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "notes": notes_list,
            "tags": all_tags,
            "projects_list": projects_list,
            "total_count": total_count
        }
    )


@app.get("/login")
async def login_page(request: Request):
    """Show login page with Google OAuth button."""
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.get("/auth/google")
async def auth_google():
    """Redirect to Google OAuth consent screen."""
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def auth_callback(code: str, response: Response):
    """
    Handle Google OAuth callback.
    Exchange code for token, get user info, create session.
    """
    try:
        # Exchange authorization code for access token
        token_data = await exchange_code_for_token(code)
        access_token = token_data["access_token"]

        # Get user information
        user_info = await get_user_info(access_token)
        user_email = user_info["email"]

        # Create session cookie
        session_cookie = create_session_cookie(user_email)

        # Set cookie and redirect to main app
        response = RedirectResponse("/")
        response.set_cookie(
            key="session",
            value=session_cookie,
            httponly=True,
            secure=os.getenv("DEBUG") != "True",  # HTTPS only in production
            samesite="lax",
            max_age=604800,  # 1 week
        )
        return response

    except Exception as e:
        # If OAuth fails, redirect back to login
        print(f"OAuth error: {e}")
        return RedirectResponse("/login?error=auth_failed")


@app.post("/auth/logout")
async def logout(response: Response):
    """Destroy session and redirect to login."""
    response = RedirectResponse("/login")
    response.delete_cookie("session")
    return response


# ============================================================================
# Notes CRUD Endpoints
# ============================================================================

@app.post("/notes")
async def create_note(
    request: Request,
    project: Annotated[str, Form()],
    content_type: Annotated[str, Form()],
    tags: Annotated[str, Form()],
    content: Annotated[str, Form()],
    user: str = Depends(require_auth)
):
    """Create new note, return HTML fragment."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    note = notes.create_note(content, project, content_type, tag_list, user)
    return templates.TemplateResponse(
        "partials/note-item.html",
        {"request": request, "note": note}
    )


@app.get("/notes/{note_id}")
async def get_note(
    request: Request,
    note_id: str,
    user: str = Depends(require_auth)
):
    """Get single note, return HTML fragment."""
    note = notes.get_note(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return templates.TemplateResponse(
        "partials/note-item.html",
        {"request": request, "note": note}
    )


@app.get("/notes/{note_id}/edit")
async def edit_note_form(
    request: Request,
    note_id: str,
    user: str = Depends(require_auth)
):
    """Get edit form, return HTML fragment."""
    note = notes.get_note(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return templates.TemplateResponse(
        "partials/note-edit.html",
        {"request": request, "note": note}
    )


@app.put("/notes/{note_id}")
async def update_note(
    request: Request,
    note_id: str,
    tags: Annotated[str, Form()],
    content: Annotated[str, Form()],
    user: str = Depends(require_auth)
):
    """Update note, return HTML fragment."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    note = notes.update_note(note_id, content, tag_list)
    return templates.TemplateResponse(
        "partials/note-item.html",
        {"request": request, "note": note}
    )


@app.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    user: str = Depends(require_auth)
):
    """Delete note, return empty response."""
    notes.delete_note(note_id)
    return ""


# ============================================================================
# Filtering and Search Endpoints
# ============================================================================

@app.get("/notes")
async def filter_notes(
    request: Request,
    project: str | None = None,
    tag: str | None = None,
    filter: str | None = None,
    offset: int = 0,
    limit: int = 20,
    user: str = Depends(require_auth)
):
    """Filter notes by project or tag, return HTML fragment."""
    notes_list = []

    if filter == "all":
        # Show all notes
        metadata = indexes.get_all_metadata(limit=limit+offset+10)
        note_ids = [m["id"] for m in metadata[offset:offset+limit]]
        notes_list = [notes.get_note(nid) for nid in note_ids if notes.get_note(nid)]
    elif project:
        # Filter by project
        note_ids = indexes.get_notes_by_project(project)
        notes_list = [notes.get_note(nid) for nid in note_ids[offset:offset+limit] if notes.get_note(nid)]
        # Sort by created date
        notes_list.sort(key=lambda n: n.get("created", ""), reverse=True)
    elif tag:
        # Filter by tag
        note_ids = indexes.get_notes_by_tag(tag)
        notes_list = [notes.get_note(nid) for nid in note_ids[offset:offset+limit] if notes.get_note(nid)]
        # Sort by created date
        notes_list.sort(key=lambda n: n.get("created", ""), reverse=True)
    else:
        # Default: show all
        metadata = indexes.get_all_metadata(limit=limit+offset+10)
        note_ids = [m["id"] for m in metadata[offset:offset+limit]]
        notes_list = [notes.get_note(nid) for nid in note_ids if notes.get_note(nid)]

    # Check if there are more notes to load
    has_more = len(notes_list) == limit

    return templates.TemplateResponse(
        "partials/note-list-only.html",
        {"request": request, "notes": notes_list, "offset": offset + limit, "has_more": has_more}
    )


@app.get("/search")
async def search_notes(
    request: Request,
    q: str = "",
    user: str = Depends(require_auth)
):
    """Search notes by title, return HTML fragment."""
    if not q or len(q.strip()) == 0:
        # Empty search - show all notes
        metadata = indexes.get_all_metadata(limit=50)
        note_ids = [m["id"] for m in metadata]
        notes_list = [notes.get_note(nid) for nid in note_ids if notes.get_note(nid)]
    else:
        # Search in metadata titles
        query_lower = q.lower()
        all_metadata = indexes.get_all_metadata(limit=500)
        matching_ids = [
            meta["id"]
            for meta in all_metadata
            if query_lower in meta.get("title", "").lower()
        ]
        notes_list = [notes.get_note(nid) for nid in matching_ids if notes.get_note(nid)]

    return templates.TemplateResponse(
        "partials/note-list-only.html",
        {"request": request, "notes": notes_list}
    )


# ============================================================================
# Project Management Endpoints
# ============================================================================

@app.get("/projects/new")
async def new_project_form(request: Request, user: str = Depends(require_auth)):
    """Get project creation form modal."""
    return templates.TemplateResponse(
        "partials/project-create-modal.html",
        {"request": request}
    )


@app.post("/projects")
async def create_project(
    request: Request,
    name: Annotated[str, Form()],
    color: Annotated[str, Form()] = "gray",
    description: Annotated[str, Form()] = "",
    user: str = Depends(require_auth)
):
    """Create new project, return updated projects list."""
    try:
        projects.create_project(name, color, description)
        # Return updated projects list
        projects_list = projects.get_all_projects()
        all_notes_count = sum(p.get("note_count", 0) for p in projects_list)
        return templates.TemplateResponse(
            "partials/projects-list.html",
            {"request": request, "projects_list": projects_list, "total_count": all_notes_count}
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/projects/{project_id}/edit")
async def edit_project_form(
    request: Request,
    project_id: str,
    user: str = Depends(require_auth)
):
    """Get project edit form modal."""
    project = projects.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return templates.TemplateResponse(
        "partials/project-edit-modal.html",
        {"request": request, "project": project}
    )


@app.put("/projects/{project_id}")
async def update_project(
    request: Request,
    project_id: str,
    name: Annotated[str, Form()],
    color: Annotated[str, Form()] = None,
    description: Annotated[str, Form()] = None,
    user: str = Depends(require_auth)
):
    """Update project, return updated projects list."""
    try:
        projects.update_project(project_id, name, color, description)
        # Return updated projects list
        projects_list = projects.get_all_projects()
        all_notes_count = sum(p.get("note_count", 0) for p in projects_list)
        return templates.TemplateResponse(
            "partials/projects-list.html",
            {"request": request, "projects_list": projects_list, "total_count": all_notes_count}
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    user: str = Depends(require_auth)
):
    """Delete project (only if empty), return success."""
    try:
        projects.delete_project(project_id)
        return ""
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/admin/regenerate")
async def regenerate_indexes_endpoint(user: str = Depends(require_auth)):
    """Manually trigger index regeneration."""
    from .regenerate import regenerate_all_indexes
    count = regenerate_all_indexes()
    return {"status": "success", "notes_indexed": count}


def main():
    """Entry point for running the app via 'uv run alma'."""
    import uvicorn
    uvicorn.run("alma.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
