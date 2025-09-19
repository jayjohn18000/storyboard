#!/usr/bin/env python3
"""
Simplified API Gateway for testing frontend-to-backend pipeline.
This version uses real services and database connections.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional

# Import shared services
from services.shared.database import get_db_session
from services.shared.services.database_service import DatabaseService
from services.shared.services.evidence_service import EvidenceService
from services.shared.services.render_service import RenderService
from services.shared.config import get_config

# Create FastAPI application
app = FastAPI(
    title="Legal Simulation API Gateway",
    description="API Gateway with real service integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get configuration
config = get_config()

# Add CORS middleware with environment-based origins
cors_origins = config.get("CORS_ORIGINS", "http://localhost:3002,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "api-gateway",
        "version": "0.1.0",
        "message": "Simplified API Gateway is running"
    }

# Service dependencies
async def get_database_service():
    """Get database service instance."""
    db_session = get_db_session()
    return DatabaseService(db_session)

async def get_evidence_service():
    """Get evidence service instance."""
    db_service = await get_database_service()
    return EvidenceService(db_service)

async def get_render_service():
    """Get render service instance."""
    db_service = await get_database_service()
    return RenderService(db_service)

# Cases API endpoints
@app.get("/api/v1/cases")
async def get_cases(db_service: DatabaseService = Depends(get_database_service)):
    """Get all cases."""
    try:
        cases = await db_service.list_cases(skip=0, limit=100)
        return [
            {
                "id": str(case.id),
                "title": case.title,
                "status": case.status,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
                "created_by": case.created_by,
                "metadata": case.metadata,
                "evidence_ids": case.evidence_ids or [],
                "storyboard_ids": case.storyboard_ids or [],
                "render_ids": case.render_ids or []
            }
            for case in cases
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cases: {str(e)}")

@app.get("/api/v1/cases/{case_id}")
async def get_case(case_id: str, db_service: DatabaseService = Depends(get_database_service)):
    """Get a specific case."""
    try:
        case = await db_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
        return {
            "id": str(case.id),
            "title": case.title,
            "status": case.status,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
            "created_by": case.created_by,
            "metadata": case.metadata,
            "evidence_ids": case.evidence_ids or [],
            "storyboard_ids": case.storyboard_ids or [],
            "render_ids": case.render_ids or []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve case: {str(e)}")

# Evidence API endpoints
@app.get("/api/v1/evidence")
async def get_evidence(evidence_service: EvidenceService = Depends(get_evidence_service)):
    """Get all evidence."""
    try:
        evidence_list = await evidence_service.list_evidence(skip=0, limit=100)
        return [
            {
                "id": evidence.id,
                "filename": evidence.metadata.filename,
                "content_type": evidence.metadata.content_type,
                "size_bytes": evidence.metadata.size_bytes,
                "checksum": evidence.metadata.checksum,
                "created_at": evidence.metadata.created_at.isoformat(),
                "worm_locked": evidence.worm_locked,
                "case_id": evidence.case_id,
                "status": evidence.status.value,
                "uploaded_by": evidence.metadata.uploaded_by,
                "processing_results": evidence.processing_result.to_dict() if evidence.processing_result else None
            }
            for evidence in evidence_list
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evidence: {str(e)}")

@app.get("/api/v1/evidence/{evidence_id}")
async def get_evidence_by_id(evidence_id: str, evidence_service: EvidenceService = Depends(get_evidence_service)):
    """Get specific evidence."""
    try:
        evidence = await evidence_service.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return {
            "id": evidence.id,
            "filename": evidence.metadata.filename,
            "content_type": evidence.metadata.content_type,
            "size_bytes": evidence.metadata.size_bytes,
            "checksum": evidence.metadata.checksum,
            "created_at": evidence.metadata.created_at.isoformat(),
            "worm_locked": evidence.worm_locked,
            "case_id": evidence.case_id,
            "status": evidence.status.value,
            "uploaded_by": evidence.metadata.uploaded_by,
            "processing_results": evidence.processing_result.to_dict() if evidence.processing_result else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evidence: {str(e)}")

# Storyboards API endpoints
@app.get("/api/v1/storyboards")
async def get_storyboards(db_service: DatabaseService = Depends(get_database_service)):
    """Get all storyboards."""
    try:
        storyboards = await db_service.list_storyboards(skip=0, limit=100)
        return [
            {
                "id": str(storyboard.id),
                "case_id": storyboard.case_id,
                "title": storyboard.title,
                "content": storyboard.content,
                "created_at": storyboard.created_at.isoformat(),
                "updated_at": storyboard.updated_at.isoformat(),
                "created_by": storyboard.created_by,
                "validation_result": storyboard.validation_result
            }
            for storyboard in storyboards
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve storyboards: {str(e)}")

@app.get("/api/v1/storyboards/{storyboard_id}")
async def get_storyboard(storyboard_id: str, db_service: DatabaseService = Depends(get_database_service)):
    """Get specific storyboard."""
    try:
        storyboard = await db_service.get_storyboard(storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found")
        
        return {
            "id": str(storyboard.id),
            "case_id": storyboard.case_id,
            "title": storyboard.title,
            "content": storyboard.content,
            "created_at": storyboard.created_at.isoformat(),
            "updated_at": storyboard.updated_at.isoformat(),
            "created_by": storyboard.created_by,
            "validation_result": storyboard.validation_result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve storyboard: {str(e)}")

# Renders API endpoints
@app.get("/api/v1/renders")
async def get_renders(render_service: RenderService = Depends(get_render_service)):
    """Get all renders."""
    try:
        renders = await render_service.list_renders(skip=0, limit=100)
        return [
            {
                "id": str(render.id),
                "case_id": render.case_id,
                "storyboard_id": render.storyboard_id,
                "timeline_id": render.timeline_id,
                "status": render.status.value,
                "priority": render.priority,
                "created_by": render.created_by,
                "created_at": render.created_at.isoformat(),
                "started_at": render.started_at.isoformat() if render.started_at else None,
                "completed_at": render.completed_at.isoformat() if render.completed_at else None,
                "width": render.width,
                "height": render.height,
                "fps": render.fps,
                "quality": render.quality,
                "profile": render.profile,
                "deterministic": render.deterministic,
                "output_format": render.output_format,
                "output_path": render.output_path,
                "file_size_bytes": render.file_size_bytes,
                "duration_seconds": render.duration_seconds,
                "render_time_seconds": render.render_time_seconds,
                "frames_rendered": render.frames_rendered,
                "total_frames": render.total_frames,
                "progress_percentage": render.progress_percentage,
                "error_message": render.error_message,
                "retry_count": render.retry_count,
                "max_retries": render.max_retries,
                "checksum": render.checksum,
                "golden_frame_checksums": render.golden_frame_checksums
            }
            for render in renders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve renders: {str(e)}")

@app.get("/api/v1/renders/{render_id}")
async def get_render(render_id: str, render_service: RenderService = Depends(get_render_service)):
    """Get specific render."""
    try:
        render = await render_service.get_render(render_id)
    if not render:
        raise HTTPException(status_code=404, detail="Render not found")
        
        return {
            "id": str(render.id),
            "case_id": render.case_id,
            "storyboard_id": render.storyboard_id,
            "timeline_id": render.timeline_id,
            "status": render.status.value,
            "priority": render.priority,
            "created_by": render.created_by,
            "created_at": render.created_at.isoformat(),
            "started_at": render.started_at.isoformat() if render.started_at else None,
            "completed_at": render.completed_at.isoformat() if render.completed_at else None,
            "width": render.width,
            "height": render.height,
            "fps": render.fps,
            "quality": render.quality,
            "profile": render.profile,
            "deterministic": render.deterministic,
            "output_format": render.output_format,
            "output_path": render.output_path,
            "file_size_bytes": render.file_size_bytes,
            "duration_seconds": render.duration_seconds,
            "render_time_seconds": render.render_time_seconds,
            "frames_rendered": render.frames_rendered,
            "total_frames": render.total_frames,
            "progress_percentage": render.progress_percentage,
            "error_message": render.error_message,
            "retry_count": render.retry_count,
            "max_retries": render.max_retries,
            "checksum": render.checksum,
            "golden_frame_checksums": render.golden_frame_checksums
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve render: {str(e)}")

@app.get("/api/v1/cases/{case_id}/renders")
async def get_case_renders(case_id: str, render_service: RenderService = Depends(get_render_service)):
    """Get renders for a specific case."""
    try:
        renders = await render_service.list_renders_by_case(case_id)
        return [
            {
                "id": str(render.id),
                "case_id": render.case_id,
                "storyboard_id": render.storyboard_id,
                "timeline_id": render.timeline_id,
                "status": render.status.value,
                "priority": render.priority,
                "created_by": render.created_by,
                "created_at": render.created_at.isoformat(),
                "started_at": render.started_at.isoformat() if render.started_at else None,
                "completed_at": render.completed_at.isoformat() if render.completed_at else None,
                "width": render.width,
                "height": render.height,
                "fps": render.fps,
                "quality": render.quality,
                "profile": render.profile,
                "deterministic": render.deterministic,
                "output_format": render.output_format,
                "output_path": render.output_path,
                "file_size_bytes": render.file_size_bytes,
                "duration_seconds": render.duration_seconds,
                "render_time_seconds": render.render_time_seconds,
                "frames_rendered": render.frames_rendered,
                "total_frames": render.total_frames,
                "progress_percentage": render.progress_percentage,
                "error_message": render.error_message,
                "retry_count": render.retry_count,
                "max_retries": render.max_retries,
                "checksum": render.checksum,
                "golden_frame_checksums": render.golden_frame_checksums
            }
            for render in renders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve case renders: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Simplified API Gateway on http://localhost:8000")
    print("📚 API Documentation available at http://localhost:8000/docs")
    uvicorn.run(
        "simple_api_gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
