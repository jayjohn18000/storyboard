"""Storyboard Service main application."""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

from .parsers.bullet_parser import BulletParser
from .parsers.storydoc_parser import StoryDocParser
from .parsers.jsonl_parser import JSONLParser
from .validators.anchor_validator import AnchorValidator
from .validators.coverage_calculator import CoverageCalculator
from .validators.lint_engine import LintEngine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from services.shared.utils.monitoring import MonitoringSetup, MetricsCollector


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_evidence_processed(event):
    """Handle EvidenceProcessed events."""
    try:
        evidence_id = event.data.get("evidence_id")
        processing_results = event.data.get("processing_results", {})
        logger.info(f"Received EvidenceProcessed event for evidence {evidence_id}")
        
        # Create storyboard row linked to the case/evidence
        await create_storyboard_from_evidence(evidence_id, processing_results)
        
    except Exception as e:
        logger.error(f"Error handling EvidenceProcessed event: {e}")


async def create_storyboard_from_evidence(evidence_id: str, processing_results: Dict[str, Any]):
    """Create a storyboard row linked to the case/evidence."""
    try:
        from ..shared.db.session import get_db
        from ..shared.repositories.evidence import EvidenceRepository
        from ..shared.models.database_models import Storyboard
        from uuid import UUID, uuid4
        from datetime import datetime
        
        async with get_db() as session:
            evidence_repo = EvidenceRepository(session)
            evidence = await evidence_repo.get_with_relationships(UUID(evidence_id))
            
            if not evidence:
                logger.error(f"Evidence {evidence_id} not found for storyboard creation")
                return
            
            # Create storyboard row
            storyboard = Storyboard(
                id=uuid4(),
                case_id=evidence.case_id,
                title=f"Auto-generated storyboard for {evidence.filename}",
                description=f"Automatically created from processed evidence: {evidence.filename}",
                status="draft",
                created_by=evidence.uploaded_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                case_metadata={
                    "auto_generated": True,
                    "source_evidence_id": evidence_id,
                    "processing_results": processing_results
                },
                scenes=[]
            )
            
            session.add(storyboard)
            await session.commit()
            await session.refresh(storyboard)
            
            logger.info(f"Created storyboard {storyboard.id} for evidence {evidence_id}")
            
    except Exception as e:
        logger.error(f"Error creating storyboard for evidence {evidence_id}: {e}")


# Initialize monitoring
monitoring = MonitoringSetup(
    service_name=os.getenv("OTEL_SERVICE_NAME", "storyboard-service"),
    service_version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0")
)

# Initialize metrics collector
metrics = MetricsCollector("storyboard-service")

# Global service instances
bullet_parser = None
storydoc_parser = None
jsonl_parser = None
anchor_validator = None
coverage_calculator = None
lint_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global bullet_parser, storydoc_parser, jsonl_parser
    global anchor_validator, coverage_calculator, lint_engine
    
    # Startup
    logger.info("Starting Storyboard Service...")
    monitoring.initialize()
    
    # Initialize services
    try:
        # Initialize parsers
        bullet_parser = BulletParser()
        storydoc_parser = StoryDocParser()
        jsonl_parser = JSONLParser()
        logger.info("Parsers initialized")
        
        # Initialize validators
        anchor_validator = AnchorValidator()
        coverage_calculator = CoverageCalculator()
        lint_engine = LintEngine()
        logger.info("Validators initialized")
        
        # Initialize event bus and subscribe to events
        try:
            from ..shared.implementations.event_bus.redis_event_bus import get_event_bus
            from ..shared.interfaces.event_bus import EventType
            
            event_bus = await get_event_bus()
            await event_bus.subscribe(EventType.EVIDENCE_PROCESSED, handle_evidence_processed)
            logger.info("Event bus initialized and subscribed to EvidenceProcessed events")
            
        except Exception as e:
            logger.warning(f"Failed to initialize event bus: {e}")
        
        logger.info("Storyboard Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Storyboard Service...")


# Create FastAPI application
app = FastAPI(
    title="Storyboard Service",
    description="Service for parsing and validating storyboards",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "service": "storyboard-service",
        "time": datetime.utcnow().isoformat() + "Z",
        "parsers_available": all([bullet_parser, storydoc_parser, jsonl_parser]),
        "validators_available": all([anchor_validator, coverage_calculator, lint_engine]),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Storyboard Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/parse/bullet")
async def parse_bullet_points(request: dict):
    """Parse bullet point storyboard format."""
    try:
        bullet_text = request.get("bullet_text")
        if not bullet_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="bullet_text is required"
            )
        
        # Parse bullet points
        result = await bullet_parser.parse(bullet_text)
        
        # Record metrics
        metrics.record_storyboard_created("bullet_parse")
        
        return {
            "status": "parsed",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Bullet parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bullet parsing failed: {str(e)}"
        )


@app.post("/parse/storydoc")
async def parse_storydoc(request: dict):
    """Parse StoryDoc DSL format."""
    try:
        storydoc_text = request.get("storydoc_text")
        if not storydoc_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="storydoc_text is required"
            )
        
        # Parse StoryDoc
        result = await storydoc_parser.parse(storydoc_text)
        
        # Record metrics
        metrics.record_storyboard_created("storydoc_parse")
        
        return {
            "status": "parsed",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"StoryDoc parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"StoryDoc parsing failed: {str(e)}"
        )


