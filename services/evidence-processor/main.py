"""Evidence Processor Service main application."""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uvicorn
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional, Dict, Any

from .implementations.ocr.tesseract_local import TesseractLocalOCR
from .implementations.asr.whisperx_local import WhisperXLocalASR
from .pipelines.document_pipeline import DocumentPipeline
from .pipelines.audio_pipeline import AudioPipeline
from .pipelines.video_pipeline import VideoPipeline
from ..shared.utils.monitoring import MonitoringSetup, MetricsCollector, ReadinessChecker
from ..shared.factories.storage_factory import StorageFactory
from ..shared.factories.ocr_factory import OCRFactory
from ..shared.factories.asr_factory import ASRFactory
from ..shared.middleware.request_context import RequestContextMiddleware


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_evidence_uploaded(event):
    """Handle EvidenceUploaded events."""
    try:
        evidence_id = event.data.get("evidence_id")
        logger.info(f"Received EvidenceUploaded event for evidence {evidence_id}")
        
        # Process the evidence
        await process_evidence(evidence_id)
        
    except Exception as e:
        logger.error(f"Error handling EvidenceUploaded event: {e}")


async def process_evidence(evidence_id: str):
    """Process evidence and publish EvidenceProcessed event."""
    try:
        from ..shared.db.session import get_db
        from ..shared.repositories.evidence import EvidenceRepository
        from ..shared.implementations.event_bus.redis_event_bus import get_event_bus
        from ..shared.events.event_factory import EventFactory
        from uuid import UUID
        
        # Get evidence from database
        async with get_db() as session:
            evidence_repo = EvidenceRepository(session)
            evidence = await evidence_repo.get_with_relationships(UUID(evidence_id))
            
            if not evidence:
                logger.error(f"Evidence {evidence_id} not found for processing")
                return
            
            # Update status to processing
            await evidence_repo.update_evidence_status(UUID(evidence_id), "processing")
            
            # Run dummy analysis based on content type
            processing_results = await run_analysis(evidence)
            
            # Mark as processed with results
            await evidence_repo.mark_as_processed(UUID(evidence_id), processing_results)
            
            # Publish EvidenceProcessed event
            event_bus = await get_event_bus()
            event = EventFactory.create_evidence_processed(
                evidence_id=evidence_id,
                processing_results=processing_results,
                processing_time_ms=processing_results.get("processing_time_ms", 0)
            )
            await event_bus.publish(event)
            
            logger.info(f"Evidence {evidence_id} processed and EvidenceProcessed event published")
            
    except Exception as e:
        logger.error(f"Error processing evidence {evidence_id}: {e}")
        # Mark as failed
        try:
            async with get_db() as session:
                evidence_repo = EvidenceRepository(session)
                await evidence_repo.mark_as_failed(UUID(evidence_id), str(e))
        except Exception as db_error:
            logger.error(f"Failed to mark evidence as failed: {db_error}")


