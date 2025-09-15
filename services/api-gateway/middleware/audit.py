"""Audit middleware for API Gateway."""

import json
import time
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import logging

from ...shared.utils.monitoring import MetricsCollector


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit middleware for logging API requests and responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("audit")
        self.metrics = MetricsCollector("api-gateway")
        self.excluded_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through audit middleware."""
        # Skip audit for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Record request start time
        start_time = time.time()
        
        # Extract request information
        request_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_id": getattr(request.state, "user_id", None),
            "user_roles": getattr(request.state, "user_roles", []),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_id": request.headers.get("x-request-id"),
        }
        
        # Log request
        self.logger.info(f"API Request: {json.dumps(request_info)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Extract response information
            response_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "response_size_bytes": len(response.body) if hasattr(response, 'body') else 0,
            }
            
            # Log response
            self.logger.info(f"API Response: {json.dumps(response_info)}")
            
            # Record metrics
            self._record_metrics(request, response, processing_time)
            
            # Add audit headers to response
            response.headers["X-Processing-Time"] = str(processing_time)
            response.headers["X-Request-ID"] = request_info.get("request_id", "")
            
            return response
            
        except Exception as e:
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log error
            error_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time_ms": round(processing_time * 1000, 2),
            }
            
            self.logger.error(f"API Error: {json.dumps(error_info)}")
            
            # Record error metrics
            self.metrics.record_error("api_error", "api-gateway")
            
            # Re-raise exception
            raise
    
    def _record_metrics(self, request: Request, response: Response, processing_time: float):
        """Record metrics for request/response."""
        # Record request metrics
        if request.url.path.startswith("/api/v1/cases"):
            self.metrics.record_evidence_processed("case_request", response.status_code < 400)
        elif request.url.path.startswith("/api/v1/evidence"):
            self.metrics.record_evidence_processed("evidence_request", response.status_code < 400)
        elif request.url.path.startswith("/api/v1/storyboards"):
            self.metrics.record_storyboard_created("storyboard_request")
        elif request.url.path.startswith("/api/v1/renders"):
            self.metrics.record_render_completed("render_request", response.status_code < 400)
        
        # Record processing time
        if processing_time > 1.0:  # Log slow requests
            self.logger.warning(f"Slow request: {request.method} {request.url.path} took {processing_time:.2f}s")


class AuditLogger:
    """Audit logger for specific operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
    
    def log_evidence_upload(self, user_id: str, evidence_id: str, filename: str, size_bytes: int):
        """Log evidence upload."""
        self.logger.info(json.dumps({
            "event": "evidence_upload",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "evidence_id": evidence_id,
            "filename": filename,
            "size_bytes": size_bytes,
        }))
    
    def log_evidence_processing(self, evidence_id: str, status: str, processing_time_ms: int):
        """Log evidence processing."""
        self.logger.info(json.dumps({
            "event": "evidence_processing",
            "timestamp": datetime.utcnow().isoformat(),
            "evidence_id": evidence_id,
            "status": status,
            "processing_time_ms": processing_time_ms,
        }))
    
    def log_storyboard_creation(self, user_id: str, storyboard_id: str, case_id: str):
        """Log storyboard creation."""
        self.logger.info(json.dumps({
            "event": "storyboard_creation",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "storyboard_id": storyboard_id,
            "case_id": case_id,
        }))
    
    def log_storyboard_validation(self, storyboard_id: str, status: str, validation_time_ms: int):
        """Log storyboard validation."""
        self.logger.info(json.dumps({
            "event": "storyboard_validation",
            "timestamp": datetime.utcnow().isoformat(),
            "storyboard_id": storyboard_id,
            "status": status,
            "validation_time_ms": validation_time_ms,
        }))
    
    def log_render_creation(self, user_id: str, render_id: str, case_id: str, quality: str):
        """Log render creation."""
        self.logger.info(json.dumps({
            "event": "render_creation",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "render_id": render_id,
            "case_id": case_id,
            "quality": quality,
        }))
    
    def log_render_completion(self, render_id: str, status: str, render_time_seconds: float):
        """Log render completion."""
        self.logger.info(json.dumps({
            "event": "render_completion",
            "timestamp": datetime.utcnow().isoformat(),
            "render_id": render_id,
            "status": status,
            "render_time_seconds": render_time_seconds,
        }))
    
    def log_worm_lock(self, user_id: str, evidence_id: str, action: str):
        """Log WORM lock operations."""
        self.logger.info(json.dumps({
            "event": "worm_lock",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "evidence_id": evidence_id,
            "action": action,
        }))
    
    def log_case_export(self, user_id: str, case_id: str, export_id: str, format: str):
        """Log case export."""
        self.logger.info(json.dumps({
            "event": "case_export",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "case_id": case_id,
            "export_id": export_id,
            "format": format,
        }))
    
    def log_security_event(self, event_type: str, user_id: str, details: dict):
        """Log security events."""
        self.logger.warning(json.dumps({
            "event": "security_event",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        }))
    
    def log_determinism_check(self, render_id: str, status: str, checksum_match: bool):
        """Log determinism check results."""
        self.logger.info(json.dumps({
            "event": "determinism_check",
            "timestamp": datetime.utcnow().isoformat(),
            "render_id": render_id,
            "status": status,
            "checksum_match": checksum_match,
        }))
