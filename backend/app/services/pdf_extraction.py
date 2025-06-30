import os
import logging
from typing import List, Dict, Any
from pypdf import PdfReader
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from PDF file and convert it to chapters.
    Each page is treated as a separate chapter.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        List of chapters with id and content
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"PDF file not found: {file_path}")
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    chapters = []
    
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            
            # Get total number of pages
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            # Extract text from each page
            for i in range(num_pages):
                page = pdf_reader.pages[i]
                text = page.extract_text()
                
                # Skip empty pages
                if not text.strip():
                    logger.warning(f"Skipping empty page {i+1}")
                    continue
                
                # Create chapter from page
                chapters.append({
                    "id": i + 1,
                    "content": text
                })
                
                logger.info(f"Extracted chapter {i+1} with {len(text)} characters")
        
        logger.info(f"Successfully extracted {len(chapters)} chapters from PDF")
        return chapters
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")

async def extract_text_from_pdf_binary(file_content: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Extract text from PDF binary content and convert it to chapters.
    Each page is treated as a separate chapter.
    
    Args:
        file_content: Binary content of the PDF file
        file_name: Name of the uploaded file (for logging)
        
    Returns:
        List of chapters with id and content
    """
    logger.info(f"Extracting text from uploaded PDF: {file_name}")
    
    chapters = []
    
    try:
        # Save the binary content to a temporary file
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, file_name)
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(file_content)
        
        # Process the saved file
        chapters = await extract_text_from_pdf(temp_file_path)
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
            logger.info(f"Removed temporary file: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {temp_file_path}, {str(e)}")
        
        return chapters
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF binary: {str(e)}")
        raise RuntimeError(f"Failed to extract text from PDF binary: {str(e)}") 