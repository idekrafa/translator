import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from app.core.config import settings
from app.core.middleware import LoggingMiddleware
from app.api.translation_routes import router as translation_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events:
    - On startup: Set up resources like output directory
    - On shutdown: Clean up resources
    """
    # Startup: Create output directory if it doesn't exist
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    logger.info(f"Created output directory: {settings.OUTPUT_DIR}")
    
    # Set OpenAI API key globally
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    
    # Log application startup
    logger.info(f"Starting {settings.PROJECT_NAME}")
    
    yield
    
    # Shutdown: Log application shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para tradução e formatação de livros",
    version="0.1.0",
    lifespan=lifespan,
)


# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add routers
app.include_router(translation_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning basic API information"""
    return JSONResponse(
        content={
            "message": f"Bem-vindo à {settings.PROJECT_NAME}",
            "version": "0.1.0",
            "docs_url": "/docs",
        }
    )


# Not found handler
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    """Custom 404 exception handler"""
    return JSONResponse(
        status_code=404,
        content={"message": f"Endpoint não encontrado: {request.url.path}"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    ) 