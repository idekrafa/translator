import os
from typing import Dict, List, Any, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Tradutor de Livros API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # OpenAI API
    OPENAI_API_KEY: str = ""
    
    # Server settings
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    RELOAD: bool = False
    
    # Application settings
    USE_BACKGROUND_TASKS: int = 1
    MAX_FILE_SIZE: int = 10485760  # 10MB in bytes
    MAX_CHAPTERS: int = 100
    
    # Output directory
    OUTPUT_DIR: str = "output"
    
    # Maximum pages per chapter
    MAX_PAGES_PER_CHAPTER: int = 10

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, list):
            return v
        return v
        
    @field_validator("OPENAI_API_KEY")
    def check_openai_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError("OPENAI_API_KEY is not set. Please set it in the .env file.")
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"  # Allow extra fields to prevent validation errors


# Create settings instance
settings = Settings()

# Create output directory if it doesn't exist
os.makedirs(settings.OUTPUT_DIR, exist_ok=True) 