import logging
import os
import uuid
import asyncio
from typing import List, Optional
from functools import lru_cache

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import JSONResponse

from app.services.pdf_extraction import extract_text_from_pdf_binary
from app.services.translation_service import batch_translate_chapters
from app.api.translation_routes import translation_jobs, process_translation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
upload_router = APIRouter(prefix="/api/upload", tags=["file-upload"])

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (Maximum file size allowed)
MAX_CHAPTERS = 100                # Maximum number of chapters allowed

@lru_cache()
def get_upload_settings():
    """Get upload settings with environment variable overrides."""
    return {
        "max_file_size": int(os.getenv("MAX_FILE_SIZE", str(MAX_FILE_SIZE))),
        "max_chapters": int(os.getenv("MAX_CHAPTERS", str(MAX_CHAPTERS))),
        "use_background_tasks": os.getenv("USE_BACKGROUND_TASKS", "1") == "1"
    }

async def validate_pdf_file(file: UploadFile, settings: dict) -> bytes:
    """
    Validate PDF file type and size, returning file content if valid.
    
    Args:
        file: The uploaded file
        settings: Upload settings dictionary
        
    Returns:
        Binary content of the file
        
    Raises:
        HTTPException: If validation fails
    """
    # Check file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are supported"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Check file size
    max_size = settings["max_file_size"]
    if len(file_content) > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds the maximum limit of {max_size_mb:.1f}MB"
        )
    
    return file_content

@upload_router.post("/pdf")
async def upload_pdf_for_translation(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    output_format: str = Form("docx"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    settings: dict = Depends(get_upload_settings)
):
    """
    Upload a PDF file for translation.
    
    The PDF will be processed, text extracted, and then translated to the target language.
    This endpoint accepts PDF files only, validates them, and starts a background job
    for translation.
    
    Args:
        file: The PDF file to translate
        target_language: Target language for translation
        output_format: Output document format (docx or pdf)
        background_tasks: FastAPI background tasks
        settings: Application settings
        
    Returns:
        JSON with job ID and status information
    """
    try:
        # Validate the file
        file_content = await validate_pdf_file(file, settings)
        
        # Extract text from PDF
        logger.info(f"Extracting text from PDF: {file.filename}, size: {len(file_content) / 1024:.2f}KB")
        chapters = await extract_text_from_pdf_binary(file_content, file.filename)
        
        # Check if extraction succeeded
        if not chapters:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract text from the PDF. The file might be encrypted, damaged, or contain only images."
            )
            
        # Check maximum number of chapters
        max_chapters = settings["max_chapters"]
        if len(chapters) > max_chapters:
            raise HTTPException(
                status_code=400,
                detail=f"The PDF contains too many pages/chapters ({len(chapters)}). Maximum allowed is {max_chapters}."
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        translation_jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "message": "PDF queued for translation",
            "current_chapter": 0,
            "total_chapters": len(chapters)
        }
        
        # Start translation using the appropriate method
        if settings["use_background_tasks"]:
            # Use FastAPI's background tasks
            background_tasks.add_task(
                process_translation,
                job_id,
                chapters,
                target_language,
                output_format
            )
            logger.info(f"Translation job {job_id} added to background tasks")
        else:
            # Use asyncio.create_task
            asyncio.create_task(
                process_translation(
                    job_id,
                    chapters,
                    target_language,
                    output_format
                )
            )
            logger.info(f"Translation job {job_id} started with asyncio.create_task")
        
        # Return response with job information
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": "pending",
                "message": "PDF queued for translation",
                "file_url": f"/api/translation/status/{job_id}",
                "chapters_extracted": len(chapters)
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log and convert other exceptions to HTTP 500
        logger.error(f"Error processing PDF upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        ) 