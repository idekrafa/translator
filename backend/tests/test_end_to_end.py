import pytest
import os
import io
import uuid
import time
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.main import app
from app.api.translation_routes import translation_jobs
from app.services.pdf_extraction import extract_text_from_pdf_binary
from app.services.translation_service import batch_translate_chapters


@pytest.mark.e2e
class TestEndToEnd:
    """
    End-to-end tests for the book translation API.
    Testing the complete flow from API request to response.
    """
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app"""
        with TestClient(app) as test_client:
            yield test_client
    
    @pytest.fixture
    def sample_pdf_bytes(self):
        """Create a sample PDF in memory for testing"""
        buffer = io.BytesIO()
        
        # Create a PDF with 2 pages
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Page 1
        c.drawString(100, 750, "E2E Test PDF - Page 1")
        c.drawString(100, 730, "This content will be translated")
        c.showPage()
        
        # Page 2
        c.drawString(100, 750, "E2E Test PDF - Page 2")
        c.drawString(100, 730, "More content for translation")
        c.showPage()
        
        c.save()
        
        # Get the PDF content
        buffer.seek(0)
        return buffer.read()
    
    @pytest.mark.asyncio
    @patch("app.api.file_upload_routes.asyncio.create_task")
    @patch("app.api.file_upload_routes.extract_text_from_pdf_binary")
    @patch("uuid.uuid4")
    async def test_pdf_upload_and_translation_flow(self, mock_uuid, mock_extract, mock_create_task, client, sample_pdf_bytes):
        """Test the complete flow of uploading a PDF, extracting text, and processing translation"""
        # Setup mock PDF extraction
        mock_chapters = [
            {"id": 1, "content": "E2E Test PDF - Page 1\nThis content will be translated"},
            {"id": 2, "content": "E2E Test PDF - Page 2\nMore content for translation"}
        ]
        mock_extract.return_value = mock_chapters
        
        # Setup a deterministic UUID for testing
        test_uuid = "12345678-1234-5678-1234-567812345678"
        mock_uuid.return_value = uuid.UUID(test_uuid)
        
        # Create test data for the file upload
        files = {"file": ("test_document.pdf", sample_pdf_bytes, "application/pdf")}
        data = {"target_language": "Português", "output_format": "docx"}
        
        # 1. Upload PDF for translation
        response = client.post("/api/upload/pdf", files=files, data=data)
        
        # Verify initial response
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["job_id"] == test_uuid
        assert response_data["status"] == "pending"
        assert response_data["chapters_extracted"] == 2
        
        # Verify extraction function was called correctly
        mock_extract.assert_called_once()
        
        # Verify create_task was called
        mock_create_task.assert_called_once()
        
        # 2. Check job status (simulate process running)
        translation_jobs[test_uuid]["status"] = "translating"
        translation_jobs[test_uuid]["progress"] = 0.5
        translation_jobs[test_uuid]["current_chapter"] = 1
        translation_jobs[test_uuid]["message"] = "Translating chapter 1 of 2"
        
        response = client.get(f"/api/translation/status/{test_uuid}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] == "translating"
        assert status_data["progress"] == 0.5
        assert status_data["current_chapter"] == 1
        
        # 3. Simulate translation completion
        translation_jobs[test_uuid]["status"] = "completed"
        translation_jobs[test_uuid]["progress"] = 1.0
        translation_jobs[test_uuid]["message"] = "Translation completed"
        translation_jobs[test_uuid]["file_path"] = f"output/{test_uuid}.docx"
        
        # Create a dummy output file for testing download
        os.makedirs("output", exist_ok=True)
        with open(f"output/{test_uuid}.docx", "wb") as f:
            f.write(b"Dummy DOCX content for testing")
        
        # 4. Check final status
        response = client.get(f"/api/translation/status/{test_uuid}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] == "completed"
        assert status_data["progress"] == 1.0
        
        # 5. Test download endpoint
        with patch("fastapi.responses.FileResponse.__call__", return_value=b"Dummy DOCX content"):
            response = client.get(f"/api/translation/download/{test_uuid}")
            assert response.status_code == 200
        
        # Clean up the test file
        try:
            os.remove(f"output/{test_uuid}.docx")
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_invalid_file_type(self, client):
        """Test uploading an invalid file type"""
        # Create a text file instead of PDF
        text_content = b"This is not a PDF file"
        
        files = {"file": ("test_document.txt", text_content, "text/plain")}
        data = {"target_language": "Português", "output_format": "docx"}
        
        # Make the request
        response = client.post("/api/upload/pdf", files=files, data=data)
        
        # Verify response shows the appropriate error
        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_oversized_file(self, client):
        """Test uploading a file that exceeds size limits"""
        # Create a mock oversized PDF by patching the file content check
        with patch("app.api.file_upload_routes.MAX_FILE_SIZE", 100):  # Set tiny limit for testing
            # Create a regular PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.drawString(100, 750, "Oversized test PDF")
            c.save()
            buffer.seek(0)
            
            # Submit file larger than our patched limit
            files = {"file": ("oversized.pdf", buffer.read(), "application/pdf")}
            data = {"target_language": "Português"}
            
            response = client.post("/api/upload/pdf", files=files, data=data)
            
            # Verify size limit error
            assert response.status_code == 400
            assert "exceeds the maximum limit" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("app.api.translation_routes.batch_translate_chapters")
    async def test_chapter_based_translation_flow(self, mock_batch_translate, client):
        """Test the complete flow of submitting chapters for translation"""
        # Setup mock for the batch translation
        mock_translated_chapters = [
            {"id": 1, "content": "Conteúdo traduzido do capítulo 1"},
            {"id": 2, "content": "Conteúdo traduzido do capítulo 2"}
        ]
        mock_batch_translate.return_value = mock_translated_chapters
        
        # Setup a deterministic UUID for testing
        test_uuid = "87654321-8765-4321-8765-432187654321"
        with patch("uuid.uuid4", return_value=uuid.UUID(test_uuid)):
            # Create test chapter data
            test_data = {
                "chapters": [
                    {"id": 1, "content": "Content of chapter 1"},
                    {"id": 2, "content": "Content of chapter 2"}
                ],
                "target_language": "Português",
                "output_format": "pdf"
            }
            
            # 1. Submit chapters for translation
            response = client.post("/api/translation/translate", json=test_data)
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["job_id"] == test_uuid
            assert response_data["status"] == "queued"
            
            # 2. Check job status (initial state)
            response = client.get(f"/api/translation/status/{test_uuid}")
            assert response.status_code == 200
            assert response.json()["status"] == "queued"
            
            # 3. Simulate translation progress
            translation_jobs[test_uuid]["status"] = "translating"
            translation_jobs[test_uuid]["progress"] = 0.5
            translation_jobs[test_uuid]["current_chapter"] = 1
            translation_jobs[test_uuid]["message"] = "Traduzindo capítulo 1/2..."
            
            response = client.get(f"/api/translation/status/{test_uuid}")
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "translating"
            assert status_data["progress"] == 0.5
            assert status_data["current_chapter"] == 1
            
            # 4. Simulate translation completion
            translation_jobs[test_uuid]["status"] = "completed"
            translation_jobs[test_uuid]["progress"] = 1.0
            translation_jobs[test_uuid]["message"] = "Tradução concluída"
            translation_jobs[test_uuid]["file_path"] = f"output/{test_uuid}.pdf"
            
            # Create a dummy output file for testing download
            os.makedirs("output", exist_ok=True)
            with open(f"output/{test_uuid}.pdf", "wb") as f:
                f.write(b"Dummy PDF content for testing")
            
            # 5. Check final status
            response = client.get(f"/api/translation/status/{test_uuid}")
            assert response.status_code == 200
            assert response.json()["status"] == "completed"
            
            # 6. Test download endpoint
            with patch("fastapi.responses.FileResponse.__call__", return_value=b"Dummy PDF content"):
                response = client.get(f"/api/translation/download/{test_uuid}")
                assert response.status_code == 200
            
            # Clean up the test file
            try:
                os.remove(f"output/{test_uuid}.pdf")
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_nonexistent_job(self, client):
        """Test requesting status for a non-existent job"""
        # Generate a random job ID that doesn't exist
        nonexistent_id = str(uuid.uuid4())
        
        # Request status for non-existent job
        response = client.get(f"/api/translation/status/{nonexistent_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Request download for non-existent job
        response = client.get(f"/api/translation/download/{nonexistent_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test the root endpoint of the API"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "api_name" in data
        assert "version" in data
        assert data["api_name"] == "Book Translation API" 