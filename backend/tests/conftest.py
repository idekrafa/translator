import pytest # type: ignore
import os
import sys
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

@pytest.fixture
def client():
    """
    Create a test client for FastAPI app.
    This fixture is used by all tests that need to make HTTP requests to the API.
    """
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_openai_key():
    """
    Mock the OpenAI API key environment variable.
    This ensures tests don't use a real API key.
    """
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-for-pytest"}):
        yield

@pytest.fixture
def sample_chapters():
    """
    Return sample chapter data for tests.
    """
    return [
        {"id": 1, "content": "This is the first chapter content."},
        {"id": 2, "content": "This is the second chapter content."},
        {"id": 3, "content": "This is the third chapter content."}
    ]

@pytest.fixture
def sample_translated_chapters():
    """
    Return sample translated chapter data for tests.
    """
    return [
        {"id": 1, "content": "Este é o conteúdo do primeiro capítulo."},
        {"id": 2, "content": "Este é o conteúdo do segundo capítulo."},
        {"id": 3, "content": "Este é o conteúdo do terceiro capítulo."}
    ]

# Define async mock functions for testing without hitting the OpenAI API
async def mock_translate_text(text: str, target_language: str) -> str:
    """Mock translation function that returns predictable responses"""
    return f"Translated to {target_language}: {text[:20]}..." if text else ""

async def mock_translate_chapter(chapter_content: str, target_language: str) -> str:
    """Mock chapter translation that works regardless of content size"""
    return f"Chapter translated to {target_language}: {chapter_content[:30]}..."

async def mock_batch_translate_chapters(chapters, target_language: str):
    """Mock batch chapter translation that processes all chapters"""
    return [
        {"id": chapter["id"], "content": f"Chapter {chapter['id']} translated to {target_language}"}
        for chapter in chapters
    ]

@pytest.fixture
def mock_translation_services():
    """
    Patch all translation service functions for testing.
    """
    with patch("app.services.translation_service.translate_text", mock_translate_text), \
         patch("app.services.translation_service.translate_chapter", mock_translate_chapter), \
         patch("app.services.translation_service.batch_translate_chapters", mock_batch_translate_chapters), \
         patch("app.api.translation_routes.batch_translate_chapters", mock_batch_translate_chapters), \
         patch("app.api.translation_routes.translate_chapter", mock_translate_chapter):
        yield
