"""
OpenAI API client wrapper that works with both older (0.x) and newer (1.x+) versions.
This abstraction shields the rest of the codebase from OpenAI API changes.
"""
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Determine which OpenAI client to use based on available packages
try:
    # Try importing newer version first
    import openai
    from openai import AsyncOpenAI
    OPENAI_VERSION = getattr(openai, "__version__", "1.0.0")
    IS_LEGACY = False
    logger.info(f"Using OpenAI API version {OPENAI_VERSION} (modern client)")
except (ImportError, AttributeError):
    try:
        # Fall back to older version
        import openai
        OPENAI_VERSION = getattr(openai, "__version__", "0.0.0")
        IS_LEGACY = True
        logger.info(f"Using OpenAI API version {OPENAI_VERSION} (legacy client)")
    except ImportError:
        logger.error("OpenAI package not found. Please install with: pip install openai")
        raise


class OpenAIClient:
    """
    Unified OpenAI client that abstracts away version differences.
    This ensures our code works with both older and newer versions.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI client with the provided API key or from environment."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("API key not found. Please provide an API key or set OPENAI_API_KEY environment variable.")
        
        # Log key format for debugging (only first/last few characters)
        key_start = self.api_key[:4]
        key_end = self.api_key[-4:] if len(self.api_key) > 8 else ""
        logger.info(f"Using API key format: {key_start}...{key_end}")
        
        # Initialize the appropriate client
        if IS_LEGACY:
            # Legacy client (0.x)
            openai.api_key = self.api_key
            self.client = openai
        else:
            # Modern client (1.x+)
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Create a chat completion using the appropriate client version.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The model to use (default: gpt-3.5-turbo)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 1000)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The generated text response
        """
        try:
            if IS_LEGACY:
                # Legacy client (0.x)
                response = await asyncio.to_thread(
                    self.client.ChatCompletion.create,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                return response["choices"][0]["message"]["content"]
            else:
                # Modern client (1.x+)
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise


# Singleton instance for reuse
_client_instance = None

async def get_client() -> OpenAIClient:
    """Get or create the OpenAI client singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance


async def translate_with_openai(
    text: str, 
    target_language: str, 
    model: str = "gpt-3.5-turbo"
) -> str:
    """
    Translate text using OpenAI's chat models.
    
    Args:
        text: The text to translate
        target_language: The target language for translation
        model: The model to use (default: gpt-3.5-turbo)
        
    Returns:
        The translated text
    """
    if not text.strip():
        logger.warning("Empty text provided for translation")
        return ""
    
    client = await get_client()
    
    logger.info(f"Translating {len(text)} chars to {target_language} using {model}")
    
    messages = [
        {
            "role": "system", 
            "content": f"You are a professional translator. Translate the following text from English to {target_language} while preserving paragraph breaks, formatting, and the original meaning as accurately as possible."
        },
        {
            "role": "user", 
            "content": text
        }
    ]
    
    translated_text = await client.create_chat_completion(
        messages=messages,
        model=model,
        temperature=0.3,
        max_tokens=4000
    )
    
    logger.info(f"Translation successful, received {len(translated_text)} chars")
    return translated_text.strip() 