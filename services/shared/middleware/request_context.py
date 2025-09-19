"""Request context middleware for capturing request information."""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to capture request context for logging and tracing."""
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.tracer = trace.get_tracer(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Create span for the request
        with self.tracer.start_span(f"{request.method} {request.url.path}") as span:
            # Set span attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.route", request.url.path)
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("request.id", request_id)
            
            # Extract case_id and evidence_id from path parameters
            path_params = request.path_params
            if "case_id" in path_params:
                span.set_attribute("case.id", path_params["case_id"])
            if "evidence_id" in path_params:
                span.set_attribute("evidence.id", path_params["evidence_id"])
            if "storyboard_id" in path_params:
                span.set_attribute("storyboard.id", path_params["storyboard_id"])
            if "timeline_id" in path_params:
                span.set_attribute("timeline.id", path_params["timeline_id"])
            if "render_id" in path_params:
                span.set_attribute("render.id", path_params["render_id"])
            
            # Extract from query parameters
            query_params = request.query_params
            if "case_id" in query_params:
                span.set_attribute("case.id", query_params["case_id"])
            if "evidence_id" in query_params:
                span.set_attribute("evidence.id", query_params["evidence_id"])
            
            # Add request context to logging
            logger = logging.getLogger(__name__)
            
            # Create a custom log record with request context
            class RequestLogRecord(logging.LogRecord):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.request_id = request_id
                    self.route = request.url.path
                    self.service = self.service_name
            
            # Process request
            try:
                response = await call_next(request)
                
                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("latency.ms", latency_ms)
                
                # Log request completion
                logger.info(
                    f"{request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "route": request.url.path,
                        "latency": latency_ms,
                        "status_code": response.status_code,
                        "service": self.service_name
                    }
                )
                
                return response
                
            except Exception as e:
                # Calculate latency for failed requests
                latency_ms = (time.time() - start_time) * 1000
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.set_attribute("latency.ms", latency_ms)
                
                # Log request failure
                logger.error(
                    f"{request.method} {request.url.path} - ERROR: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "route": request.url.path,
                        "latency": latency_ms,
                        "error": str(e),
                        "service": self.service_name
                    },
                    exc_info=True
                )
                
                raise
