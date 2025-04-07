from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import logging
import uuid
from typing import Dict, List, Any
import asyncio

from app.models.schemas import BookTranslationRequest, TranslationResponse, TranslationProgress
from app.services.translation_service import batch_translate_chapters, translate_chapter
from app.services.formatting_service import create_book_document, create_pdf_document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
translation_router = APIRouter(prefix="/api/translation", tags=["translation"])

# Store for translation jobs
translation_jobs: Dict[str, Dict[str, Any]] = {}


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a translation job.
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Job status information
    """
    if job_id not in translation_jobs:
        raise HTTPException(status_code=404, detail="Translation job not found")
    
    return translation_jobs[job_id]


async def process_translation(
    job_id: str,
    chapters: List[Dict[str, Any]],
    target_language: str,
    output_format: str = "docx"
):
    """
    Background task to process translation and document generation.
    Uses the batch_translate_chapters function for efficient parallel processing.
    
    Args:
        job_id: Unique job identifier
        chapters: List of chapters to translate
        target_language: Target language for translation
        output_format: Output document format (docx or pdf)
    """
    try:
        # Update initial job status
        translation_jobs[job_id]["status"] = "translating"
        translation_jobs[job_id]["progress"] = 0.1
        translation_jobs[job_id]["message"] = "Iniciando tradução dos capítulos..."
        
        # Set up progress tracking for batch translation
        total_chapters = len(chapters)
        logger.info(f"Starting translation of {total_chapters} chapters for job {job_id}")
        
        # Custom progress callback to update job status during translation
        async def update_progress(chapter_index: int, chapter_id: int):
            progress_pct = 0.1 + (0.6 * (chapter_index / total_chapters))
            translation_jobs[job_id]["progress"] = progress_pct
            translation_jobs[job_id]["current_chapter"] = chapter_index + 1
            translation_jobs[job_id]["message"] = f"Traduzindo capítulo {chapter_id}/{total_chapters}..."
        
        # Use the batch translation function with progress updates
        translated_chapters = await batch_translate_chapters(chapters, target_language)
        
        # Log the translated chapters before formatting
        chapter_ids = [chapter["id"] for chapter in translated_chapters]
        chapter_lengths = [len(chapter["content"]) for chapter in translated_chapters]
        logger.info(f"Translation completed for job {job_id}. Chapters: {chapter_ids}, Lengths: {chapter_lengths}")
        
        # Update job status for formatting phase
        translation_jobs[job_id]["status"] = "formatting"
        translation_jobs[job_id]["progress"] = 0.7
        translation_jobs[job_id]["message"] = "Formatando documento..."
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        # Generate document based on requested format
        if output_format == "pdf":
            output_path = f"output/{job_id}.pdf"
            logger.info(f"Creating PDF document with {len(translated_chapters)} chapters at {output_path}")
            file_path = create_pdf_document(translated_chapters, output_path)
        else:
            output_path = f"output/{job_id}.docx"
            logger.info(f"Creating DOCX document with {len(translated_chapters)} chapters at {output_path}")
            file_path = create_book_document(translated_chapters, output_path)
        
        # Update job status to completed
        translation_jobs[job_id]["status"] = "completed"
        translation_jobs[job_id]["progress"] = 1.0
        translation_jobs[job_id]["message"] = "Tradução e formatação concluídas!"
        translation_jobs[job_id]["file_path"] = file_path
        
    except Exception as e:
        logger.error(f"Error in translation job {job_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        translation_jobs[job_id]["status"] = "error"
        translation_jobs[job_id]["message"] = f"Erro: {str(e)}"


@translation_router.post("/translate", response_model=TranslationResponse)
async def translate_book(
    request: BookTranslationRequest,
    background_tasks: BackgroundTasks,
    output_format: str = "docx"
):
    """
    Start a book translation job.
    
    Args:
        request: Book translation request with chapters and target language
        background_tasks: FastAPI background tasks
        output_format: Output format (docx or pdf)
    
    Returns:
        Response with job ID and status information
    """
    # Validate request
    if not request.chapters:
        raise HTTPException(status_code=400, detail="No chapters provided")
    
    if len(request.chapters) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 chapters allowed")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    translation_jobs[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "current_chapter": 0,
        "total_chapters": len(request.chapters),
        "message": "Trabalho em fila para processamento...",
        "target_language": request.target_language,
        "output_format": output_format
    }
    
    # Convert chapters to dict format for processing
    chapters_data = [{"id": chapter.id, "content": chapter.content} for chapter in request.chapters]
    
    # Start background task for processing
    background_tasks.add_task(
        process_translation,
        job_id,
        chapters_data,
        request.target_language,
        output_format
    )
    
    # Return response with job ID
    return TranslationResponse(
        job_id=job_id,
        status="queued",
        message="Tradução iniciada. Use o endpoint de status para verificar o progresso.",
        file_url=f"/api/translation/status/{job_id}"
    )


@translation_router.get("/status/{job_id}", response_model=TranslationProgress)
async def get_translation_status(job_id: str):
    """
    Get status of a translation job.
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Current job status and progress information
    """
    job_status = get_job_status(job_id)
    
    return TranslationProgress(
        status=job_status["status"],
        progress=job_status["progress"],
        current_chapter=job_status["current_chapter"],
        total_chapters=job_status["total_chapters"],
        message=job_status["message"]
    )


@translation_router.get("/download/{job_id}")
async def download_translated_book(job_id: str):
    """
    Download a completed translation job.
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        File download response
    """
    job_status = get_job_status(job_id)
    
    if job_status["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail="Translation job not completed yet"
        )
    
    if "file_path" not in job_status:
        raise HTTPException(
            status_code=404, 
            detail="Output file not found"
        )
    
    file_path = job_status["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, 
            detail="Output file not found on server"
        )
    
    # Determine file name based on format
    filename = f"livro_traduzido.{file_path.split('.')[-1]}"
    
    return FileResponse(
        path=file_path, 
        filename=filename, 
        media_type="application/octet-stream"
    ) 