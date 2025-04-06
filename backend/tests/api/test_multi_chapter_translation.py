import pytest # type: ignore
from unittest.mock import patch, MagicMock, AsyncMock
import json
import uuid
import os
from fastapi.testclient import TestClient
from pathlib import Path
from fastapi.responses import Response

@pytest.mark.asyncio
@patch("app.api.translation_routes.create_book_document")
@patch("app.api.translation_routes.get_job_status")
async def test_translate_multiple_chapters(
    mock_get_job_status, 
    mock_create_document, 
    client,
    mock_translation_services
):
    """Test the translation of multiple chapters"""
    # Setup mocks
    mock_job_id = str(uuid.uuid4())
    mock_create_document.return_value = f"output/{mock_job_id}.docx"
    mock_get_job_status.return_value = {
        "job_id": mock_job_id,
        "status": "translating",
        "progress": 0.5,
        "message": "Translating chapters...",
        "current_chapter": 2,
        "total_chapters": 3
    }
    
    # Test data with 3 chapters
    test_data = {
        "chapters": [
            {"id": 1, "content": "Content for chapter 1"},
            {"id": 2, "content": "Content for chapter 2"},
            {"id": 3, "content": "Content for chapter 3"}
        ],
        "target_language": "Português"
    }
    
    # Submit translation request
    response = client.post("/api/translation/translate", json=test_data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Verify response contains expected fields
    response_data = response.json()
    assert "job_id" in response_data
    assert "status" in response_data
    assert response_data["status"] == "queued"

@pytest.mark.asyncio
@patch("app.api.translation_routes.get_job_status")
async def test_translation_status_tracking(
    mock_get_job_status,
    client,
    mock_translation_services
):
    """Test status tracking for a multi-chapter translation job"""
    # Setup mocks
    mock_job_id = str(uuid.uuid4())
    
    # Initial status - translating
    mock_get_job_status.return_value = {
        "job_id": mock_job_id,
        "status": "translating",
        "progress": 0.5,
        "message": "Translating chapter 1 of 2",
        "current_chapter": 1,
        "total_chapters": 2
    }
    
    # Submit job
    test_data = {
        "chapters": [
            {"id": 1, "content": "Chapter 1 content"},
            {"id": 2, "content": "Chapter 2 content"}
        ],
        "target_language": "Espanhol"
    }
    
    response = client.post("/api/translation/translate", json=test_data)
    assert response.status_code == 200
    
    # Mock job status
    mock_response = client.get(f"/api/translation/status/{mock_job_id}")
    assert mock_response.status_code == 200
    status_data = mock_response.json()
    assert status_data["status"] == "translating"
    assert status_data["progress"] == 0.5
    
    # Update status to completed
    mock_get_job_status.return_value = {
        "job_id": mock_job_id,
        "status": "completed",
        "progress": 1.0,
        "message": "Translation completed",
        "current_chapter": 2,
        "total_chapters": 2,
        "file_path": f"output/{mock_job_id}.docx"
    }
    
    # Check completed status
    mock_response = client.get(f"/api/translation/status/{mock_job_id}")
    assert mock_response.status_code == 200
    status_data = mock_response.json()
    assert status_data["status"] == "completed"
    assert status_data["progress"] == 1.0

@pytest.mark.asyncio
async def test_error_handling_for_invalid_chapters(client):
    """Test error handling for invalid chapters"""
    # Test with empty chapters array
    test_data = {
        "chapters": [],
        "target_language": "Alemão"
    }
    
    response = client.post("/api/translation/translate", json=test_data)
    assert response.status_code == 400
    assert "detail" in response.json()

@pytest.mark.asyncio
@patch("app.api.translation_routes.process_translation")
async def test_error_during_processing(mock_process_translation, client):
    """Test handling errors during the translation process"""
    # Setup the mock to raise an exception
    mock_process_translation.side_effect = RuntimeError("Test error during processing")
    
    # Test with valid data
    test_data = {
        "chapters": [
            {"id": 1, "content": "Content for chapter 1"}
        ],
        "target_language": "Francês"
    }
    
    # The API should still accept the request since the error happens in the background task
    response = client.post("/api/translation/translate", json=test_data)
    assert response.status_code == 200
    
    # Verify response contains expected fields
    response_data = response.json()
    assert "job_id" in response_data
    assert "status" in response_data
    assert response_data["status"] == "queued"

@pytest.mark.asyncio
@patch("app.api.translation_routes.get_job_status")
@patch("os.path.exists")
@patch("fastapi.responses.FileResponse")
async def test_download_translated_book(mock_file_response, mock_path_exists, mock_get_job_status, client):
    """Test downloading a completed translation"""
    # Setup mocks
    mock_job_id = str(uuid.uuid4())
    mock_file_path = f"output/{mock_job_id}.docx"
    
    # Mock FileResponse to return a dummy Response directly
    mock_file_response.return_value = {"dummy": "response"}
    
    # Mock that the job is completed
    mock_get_job_status.return_value = {
        "job_id": mock_job_id,
        "status": "completed",
        "progress": 1.0,
        "message": "Translation completed",
        "file_path": mock_file_path
    }
    
    # Mock that the file exists
    mock_path_exists.return_value = True
    
    # Create an actual test file to ensure it exists
    os.makedirs("output", exist_ok=True)
    with open(mock_file_path, "w") as f:
        f.write("Test content")
        
    try:
        # Test download endpoint
        response = client.get(f"/api/translation/download/{mock_job_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    finally:
        # Clean up the test file
        if os.path.exists(mock_file_path):
            os.remove(mock_file_path) 