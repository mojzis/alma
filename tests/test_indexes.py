"""Tests for index management."""

import pytest
from pathlib import Path
from alma import indexes


def test_indexes_directory_created(temp_notes_dir):
    """Test that indexes directory is created."""
    indexes_dir = Path(temp_notes_dir) / ".indexes"
    assert indexes_dir.exists()
    assert indexes_dir.is_dir()


def test_project_index(temp_notes_dir):
    """Test project index operations."""
    note_id = "test-note-123"
    project = "personal"

    # Add to index
    indexes.add_to_project_index(project, note_id)

    # Retrieve from index
    note_ids = indexes.get_notes_by_project(project)
    assert note_id in note_ids

    # Remove from index
    indexes.remove_from_project_index(project, note_id)
    note_ids = indexes.get_notes_by_project(project)
    assert note_id not in note_ids


def test_tags_index(temp_notes_dir):
    """Test tags index operations."""
    note_id = "test-note-456"
    tags = ["python", "testing"]

    # Add to index
    indexes.add_to_tags_index(tags, note_id)

    # Retrieve from index
    note_ids = indexes.get_notes_by_tag("python")
    assert note_id in note_ids

    note_ids = indexes.get_notes_by_tag("testing")
    assert note_id in note_ids

    # Get all tags
    all_tags = indexes.get_all_tags()
    assert "python" in all_tags
    assert "testing" in all_tags


def test_metadata_index(temp_notes_dir):
    """Test metadata index operations."""
    note_id = "test-note-789"
    title = "Test Note"
    created = "2025-01-01T10:00:00"
    modified = "2025-01-01T10:00:00"
    file_path = "notes/personal/test.md"
    project = "personal"

    # Add to index
    indexes.add_to_metadata_index(note_id, title, created, modified, file_path, project)

    # Retrieve from index
    metadata = indexes.get_note_metadata(note_id)
    assert metadata is not None
    assert metadata["title"] == title
    assert metadata["id"] == note_id

    # Get all metadata
    all_metadata = indexes.get_all_metadata()
    note_found = any(m["id"] == note_id for m in all_metadata)
    assert note_found
