"""Timeline data models for legal simulation platform."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class TimelineStatus(Enum):
    """Timeline compilation status."""
    DRAFT = "draft"
    COMPILING = "compiling"
    COMPILED = "compiled"
    FAILED = "failed"


class ClipType(Enum):
    """Clip type enumeration."""
    EVIDENCE = "evidence"
    TRANSITION = "transition"
    TEXT_OVERLAY = "text_overlay"
    AUDIO_NARRATION = "audio_narration"


@dataclass
class TimelineClip:
    """Individual clip in timeline."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    clip_type: ClipType = ClipType.EVIDENCE
    start_time: float = 0.0
    duration: float = 1.0
    source_id: str = ""  # Evidence ID or other source
    metadata: Dict[str, Any] = field(default_factory=dict)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    transitions: Dict[str, Any] = field(default_factory=dict)
    
    def get_end_time(self) -> float:
        """Get end time of clip."""
        return self.start_time + self.duration
    
    def overlaps_with(self, other: "TimelineClip") -> bool:
        """Check if clip overlaps with another."""
        return not (self.get_end_time() <= other.start_time or 
                   other.get_end_time() <= self.start_time)


@dataclass
class TimelineTrack:
    """Track containing clips."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    track_type: str = "video"  # video, audio, text
    clips: List[TimelineClip] = field(default_factory=list)
    volume: float = 1.0
    muted: bool = False
    
    def add_clip(self, clip: TimelineClip) -> None:
        """Add clip to track."""
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.start_time)
    
    def remove_clip(self, clip_id: str) -> bool:
        """Remove clip from track."""
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                del self.clips[i]
                return True
        return False
    
    def get_total_duration(self) -> float:
        """Get total duration of track."""
        if not self.clips:
            return 0.0
        return max(clip.get_end_time() for clip in self.clips)


@dataclass
class TimelineMetadata:
    """Metadata for timeline."""
    title: str
    description: str
    storyboard_id: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"
    fps: int = 30
    resolution: tuple = (1920, 1080)


@dataclass
class CompilationResult:
    """Result of timeline compilation."""
    success: bool
    output_path: str = ""
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    compilation_time_ms: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    compiled_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Timeline:
    """Main timeline data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: TimelineMetadata = field(default_factory=TimelineMetadata)
    status: TimelineStatus = TimelineStatus.DRAFT
    tracks: List[TimelineTrack] = field(default_factory=list)
    compilation_result: Optional[CompilationResult] = None
    usd_scene_data: Optional[bytes] = None
    
    def add_track(self, track: TimelineTrack) -> None:
        """Add track to timeline."""
        self.tracks.append(track)
        self.metadata.updated_at = datetime.utcnow()
    
    def remove_track(self, track_id: str) -> bool:
        """Remove track from timeline."""
        for i, track in enumerate(self.tracks):
            if track.id == track_id:
                del self.tracks[i]
                self.metadata.updated_at = datetime.utcnow()
                return True
        return False
    
    def get_total_duration(self) -> float:
        """Get total duration of timeline."""
        if not self.tracks:
            return 0.0
        return max(track.get_total_duration() for track in self.tracks)
    
    def validate_timeline(self) -> List[str]:
        """Validate timeline for conflicts and issues."""
        errors = []
        
        for track in self.tracks:
            # Check for overlapping clips
            for i, clip1 in enumerate(track.clips):
                for j, clip2 in enumerate(track.clips[i+1:], i+1):
                    if clip1.overlaps_with(clip2):
                        errors.append(
                            f"Overlapping clips in track '{track.name}': "
                            f"{clip1.id} and {clip2.id}"
                        )
            
            # Check for gaps
            if len(track.clips) > 1:
                sorted_clips = sorted(track.clips, key=lambda c: c.start_time)
                for i in range(len(sorted_clips) - 1):
                    current_end = sorted_clips[i].get_end_time()
                    next_start = sorted_clips[i + 1].start_time
                    if current_end < next_start:
                        gap_duration = next_start - current_end
                        if gap_duration > 0.1:  # Gap larger than 100ms
                            errors.append(
                                f"Gap in track '{track.name}' between "
                                f"{sorted_clips[i].id} and {sorted_clips[i + 1].id}: "
                                f"{gap_duration:.2f}s"
                            )
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert timeline to dictionary."""
        result = {
            "id": self.id,
            "metadata": {
                "title": self.metadata.title,
                "description": self.metadata.description,
                "storyboard_id": self.metadata.storyboard_id,
                "created_by": self.metadata.created_by,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "version": self.metadata.version,
                "fps": self.metadata.fps,
                "resolution": list(self.metadata.resolution),
            },
            "status": self.status.value,
            "tracks": [
                {
                    "id": track.id,
                    "name": track.name,
                    "track_type": track.track_type,
                    "volume": track.volume,
                    "muted": track.muted,
                    "clips": [
                        {
                            "id": clip.id,
                            "clip_type": clip.clip_type.value,
                            "start_time": clip.start_time,
                            "duration": clip.duration,
                            "source_id": clip.source_id,
                            "metadata": clip.metadata,
                            "effects": clip.effects,
                            "transitions": clip.transitions,
                        }
                        for clip in track.clips
                    ],
                }
                for track in self.tracks
            ],
        }
        
        if self.compilation_result:
            result["compilation_result"] = {
                "success": self.compilation_result.success,
                "output_path": self.compilation_result.output_path,
                "duration_seconds": self.compilation_result.duration_seconds,
                "file_size_bytes": self.compilation_result.file_size_bytes,
                "compilation_time_ms": self.compilation_result.compilation_time_ms,
                "errors": self.compilation_result.errors,
                "warnings": self.compilation_result.warnings,
                "compiled_at": self.compilation_result.compiled_at.isoformat(),
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Timeline":
        """Create timeline from dictionary."""
        metadata = TimelineMetadata(
            title=data["metadata"]["title"],
            description=data["metadata"]["description"],
            storyboard_id=data["metadata"]["storyboard_id"],
            created_by=data["metadata"]["created_by"],
            created_at=datetime.fromisoformat(data["metadata"]["created_at"]),
            updated_at=datetime.fromisoformat(data["metadata"]["updated_at"]),
            version=data["metadata"].get("version", "1.0"),
            fps=data["metadata"].get("fps", 30),
            resolution=tuple(data["metadata"].get("resolution", [1920, 1080])),
        )
        
        tracks = []
        for track_data in data.get("tracks", []):
            clips = [
                TimelineClip(
                    id=clip["id"],
                    clip_type=ClipType(clip["clip_type"]),
                    start_time=clip["start_time"],
                    duration=clip["duration"],
                    source_id=clip["source_id"],
                    metadata=clip.get("metadata", {}),
                    effects=clip.get("effects", []),
                    transitions=clip.get("transitions", {}),
                )
                for clip in track_data.get("clips", [])
            ]
            
            track = TimelineTrack(
                id=track_data["id"],
                name=track_data.get("name", ""),
                track_type=track_data.get("track_type", "video"),
                clips=clips,
                volume=track_data.get("volume", 1.0),
                muted=track_data.get("muted", False),
            )
            tracks.append(track)
        
        compilation_result = None
        if "compilation_result" in data:
            cr_data = data["compilation_result"]
            compilation_result = CompilationResult(
                success=cr_data["success"],
                output_path=cr_data.get("output_path", ""),
                duration_seconds=cr_data.get("duration_seconds", 0.0),
                file_size_bytes=cr_data.get("file_size_bytes", 0),
                compilation_time_ms=cr_data.get("compilation_time_ms", 0),
                errors=cr_data.get("errors", []),
                warnings=cr_data.get("warnings", []),
                compiled_at=datetime.fromisoformat(cr_data["compiled_at"]),
            )
        
        return cls(
            id=data["id"],
            metadata=metadata,
            status=TimelineStatus(data["status"]),
            tracks=tracks,
            compilation_result=compilation_result,
        )
