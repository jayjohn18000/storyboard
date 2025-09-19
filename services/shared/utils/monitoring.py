"""Monitoring and observability utilities using OpenTelemetry."""

import os
from typing import Dict, Any, Optional
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
try:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
except ImportError:
    SQLAlchemyInstrumentor = None
from opentelemetry.instrumentation.redis import RedisInstrumentor
try:
    from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor
except ImportError:
    Boto3SQSInstrumentor = None
try:
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
except ImportError:
    Psycopg2Instrumentor = None
try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except ImportError:
    HTTPXClientInstrumentor = None
import logging


class MonitoringSetup:
    """Setup OpenTelemetry monitoring."""
    
    def __init__(self, service_name: str, service_version: str = "0.1.0"):
        self.service_name = service_name
        self.service_version = service_version
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize OpenTelemetry monitoring."""
        if self._initialized:
            return
        
        # Get configuration from environment
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        otlp_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.namespace": "legal-sim",
        })
        
        # Setup tracing
        self._setup_tracing(otlp_endpoint, otlp_headers, resource)
        
        # Setup metrics
        self._setup_metrics(otlp_endpoint, otlp_headers, resource)
        
        # Setup logging
        self._setup_logging()
        
        # Instrument libraries
        self._instrument_libraries()
        
        self._initialized = True
    
    def _setup_tracing(self, endpoint: str, headers: str, resource: Resource) -> None:
        """Setup OpenTelemetry tracing."""
        # Create span exporter
        span_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=self._parse_headers(headers),
        )
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Add span processor
        span_processor = BatchSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
    
    def _setup_metrics(self, endpoint: str, headers: str, resource: Resource) -> None:
        """Setup OpenTelemetry metrics."""
        # Create metric exporter
        metric_exporter = OTLPMetricExporter(
            endpoint=endpoint,
            headers=self._parse_headers(headers),
        )
        
        # Create metric reader
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=30000,  # 30 seconds
        )
        
        # Create meter provider
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader],
        )
        
        # Set global meter provider
        metrics.set_meter_provider(meter_provider)
    
    def _setup_logging(self) -> None:
        """Setup structured JSON logging."""
        import json
        import sys
        from datetime import datetime
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": record.levelname,
                    "service": self.service_name,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                
                # Add request context if available
                if hasattr(record, 'request_id'):
                    log_entry["request_id"] = record.request_id
                if hasattr(record, 'route'):
                    log_entry["route"] = record.route
                if hasattr(record, 'latency'):
                    log_entry["latency_ms"] = record.latency
                
                # Add exception info if present
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add JSON formatter to console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(console_handler)
    
    def _instrument_libraries(self) -> None:
        """Instrument common libraries."""
        try:
            FastAPIInstrumentor.instrument()
            RequestsInstrumentor.instrument()
            if SQLAlchemyInstrumentor:
                SQLAlchemyInstrumentor.instrument()
            RedisInstrumentor.instrument()
            if Boto3SQSInstrumentor:
                Boto3SQSInstrumentor.instrument()
            if Psycopg2Instrumentor:
                Psycopg2Instrumentor.instrument()
            if HTTPXClientInstrumentor:
                HTTPXClientInstrumentor.instrument()
        except Exception as e:
            logging.warning(f"Failed to instrument some libraries: {e}")
    
    def _parse_headers(self, headers_str: str) -> Optional[Dict[str, str]]:
        """Parse headers string into dictionary."""
        if not headers_str:
            return None
        
        headers = {}
        for header in headers_str.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()
        
        return headers


class MetricsCollector:
    """Collects application metrics."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.meter = metrics.get_meter(service_name)
        
        # Create metrics
        self._create_metrics()
    
    def _create_metrics(self) -> None:
        """Create application metrics."""
        # Evidence processing metrics
        self.evidence_processed = self.meter.create_counter(
            name="evidence_processed_total",
            description="Total number of evidence items processed",
        )
        
        self.evidence_processing_duration = self.meter.create_histogram(
            name="evidence_processing_duration_seconds",
            description="Duration of evidence processing",
        )
        
        # Storyboard metrics
        self.storyboards_created = self.meter.create_counter(
            name="storyboards_created_total",
            description="Total number of storyboards created",
        )
        
        self.storyboard_validation_duration = self.meter.create_histogram(
            name="storyboard_validation_duration_seconds",
            description="Duration of storyboard validation",
        )
        
        # Timeline metrics
        self.timelines_compiled = self.meter.create_counter(
            name="timelines_compiled_total",
            description="Total number of timelines compiled",
        )
        
        self.timeline_compilation_duration = self.meter.create_histogram(
            name="timeline_compilation_duration_seconds",
            description="Duration of timeline compilation",
        )
        
        # Render metrics
        self.renders_completed = self.meter.create_counter(
            name="renders_completed_total",
            description="Total number of renders completed",
        )
        
        self.render_duration = self.meter.create_histogram(
            name="render_duration_seconds",
            description="Duration of render operations",
        )
        
        self.render_queue_size = self.meter.create_gauge(
            name="render_queue_size",
            description="Current size of render queue",
        )
        
        # Evidence upload metrics
        self.evidence_uploaded = self.meter.create_counter(
            name="evidence_uploaded_total",
            description="Total number of evidence items uploaded",
        )
        
        self.evidence_committed = self.meter.create_counter(
            name="evidence_committed_total",
            description="Total number of evidence items committed",
        )
        
        # Error metrics
        self.errors_total = self.meter.create_counter(
            name="errors_total",
            description="Total number of errors",
        )
    
    def record_evidence_uploaded(self, file_size: int, content_type: str) -> None:
        """Record evidence upload."""
        self.evidence_uploaded.add(1, {"content_type": content_type, "size_category": self._get_size_category(file_size)})
    
    def record_evidence_committed(self, evidence_id: str) -> None:
        """Record evidence commit."""
        self.evidence_committed.add(1, {"evidence_id": evidence_id})
    
    def record_evidence_processed(self, evidence_type: str, success: bool) -> None:
        """Record evidence processing."""
        self.evidence_processed.add(1, {"type": evidence_type, "success": str(success)})
    
    def record_evidence_processing_duration(self, duration: float, evidence_type: str) -> None:
        """Record evidence processing duration."""
        self.evidence_processing_duration.record(duration, {"type": evidence_type})
    
    def record_storyboard_created(self, case_id: str) -> None:
        """Record storyboard creation."""
        self.storyboards_created.add(1, {"case_id": case_id})
    
    def record_storyboard_validation_duration(self, duration: float, case_id: str) -> None:
        """Record storyboard validation duration."""
        self.storyboard_validation_duration.record(duration, {"case_id": case_id})
    
    def record_timeline_compiled(self, storyboard_id: str) -> None:
        """Record timeline compilation."""
        self.timelines_compiled.add(1, {"storyboard_id": storyboard_id})
    
    def record_timeline_compilation_duration(self, duration: float, storyboard_id: str) -> None:
        """Record timeline compilation duration."""
        self.timeline_compilation_duration.record(duration, {"storyboard_id": storyboard_id})
    
    def record_render_completed(self, render_id: str, success: bool) -> None:
        """Record render completion."""
        self.renders_completed.add(1, {"render_id": render_id, "success": str(success)})
    
    def record_render_duration(self, duration: float, render_id: str) -> None:
        """Record render duration."""
        self.render_duration.record(duration, {"render_id": render_id})
    
    def update_render_queue_size(self, size: int) -> None:
        """Update render queue size."""
        self.render_queue_size.set(size)
    
    def record_error(self, error_type: str, service: str) -> None:
        """Record error occurrence."""
        self.errors_total.add(1, {"type": error_type, "service": service})
    
    def _get_size_category(self, file_size: int) -> str:
        """Get size category for file size."""
        if file_size < 1024 * 1024:  # < 1MB
            return "small"
        elif file_size < 10 * 1024 * 1024:  # < 10MB
            return "medium"
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return "large"
        else:
            return "very_large"


