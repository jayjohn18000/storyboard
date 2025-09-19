"""Render management API routes."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from ...shared.models.render import RenderJob, RenderStatus, RenderQuality
from ...shared.services.render_service import RenderService
from ...shared.services.database_service import DatabaseService
from ...shared.policy.middleware import requires
from ..middleware.auth import get_current_user
from ..middleware.mode_enforcer import ModeEnforcer

logger = logging.getLogger(__name__)


router = APIRouter()


async def get_render_service() -> RenderService:
    """Get render service instance."""
    db_service = DatabaseService()
    return RenderService(db_service)


class RenderRequest(BaseModel):
    """Request model for creating a render job."""
    timeline_id: str = Field(..., description="Timeline ID to render")
    storyboard_id: str = Field(..., description="Storyboard ID")
    case_id: str = Field(..., description="Case ID")
    width: int = Field(default=1920, description="Render width")
    height: int = Field(default=1080, description="Render height")
    fps: int = Field(default=30, description="Frames per second")
    quality: RenderQuality = Field(default=RenderQuality.STANDARD, description="Render quality")
    profile: str = Field(default="neutral", description="Render profile")
    deterministic: bool = Field(default=True, description="Use deterministic rendering")
    seed: Optional[int] = Field(None, description="Random seed for deterministic rendering")
    output_format: str = Field(default="mp4", description="Output format")
    priority: int = Field(default=0, description="Render priority")


class RenderResponse(BaseModel):
    """Response model for render job data."""
    id: str
    timeline_id: str
    storyboard_id: str
    case_id: str
    status: RenderStatus
    priority: int
    created_by: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    width: int
    height: int
    fps: int
    quality: RenderQuality
    profile: str
    deterministic: bool
    seed: Optional[int]
    output_format: str
    output_path: str
    file_size_bytes: int
    duration_seconds: float
    render_time_seconds: float
    frames_rendered: int
    total_frames: int
    progress_percentage: float
    error_message: str
    retry_count: int
    max_retries: int
    checksum: str
    golden_frame_checksums: List[str]


class RenderUpdateRequest(BaseModel):
    """Request model for updating a render job."""
    priority: Optional[int] = Field(None, description="Render priority")


@router.post("/", response_model=RenderResponse, status_code=status.HTTP_201_CREATED)
@requires("render_manager")
async def create_render(
    request: RenderRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Create a new render job."""
    # Check permissions
    if not mode_enforcer.can_create_render(current_user, request.case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create render"
        )
    
    try:
        # Create render job
        render_job = await render_service.create_render_job(
            case_id=request.case_id,
            storyboard_id=request.storyboard_id,
            timeline_id=request.timeline_id,
            created_by=current_user,
            render_config={
                "width": request.width,
                "height": request.height,
                "fps": request.fps,
                "quality": request.quality.value,
                "profile": request.profile,
                "deterministic": request.deterministic,
                "seed": request.seed,
                "output_format": request.output_format,
                "priority": request.priority,
            }
        )
        
        return RenderResponse(
            id=render_job.id,
            timeline_id=render_job.timeline_id,
            storyboard_id=render_job.storyboard_id,
            case_id=render_job.case_id,
            status=render_job.status,
            priority=render_job.priority,
            created_by=render_job.created_by,
            created_at=render_job.created_at,
            started_at=render_job.started_at,
            completed_at=render_job.completed_at,
            width=render_job.width,
            height=render_job.height,
            fps=render_job.fps,
            quality=render_job.quality,
            profile=render_job.profile,
            deterministic=render_job.deterministic,
            seed=render_job.seed,
            output_format=render_job.output_format,
            output_path=render_job.output_path,
            file_size_bytes=render_job.file_size_bytes,
            duration_seconds=render_job.duration_seconds,
            render_time_seconds=render_job.render_time_seconds,
            frames_rendered=render_job.frames_rendered,
            total_frames=render_job.total_frames,
            progress_percentage=render_job.progress_percentage,
            error_message=render_job.error_message,
            retry_count=render_job.retry_count,
            max_retries=render_job.max_retries,
            checksum=render_job.checksum,
            golden_frame_checksums=render_job.golden_frame_checksums,
        )
        
    except Exception as e:
        logger.error(f"Failed to create render job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create render job: {str(e)}"
        )


