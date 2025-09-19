#!/usr/bin/env python3
"""
Simplified API Gateway for testing frontend-to-backend pipeline.
This version doesn't require database connections.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Create FastAPI application
app = FastAPI(
    title="Legal Simulation API Gateway",
    description="Simplified API Gateway for testing",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000"],
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

# Mock data for testing
MOCK_CASES = [
    {
        "id": "case-1",
        "title": "Sample Case 1",
        "status": "draft",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by": "user-1",
        "metadata": {
            "title": "Sample Case 1",
            "case_type": "CIVIL",
            "jurisdiction": "Federal Court",
            "created_by": "user-1"
        },
        "evidence_ids": ["evidence-1", "evidence-2"],
        "storyboard_ids": ["storyboard-1"],
        "render_ids": ["render-1"]
    }
]

MOCK_EVIDENCE = [
    {
        "id": "evidence-1",
        "filename": "sample-document.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024000,
        "checksum": "abc123def456",
        "created_at": "2024-01-01T00:00:00Z",
        "worm_locked": False,
        "case_id": "case-1",
        "status": "processed",
        "uploaded_by": "user-1",
        "processing_results": {
            "text": "Sample document content",
            "entities": ["John Doe", "ABC Corp"],
            "confidence": {"overall": 0.95}
        }
    },
    {
        "id": "evidence-2",
        "filename": "sample-image.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 512000,
        "checksum": "def456ghi789",
        "created_at": "2024-01-01T00:00:00Z",
        "worm_locked": False,
        "case_id": "case-1",
        "status": "processed",
        "uploaded_by": "user-1",
        "processing_results": {
            "text": "Sample image description",
            "entities": ["Jane Smith"],
            "confidence": {"overall": 0.88}
        }
    }
]

MOCK_STORYBOARDS = [
    {
        "id": "storyboard-1",
        "case_id": "case-1",
        "title": "Sample Storyboard",
        "content": '{"scenes": [{"id": "scene-1", "description": "Opening scene", "duration_seconds": 30}]}',
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by": "user-1",
        "validation_result": {
            "is_valid": True,
            "errors": []
        }
    }
]

MOCK_RENDERS = [
    {
        "id": "render-1",
        "case_id": "case-1",
        "storyboard_id": "storyboard-1",
        "timeline_id": "timeline-1",
        "status": "completed",
        "priority": 0,
        "created_by": "user-1",
        "created_at": "2024-01-01T00:00:00Z",
        "started_at": "2024-01-01T00:01:00Z",
        "completed_at": "2024-01-01T00:05:00Z",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "quality": "standard",
        "profile": "neutral",
        "deterministic": True,
        "output_format": "mp4",
        "output_path": "/renders/render-1.mp4",
        "file_size_bytes": 50000000,
        "duration_seconds": 120,
        "render_time_seconds": 240,
        "frames_rendered": 3600,
        "total_frames": 3600,
        "progress_percentage": 100,
        "error_message": "",
        "retry_count": 0,
        "max_retries": 3,
        "checksum": "render123checksum",
        "golden_frame_checksums": ["frame1", "frame2"]
    }
]

# Cases API endpoints
@app.get("/api/v1/cases")
async def get_cases():
    """Get all cases."""
    return MOCK_CASES

@app.get("/api/v1/cases/{case_id}")
async def get_case(case_id: str):
    """Get a specific case."""
    case = next((c for c in MOCK_CASES if c["id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

# Evidence API endpoints
@app.get("/api/v1/evidence")
async def get_evidence():
    """Get all evidence."""
    return MOCK_EVIDENCE

@app.get("/api/v1/evidence/{evidence_id}")
async def get_evidence_by_id(evidence_id: str):
    """Get specific evidence."""
    evidence = next((e for e in MOCK_EVIDENCE if e["id"] == evidence_id), None)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence

@app.post("/api/v1/evidence/upload")
async def upload_evidence():
    """Upload evidence (mock)."""
    return {
        "id": "evidence-new",
        "filename": "uploaded-file.pdf",
        "status": "uploaded",
        "message": "File uploaded successfully"
    }

# Storyboards API endpoints
@app.get("/api/v1/storyboards")
async def get_storyboards():
    """Get all storyboards."""
    return MOCK_STORYBOARDS

@app.get("/api/v1/storyboards/{storyboard_id}")
async def get_storyboard(storyboard_id: str):
    """Get specific storyboard."""
    storyboard = next((s for s in MOCK_STORYBOARDS if s["id"] == storyboard_id), None)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return storyboard

# Renders API endpoints
@app.get("/api/v1/renders")
async def get_renders():
    """Get all renders."""
    return MOCK_RENDERS

@app.get("/api/v1/renders/{render_id}")
async def get_render(render_id: str):
    """Get specific render."""
    render = next((r for r in MOCK_RENDERS if r["id"] == render_id), None)
    if not render:
        raise HTTPException(status_code=404, detail="Render not found")
    return render

@app.get("/api/v1/cases/{case_id}/renders")
async def get_case_renders(case_id: str):
    """Get renders for a specific case."""
    case_renders = [r for r in MOCK_RENDERS if r["case_id"] == case_id]
    return case_renders

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
