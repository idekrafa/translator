import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json
from uuid import uuid4

# Configure logging
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    
    Adds a request ID to each request and logs request/response details
    including timing information.
    """
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request started | {request_id} | {request.method} {request.url.path}"
        )
        
        # Process request and catch any exceptions
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(
                f"Request completed | {request_id} | {request.method} {request.url.path} | "
                f"Status: {response.status_code} | Time: {process_time:.4f}s"
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log exception details
            logger.error(
                f"Request failed | {request_id} | {request.method} {request.url.path} | "
                f"Error: {str(e)} | Time: {process_time:.4f}s"
            )
            
            # Return error response
            error_message = str(e)
            content = json.dumps({
                "detail": error_message,
                "request_id": request_id
            })
            
            return Response(
                content=content,
                status_code=500,
                media_type="application/json",
                headers={
                    "X-Process-Time": f"{process_time:.4f}",
                    "X-Request-ID": request_id
                }
            ) 