@router.get("/", response_model=List[RenderResponse])
async def list_renders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[RenderStatus] = None,
    case_id_filter: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """List render jobs with optional filtering."""
    # Check permissions
    if not mode_enforcer.can_list_renders(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to list renders"
        )
    
    try:
        # Get renders from service
        renders = await render_service.list_render_jobs(
            case_id=case_id_filter,
            skip=skip,
            limit=limit,
            status_filter=status_filter
        )
        
        return [
            RenderResponse(
                id=render.id,
                timeline_id=render.timeline_id,
                storyboard_id=render.storyboard_id,
                case_id=render.case_id,
                status=render.status,
                priority=render.priority,
                created_by=render.created_by,
                created_at=render.created_at,
                started_at=render.started_at,
                completed_at=render.completed_at,
                width=render.width,
                height=render.height,
                fps=render.fps,
                quality=render.quality,
                profile=render.profile,
                deterministic=render.deterministic,
                seed=render.seed,
                output_format=render.output_format,
                output_path=render.output_path,
                file_size_bytes=render.file_size_bytes,
                duration_seconds=render.duration_seconds,
                render_time_seconds=render.render_time_seconds,
                frames_rendered=render.frames_rendered,
                total_frames=render.total_frames,
                progress_percentage=render.progress_percentage,
                error_message=render.error_message,
                retry_count=render.retry_count,
                max_retries=render.max_retries,
                checksum=render.checksum,
                golden_frame_checksums=render.golden_frame_checksums,
            )
            for render in renders
        ]
        
    except Exception as e:
        logger.error(f"Failed to list renders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list renders: {str(e)}"
        )


