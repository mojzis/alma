"""Pytest configuration and fixtures."""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Set environment variables BEFORE any imports
# This ensures they're available when the app module loads
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8000/auth/callback"
os.environ["DEBUG"] = "True"


@pytest.fixture(scope="session", autouse=True)
def test_env():
    """Set up test environment variables at session level."""
    # Already set at module level above
    yield
    # Cleanup after all tests
    for key in ["SECRET_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "DEBUG"]:
        os.environ.pop(key, None)


@pytest.fixture
def temp_notes_dir():
    """Create a temporary directory for notes during testing."""
    temp_dir = tempfile.mkdtemp()
    notes_dir = Path(temp_dir) / "notes"
    indexes_dir = Path(temp_dir) / ".indexes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    indexes_dir.mkdir(parents=True, exist_ok=True)

    # Create default project directories
    (notes_dir / "personal").mkdir(exist_ok=True)
    (notes_dir / "work").mkdir(exist_ok=True)
    (notes_dir / "reference").mkdir(exist_ok=True)

    # Monkey patch the notes directory
    original_notes_dir = os.getcwd()
    os.chdir(temp_dir)

    yield temp_dir

    # Cleanup
    os.chdir(original_notes_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(temp_notes_dir):
    """Create a test client for the FastAPI app."""
    from alma.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client."""
    # Create a mock session cookie
    from alma.auth import create_session_cookie

    session_cookie = create_session_cookie("test@example.com")
    client.cookies.set("session", session_cookie)

    yield client
