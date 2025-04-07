import os
import pytest
from pathlib import Path
import io
import asyncio
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

from app.main import app
from app.services.pdf_extraction import extract_text_from_pdf_binary
from app.api.file_upload_routes import get_upload_settings

@pytest.fixture
def client():
    """Return a TestClient for testing API calls"""
    return TestClient(app)

@pytest.fixture
def sample_pdf_bytes():
    """Create a sample PDF in memory for testing"""
    buffer = io.BytesIO()
    
    # Create a PDF with 2 pages
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Page 1
    c.drawString(100, 750, "API Test PDF - Page 1")
    c.drawString(100, 730, "This content will be translated")
    c.showPage()
    
    # Page 2
    c.drawString(100, 750, "API Test PDF - Page 2")
    c.drawString(100, 730, "More content for translation")
    c.showPage()
    
    c.save()
    
    # Get the PDF content
    buffer.seek(0)
    return buffer.read()

@pytest.fixture
def mock_settings():
    """Mock settings for testing with both background tasks methods"""
    # Return settings first with background_tasks=True, then with False
    with patch('app.api.file_upload_routes.get_upload_settings', return_value={
        "max_file_size": MAX_TEST_FILE_SIZE,
        "max_chapters": 100,
        "use_background_tasks": True  # Test with background tasks first
    }):
        yield
        
# Constants for testing
MAX_TEST_FILE_SIZE = 1024 * 1024  # 1MB for testing

@pytest.mark.asyncio
@pytest.mark.api
@patch("app.api.file_upload_routes.extract_text_from_pdf_binary")
@patch("app.api.file_upload_routes.BackgroundTasks.add_task")
async def test_upload_pdf_with_background_tasks(mock_add_task, mock_extract, client, sample_pdf_bytes, mock_settings):
    """Test uploading a PDF file for translation using BackgroundTasks"""
    # Mock the PDF extraction function
    mock_chapters = [
        {"id": 1, "content": "API Test PDF - Page 1"},
        {"id": 2, "content": "API Test PDF - Page 2"}
    ]
    mock_extract.return_value = mock_chapters
    
    # Setup mock UUID for deterministic testing
    mock_uuid = "12345678-1234-5678-1234-567812345678"
    with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
        # Create test data
        files = {"file": ("test_document.pdf", sample_pdf_bytes, "application/pdf")}
        data = {"target_language": "Português", "output_format": "docx"}
        
        # Make the request
        response = client.post("/api/upload/pdf", files=files, data=data)
        
        # Verify response
        assert response.status_code == 202
        response_data = response.json()
        
        # Check response content
        assert response_data["job_id"] == mock_uuid
        assert response_data["status"] == "pending"
        assert "chapters_extracted" in response_data
        assert response_data["chapters_extracted"] == 2
        
        # Verify extraction was called with correct args
        mock_extract.assert_called_once()
        
        # Verify background task was added with correct args
        mock_add_task.assert_called_once()
        # Check the arguments
        args = mock_add_task.call_args[0]
        assert args[0].__name__ == "process_translation"  # First arg is the function
        assert len(args) == 5  # Function + 4 args
        assert args[1] == mock_uuid  # job_id
        assert args[2] == mock_chapters  # chapters
        assert args[3] == "Português"  # target_language
        assert args[4] == "docx"  # output_format

@pytest.mark.asyncio
@pytest.mark.api
@patch("app.api.file_upload_routes.extract_text_from_pdf_binary")
@patch("app.api.file_upload_routes.asyncio.create_task")
@patch("app.api.file_upload_routes.get_upload_settings", return_value={
    "max_file_size": MAX_TEST_FILE_SIZE,
    "max_chapters": 100,
    "use_background_tasks": False  # Test with asyncio
})
async def test_upload_pdf_with_asyncio(mock_get_settings, mock_create_task, mock_extract, client, sample_pdf_bytes):
    """Test uploading a PDF file for translation using asyncio.create_task"""
    # Mock the PDF extraction function
    mock_chapters = [
        {"id": 1, "content": "API Test PDF - Page 1"},
        {"id": 2, "content": "API Test PDF - Page 2"}
    ]
    mock_extract.return_value = mock_chapters
    
    # Setup mock UUID for deterministic testing
    mock_uuid = "12345678-1234-5678-1234-567812345678"
    with patch("uuid.uuid4", return_value=uuid.UUID(mock_uuid)):
        # Create test data
        files = {"file": ("test_document.pdf", sample_pdf_bytes, "application/pdf")}
        data = {"target_language": "Português", "output_format": "docx"}
        
        # Make the request
        response = client.post("/api/upload/pdf", files=files, data=data)
        
        # Verify response
        assert response.status_code == 202
        response_data = response.json()
        
        # Check response content
        assert response_data["job_id"] == mock_uuid
        assert response_data["status"] == "pending"
        assert "chapters_extracted" in response_data
        assert response_data["chapters_extracted"] == 2
        
        # Verify extraction was called with correct args
        mock_extract.assert_called_once()
        
        # Verify create_task was called
        mock_create_task.assert_called_once()
        # Get the coroutine passed to create_task
        process_coro = mock_create_task.call_args[0][0]
        # We can't directly inspect the coroutine arguments, but we can check it's the right type
        assert isinstance(process_coro, asyncio.coroutines._CoroutineWrapper)

@pytest.mark.asyncio
@pytest.mark.api
async def test_upload_invalid_file_type(client):
    """Test uploading a non-PDF file"""
    # Create a text file instead of PDF
    text_content = b"This is not a PDF file"
    
    files = {"file": ("test_document.txt", text_content, "text/plain")}
    data = {"target_language": "Português", "output_format": "docx"}
    
    # Make the request
    response = client.post("/api/upload/pdf", files=files, data=data)
    
    # Verify response
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

@pytest.mark.asyncio
@pytest.mark.api
@patch("app.api.file_upload_routes.get_upload_settings", return_value={
    "max_file_size": 100,  # Very small size limit
    "max_chapters": 100,
    "use_background_tasks": True
})
async def test_upload_oversized_file(mock_settings, client, sample_pdf_bytes):
    """Test uploading a file that exceeds the size limit"""
    # Create test data with a PDF larger than our tiny limit
    files = {"file": ("large_file.pdf", sample_pdf_bytes, "application/pdf")}
    data = {"target_language": "Português", "output_format": "docx"}
    
    # Make the request
    response = client.post("/api/upload/pdf", files=files, data=data)
    
    # Verify response shows the appropriate error
    assert response.status_code == 400
    assert "exceeds the maximum limit" in response.json()["detail"] 