@router.get("/{render_id}", response_model=RenderResponse)
async def get_render(
    render_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Get a specific render job by ID."""
    # Check permissions
    if not mode_enforcer.can_view_render(current_user, render_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view render"
        )
    
    try:
        # Get render from service
        render_job = await render_service.get_render_job(render_id)
        if not render_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render not found"
            )
        
        return RenderResponse(
            id=render_job.id,
            timeline_id=render_job.timeline_id,
            storyboard_id=render_job.storyboard_id,
            case_id=render_job.case_id,
            status=render_job.status,
            priority=render_job.priority,
            created_by=render_job.created_by,
            created_at=render_job.created_at,
            started_at=render_job.started_at,
            completed_at=render_job.completed_at,
            width=render_job.width,
            height=render_job.height,
            fps=render_job.fps,
            quality=render_job.quality,
            profile=render_job.profile,
            deterministic=render_job.deterministic,
            seed=render_job.seed,
            output_format=render_job.output_format,
            output_path=render_job.output_path,
            file_size_bytes=render_job.file_size_bytes,
            duration_seconds=render_job.duration_seconds,
            render_time_seconds=render_job.render_time_seconds,
            frames_rendered=render_job.frames_rendered,
            total_frames=render_job.total_frames,
            progress_percentage=render_job.progress_percentage,
            error_message=render_job.error_message,
            retry_count=render_job.retry_count,
            max_retries=render_job.max_retries,
            checksum=render_job.checksum,
            golden_frame_checksums=render_job.golden_frame_checksums,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get render {render_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get render: {str(e)}"
        )


@router.get("/cases/{case_id}/renders", response_model=List[RenderResponse])
async def get_case_renders(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Get all renders for a specific case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case renders"
        )
    
    try:
        # Get renders for case from service
        renders = await render_service.list_render_jobs(case_id=case_id)
        
        return [
            RenderResponse(
                id=render.id,
                timeline_id=render.timeline_id,
                storyboard_id=render.storyboard_id,
                case_id=render.case_id,
                status=render.status,
                priority=render.priority,
                created_by=render.created_by,
                created_at=render.created_at,
                started_at=render.started_at,
                completed_at=render.completed_at,
                width=render.width,
                height=render.height,
                fps=render.fps,
                quality=render.quality,
                profile=render.profile,
                deterministic=render.deterministic,
                seed=render.seed,
                output_format=render.output_format,
                output_path=render.output_path,
                file_size_bytes=render.file_size_bytes,
                duration_seconds=render.duration_seconds,
                render_time_seconds=render.render_time_seconds,
                frames_rendered=render.frames_rendered,
                total_frames=render.total_frames,
                progress_percentage=render.progress_percentage,
                error_message=render.error_message,
                retry_count=render.retry_count,
                max_retries=render.max_retries,
                checksum=render.checksum,
                golden_frame_checksums=render.golden_frame_checksums,
            )
            for render in renders
        ]
        
    except Exception as e:
        logger.error(f"Failed to get renders for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get case renders: {str(e)}"
        )


@router.put("/{render_id}", response_model=RenderResponse)
async def update_render(
    render_id: str,
    request: RenderUpdateRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Update a render job."""
    # Check permissions
    if not mode_enforcer.can_edit_render(current_user, render_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit render"
        )
    
    try:
        # Get render from service
        render_job = await render_service.get_render_job(render_id)
        if not render_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render not found"
            )
        
        # Check if render can be modified
        if render_job.status in [RenderStatus.PROCESSING, RenderStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify render in current status"
            )
        
        # Update render
        update_data = {}
        if request.priority is not None:
            update_data["priority"] = request.priority
        
        updated_render = await render_service.update_render_job(render_id, **update_data)
        if not updated_render:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render not found"
            )
        
        return RenderResponse(
            id=updated_render.id,
            timeline_id=updated_render.timeline_id,
            storyboard_id=updated_render.storyboard_id,
            case_id=updated_render.case_id,
            status=updated_render.status,
            priority=updated_render.priority,
            created_by=updated_render.created_by,
            created_at=updated_render.created_at,
            started_at=updated_render.started_at,
            completed_at=updated_render.completed_at,
            width=updated_render.width,
            height=updated_render.height,
            fps=updated_render.fps,
            quality=updated_render.quality,
            profile=updated_render.profile,
            deterministic=updated_render.deterministic,
            seed=updated_render.seed,
            output_format=updated_render.output_format,
            output_path=updated_render.output_path,
            file_size_bytes=updated_render.file_size_bytes,
            duration_seconds=updated_render.duration_seconds,
            render_time_seconds=updated_render.render_time_seconds,
            frames_rendered=updated_render.frames_rendered,
            total_frames=updated_render.total_frames,
            progress_percentage=updated_render.progress_percentage,
            error_message=updated_render.error_message,
            retry_count=updated_render.retry_count,
            max_retries=updated_render.max_retries,
            checksum=updated_render.checksum,
            golden_frame_checksums=updated_render.golden_frame_checksums,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update render {render_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update render: {str(e)}"
        )


@router.delete("/{render_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_render(
    render_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Cancel a render job."""
    # Check permissions
    if not mode_enforcer.can_cancel_render(current_user, render_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to cancel render"
        )
    
    try:
        # Get render from service
        render_job = await render_service.get_render_job(render_id)
        if not render_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render not found"
            )
        
        # Check if render can be cancelled
        if render_job.status in [RenderStatus.COMPLETED, RenderStatus.FAILED, RenderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel render in current status"
            )
        
        # Cancel render
        success = await render_service.cancel_render_job(render_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel render"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel render {render_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel render: {str(e)}"
        )


@router.get("/{render_id}/status", response_model=dict)
async def get_render_status(
    render_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Get render job status."""
    # Check permissions
    if not mode_enforcer.can_view_render(current_user, render_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view render status"
        )
    
    try:
        # Get render status from service
        status_data = await render_service.get_render_status(render_id)
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render not found"
            )
        
        return status_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get render status {render_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get render status: {str(e)}"
        )


@router.get("/{render_id}/download")
async def download_render(
    render_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Download rendered video."""
    # Check permissions
    if not mode_enforcer.can_download_render(current_user, render_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download render"
        )
    
    try:
        # Get render from service
        render_job = await render_service.get_render_job(render_id)
        if not render_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render not found"
            )
        
        # Check if render is completed
        if render_job.status != RenderStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Render is not completed"
            )
        
        # Get file from render orchestrator
        from ...shared.http_client import get_http_client
        from ...shared.config import get_service_url
        
        http_client = await get_http_client()
        render_url = get_service_url("render")
        
        response = await http_client.request(
            "GET",
            f"{render_url}/render/download/{render_id}",
            timeout=30
        )
        
        # Return file response
        from fastapi.responses import Response
        return Response(
            content=response.content,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename=render_{render_id}.mp4"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download render {render_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download render: {str(e)}"
        )


@router.post("/{render_id}/retry", response_model=RenderResponse)
async def retry_render(
    render_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Retry a failed render job."""
    # Check permissions
    if not mode_enforcer.can_edit_render(current_user, render_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to retry render"
        )
    
    try:
        # Retry render job
        success = await render_service.retry_render_job(render_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot retry render job"
            )
        
        # Get updated render job
        render_job = await render_service.get_render_job(render_id)
        if not render_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Render not found"
            )
        
        return RenderResponse(
            id=render_job.id,
            timeline_id=render_job.timeline_id,
            storyboard_id=render_job.storyboard_id,
            case_id=render_job.case_id,
            status=render_job.status,
            priority=render_job.priority,
            created_by=render_job.created_by,
            created_at=render_job.created_at,
            started_at=render_job.started_at,
            completed_at=render_job.completed_at,
            width=render_job.width,
            height=render_job.height,
            fps=render_job.fps,
            quality=render_job.quality,
            profile=render_job.profile,
            deterministic=render_job.deterministic,
            seed=render_job.seed,
            output_format=render_job.output_format,
            output_path=render_job.output_path,
            file_size_bytes=render_job.file_size_bytes,
            duration_seconds=render_job.duration_seconds,
            render_time_seconds=render_job.render_time_seconds,
            frames_rendered=render_job.frames_rendered,
            total_frames=render_job.total_frames,
            progress_percentage=render_job.progress_percentage,
            error_message=render_job.error_message,
            retry_count=render_job.retry_count,
            max_retries=render_job.max_retries,
            checksum=render_job.checksum,
            golden_frame_checksums=render_job.golden_frame_checksums,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry render {render_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry render: {str(e)}"
        )


@router.get("/queue/stats", response_model=dict)
async def get_queue_stats(
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    render_service: RenderService = Depends(get_render_service)
):
    """Get render queue statistics."""
    # Check permissions
    if not mode_enforcer.can_view_queue_stats(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view queue stats"
        )
    
    try:
        # Get queue stats from service
        stats = await render_service.get_queue_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}"
        )
