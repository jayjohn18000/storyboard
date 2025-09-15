"""Render data models for legal simulation platform."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class RenderStatus(Enum):
    """Render job status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RenderQuality(Enum):
    """Render quality levels."""
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class RenderJob:
    """Render job data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timeline_id: str = ""
    storyboard_id: str = ""
    case_id: str = ""
    status: RenderStatus = RenderStatus.QUEUED
    priority: int = 0
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Render configuration
    width: int = 1920
    height: int = 1080
    fps: int = 30
    quality: RenderQuality = RenderQuality.STANDARD
    profile: str = "neutral"  # neutral, cinematic
    deterministic: bool = True
    seed: Optional[int] = None
    
    # Output configuration
    output_format: str = "mp4"
    output_path: str = ""
    file_size_bytes: int = 0
    duration_seconds: float = 0.0
    
    # Processing metadata
    render_time_seconds: float = 0.0
    frames_rendered: int = 0
    total_frames: int = 0
    progress_percentage: float = 0.0
    
    # Error handling
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    
    # Determinism
    checksum: str = ""
    golden_frame_checksums: List[str] = field(default_factory=list)
    
    def start_processing(self) -> None:
        """Mark job as started."""
        self.status = RenderStatus.PROCESSING
        self.started_at = datetime.utcnow()
    
    def complete_processing(self, output_path: str, file_size: int, duration: float) -> None:
        """Mark job as completed."""
        self.status = RenderStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.output_path = output_path
        self.file_size_bytes = file_size
        self.duration_seconds = duration
        self.progress_percentage = 100.0
        
        if self.started_at:
            self.render_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def fail_processing(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = RenderStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        
        if self.started_at:
            self.render_time_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def update_progress(self, frames_rendered: int, total_frames: int) -> None:
        """Update render progress."""
        self.frames_rendered = frames_rendered
        self.total_frames = total_frames
        self.progress_percentage = (frames_rendered / total_frames * 100) if total_frames > 0 else 0.0
    
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == RenderStatus.FAILED
    
    def increment_retry(self) -> None:
        """Increment retry count and reset status."""
        self.retry_count += 1
        self.status = RenderStatus.QUEUED
        self.error_message = ""
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert render job to dictionary."""
        return {
            "id": self.id,
            "timeline_id": self.timeline_id,
            "storyboard_id": self.storyboard_id,
            "case_id": self.case_id,
            "status": self.status.value,
            "priority": self.priority,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "quality": self.quality.value,
            "profile": self.profile,
            "deterministic": self.deterministic,
            "seed": self.seed,
            "output_format": self.output_format,
            "output_path": self.output_path,
            "file_size_bytes": self.file_size_bytes,
            "duration_seconds": self.duration_seconds,
            "render_time_seconds": self.render_time_seconds,
            "frames_rendered": self.frames_rendered,
            "total_frames": self.total_frames,
            "progress_percentage": self.progress_percentage,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "checksum": self.checksum,
            "golden_frame_checksums": self.golden_frame_checksums,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RenderJob":
        """Create render job from dictionary."""
        job = cls(
            id=data["id"],
            timeline_id=data.get("timeline_id", ""),
            storyboard_id=data.get("storyboard_id", ""),
            case_id=data.get("case_id", ""),
            status=RenderStatus(data["status"]),
            priority=data.get("priority", 0),
            created_by=data.get("created_by", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            width=data.get("width", 1920),
            height=data.get("height", 1080),
            fps=data.get("fps", 30),
            quality=RenderQuality(data.get("quality", "standard")),
            profile=data.get("profile", "neutral"),
            deterministic=data.get("deterministic", True),
            seed=data.get("seed"),
            output_format=data.get("output_format", "mp4"),
            output_path=data.get("output_path", ""),
            file_size_bytes=data.get("file_size_bytes", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            render_time_seconds=data.get("render_time_seconds", 0.0),
            frames_rendered=data.get("frames_rendered", 0),
            total_frames=data.get("total_frames", 0),
            progress_percentage=data.get("progress_percentage", 0.0),
            error_message=data.get("error_message", ""),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            checksum=data.get("checksum", ""),
            golden_frame_checksums=data.get("golden_frame_checksums", []),
        )
        
        if data.get("started_at"):
            job.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            job.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return job


@dataclass
class RenderQueue:
    """Render queue management."""
    jobs: List[RenderJob] = field(default_factory=list)
    max_concurrent_jobs: int = 4
    current_jobs: int = 0
    
    def add_job(self, job: RenderJob) -> None:
        """Add job to queue."""
        self.jobs.append(job)
        self.jobs.sort(key=lambda j: (-j.priority, j.created_at))
    
    def get_next_job(self) -> Optional[RenderJob]:
        """Get next job from queue."""
        if self.current_jobs >= self.max_concurrent_jobs:
            return None
        
        for job in self.jobs:
            if job.status == RenderStatus.QUEUED:
                return job
        
        return None
    
    def remove_job(self, job_id: str) -> bool:
        """Remove job from queue."""
        for i, job in enumerate(self.jobs):
            if job.id == job_id:
                del self.jobs[i]
                return True
        return False
    
    def get_job_status(self, job_id: str) -> Optional[RenderJob]:
        """Get job by ID."""
        for job in self.jobs:
            if job.id == job_id:
                return job
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = {
            "total_jobs": len(self.jobs),
            "queued": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        
        for job in self.jobs:
            stats[job.status.value] += 1
        
        return stats