class TraceContext:
    """Context manager for tracing operations."""
    
    def __init__(self, operation_name: str, **attributes):
        self.operation_name = operation_name
        self.attributes = attributes
        self.tracer = trace.get_tracer(__name__)
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.operation_name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self.span.set_attribute("error", True)
            self.span.set_attribute("error.type", exc_type.__name__)
        else:
            self.span.set_status(trace.Status(trace.StatusCode.OK))
        
        self.span.end()


class ReadinessChecker:
    """Check service readiness by verifying dependencies."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(__name__)
    
    async def check_database(self) -> bool:
        """Check database connectivity."""
        with self.tracer.start_span("readiness.database_check") as span:
            try:
                # Import here to avoid circular imports
                from ..database import get_db
                async with get_db() as db:
                    # Simple query to test connectivity
                    await db.execute("SELECT 1")
                span.set_attribute("database.status", "healthy")
                return True
            except Exception as e:
                span.set_attribute("database.status", "unhealthy")
                span.set_attribute("database.error", str(e))
                return False
    
    async def check_redis(self) -> bool:
        """Check Redis connectivity."""
        with self.tracer.start_span("readiness.redis_check") as span:
            try:
                import redis.asyncio as redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                client = redis.from_url(redis_url)
                await client.ping()
                await client.close()
                span.set_attribute("redis.status", "healthy")
                return True
            except Exception as e:
                span.set_attribute("redis.status", "unhealthy")
                span.set_attribute("redis.error", str(e))
                return False
    
    async def check_external_services(self) -> Dict[str, bool]:
        """Check external service dependencies."""
        with self.tracer.start_span("readiness.external_services_check") as span:
            results = {}
            
            # Check each service endpoint
            services = ["evidence", "storyboard", "timeline", "render"]
            for service in services:
                try:
                    from ..config import get_service_url
                    from ..http_client import get_http_client
                    
                    url = get_service_url(service)
                    client = get_http_client()
                    
                    response = await client.request_json("GET", f"{url}/health", timeout=2)
                    results[service] = response.get("status") == "ok"
                    span.set_attribute(f"service.{service}.status", "healthy" if results[service] else "unhealthy")
                except Exception as e:
                    results[service] = False
                    span.set_attribute(f"service.{service}.status", "unhealthy")
                    span.set_attribute(f"service.{service}.error", str(e))
            
            return results
    
    async def is_ready(self) -> Dict[str, Any]:
        """Comprehensive readiness check."""
        with self.tracer.start_span("readiness.check") as span:
            span.set_attribute("service.name", self.service_name)
            
            db_ready = await self.check_database()
            redis_ready = await self.check_redis()
            external_services = await self.check_external_services()
            
            all_ready = db_ready and redis_ready and all(external_services.values())
            
            span.set_attribute("readiness.overall", all_ready)
            span.set_attribute("readiness.database", db_ready)
            span.set_attribute("readiness.redis", redis_ready)
            
            return {
                "ready": all_ready,
                "service": self.service_name,
                "checks": {
                    "database": db_ready,
                    "redis": redis_ready,
                    "external_services": external_services
                }
            }
