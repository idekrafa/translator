import os
from typing import Dict, List, Any
import logging
import json
import asyncio
from .openai_client import translate_with_openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def translate_text(text: str, target_language: str, max_retries: int = 3) -> str:
    """
    Translate text using OpenAI with retry logic.
    
    Args:
        text: The text to translate
        target_language: The target language for translation
        max_retries: Maximum number of retry attempts for API errors
    
    Returns:
        The translated text
    """
    retries = 0
    last_error = None
    
    while retries <= max_retries:
        try:
            if not text.strip():
                logger.warning("Empty text provided for translation")
                return ""
            
            # Use our abstracted wrapper for OpenAI translation
            return await translate_with_openai(text, target_language)
            
        except Exception as e:
            last_error = e
            retries += 1
            wait_time = 2 ** retries  # Exponential backoff: 2, 4, 8 seconds
            
            logger.warning(f"Translation error (attempt {retries}/{max_retries}): {str(e)}. Retrying in {wait_time} seconds...")
            
            if retries <= max_retries:
                await asyncio.sleep(wait_time)
            else:
                # Log the final error
                import traceback
                logger.error(f"Translation failed after {max_retries} attempts. Last error: {str(last_error)}\n{traceback.format_exc()}")
                raise RuntimeError(f"Translation error after {max_retries} attempts: {str(last_error)}")
    
    # This should never be reached due to the raise in the else clause above
    raise RuntimeError(f"Unexpected error in translation retry logic")


async def translate_chapter(chapter_content: str, target_language: str) -> str:
    """
    Process entire chapter in a single request if possible, or process chunks in parallel.
    
    Args:
        chapter_content: The chapter content to translate
        target_language: The target language for translation
    
    Returns:
        The translated chapter
    """
    # Set optimal chunk size for modern OpenAI models (higher limit than before)
    chunk_size = 4000  # Conservative value that works well with gpt-4 and gpt-3.5-turbo
    
    # For small chapters, process in a single request
    if len(chapter_content) <= chunk_size:
        logger.info(f"Translating entire chapter as single unit ({len(chapter_content)} chars)")
        return await translate_text(chapter_content, target_language)
    
    # For large chapters, split into chunks and process concurrently
    chunks = []
    for i in range(0, len(chapter_content), chunk_size):
        chunks.append(chapter_content[i:i+chunk_size])
    
    logger.info(f"Splitting chapter into {len(chunks)} chunks for parallel processing")
    
    # Create tasks for translating each chunk concurrently
    async def translate_chunk(chunk_index, chunk_text):
        logger.info(f"Translating chunk {chunk_index+1}/{len(chunks)}, size: {len(chunk_text)} chars")
        translated = await translate_text(chunk_text, target_language)
        logger.info(f"Completed chunk {chunk_index+1}/{len(chunks)}")
        return translated
    
    # Create and execute all translation tasks concurrently
    tasks = [translate_chunk(i, chunk) for i, chunk in enumerate(chunks)]
    translated_chunks = await asyncio.gather(*tasks)
    
    # Join chunks back together
    return "\n".join(translated_chunks)


async def batch_translate_chapters(chapters: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
    """
    Translate all chapters concurrently using asyncio.gather.
    
    Args:
        chapters: List of chapter dictionaries with 'id' and 'content' keys
        target_language: The target language for translation
    
    Returns:
        List of translated chapter dictionaries
    """
    logger.info(f"Starting batch translation of {len(chapters)} chapters to {target_language}")
    
    # Create tasks for translating each chapter concurrently
    async def translate_single_chapter(chapter):
        chapter_id = chapter['id']
        logger.info(f"Translating chapter {chapter_id}")
        translated_content = await translate_chapter(chapter["content"], target_language)
        logger.info(f"Completed translation of chapter {chapter_id}")
        return {
            "id": chapter_id,
            "content": translated_content
        }
    
    # Create a list of translation tasks
    translation_tasks = [translate_single_chapter(chapter) for chapter in chapters]
    
    # Execute all translation tasks concurrently
    results = await asyncio.gather(*translation_tasks)
    
    # Sort chapters by ID to maintain order
    translated_chapters = sorted(results, key=lambda x: x["id"])
    
    logger.info(f"Completed batch translation of {len(chapters)} chapters")
    return translated_chapters 