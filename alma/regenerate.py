"""Manual index regeneration script.

Run this script after:
- git pull that brings in external changes
- Direct editing of markdown files
- Index corruption or issues
- Initial setup with existing notes

Usage:
    uv run python -m alma.regenerate
    or
    uv run python alma/regenerate.py
"""

from pathlib import Path
import frontmatter
from . import indexes

NOTES_DIR = Path("notes")


def regenerate_all_indexes():
    """Rebuild all indexes from markdown files."""
    print("🔄 Regenerating all indexes from markdown files...")

    # Clear existing indexes
    print("  Clearing old indexes...")
    indexes.clear_all_indexes()

    count = 0
    errors = 0

    # Scan all markdown files
    for md_file in NOTES_DIR.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            metadata = post.metadata

            note_id = metadata.get("id")
            if not note_id:
                print(f"  ⚠️  Warning: {md_file} missing 'id' in frontmatter, skipping")
                errors += 1
                continue

            # Rebuild all indexes
            project = metadata.get("project", "unknown")
            tags = metadata.get("tags", [])
            title = metadata.get("title", "Untitled")
            created = metadata.get("created", "")
            modified = metadata.get("modified", "")
            content_type = metadata.get("type", "note")

            indexes.add_to_project_index(project, note_id)
            indexes.add_to_tags_index(tags, note_id)
            indexes.add_to_metadata_index(
                note_id, title, created, modified, str(md_file), project, content_type, tags
            )

            count += 1

        except Exception as e:
            print(f"  ❌ Error processing {md_file}: {e}")
            errors += 1
            continue

    print(f"\n✓ Regeneration complete!")
    print(f"  - Indexed: {count} notes")
    if errors:
        print(f"  - Errors: {errors} files")
    print(f"\nIndexes saved to .indexes/")

    return count


if __name__ == "__main__":
    regenerate_all_indexes()
