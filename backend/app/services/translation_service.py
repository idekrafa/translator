import os
from typing import Dict, List, Any
import logging
import json
from openai import AsyncOpenAI
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def translate_text(text: str, target_language: str, max_retries: int = 3) -> str:
    """
    Translate text using OpenAI GPT-4o-mini via official client.
    Includes basic retry logic for API errors.
    
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
            # Get API key from environment
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("API key não encontrada. Verifique o arquivo .env")
            
            # Log key format for debugging (only first/last few characters)
            key_start = api_key[:8]
            key_end = api_key[-4:] if len(api_key) > 8 else ""
            logger.info(f"Using API key format: {key_start}...{key_end}")
            
            # Use the official AsyncOpenAI client
            client = AsyncOpenAI(
                api_key=api_key,
                timeout=120.0
            )
            
            # Log request parameters
            logger.info(f"API Request - Model: gpt-4o-mini, Target language: {target_language}, Text length: {len(text)} chars")
            
            # Ensure text is not empty
            if not text.strip():
                logger.warning("Empty text provided for translation")
                return ""
                
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a professional translator. Translate the following text from English to {target_language} while preserving paragraph breaks, formatting, and the original meaning as accurately as possible."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Extract the translated text from the response
            translated_text = response.choices[0].message.content
            logger.info(f"Translation successful, received {len(translated_text)} chars")
            return translated_text.strip()
        
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
    # Use a larger chunk size to minimize chunking
    chunk_size = 8000  # Significantly increased from original 1500
    
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