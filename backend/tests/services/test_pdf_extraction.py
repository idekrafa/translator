import os
import pytest
from pathlib import Path
import PyPDF2
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.services.pdf_extraction import extract_text_from_pdf, extract_text_from_pdf_binary

@pytest.fixture
def sample_pdf_path():
    """Create a sample PDF file for testing"""
    test_dir = "test_output"
    Path(test_dir).mkdir(exist_ok=True)
    pdf_path = os.path.join(test_dir, "sample_test.pdf")
    
    # Create a PDF with 3 pages
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Page 1
    c.drawString(100, 750, "This is page 1 of the test PDF.")
    c.drawString(100, 730, "It should be extracted as chapter 1.")
    c.showPage()
    
    # Page 2
    c.drawString(100, 750, "This is page 2 of the test PDF.")
    c.drawString(100, 730, "It should be extracted as chapter 2.")
    c.showPage()
    
    # Page 3
    c.drawString(100, 750, "This is page 3 of the test PDF.")
    c.drawString(100, 730, "It should be extracted as chapter 3.")
    c.showPage()
    
    c.save()
    
    yield pdf_path
    
    # Clean up after tests
    try:
        os.remove(pdf_path)
    except Exception as e:
        print(f"Failed to delete test PDF: {e}")

@pytest.fixture
def sample_pdf_binary():
    """Create a sample PDF in memory for testing"""
    buffer = io.BytesIO()
    
    # Create a PDF with 2 pages
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Page 1
    c.drawString(100, 750, "BINARY_PDF_TEST page 1")
    c.drawString(100, 730, "Binary PDF content for chapter 1")
    c.showPage()
    
    # Page 2
    c.drawString(100, 750, "BINARY_PDF_TEST page 2")
    c.drawString(100, 730, "Binary PDF content for chapter 2")
    c.showPage()
    
    c.save()
    
    # Get the PDF content
    buffer.seek(0)
    return buffer.read()

@pytest.mark.asyncio
@pytest.mark.unit
async def test_extract_text_from_pdf(sample_pdf_path):
    """Test extracting text from a PDF file"""
    # Extract chapters from PDF
    chapters = await extract_text_from_pdf(sample_pdf_path)
    
    # Verify the correct number of chapters
    assert len(chapters) == 3
    
    # Verify chapter IDs
    assert chapters[0]["id"] == 1
    assert chapters[1]["id"] == 2
    assert chapters[2]["id"] == 3
    
    # Verify content contains expected text
    assert "page 1" in chapters[0]["content"]
    assert "page 2" in chapters[1]["content"]
    assert "page 3" in chapters[2]["content"]

@pytest.mark.asyncio
@pytest.mark.unit
async def test_extract_text_from_pdf_binary(sample_pdf_binary):
    """Test extracting text from binary PDF content"""
    # Extract chapters from binary PDF
    chapters = await extract_text_from_pdf_binary(sample_pdf_binary, "test.pdf")
    
    # Verify the correct number of chapters
    assert len(chapters) == 2
    
    # Verify chapter IDs
    assert chapters[0]["id"] == 1
    assert chapters[1]["id"] == 2
    
    # Verify content contains expected text
    assert "BINARY_PDF_TEST" in chapters[0]["content"]
    assert "BINARY_PDF_TEST" in chapters[1]["content"]
    
    # Verify chapter-specific content
    assert "chapter 1" in chapters[0]["content"].lower()
    assert "chapter 2" in chapters[1]["content"].lower()

@pytest.mark.asyncio
@pytest.mark.unit
async def test_extract_text_from_nonexistent_pdf():
    """Test extracting text from a nonexistent PDF file"""
    with pytest.raises(FileNotFoundError):
        await extract_text_from_pdf("nonexistent_file.pdf") 