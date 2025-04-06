import os
import pytest
from pathlib import Path
import PyPDF2
from app.services.formatting_service import create_pdf_document
import re

@pytest.fixture
def mock_chapters():
    """Fixture providing distinctly identifiable chapters for testing"""
    return [
        {
            "id": 1, 
            "content": "CHAPTER_1_CONTENT. This is unique text for chapter one. It should only appear in the first chapter section."
        },
        {
            "id": 2, 
            "content": "CHAPTER_2_CONTENT. This is distinct text for chapter two. It must be isolated from other chapters."
        },
        {
            "id": 3, 
            "content": "CHAPTER_3_CONTENT. This is specific content for chapter three. It should be separate from previous chapters."
        }
    ]

@pytest.fixture
def output_dir():
    """Fixture to create and clean up the output directory for tests"""
    test_output_dir = "test_output"
    Path(test_output_dir).mkdir(exist_ok=True)
    yield test_output_dir
    
    # Clean up PDFs after tests
    for file in Path(test_output_dir).glob("*.pdf"):
        try:
            file.unlink()
        except Exception as e:
            print(f"Failed to delete {file}: {e}")

def test_pdf_creation(mock_chapters, output_dir):
    """Test that PDFs are created correctly with multiple chapters"""
    # Create a test PDF
    output_path = f"{output_dir}/test_book.pdf"
    
    # Generate the PDF
    result_path = create_pdf_document(mock_chapters, output_path)
    
    # Check that the file was created
    assert os.path.exists(result_path)
    assert result_path == output_path
    
    # Verify PDF content using PyPDF2
    with open(result_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Get the total number of pages
        page_count = len(pdf_reader.pages)
        
        # A proper book should have at least 3 pages (one per chapter at minimum)
        assert page_count >= 3
        
        # Extract text from each page
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # Verify that all chapters are included in the PDF
        assert "Capítulo 1" in text
        assert "Capítulo 2" in text
        assert "Capítulo 3" in text
        
        # Verify content from each chapter is present
        assert "CHAPTER_1_CONTENT" in text
        assert "CHAPTER_2_CONTENT" in text
        assert "CHAPTER_3_CONTENT" in text

def test_pdf_chapter_separation(mock_chapters, output_dir):
    """Test that PDF correctly separates multiple chapters"""
    output_path = f"{output_dir}/chapter_separation_test.pdf"
    
    # Generate the PDF
    result_path = create_pdf_document(mock_chapters, output_path)
    assert os.path.exists(result_path)
    
    # Extract text from each page
    with open(result_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        page_texts = [page.extract_text() for page in pdf_reader.pages]
        
        # Combined text for searching
        full_text = " ".join(page_texts)
        
        # 1. Check that all chapters are present
        assert "Capítulo 1" in full_text
        assert "Capítulo 2" in full_text
        assert "Capítulo 3" in full_text
        
        # 2. Check that all chapter content is present
        assert "CHAPTER_1_CONTENT" in full_text
        assert "CHAPTER_2_CONTENT" in full_text
        assert "CHAPTER_3_CONTENT" in full_text
        
        # 3. Chapter separation check: Find where each chapter starts in the pages
        chapter_pages = {}
        for i, page_text in enumerate(page_texts):
            if "Capítulo 1" in page_text:
                chapter_pages[1] = i
            if "Capítulo 2" in page_text:
                chapter_pages[2] = i
            if "Capítulo 3" in page_text:
                chapter_pages[3] = i
        
        # Ensure all chapters were found
        assert len(chapter_pages) == 3, f"Not all chapters found in the PDF. Found: {list(chapter_pages.keys())}"
        
        # 4. Check that chapters appear in the correct order
        assert chapter_pages[1] < chapter_pages[2] < chapter_pages[3], "Chapters are not in the correct order"
        
        # 5. Verify chapter content appears on the right pages
        assert "CHAPTER_1_CONTENT" in page_texts[chapter_pages[1]]
        assert "CHAPTER_2_CONTENT" in page_texts[chapter_pages[2]]
        assert "CHAPTER_3_CONTENT" in page_texts[chapter_pages[3]]
        
        # 6. Check that content doesn't bleed between chapters
        # If chapters start on different pages, verify content isolation
        if chapter_pages[1] != chapter_pages[2]:
            assert "CHAPTER_2_CONTENT" not in page_texts[chapter_pages[1]]
        if chapter_pages[2] != chapter_pages[3]:
            assert "CHAPTER_3_CONTENT" not in page_texts[chapter_pages[2]]

def test_chapter_order_independence(output_dir):
    """Test that chapters are ordered correctly regardless of input order"""
    # Create chapters in non-sequential order
    unordered_chapters = [
        {"id": 3, "content": "CHAPTER_3_CONTENT. This should appear third."},
        {"id": 1, "content": "CHAPTER_1_CONTENT. This should appear first."},
        {"id": 2, "content": "CHAPTER_2_CONTENT. This should appear second."}
    ]
    
    output_path = f"{output_dir}/chapter_order_test.pdf"
    result_path = create_pdf_document(unordered_chapters, output_path)
    
    # Verify the PDF
    with open(result_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()
        
        # Check order using regex pattern to find the relative positions of content
        ch1_pos = full_text.find("CHAPTER_1_CONTENT")
        ch2_pos = full_text.find("CHAPTER_2_CONTENT")
        ch3_pos = full_text.find("CHAPTER_3_CONTENT")
        
        # All content should be found
        assert ch1_pos != -1, "Chapter 1 content not found"
        assert ch2_pos != -1, "Chapter 2 content not found" 
        assert ch3_pos != -1, "Chapter 3 content not found"
        
        # Content should appear in the correct order despite input order
        assert ch1_pos < ch2_pos < ch3_pos, "Chapters not ordered correctly in the output PDF"

def test_varying_chapter_lengths(output_dir):
    """Test that chapters of different lengths are correctly handled"""
    # Create chapters with significantly different lengths
    varying_chapters = [
        {"id": 1, "content": "Short chapter."},
        {"id": 2, "content": "Medium length chapter. " * 10},
        {"id": 3, "content": "Very long chapter content. " * 50}
    ]
    
    output_path = f"{output_dir}/varying_length_test.pdf"
    result_path = create_pdf_document(varying_chapters, output_path)
    
    # Verify the PDF
    with open(result_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()
        
        # Check that all three chapter titles exist
        assert "Capítulo 1" in full_text
        assert "Capítulo 2" in full_text
        assert "Capítulo 3" in full_text
        
        # Verify content from each chapter is present
        assert "Short chapter" in full_text
        assert "Medium length chapter" in full_text
        assert "Very long chapter content" in full_text