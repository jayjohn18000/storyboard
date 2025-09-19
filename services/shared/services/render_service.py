"""Render service for managing render jobs."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..models.database_models import Render
from ..models.render import RenderJob, RenderStatus, RenderQuality
from .database_service import DatabaseService
from ..http_client import get_http_client
from ..config import get_service_url

logger = logging.getLogger(__name__)


class RenderService:
    """Service for managing render jobs."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def create_render_job(
        self,
        case_id: str,
        storyboard_id: str,
        timeline_id: str,
        created_by: str,
        render_config: Dict[str, Any] = None
    ) -> RenderJob:
        """Create a new render job."""
        try:
            # Create render job model
            render_job = RenderJob(
                timeline_id=timeline_id,
                storyboard_id=storyboard_id,
                case_id=case_id,
                created_by=created_by,
                width=render_config.get("width", 1920) if render_config else 1920,
                height=render_config.get("height", 1080) if render_config else 1080,
                fps=render_config.get("fps", 30) if render_config else 30,
                quality=RenderQuality(render_config.get("quality", "standard")) if render_config else RenderQuality.STANDARD,
                profile=render_config.get("profile", "neutral") if render_config else "neutral",
                deterministic=render_config.get("deterministic", True) if render_config else True,
                seed=render_config.get("seed") if render_config else None,
                output_format=render_config.get("output_format", "mp4") if render_config else "mp4",
                priority=render_config.get("priority", 0) if render_config else 0,
            )
            
            # Save to database
            db_render = await self.db_service.create_render(
                case_id=case_id,
                storyboard_id=storyboard_id,
                title=f"Render for Storyboard {storyboard_id}",
                description=f"Render job for timeline {timeline_id}",
                created_by=created_by,
                render_config=render_job.to_dict()
            )
            
            # Update render job with database ID
            render_job.id = str(db_render.id)
            
            # Queue render job with render orchestrator
            await self._queue_render_job(render_job)
            
            logger.info(f"Created render job {render_job.id} for case {case_id}")
            return render_job
            
        except Exception as e:
            logger.error(f"Failed to create render job: {e}")
            raise
    
    async def get_render_job(self, render_id: str) -> Optional[RenderJob]:
        """Get render job by ID."""
        try:
            db_render = await self.db_service.get_render(render_id)
            if not db_render:
                return None
            
            # Convert database model to RenderJob
            render_config = db_render.render_config or {}
            render_job = RenderJob(
                id=str(db_render.id),
                timeline_id=render_config.get("timeline_id", ""),
                storyboard_id=str(db_render.storyboard_id),
                case_id=str(db_render.case_id),
                status=RenderStatus(db_render.status),
                priority=render_config.get("priority", 0),
                created_by=str(db_render.created_by),
                created_at=db_render.created_at,
                started_at=db_render.started_at,
                completed_at=db_render.completed_at,
                width=render_config.get("width", 1920),
                height=render_config.get("height", 1080),
                fps=render_config.get("fps", 30),
                quality=RenderQuality(render_config.get("quality", "standard")),
                profile=render_config.get("profile", "neutral"),
                deterministic=render_config.get("deterministic", True),
                seed=render_config.get("seed"),
                output_format=render_config.get("output_format", "mp4"),
                output_path=db_render.output_path or "",
                file_size_bytes=db_render.file_size or 0,
                duration_seconds=render_config.get("duration_seconds", 0.0),
                render_time_seconds=render_config.get("render_time_seconds", 0.0),
                frames_rendered=render_config.get("frames_rendered", 0),
                total_frames=render_config.get("total_frames", 0),
                progress_percentage=render_config.get("progress_percentage", 0.0),
                error_message=render_config.get("error_message", ""),
                retry_count=render_config.get("retry_count", 0),
                max_retries=render_config.get("max_retries", 3),
                checksum=render_config.get("checksum", ""),
                golden_frame_checksums=render_config.get("golden_frame_checksums", []),
            )
            
            return render_job
            
        except Exception as e:
            logger.error(f"Failed to get render job {render_id}: {e}")
            return None
    
    async def list_render_jobs(
        self,
        case_id: Optional[str] = None,
        storyboard_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[RenderStatus] = None
    ) -> List[RenderJob]:
        """List render jobs with optional filtering."""
        try:
            db_renders = await self.db_service.list_renders(
                case_id=case_id,
                storyboard_id=storyboard_id,
                skip=skip,
                limit=limit,
                status_filter=status_filter.value if status_filter else None
            )
            
            render_jobs = []
            for db_render in db_renders:
                render_config = db_render.render_config or {}
                render_job = RenderJob(
                    id=str(db_render.id),
                    timeline_id=render_config.get("timeline_id", ""),
                    storyboard_id=str(db_render.storyboard_id),
                    case_id=str(db_render.case_id),
                    status=RenderStatus(db_render.status),
                    priority=render_config.get("priority", 0),
                    created_by=str(db_render.created_by),
                    created_at=db_render.created_at,
                    started_at=db_render.started_at,
                    completed_at=db_render.completed_at,
                    width=render_config.get("width", 1920),
                    height=render_config.get("height", 1080),
                    fps=render_config.get("fps", 30),
                    quality=RenderQuality(render_config.get("quality", "standard")),
                    profile=render_config.get("profile", "neutral"),
                    deterministic=render_config.get("deterministic", True),
                    seed=render_config.get("seed"),
                    output_format=render_config.get("output_format", "mp4"),
                    output_path=db_render.output_path or "",
                    file_size_bytes=db_render.file_size or 0,
                    duration_seconds=render_config.get("duration_seconds", 0.0),
                    render_time_seconds=render_config.get("render_time_seconds", 0.0),
                    frames_rendered=render_config.get("frames_rendered", 0),
                    total_frames=render_config.get("total_frames", 0),
                    progress_percentage=render_config.get("progress_percentage", 0.0),
                    error_message=render_config.get("error_message", ""),
                    retry_count=render_config.get("retry_count", 0),
                    max_retries=render_config.get("max_retries", 3),
                    checksum=render_config.get("checksum", ""),
                    golden_frame_checksums=render_config.get("golden_frame_checksums", []),
                )
                render_jobs.append(render_job)
            
            return render_jobs
            
        except Exception as e:
            logger.error(f"Failed to list render jobs: {e}")
            return []
    
    async def update_render_job(self, render_id: str, **kwargs) -> Optional[RenderJob]:
        """Update render job."""
        try:
            # Update database
            updated_render = await self.db_service.update_render(render_id, **kwargs)
            if not updated_render:
                return None
            
            # Get updated render job
            return await self.get_render_job(render_id)
            
        except Exception as e:
            logger.error(f"Failed to update render job {render_id}: {e}")
            return None
    
    async def cancel_render_job(self, render_id: str) -> bool:
        """Cancel render job."""
        try:
            # Update status in database
            await self.db_service.update_render(
                render_id,
                status="cancelled",
                completed_at=datetime.utcnow()
            )
            
            # Cancel job in render orchestrator
            await self._cancel_render_job(render_id)
            
            logger.info(f"Cancelled render job {render_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel render job {render_id}: {e}")
            return False
    
    async def retry_render_job(self, render_id: str) -> bool:
        """Retry failed render job."""
        try:
            render_job = await self.get_render_job(render_id)
            if not render_job:
                return False
            
            if not render_job.can_retry():
                return False
            
            # Increment retry count and reset status
            render_job.increment_retry()
            
            # Update database
            await self.db_service.update_render(
                render_id,
                render_config=render_job.to_dict(),
                status=render_job.status.value
            )
            
            # Queue retry job
            await self._queue_render_job(render_job)
            
            logger.info(f"Retrying render job {render_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry render job {render_id}: {e}")
            return False
    
    async def get_render_status(self, render_id: str) -> Optional[Dict[str, Any]]:
        """Get render job status."""
        try:
            render_job = await self.get_render_job(render_id)
            if not render_job:
                return None
            
            return {
                "status": render_job.status.value,
                "progress_percentage": render_job.progress_percentage,
                "frames_rendered": render_job.frames_rendered,
                "total_frames": render_job.total_frames,
                "error_message": render_job.error_message,
                "render_time_seconds": render_job.render_time_seconds,
            }
            
        except Exception as e:
            logger.error(f"Failed to get render status {render_id}: {e}")
            return None
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get render queue statistics."""
        try:
            # Get stats from render orchestrator
            http_client = await get_http_client()
            render_url = get_service_url("render")
            
            response = await http_client.request_json(
                "GET",
                f"{render_url}/queue/stats",
                timeout=10
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            # Return mock stats if service unavailable
            return {
                "total_jobs": 0,
                "queued": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            }
    
    async def _queue_render_job(self, render_job: RenderJob) -> None:
        """Queue render job with render orchestrator."""
        try:
            http_client = await get_http_client()
            render_url = get_service_url("render")
            
            # Prepare render request
            render_request = {
                "timeline_id": render_job.timeline_id,
                "storyboard_id": render_job.storyboard_id,
                "case_id": render_job.case_id,
                "width": render_job.width,
                "height": render_job.height,
                "fps": render_job.fps,
                "quality": render_job.quality.value,
                "profile": render_job.profile,
                "deterministic": render_job.deterministic,
                "seed": render_job.seed,
                "output_format": render_job.output_format,
                "priority": render_job.priority,
            }
            
            # Send request to render orchestrator
            response = await http_client.request_json(
                "POST",
                f"{render_url}/render/scene",
                json=render_request,
                timeout=30
            )
            
            logger.info(f"Queued render job {render_job.id} with orchestrator")
            
        except Exception as e:
            logger.error(f"Failed to queue render job {render_job.id}: {e}")
            # Update status to failed
            await self.db_service.update_render(
                render_job.id,
                status="failed",
                render_config={**render_job.to_dict(), "error_message": str(e)}
            )
            raise
    
    async def _cancel_render_job(self, render_id: str) -> None:
        """Cancel render job in render orchestrator."""
        try:
            http_client = await get_http_client()
            render_url = get_service_url("render")
            
            # Send cancel request to render orchestrator
            await http_client.request_json(
                "DELETE",
                f"{render_url}/renders/{render_id}",
                timeout=10
            )
            
            logger.info(f"Cancelled render job {render_id} in orchestrator")
            
        except Exception as e:
            logger.error(f"Failed to cancel render job {render_id} in orchestrator: {e}")
            # Don't raise - we've already updated the database status
