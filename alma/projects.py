"""Project management module."""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from slugify import slugify

from . import indexes

INDEXES_DIR = Path(".indexes")
PROJECTS_CONFIG = INDEXES_DIR / "projects_config.json"

# Single default project that ships with the app
DEFAULT_PROJECT = {
    "id": "default",
    "name": "Default",
    "color": "blue",
    "description": "Default project for all notes",
    "is_default": True,
    "created": datetime.now().isoformat(),
}


def load_projects_config() -> List[Dict]:
    """Load projects configuration from JSON."""
    if not PROJECTS_CONFIG.exists():
        # Initialize with default project
        return [DEFAULT_PROJECT.copy()]

    try:
        data = json.loads(PROJECTS_CONFIG.read_text())
        projects = data.get("projects", [])

        # Ensure default project always exists
        has_default = any(p.get("id") == "default" for p in projects)
        if not has_default:
            projects.insert(0, DEFAULT_PROJECT.copy())

        return projects
    except (json.JSONDecodeError, IOError):
        return [DEFAULT_PROJECT.copy()]


def save_projects_config(projects: List[Dict]):
    """Save projects configuration to JSON."""
    data = {"projects": projects}
    PROJECTS_CONFIG.write_text(json.dumps(data, indent=2))


def get_all_projects() -> List[Dict]:
    """Get all projects with note counts."""
    projects = load_projects_config()

    # Add note counts from index
    projects_index = indexes.load_index(indexes.PROJECTS_INDEX)
    for project in projects:
        note_ids = projects_index.get(project["id"], [])
        project["note_count"] = len(note_ids)

    return projects


def create_project(name: str, color: str = "gray", description: str = "") -> Dict:
    """Create a new project."""
    # Generate ID from name
    project_id = slugify(name, max_length=50)
    if not project_id:
        raise ValueError("Invalid project name")

    # Load existing projects
    projects = load_projects_config()

    # Check for duplicate ID
    if any(p.get("id") == project_id for p in projects):
        raise ValueError(f"Project '{name}' already exists")

    # Validate color
    valid_colors = ["blue", "green", "purple", "orange", "red", "gray", "pink", "yellow"]
    if color not in valid_colors:
        color = "gray"

    # Create project
    project = {
        "id": project_id,
        "name": name,
        "color": color,
        "description": description,
        "is_default": False,
        "created": datetime.now().isoformat(),
    }

    # Add to list and save
    projects.append(project)
    save_projects_config(projects)

    # Create directory
    project_dir = Path("notes") / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    return project


def update_project(project_id: str, name: str = None, color: str = None, description: str = None) -> Dict:
    """Update project metadata."""
    projects = load_projects_config()

    # Find project
    project = None
    for p in projects:
        if p.get("id") == project_id:
            project = p
            break

    if not project:
        raise ValueError(f"Project '{project_id}' not found")

    # Update fields
    if name is not None:
        project["name"] = name
    if color is not None:
        valid_colors = ["blue", "green", "purple", "orange", "red", "gray", "pink", "yellow"]
        if color in valid_colors:
            project["color"] = color
    if description is not None:
        project["description"] = description

    project["modified"] = datetime.now().isoformat()

    # Save
    save_projects_config(projects)

    return project


def delete_project(project_id: str) -> bool:
    """Delete a project (must be empty and not default)."""
    # Load projects config first
    projects = load_projects_config()

    # Check if project exists
    project = None
    for p in projects:
        if p.get("id") == project_id:
            project = p
            break

    if not project:
        raise ValueError(f"Project '{project_id}' not found")

    # Cannot delete default project
    if project_id == "default" or project.get("is_default"):
        raise ValueError("Cannot delete default project")

    # Check if project has notes
    projects_index = indexes.load_index(indexes.PROJECTS_INDEX)
    note_ids = projects_index.get(project_id, [])
    if note_ids:
        raise ValueError(f"Cannot delete project with {len(note_ids)} notes. Move notes first.")

    # Remove from config
    projects = [p for p in projects if p.get("id") != project_id]
    save_projects_config(projects)

    return True


def get_project(project_id: str) -> Dict | None:
    """Get single project by ID."""
    projects = load_projects_config()
    for p in projects:
        if p.get("id") == project_id:
            return p
    return None


def project_exists(project_id: str) -> bool:
    """Check if project exists."""
    return get_project(project_id) is not None