@app.post("/parse/jsonl")
async def parse_jsonl(request: dict):
    """Parse JSONL storyboard format."""
    try:
        jsonl_data = request.get("jsonl_data")
        if not jsonl_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="jsonl_data is required"
            )
        
        # Parse JSONL
        result = await jsonl_parser.parse(jsonl_data)
        
        # Record metrics
        metrics.record_storyboard_created("jsonl_parse")
        
        return {
            "status": "parsed",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"JSONL parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"JSONL parsing failed: {str(e)}"
        )


@app.post("/validate/anchors")
async def validate_anchors(request: dict):
    """Validate evidence anchors in storyboard."""
    try:
        storyboard_data = request.get("storyboard_data")
        evidence_ids = request.get("evidence_ids", [])
        
        if not storyboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="storyboard_data is required"
            )
        
        # Validate anchors
        result = await anchor_validator.validate(storyboard_data, evidence_ids)
        
        # Record metrics
        metrics.record_storyboard_validation_duration(0.0, "anchor_validation")
        
        return {
            "status": "validated",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Anchor validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anchor validation failed: {str(e)}"
        )


@app.post("/validate/coverage")
async def validate_coverage(request: dict):
    """Validate evidence coverage in storyboard."""
    try:
        storyboard_data = request.get("storyboard_data")
        evidence_ids = request.get("evidence_ids", [])
        
        if not storyboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="storyboard_data is required"
            )
        
        # Validate coverage
        result = await coverage_calculator.calculate_coverage(storyboard_data, evidence_ids)
        
        # Record metrics
        metrics.record_storyboard_validation_duration(0.0, "coverage_validation")
        
        return {
            "status": "validated",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Coverage validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coverage validation failed: {str(e)}"
        )


@app.post("/validate/lint")
async def validate_lint(request: dict):
    """Lint storyboard for issues."""
    try:
        storyboard_data = request.get("storyboard_data")
        
        if not storyboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="storyboard_data is required"
            )
        
        # Lint storyboard
        result = await lint_engine.lint(storyboard_data)
        
        # Record metrics
        metrics.record_storyboard_validation_duration(0.0, "lint_validation")
        
        return {
            "status": "validated",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Lint validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lint validation failed: {str(e)}"
        )


@app.get("/formats")
async def get_supported_formats():
    """Get supported storyboard formats."""
    return {
        "supported_formats": [
            {
                "name": "bullet_points",
                "description": "Bullet point format",
                "example": "• Scene 1: Evidence display\n  - Show document A\n  - Highlight key text",
            },
            {
                "name": "storydoc",
                "description": "StoryDoc DSL format",
                "example": "scene evidence_display {\n  title: \"Evidence Display\"\n  duration: 5s\n  evidence: document_A\n}",
            },
            {
                "name": "jsonl",
                "description": "JSON Lines format",
                "example": "{\"scene_type\": \"evidence_display\", \"title\": \"Scene 1\", \"duration\": 5}",
            },
        ],
        "validation_rules": [
            "Evidence anchors must reference valid evidence IDs",
            "Scene durations must be positive",
            "Camera configurations must be valid",
            "Lighting configurations must be valid",
            "Material configurations must be valid",
        ]
    }


@app.get("/storyboards/{storyboard_id}")
async def get_storyboard(storyboard_id: str):
    """Get storyboard by ID."""
    try:
        from ..shared.db.session import get_db
        from ..shared.models.database_models import Storyboard
        from sqlalchemy import select
        from uuid import UUID
        
        async with get_db() as session:
            query = select(Storyboard).where(Storyboard.id == UUID(storyboard_id))
            result = await session.execute(query)
            storyboard = result.scalar_one_or_none()
            
            if not storyboard:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Storyboard not found: {storyboard_id}"
                )
            
            return {
                "storyboard_id": str(storyboard.id),
                "case_id": str(storyboard.case_id),
                "title": storyboard.title,
                "description": storyboard.description,
                "status": storyboard.status,
                "created_by": str(storyboard.created_by),
                "created_at": storyboard.created_at.isoformat() + "Z",
                "updated_at": storyboard.updated_at.isoformat() + "Z",
                "scenes": storyboard.scenes or [],
                "case_metadata": storyboard.case_metadata or {}
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get storyboard {storyboard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storyboard: {str(e)}"
        )


@app.get("/cases/{case_id}/storyboards")
async def get_case_storyboards(case_id: str, skip: int = 0, limit: int = 100):
    """Get storyboards for a case."""
    try:
        from ..shared.db.session import get_db
        from ..shared.models.database_models import Storyboard
        from sqlalchemy import select
        from uuid import UUID
        
        async with get_db() as session:
            query = (
                select(Storyboard)
                .where(Storyboard.case_id == UUID(case_id))
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(query)
            storyboards = result.scalars().all()
            
            storyboard_list = []
            for storyboard in storyboards:
                storyboard_list.append({
                    "storyboard_id": str(storyboard.id),
                    "case_id": str(storyboard.case_id),
                    "title": storyboard.title,
                    "description": storyboard.description,
                    "status": storyboard.status,
                    "created_by": str(storyboard.created_by),
                    "created_at": storyboard.created_at.isoformat() + "Z",
                    "updated_at": storyboard.updated_at.isoformat() + "Z",
                    "scenes": storyboard.scenes or [],
                    "case_metadata": storyboard.case_metadata or {}
                })
            
            return {
                "case_id": case_id,
                "storyboards": storyboard_list,
                "total": len(storyboard_list)
            }
        
    except Exception as e:
        logger.error(f"Failed to get storyboards for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storyboards: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    metrics.record_error("http_exception", "storyboard-service")
    
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
    metrics.record_error("unhandled_exception", "storyboard-service")
    
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
        port=int(os.getenv("API_PORT", "8002")),
        workers=int(os.getenv("API_WORKERS", "1")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