async def run_analysis(evidence) -> Dict[str, Any]:
    """Run analysis on evidence based on content type."""
    try:
        # Get file data from storage
        file_data = await storage_service.get_evidence(str(evidence.id))
        
        # Determine processing strategy based on content type
        content_type = evidence.mime_type.lower()
        
        if content_type.startswith('image/') or content_type == 'application/pdf':
            # Use document pipeline for images and PDFs
            result = await document_pipeline.process_document(str(evidence.id))
        elif content_type.startswith('audio/'):
            # Use audio pipeline for audio files
            result = await audio_pipeline.process_audio(str(evidence.id))
        elif content_type.startswith('video/'):
            # Use video pipeline for video files
            result = await video_pipeline.process_video(str(evidence.id))
        else:
            # Default processing for other file types
            result = {
                "text": f"File: {evidence.filename}",
                "entities": [],
                "confidence": {"overall": 0.8},
                "processing_time_ms": 100,
                "engine_used": "default"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed for evidence {evidence.id}: {e}")
        return {
            "text": "",
            "entities": [],
            "confidence": {"overall": 0.0, "error": str(e)},
            "processing_time_ms": 0,
            "engine_used": "error"
        }


# Initialize monitoring
monitoring = MonitoringSetup(
    service_name=os.getenv("OTEL_SERVICE_NAME", "evidence-processor"),
    service_version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0")
)

# Initialize metrics collector
metrics = MetricsCollector("evidence-processor")

# Initialize readiness checker
readiness_checker = ReadinessChecker("evidence-processor")

# Global service instances
storage_service = None
ocr_service = None
asr_service = None
document_pipeline = None
audio_pipeline = None
video_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global storage_service, ocr_service, asr_service
    global document_pipeline, audio_pipeline, video_pipeline
    
    # Startup
    logger.info("Starting Evidence Processor Service...")
    monitoring.initialize()
    
    # Initialize services
    try:
        # Initialize storage service
        env_config = {key: value for key, value in os.environ.items()}
        storage_service = StorageFactory.create_from_env(env_config)
        logger.info("Storage service initialized")
        
        # Initialize OCR service
        ocr_service = OCRFactory.create_from_env(env_config)
        logger.info("OCR service initialized")
        
        # Initialize ASR service
        asr_service = ASRFactory.create_from_env(env_config)
        logger.info("ASR service initialized")
        
        # Initialize pipelines
        document_pipeline = DocumentPipeline(storage_service, ocr_service)
        audio_pipeline = AudioPipeline(storage_service, asr_service)
        video_pipeline = VideoPipeline(storage_service, ocr_service, asr_service)
        logger.info("Processing pipelines initialized")
        
        # Initialize event bus and subscribe to events
        try:
            from ..shared.implementations.event_bus.redis_event_bus import get_event_bus
            from ..shared.interfaces.event_bus import EventType
            
            event_bus = await get_event_bus()
            await event_bus.subscribe(EventType.EVIDENCE_UPLOADED, handle_evidence_uploaded)
            logger.info("Event bus initialized and subscribed to EvidenceUploaded events")
            
        except Exception as e:
            logger.warning(f"Failed to initialize event bus: {e}")
        
        logger.info("Evidence Processor Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Evidence Processor Service...")


# Create FastAPI application
app = FastAPI(
    title="Evidence Processor Service",
    description="Service for processing evidence files with OCR and ASR",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add request context middleware
app.add_middleware(RequestContextMiddleware, service_name="evidence-processor")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "service": "evidence-processor",
        "time": datetime.utcnow().isoformat() + "Z",
        "storage_available": storage_service is not None,
        "ocr_available": ocr_service is not None,
        "asr_available": asr_service is not None,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    readiness_status = await readiness_checker.is_ready()
    
    if not readiness_status["ready"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=readiness_status
        )
    
    return readiness_status


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Evidence Processor Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/process/document")
async def process_document(request: dict):
    """Process document evidence."""
    try:
        evidence_id = request.get("evidence_id")
        if not evidence_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="evidence_id is required"
            )
        
        # Process document
        result = await document_pipeline.process_document(evidence_id)
        
        # Record metrics
        metrics.record_evidence_processed("document", True)
        
        return {
            "evidence_id": evidence_id,
            "status": "processed",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        metrics.record_evidence_processed("document", False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@app.post("/process/audio")
async def process_audio(request: dict):
    """Process audio evidence."""
    try:
        evidence_id = request.get("evidence_id")
        if not evidence_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="evidence_id is required"
            )
        
        # Process audio
        result = await audio_pipeline.process_audio(evidence_id)
        
        # Record metrics
        metrics.record_evidence_processed("audio", True)
        
        return {
            "evidence_id": evidence_id,
            "status": "processed",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        metrics.record_evidence_processed("audio", False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio processing failed: {str(e)}"
        )


@app.post("/process/video")
async def process_video(request: dict):
    """Process video evidence."""
    try:
        evidence_id = request.get("evidence_id")
        if not evidence_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="evidence_id is required"
            )
        
        # Process video
        result = await video_pipeline.process_video(evidence_id)
        
        # Record metrics
        metrics.record_evidence_processed("video", True)
        
        return {
            "evidence_id": evidence_id,
            "status": "processed",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        metrics.record_evidence_processed("video", False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing failed: {str(e)}"
        )


@app.get("/status/{evidence_id}")
async def get_processing_status(evidence_id: str):
    """Get processing status for evidence."""
    try:
        # TODO: Get status from database or cache
        return {
            "evidence_id": evidence_id,
            "status": "processed",
            "progress": 100,
        }
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@app.post("/evidence/upload")
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: str = Form("{}"),  # JSON string
):
    """Upload evidence file with SHA256 hashing and validation."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Read file data
        file_data = await file.read()
        
        # Check file size limit
        max_size_mb = int(os.getenv("MAX_UPLOAD_MB", "100"))
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if len(file_data) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds limit of {max_size_mb}MB"
            )
        
        # Calculate SHA256 hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Detect MIME type
        content_type = file.content_type
        if not content_type:
            content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                content_type = "application/octet-stream"
        
        # Parse tags
        import json
        try:
            tags_dict = json.loads(tags) if tags else {}
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tags JSON format"
            )
        
        # Create metadata
        metadata = {
            "filename": file.filename,
            "content_type": content_type,
            "size_bytes": len(file_data),
            "case_id": case_id,
            "description": description or "",
            "tags": tags_dict,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        
        # Generate evidence ID (use hash for deduplication)
        evidence_id = file_hash[:16]  # Use first 16 chars of hash as ID
        
        # Store file using content-addressed path
        object_id = await storage_service.store_evidence(
            file_data=file_data,
            metadata=metadata,
            evidence_id=evidence_id
        )
        
        # Store evidence in database
        from ..shared.db.session import get_db
        from ..shared.repositories.evidence import EvidenceRepository
        from ..shared.models.database_models import Evidence
        from uuid import UUID
        
        async with get_db() as session:
            evidence_repo = EvidenceRepository(session)
            
            # Create evidence record
            evidence_record = Evidence(
                id=UUID(evidence_id),
                case_id=UUID(case_id) if case_id else None,
                filename=file.filename,
                file_path=f"/data/evidence/{file_hash[:2]}/{file_hash}",
                file_size=len(file_data),
                mime_type=content_type,
                file_hash=file_hash,
                status="uploaded",
                uploaded_by=UUID("00000000-0000-0000-0000-000000000001"),  # TODO: Get from auth
                case_metadata=tags_dict
            )
            
            session.add(evidence_record)
            await session.commit()
            await session.refresh(evidence_record)
        
        # Record metrics
        metrics.record_evidence_uploaded(len(file_data), content_type)
        
        # Publish EvidenceUploaded event
        try:
            from ..shared.implementations.event_bus.redis_event_bus import get_event_bus
            from ..shared.events.event_factory import EventFactory
            
            event_bus = await get_event_bus()
            event = EventFactory.create_evidence_uploaded(
                evidence_id=evidence_id,
                case_id=case_id,
                filename=file.filename,
                file_size=len(file_data),
                content_type=content_type,
                uploaded_by="system"  # TODO: Get from auth context
            )
            await event_bus.publish(event)
            logger.info(f"Published EvidenceUploaded event for {evidence_id}")
            
        except Exception as e:
            logger.warning(f"Failed to publish EvidenceUploaded event: {e}")
        
        return {
            "evidence_id": evidence_id,
            "object_id": object_id,
            "file_hash": file_hash,
            "filename": file.filename,
            "content_type": content_type,
            "size_bytes": len(file_data),
            "status": "uploaded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evidence upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@app.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    """Get evidence file by ID."""
    try:
        from ..shared.db.session import get_db
        from ..shared.repositories.evidence import EvidenceRepository
        from uuid import UUID
        
        async with get_db() as session:
            evidence_repo = EvidenceRepository(session)
            
            # Get evidence from database
            evidence = await evidence_repo.get_with_relationships(UUID(evidence_id))
            
            if not evidence:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evidence not found: {evidence_id}"
                )
            
            return {
                "evidence_id": str(evidence.id),
                "filename": evidence.filename,
                "content_type": evidence.mime_type,
                "size_bytes": evidence.file_size,
                "checksum": evidence.file_hash,
                "created_at": evidence.uploaded_at.isoformat() + "Z",
                "worm_locked": evidence.status == "locked",
                "case_id": str(evidence.case_id),
                "status": evidence.status,
                "uploaded_by": str(evidence.uploaded_by),
                "processing_results": evidence.processing_results
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evidence {evidence_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence not found: {evidence_id}"
        )


@app.post("/evidence/{evidence_id}/commit")
async def commit_evidence(evidence_id: str):
    """Commit evidence and apply WORM lock."""
    try:
        from ..shared.db.session import get_db
        from ..shared.repositories.evidence import EvidenceRepository
        from ..shared.models.database_models import ChainOfCustody, EvidenceLock
        from sqlalchemy import select
        from uuid import UUID
        from datetime import datetime
        
        async with get_db() as session:
            evidence_repo = EvidenceRepository(session)
            
            # Get evidence from database
            evidence = await evidence_repo.get_with_relationships(UUID(evidence_id))
            
            if not evidence:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evidence not found: {evidence_id}"
                )
            
            # Check if already locked
            existing_lock = await session.execute(
                select(EvidenceLock).where(EvidenceLock.evidence_id == UUID(evidence_id))
            )
            if existing_lock.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Evidence is already committed and locked"
                )
            
            # Apply WORM lock to storage
            await storage_service.ensure_worm_lock(evidence_id)
            
            # Create evidence lock record
            evidence_lock = EvidenceLock(
                evidence_id=UUID(evidence_id),
                immutable_at=datetime.utcnow(),
                locked_by=evidence.uploaded_by,  # TODO: Get from auth context
                lock_reason="Evidence committed for legal proceedings"
            )
            session.add(evidence_lock)
            
            # Record chain of custody entry
            custody_entry = ChainOfCustody(
                evidence_id=UUID(evidence_id),
                action="LOCKED_WORM",
                actor="system",  # TODO: Get from auth context
                timestamp=datetime.utcnow(),
                metadata={"reason": "Evidence committed", "immutable_at": evidence_lock.immutable_at.isoformat()}
            )
            session.add(custody_entry)
            
            # Update evidence status
            await evidence_repo.update_evidence_status(UUID(evidence_id), "locked")
            
            await session.commit()
            
            # Record metrics
            metrics.record_evidence_committed(evidence_id)
            
            return {
                "evidence_id": evidence_id,
                "status": "committed",
                "immutable_at": evidence_lock.immutable_at.isoformat() + "Z",
                "locked_by": str(evidence_lock.locked_by),
                "lock_reason": evidence_lock.lock_reason
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to commit evidence {evidence_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit evidence: {str(e)}"
        )


@app.get("/evidence")
async def list_evidence(
    skip: int = 0,
    limit: int = 100,
    case_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    mime_type_filter: Optional[str] = None
):
    """List evidence with optional filtering."""
    try:
        from ..shared.db.session import get_db
        from ..shared.repositories.evidence import EvidenceRepository
        from uuid import UUID
        
        async with get_db() as session:
            evidence_repo = EvidenceRepository(session)
            
            # Build filters
            filters = {}
            if case_id:
                filters["case_id"] = UUID(case_id)
            if status_filter:
                filters["status"] = status_filter
            if mime_type_filter:
                filters["mime_type"] = mime_type_filter
            
            # Get evidence from database
            evidence_list = await evidence_repo.get_multi(
                skip=skip,
                limit=limit,
                **filters
            )
            
            # Convert to response format
            evidence_data = []
            for evidence in evidence_list:
                evidence_data.append({
                    "evidence_id": str(evidence.id),
                    "filename": evidence.filename,
                    "content_type": evidence.mime_type,
                    "size_bytes": evidence.file_size,
                    "checksum": evidence.file_hash,
                    "created_at": evidence.uploaded_at.isoformat() + "Z",
                    "worm_locked": evidence.status == "locked",
                    "case_id": str(evidence.case_id),
                    "status": evidence.status
                })
            
            return {
                "evidence": evidence_data,
                "total_count": len(evidence_data),
                "skip": skip,
                "limit": limit
            }
        
    except Exception as e:
        logger.error(f"Failed to list evidence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list evidence: {str(e)}"
        )


@app.get("/evidence/{evidence_id}/download")
async def download_evidence(evidence_id: str):
    """Download evidence file by ID."""
    try:
        from ..shared.db.session import get_db
        from ..shared.repositories.evidence import EvidenceRepository
        from uuid import UUID
        
        async with get_db() as session:
            evidence_repo = EvidenceRepository(session)
            
            # Get evidence from database
            evidence = await evidence_repo.get_with_relationships(UUID(evidence_id))
            
            if not evidence:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evidence not found: {evidence_id}"
                )
            
            # Get file data from storage
            try:
                file_data = await storage_service.get_evidence(evidence_id)
            except Exception as storage_error:
                logger.error(f"Failed to retrieve file from storage: {storage_error}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found in storage"
                )
            
            # Return file data with proper headers
            from fastapi.responses import Response
            
            return Response(
                content=file_data,
                media_type=evidence.mime_type,
                headers={
                    "Content-Disposition": f"attachment; filename=\"{evidence.filename}\"",
                    "Content-Length": str(len(file_data)),
                    "X-Evidence-ID": evidence_id,
                    "X-File-Hash": evidence.file_hash
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download evidence {evidence_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download evidence: {str(e)}"
        )


@app.get("/engines")
async def get_available_engines():
    """Get available processing engines."""
    return {
        "ocr_engines": [
            "tesseract_local",
            "tesseract_distributed",
            "ocrmypdf",
            "paddleocr",
        ],
        "asr_engines": [
            "whisperx_local",
            "whisperx_gpu",
            "whisperx_distributed",
            "pyannote_diarizer",
        ],
        "supported_formats": {
            "documents": ["pdf", "doc", "docx", "txt", "rtf"],
            "images": ["jpg", "jpeg", "png", "tiff", "bmp"],
            "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
            "video": ["mp4", "avi", "mov", "mkv", "webm"],
        }
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    metrics.record_error("http_exception", "evidence-processor")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    metrics.record_error("unhandled_exception", "evidence-processor")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url),
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8001")),
        workers=int(os.getenv("API_WORKERS", "1")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
