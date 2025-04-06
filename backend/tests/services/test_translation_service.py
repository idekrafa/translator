import pytest # type: ignore
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
from app.services.translation_service import (
    translate_text, 
    translate_chapter, 
    batch_translate_chapters
)

@pytest.mark.asyncio
@patch("app.services.translation_service.translate_text")
async def test_translate_chapter(mock_translate_text):
    """Test translating a single chapter that requires chunking"""
    # Setup mock to return different translations for different chunks
    mock_translate_text.side_effect = [
        "Chunk 1 translated",
        "Chunk 2 translated",
        "Chunk 3 translated"
    ]
    
    # Create a chapter with content that will be split into chunks
    # The function now uses 8000 char chunks, so we need a larger test content
    long_content = "A" * 24000  # Should create 3 chunks with 8000 char size
    
    result = await translate_chapter(long_content, "Espanhol")
    
    # Verify that translate_text was called for each chunk
    assert mock_translate_text.call_count == 3
    
    # Verify the chunks were combined in the result
    assert "Chunk 1 translated\nChunk 2 translated\nChunk 3 translated" == result

@pytest.mark.asyncio
@patch("app.services.translation_service.translate_text")
async def test_translate_chapter_single_request(mock_translate_text):
    """Test that small chapters are processed in a single request"""
    # Setup mock
    mock_translate_text.return_value = "Complete chapter translated"
    
    # Content that's small enough to fit in one request
    content = "A" * 7000  # Under the 8000 character limit
    
    result = await translate_chapter(content, "Italiano")
    
    # Should call translate_text only once
    mock_translate_text.assert_called_once()
    assert result == "Complete chapter translated"

@pytest.mark.asyncio
@patch("app.services.translation_service.translate_chapter")
async def test_batch_translate_chapters(mock_translate_chapter):
    """Test translating multiple chapters sequentially"""
    # Setup mock to return different translations for each chapter
    mock_translate_chapter.side_effect = [
        "Chapter 1 translated to Portuguese",
        "Chapter 2 translated to Portuguese",
        "Chapter 3 translated to Portuguese"
    ]
    
    # Create test chapters
    chapters = [
        {"id": 1, "content": "Chapter 1 content"},
        {"id": 2, "content": "Chapter 2 content"},
        {"id": 3, "content": "Chapter 3 content"}
    ]
    
    result = await batch_translate_chapters(chapters, "Português")
    
    # Verify translate_chapter was called for each chapter
    assert mock_translate_chapter.call_count == 3
    
    # Verify the result contains all chapters with translations
    assert len(result) == 3
    assert result[0]["id"] == 1
    assert result[0]["content"] == "Chapter 1 translated to Portuguese"
    assert result[1]["id"] == 2
    assert result[1]["content"] == "Chapter 2 translated to Portuguese"
    assert result[2]["id"] == 3
    assert result[2]["content"] == "Chapter 3 translated to Portuguese"

@pytest.mark.asyncio
@patch("app.services.translation_service.AsyncOpenAI")
async def test_direct_translation(mock_openai_client):
    """Test direct text translation without rate limiting"""
    # Create a mock OpenAI client and response
    mock_client_instance = AsyncMock()
    mock_openai_client.return_value = mock_client_instance
    
    # Create a mock chat completions response
    mock_chat_completions = AsyncMock()
    mock_client_instance.chat = AsyncMock()
    mock_client_instance.chat.completions = AsyncMock()
    mock_client_instance.chat.completions.create = mock_chat_completions
    
    # Configure mock response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message = AsyncMock()
    mock_response.choices[0].message.content = "Contenu de test"
    mock_chat_completions.return_value = mock_response
    
    # Set up a mock environment
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        # Call translate_text directly
        result = await translate_text("Test content", "French")
        
        # Verify the result and that the API was called correctly
        assert result == "Contenu de test"
        mock_chat_completions.assert_called_once()
        call_args = mock_chat_completions.call_args[1]
        assert call_args["model"] == "gpt-4o-mini"
        assert call_args["temperature"] == 0.3
        assert len(call_args["messages"]) == 2
        assert "French" in call_args["messages"][0]["content"]
        assert call_args["messages"][1]["content"] == "Test content"

@pytest.mark.asyncio
@patch("app.services.translation_service.AsyncOpenAI")
async def test_error_handling(mock_openai_client):
    """Test error handling and retries in translation"""
    # Create a mock OpenAI client
    mock_client_instance = AsyncMock()
    mock_openai_client.return_value = mock_client_instance
    
    # Create a mock completion that raises an error
    mock_chat_completions = AsyncMock()
    mock_client_instance.chat = AsyncMock()
    mock_client_instance.chat.completions = AsyncMock()
    mock_client_instance.chat.completions.create = mock_chat_completions
    
    # Configure mock to raise an error
    error_message = "Test API error"
    mock_chat_completions.side_effect = Exception(error_message)
    
    # Set up a mock environment
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        # Attempt to translate with an error, with reduced retries for faster test
        with pytest.raises(RuntimeError) as excinfo:
            await translate_text("Test content", "German", max_retries=1)
        
        # Verify error handling
        assert "Translation error after 1 attempts" in str(excinfo.value)
        assert error_message in str(excinfo.value)
        
        # Verify the API was called expected number of times (initial + 1 retry)
        assert mock_chat_completions.call_count == 2 