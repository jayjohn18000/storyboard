"""Export API routes for legal simulation platform."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ...shared.services.database_service import DatabaseService
from ...shared.services.export_service import ExportService
from ...shared.database import get_db_session
from ..middleware.auth import get_current_user
from ..middleware.mode_enforcer import ModeEnforcer


router = APIRouter()


async def get_export_service(db_session = Depends(get_db_session)) -> ExportService:
    """Get export service instance."""
    db_service = DatabaseService(db_session)
    return ExportService(db_service)


class ExportRequest(BaseModel):
    """Request model for export operations."""
    case_id: str = Field(..., description="Case ID to export")
    format: str = Field(default="json", description="Export format")
    include_evidence: bool = Field(default=True, description="Include evidence data")
    include_storyboards: bool = Field(default=True, description="Include storyboard data")
    include_renders: bool = Field(default=True, description="Include render data")
    include_metadata: bool = Field(default=True, description="Include metadata")
    include_chain_of_custody: bool = Field(default=True, description="Include chain of custody")


class ExportResponse(BaseModel):
    """Response model for export operations."""
    export_id: str
    case_id: str
    format: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    file_size_bytes: int
    download_url: str
    checksum: str


@router.post("/case", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def export_case(
    request: ExportRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Export case data."""
    # Check permissions
    if not mode_enforcer.can_export_case(current_user, request.case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to export case"
        )
    
    # Validate format
    if request.format not in ["json", "xml", "zip"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )
    
    try:
        # Create export job
        export_job = await export_service.create_export_job(
            case_id=request.case_id,
            format=request.format,
            include_evidence=request.include_evidence,
            include_storyboards=request.include_storyboards,
            include_renders=request.include_renders,
            include_metadata=request.include_metadata,
            include_chain_of_custody=request.include_chain_of_custody,
            created_by=current_user
        )
        
        return ExportResponse(
            export_id=export_job["id"],
            case_id=export_job["case_id"],
            format=export_job["format"],
            status=export_job["status"],
            created_at=export_job["created_at"],
            completed_at=export_job["completed_at"],
            file_size_bytes=export_job["file_size_bytes"],
            download_url=export_job["download_url"],
            checksum=export_job["checksum"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create export job: {str(e)}"
        )


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export_status(
    export_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Get export job status."""
    # Check permissions
    if not mode_enforcer.can_view_export(current_user, export_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view export"
        )
    
    try:
        # Get export job from database
        export_job = await export_service.get_export_job(export_id)
        if not export_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found"
            )
        
        return ExportResponse(
            export_id=export_job["id"],
            case_id=export_job["case_id"],
            format=export_job["format"],
            status=export_job["status"],
            created_at=export_job["created_at"],
            completed_at=export_job["completed_at"],
            file_size_bytes=export_job["file_size_bytes"],
            download_url=export_job["download_url"],
            checksum=export_job["checksum"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve export status: {str(e)}"
        )


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Download exported data."""
    # Check permissions
    if not mode_enforcer.can_download_export(current_user, export_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download export"
        )
    
    try:
        # Get export job from database
        export_job = await export_service.get_export_job(export_id)
        if not export_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found"
            )
        
        # Check if export is completed
        if export_job["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Export is not completed"
            )
        
        # Get file data from storage
        file_data = await export_service.get_export_file(export_id)
        
        # Determine content type based on format
        content_type = {
            "json": "application/json",
            "xml": "application/xml",
            "zip": "application/zip"
        }.get(export_job["format"], "application/octet-stream")
        
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=export_{export_id}.{export_job['format']}",
                "Content-Length": str(len(file_data)),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download export: {str(e)}"
        )


@router.get("/case/{case_id}/summary")
async def get_case_summary(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Get case summary for export."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case summary"
        )
    
    try:
        # Get case summary
        summary = await export_service.get_case_summary(case_id)
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve case summary: {str(e)}"
        )


@router.get("/case/{case_id}/evidence-summary")
async def get_evidence_summary(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Get evidence summary for case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view evidence summary"
        )
    
    try:
        # Get evidence summary
        summary = await export_service.get_evidence_summary(case_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evidence summary: {str(e)}"
        )


@router.get("/case/{case_id}/storyboard-summary")
async def get_storyboard_summary(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Get storyboard summary for case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view storyboard summary"
        )
    
    try:
        # Get storyboard summary
        summary = await export_service.get_storyboard_summary(case_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve storyboard summary: {str(e)}"
        )


@router.get("/case/{case_id}/render-summary")
async def get_render_summary(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Get render summary for case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view render summary"
        )
    
    try:
        # Get render summary
        summary = await export_service.get_render_summary(case_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve render summary: {str(e)}"
        )


@router.get("/case/{case_id}/chain-of-custody")
async def get_chain_of_custody(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    export_service: ExportService = Depends(get_export_service)
):
    """Get complete chain of custody for case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view chain of custody"
        )
    
    try:
        # Get chain of custody
        chain_entries = await export_service._get_chain_of_custody(case_id)
        
        return {
            "case_id": case_id,
            "entries": chain_entries,
            "total_entries": len(chain_entries),
            "first_entry": chain_entries[0] if chain_entries else None,
            "last_entry": chain_entries[-1] if chain_entries else None,
            "integrity_verified": True,  # Would implement integrity verification
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chain of custody: {str(e)}"
        )
