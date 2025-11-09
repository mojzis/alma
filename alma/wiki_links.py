"""Wiki-link parsing and indexing."""

import re
from typing import Set, List
from . import indexes
from pathlib import Path

# Pattern to match [[wiki links]]
WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')

# Wiki-links index file
WIKI_LINKS_INDEX = indexes.INDEXES_DIR / "wiki-links.json"


def extract_wiki_links(content: str) -> Set[str]:
    """Extract wiki-style links [[link]] from content."""
    return set(WIKI_LINK_PATTERN.findall(content))


def add_wiki_links_to_index(note_id: str, links: Set[str]):
    """Store wiki links for a note."""
    index = indexes.load_index(WIKI_LINKS_INDEX)
    index[note_id] = list(links)
    indexes.save_index(WIKI_LINKS_INDEX, index)


def remove_wiki_links_from_index(note_id: str):
    """Remove wiki links for a note."""
    index = indexes.load_index(WIKI_LINKS_INDEX)
    if note_id in index:
        del index[note_id]
        indexes.save_index(WIKI_LINKS_INDEX, index)


def get_backlinks(note_title: str) -> List[str]:
    """Find all notes that link to this note title."""
    index = indexes.load_index(WIKI_LINKS_INDEX)
    backlinks = []
    note_title_lower = note_title.lower()

    for note_id, links in index.items():
        # Case-insensitive comparison
        if any(link.lower() == note_title_lower for link in links):
            backlinks.append(note_id)

    return backlinks


def resolve_wiki_link(link_text: str) -> str | None:
    """Find note ID by title (case-insensitive match)."""
    all_metadata = indexes.get_all_metadata(limit=1000)
    link_lower = link_text.lower()

    # Try exact match first
    for meta in all_metadata:
        if meta["title"].lower() == link_lower:
            return meta["id"]

    return None


def render_wiki_links(content: str) -> str:
    """Convert [[wiki links]] to HTML links."""
    def replace_link(match):
        link_text = match.group(1)
        note_id = resolve_wiki_link(link_text)

        if note_id:
            # Found the note - make it clickable
            return f'<a href="#note-{note_id}" class="wiki-link" onclick="scrollToNote(\'{note_id}\')">[[{link_text}]]</a>'
        else:
            # Note not found - show as broken link
            return f'<span class="wiki-link-broken">[[{link_text}]]</span>'

    return re.sub(WIKI_LINK_PATTERN, replace_link, content)
