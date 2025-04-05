from typing import List, Optional
from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """Schema representing a book chapter to be translated"""
    id: int
    content: str


class BookTranslationRequest(BaseModel):
    """Schema for book translation request"""
    chapters: List[Chapter]
    target_language: str = Field(..., description="Target language for translation")


class TranslationResponse(BaseModel):
    """Schema for translation response"""
    status: str
    message: str
    file_url: Optional[str] = None


class TranslationProgress(BaseModel):
    """Schema for translation progress updates"""
    status: str
    progress: float = Field(..., ge=0, le=1)
    current_chapter: int
    total_chapters: int
    message: str 