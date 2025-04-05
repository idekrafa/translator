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
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Output directory
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    
    # Maximum pages per chapter
    MAX_PAGES_PER_CHAPTER: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"

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


# Create settings instance
settings = Settings()

# Create output directory if it doesn't exist
os.makedirs(settings.OUTPUT_DIR, exist_ok=True) 