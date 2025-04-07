from pydantic import BaseModel, Field
from typing import Optional


class Chapter(BaseModel):
    """Representation of a book chapter"""
    id: int = Field(..., description="The Chapter ID")
    content: str = Field(..., description="The chapter content")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "content": "Once upon a time in a land far away..."
            }
        } 