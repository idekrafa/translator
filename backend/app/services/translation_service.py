import os
from typing import Dict, List, Any
import asyncio
import logging
import json
import httpx
import random
import time
from openai import AsyncOpenAI  # Import AsyncOpenAI client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações de rate limiting e retry
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1  # segundos
MAX_RETRY_DELAY = 60  # segundos

# Não inicializa o cliente globalmente
# client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def translate_text_with_retry(text: str, target_language: str) -> str:
    """
    Translate text with retry logic to handle rate limits and network issues.
    
    Args:
        text: The text to translate
        target_language: The target language for translation
    
    Returns:
        The translated text
    """
    retry_count = 0
    retry_delay = INITIAL_RETRY_DELAY
    
    while retry_count < MAX_RETRIES:
        try:
            return await translate_text(text, target_language)
        except RuntimeError as e:
            error_message = str(e)
            
            # Network or rate limit errors should be retried
            if "Network connection issue" in error_message or "Rate limit exceeded" in error_message:
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    logger.error(f"Maximum retries ({MAX_RETRIES}) reached. Giving up.")
                    raise RuntimeError(f"Failed after {MAX_RETRIES} retries: {error_message}")
                
                # Apply exponential backoff with jitter
                jitter = random.uniform(0, 0.1 * retry_delay)
                sleep_time = min(retry_delay + jitter, MAX_RETRY_DELAY)
                
                logger.warning(f"Error occurred, retrying in {sleep_time:.2f} seconds (retry {retry_count}/{MAX_RETRIES}): {error_message}")
                await asyncio.sleep(sleep_time)
                
                # Increase delay for next retry
                retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
            else:
                # Other errors should not be retried
                logger.error(f"Non-retryable error: {error_message}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error in translation: {str(e)}")
            raise RuntimeError(f"Unexpected error in translation: {str(e)}")


async def translate_text(text: str, target_language: str) -> str:
    """
    Translate text using OpenAI GPT-4o-mini via official client.
    
    Args:
        text: The text to translate
        target_language: The target language for translation
    
    Returns:
        The translated text
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key não encontrada. Verifique o arquivo .env")
        
        # Log key format for debugging (only first/last few characters)
        key_start = api_key[:8]
        key_end = api_key[-4:] if len(api_key) > 8 else ""
        logger.info(f"Using API key format: {key_start}...{key_end}")
        
        # Use the official AsyncOpenAI client with increased timeout
        client = AsyncOpenAI(
            api_key=api_key,
            timeout=120.0,  # Increase timeout to 120 seconds
            max_retries=3   # Add automatic retries
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
            max_tokens=2000  # Reduced from 4000 to avoid potential limits
        )
        
        # Extract the translated text from the response
        translated_text = response.choices[0].message.content
        logger.info(f"Translation successful, received {len(translated_text)} chars")
        return translated_text.strip()
    
    except Exception as e:
        import traceback
        logger.error(f"Translation error: {str(e)}\n{traceback.format_exc()}")
        # Provide more descriptive error
        if "ReadError" in str(e) or "BrokenResourceError" in str(e):
            raise RuntimeError(f"Network connection issue with OpenAI API: {str(e)}")
        elif "AuthenticationError" in str(e):
            raise RuntimeError(f"Authentication error with OpenAI API. Check your API key format.")
        elif "RateLimitError" in str(e):
            raise RuntimeError(f"Rate limit exceeded with OpenAI API. Try again later.")
        else:
            raise RuntimeError(f"Failed to translate text: {str(e)}")


async def translate_chapter(chapter_content: str, target_language: str) -> str:
    """
    Divide chapter into manageable chunks and translate each chunk.
    
    Args:
        chapter_content: The chapter content to translate
        target_language: The target language for translation
    
    Returns:
        The translated chapter
    """
    # Approximate character limit per chunk (about 500 tokens)
    chunk_size = 1500  # Reduced from 3000 to avoid timeout issues
    
    # Split chapter into chunks
    chunks = []
    for i in range(0, len(chapter_content), chunk_size):
        chunks.append(chapter_content[i:i+chunk_size])
    
    logger.info(f"Splitting chapter into {len(chunks)} chunks of {chunk_size} chars each")
    
    # Translate each chunk with delay between requests to avoid rate limiting
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        # Add a small delay between chunks to avoid rate limiting
        if i > 0:
            await asyncio.sleep(2)  # Increased from 1 to 2 seconds delay between chunk translations
            
        logger.info(f"Translating chunk {i+1}/{len(chunks)}, size: {len(chunk)} chars")
        translated_chunk = await translate_text_with_retry(chunk, target_language)
        translated_chunks.append(translated_chunk)
        logger.info(f"Completed chunk {i+1}/{len(chunks)}")
    
    # Join chunks back together
    return "\n".join(translated_chunks)


async def batch_translate_chapters(chapters: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
    """
    Translate chapters sequentially to avoid rate limits.
    
    Args:
        chapters: List of chapter dictionaries with 'id' and 'content' keys
        target_language: The target language for translation
    
    Returns:
        List of translated chapter dictionaries
    """
    # Process chapters sequentially to avoid hammering the API
    translated_chapters = []
    
    for chapter in chapters:
        logger.info(f"Translating chapter {chapter['id']}")
        translated_content = await translate_chapter(chapter["content"], target_language)
        translated_chapters.append({
            "id": chapter["id"],
            "content": translated_content
        })
        
        # Add delay between chapters
        if chapter != chapters[-1]:  # If not the last chapter
            await asyncio.sleep(2)  # 2 second delay between chapters
    
    # Sort chapters by ID to maintain order
    translated_chapters.sort(key=lambda x: x["id"])
    
    return translated_chapters 