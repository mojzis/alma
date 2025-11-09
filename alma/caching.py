"""Performance caching utilities."""

from functools import lru_cache
from datetime import datetime, timedelta
from typing import Any, Optional

# Simple in-memory cache with TTL
_cache: dict[str, tuple[Any, datetime]] = {}
_cache_timeout = timedelta(minutes=5)


def cache_get(key: str) -> Optional[Any]:
    """Get from cache if not expired."""
    if key in _cache:
        value, timestamp = _cache[key]
        if datetime.now() - timestamp < _cache_timeout:
            return value
        else:
            # Expired, remove it
            del _cache[key]
    return None


def cache_set(key: str, value: Any) -> None:
    """Set cache value with current timestamp."""
    _cache[key] = (value, datetime.now())


def cache_invalidate(key: str) -> None:
    """Invalidate a specific cache entry."""
    if key in _cache:
        del _cache[key]


def cache_clear() -> None:
    """Clear all cache entries."""
    _cache.clear()


def cache_invalidate_pattern(pattern: str) -> None:
    """Invalidate all cache entries matching a pattern."""
    keys_to_delete = [key for key in _cache.keys() if pattern in key]
    for key in keys_to_delete:
        del _cache[key]


# LRU cache for frequently accessed functions
@lru_cache(maxsize=100)
def get_note_metadata_cached(note_id: str) -> Optional[dict]:
    """Cached note metadata retrieval."""
    from . import indexes
    return indexes.get_note_metadata(note_id)


def invalidate_note_cache(note_id: str) -> None:
    """Invalidate cached data for a specific note."""
    get_note_metadata_cached.cache_clear()
    cache_invalidate(f"note:{note_id}")
    cache_invalidate_pattern(f"notes:")
    cache_invalidate_pattern(f"project:")
    cache_invalidate_pattern(f"tag:")
