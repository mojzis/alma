"""Index management system for fast note lookups."""

import json
from pathlib import Path
from typing import Dict, List, Set

INDEXES_DIR = Path(".indexes")
INDEXES_DIR.mkdir(exist_ok=True)

# Index file paths
PROJECTS_INDEX = INDEXES_DIR / "projects.json"
TAGS_INDEX = INDEXES_DIR / "tags.json"
METADATA_INDEX = INDEXES_DIR / "metadata.json"


def load_index(index_path: Path) -> dict:
    """Load index from JSON file."""
    if not index_path.exists():
        return {}
    try:
        return json.loads(index_path.read_text())
    except (json.JSONDecodeError, IOError):
        return {}


def save_index(index_path: Path, data: dict):
    """Save index to JSON file."""
    index_path.write_text(json.dumps(data, indent=2))


# ============================================================================
# Projects Index
# ============================================================================

def add_to_project_index(project: str, note_id: str):
    """Add note to project index."""
    index = load_index(PROJECTS_INDEX)
    if project not in index:
        index[project] = []
    if note_id not in index[project]:
        index[project].append(note_id)
    save_index(PROJECTS_INDEX, index)


def remove_from_project_index(project: str, note_id: str):
    """Remove note from project index."""
    index = load_index(PROJECTS_INDEX)
    if project in index and note_id in index[project]:
        index[project].remove(note_id)
        if not index[project]:  # Remove empty project lists
            del index[project]
        save_index(PROJECTS_INDEX, index)


def get_notes_by_project(project: str) -> List[str]:
    """Get all note IDs for a project."""
    index = load_index(PROJECTS_INDEX)
    return index.get(project, [])


def get_all_projects() -> List[str]:
    """Get list of all projects."""
    index = load_index(PROJECTS_INDEX)
    return sorted(index.keys())


# ============================================================================
# Tags Index
# ============================================================================

def add_to_tags_index(tags: List[str], note_id: str):
    """Add note to tag indexes."""
    if not tags:
        return
    index = load_index(TAGS_INDEX)
    for tag in tags:
        if tag not in index:
            index[tag] = []
        if note_id not in index[tag]:
            index[tag].append(note_id)
    save_index(TAGS_INDEX, index)


def remove_from_tags_index(tags: List[str], note_id: str):
    """Remove note from tag indexes."""
    if not tags:
        return
    index = load_index(TAGS_INDEX)
    for tag in tags:
        if tag in index and note_id in index[tag]:
            index[tag].remove(note_id)
            if not index[tag]:  # Remove empty tag lists
                del index[tag]
    save_index(TAGS_INDEX, index)


def update_tags_index(old_tags: List[str], new_tags: List[str], note_id: str):
    """Update tags when note is modified."""
    # Remove from tags that are no longer present
    removed_tags = set(old_tags) - set(new_tags)
    if removed_tags:
        remove_from_tags_index(list(removed_tags), note_id)

    # Add to new tags
    added_tags = set(new_tags) - set(old_tags)
    if added_tags:
        add_to_tags_index(list(added_tags), note_id)


def get_notes_by_tag(tag: str) -> List[str]:
    """Get all note IDs for a tag."""
    index = load_index(TAGS_INDEX)
    return index.get(tag, [])


def get_all_tags() -> List[str]:
    """Get list of all tags, sorted by usage count."""
    index = load_index(TAGS_INDEX)
    # Sort by number of notes (descending), then alphabetically
    return sorted(index.keys(), key=lambda t: (-len(index[t]), t.lower()))


# ============================================================================
# Metadata Index
# ============================================================================

def add_to_metadata_index(
    note_id: str,
    title: str,
    created: str,
    modified: str,
    file_path: str,
    project: str,
    content_type: str,
    tags: List[str],
):
    """Add note metadata to index."""
    index = load_index(METADATA_INDEX)
    index[note_id] = {
        "title": title,
        "created": created,
        "modified": modified,
        "file_path": file_path,
        "project": project,
        "type": content_type,
        "tags": tags,
    }
    save_index(METADATA_INDEX, index)


def update_metadata_index(note_id: str, **kwargs):
    """Update metadata for a note."""
    index = load_index(METADATA_INDEX)
    if note_id in index:
        index[note_id].update(kwargs)
        save_index(METADATA_INDEX, index)


def remove_from_metadata_index(note_id: str):
    """Remove note from metadata index."""
    index = load_index(METADATA_INDEX)
    if note_id in index:
        del index[note_id]
        save_index(METADATA_INDEX, index)


def get_note_metadata(note_id: str) -> dict | None:
    """Get metadata for a note."""
    index = load_index(METADATA_INDEX)
    metadata = index.get(note_id)
    if metadata:
        return {"id": note_id, **metadata}
    return None


def get_all_metadata(limit: int = 100, offset: int = 0) -> List[dict]:
    """Get all note metadata, sorted by created date (newest first)."""
    index = load_index(METADATA_INDEX)

    # Convert to list with IDs
    metadata_list = [
        {"id": note_id, **meta}
        for note_id, meta in index.items()
    ]

    # Sort by created date (newest first)
    metadata_list.sort(key=lambda x: x.get("created", ""), reverse=True)

    # Apply pagination
    return metadata_list[offset:offset + limit]


# ============================================================================
# Utility Functions
# ============================================================================

def clear_all_indexes():
    """Clear all index files (useful for regeneration)."""
    for index_file in INDEXES_DIR.glob("*.json"):
        index_file.write_text("{}")
