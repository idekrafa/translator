"""
Book Translation API - Main application
"""
import os
import logging
import sys
import tempfile
from contextlib import asynccontextmanager
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import LoggingMiddleware
from app.api.translation_routes import translation_router
from app.api.file_upload_routes import upload_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Application version
__version__ = "0.1.0"

# App state and lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    Handles initialization and cleanup of resources.
    """
    # Create temp directory for uploads on startup
    temp_dir = os.path.join(os.getcwd(), "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Created temp directory for uploads: {temp_dir}")
    
    # Allow application to run
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title="Book Translation API",
    description="API for translating books and PDFs",
    version=__version__,
    lifespan=lifespan
)

# Set up middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(translation_router)
app.include_router(upload_router)

# Root endpoint for API info
@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "api_name": "Book Translation API",
        "version": __version__,
        "status": "running"
    }

# Custom 404 handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    """Custom 404 handler with more helpful message"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Endpoint not found: {request.url.path}",
            "available_endpoints": [
                "/api/translation/translate",
                "/api/translation/status/{job_id}",
                "/api/translation/download/{job_id}",
                "/api/upload/pdf"
            ]
        }
    )

def create_app() -> FastAPI:
    """
    Factory function to create the FastAPI application.
    Useful for testing and alternative deployment methods.
    """
    return app

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the API server.
    This function is used by the console script entry point.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        reload: Whether to enable auto-reload for development
    """
    # Check if port is available; if not, try next port
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
    except socket.error:
        # Port is not available, try next port
        logger.warning(f"Port {port} is already in use. Trying port {port + 1}")
        port += 1
    finally:
        s.close()
        
    # Start server
    logger.info(f"Starting server at http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)

# Run the app with uvicorn when script is executed directly
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "").lower() in ("1", "true", "yes")
    start_server(port=port, reload=reload) 