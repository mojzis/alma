"""Notes CRUD module - manages markdown files with frontmatter."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List

import frontmatter
from slugify import slugify

from . import indexes, wiki_links

NOTES_DIR = Path("notes")


def create_note(
    content: str,
    project: str,
    content_type: str,
    tags: List[str],
    user: str
) -> dict:
    """Create a new note as a markdown file with frontmatter."""
    # Generate unique ID
    note_id = str(uuid.uuid4())

    # Extract title from first line or use content preview
    lines = content.strip().split("\n")
    title = lines[0][:100] if lines else "Untitled"

    # Generate timestamps
    now = datetime.now()
    created = now.isoformat()
    modified = created

    # Create frontmatter metadata
    metadata = {
        "id": note_id,
        "title": title,
        "created": created,
        "modified": modified,
        "project": project,
        "type": content_type,
        "tags": tags,
        "user": user,
    }

    # Create post with frontmatter
    post = frontmatter.Post(content, **metadata)

    # Generate filename
    filename = _generate_filename(title)
    project_dir = NOTES_DIR / project
    project_dir.mkdir(parents=True, exist_ok=True)
    file_path = project_dir / filename

    # Write file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    # Update indexes synchronously
    indexes.add_to_project_index(project, note_id)
    indexes.add_to_tags_index(tags, note_id)
    indexes.add_to_metadata_index(
        note_id, title, created, modified, str(file_path), project, content_type, tags
    )

    # Extract and index wiki-links
    links = wiki_links.extract_wiki_links(content)
    wiki_links.add_wiki_links_to_index(note_id, links)

    # Return note dict
    return {
        "id": note_id,
        "title": title,
        "content": content,
        "created": created,
        "modified": modified,
        "project": project,
        "type": content_type,
        "tags": tags,
        "user": user,
        "file_path": str(file_path),
    }


def get_note(note_id: str) -> dict | None:
    """Load note from file by ID."""
    file_path = _find_file_by_id(note_id)
    if not file_path:
        return None

    post = frontmatter.load(file_path)
    metadata = post.metadata

    title = metadata.get("title", "Untitled")
    content = post.content

    # Get backlinks for this note
    backlinks = wiki_links.get_backlinks(title)

    return {
        "id": metadata.get("id"),
        "title": title,
        "content": content,
        "content_html": wiki_links.render_wiki_links(content),
        "created": metadata.get("created"),
        "modified": metadata.get("modified"),
        "project": metadata.get("project"),
        "type": metadata.get("type"),
        "tags": metadata.get("tags", []),
        "user": metadata.get("user"),
        "file_path": str(file_path),
        "backlinks": backlinks,
    }


def list_notes(project: str | None = None, limit: int = 50) -> List[dict]:
    """List notes, optionally filtered by project."""
    notes = []

    # Determine which directories to search
    if project:
        search_dirs = [NOTES_DIR / project]
    else:
        # Search all project directories
        search_dirs = [d for d in NOTES_DIR.iterdir() if d.is_dir()]

    # Find all markdown files
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for md_file in search_dir.glob("*.md"):
            try:
                post = frontmatter.load(md_file)
                metadata = post.metadata

                notes.append({
                    "id": metadata.get("id"),
                    "title": metadata.get("title"),
                    "content": post.content,
                    "created": metadata.get("created"),
                    "modified": metadata.get("modified"),
                    "project": metadata.get("project"),
                    "type": metadata.get("type"),
                    "tags": metadata.get("tags", []),
                    "user": metadata.get("user"),
                    "file_path": str(md_file),
                })
            except Exception as e:
                print(f"Error loading {md_file}: {e}")
                continue

    # Sort by created date (newest first)
    notes.sort(key=lambda n: n.get("created", ""), reverse=True)

    return notes[:limit]


def update_note(note_id: str, content: str, tags: List[str]) -> dict:
    """Update an existing note."""
    file_path = _find_file_by_id(note_id)
    if not file_path:
        raise ValueError(f"Note {note_id} not found")

    # Load existing note
    post = frontmatter.load(file_path)

    # Get old values for index updates
    old_tags = post.metadata.get("tags", [])

    # Update content
    post.content = content

    # Update metadata
    modified = datetime.now().isoformat()
    post["tags"] = tags
    post["modified"] = modified

    # Update title from first line
    lines = content.strip().split("\n")
    title = lines[0][:100] if lines else post.get("title", "Untitled")
    post["title"] = title

    # Write updated file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    # Update indexes
    if set(old_tags) != set(tags):
        indexes.update_tags_index(old_tags, tags, note_id)
    indexes.update_metadata_index(note_id, modified=modified, title=title, tags=tags)

    # Update wiki-links index
    links = wiki_links.extract_wiki_links(content)
    wiki_links.add_wiki_links_to_index(note_id, links)

    # Return updated note
    return get_note(note_id)


def delete_note(note_id: str) -> bool:
    """Delete a note file."""
    # Get note data before deleting
    note = get_note(note_id)
    if not note:
        return False

    file_path = Path(note["file_path"])

    # Remove from indexes
    indexes.remove_from_project_index(note["project"], note_id)
    indexes.remove_from_tags_index(note.get("tags", []), note_id)
    indexes.remove_from_metadata_index(note_id)
    wiki_links.remove_wiki_links_from_index(note_id)

    # Delete file
    file_path.unlink()
    return True


def _generate_filename(title: str) -> str:
    """Generate filename: YYYYMMDD-HHMMSS-slug.md"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(title, max_length=50)
    if not slug:
        slug = "note"
    return f"{timestamp}-{slug}.md"


def _find_file_by_id(note_id: str) -> Path | None:
    """Find note file by searching for ID in frontmatter."""
    # Search all project directories
    for md_file in NOTES_DIR.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            if post.metadata.get("id") == note_id:
                return md_file
        except Exception:
            continue

    return None
