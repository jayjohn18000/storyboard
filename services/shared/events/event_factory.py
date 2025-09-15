"""Event factory for creating typed events."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ..interfaces.event_bus import Event, EventType


class EventFactory:
    """Factory for creating typed events."""
    
    @staticmethod
    def create_evidence_uploaded(
        evidence_id: str,
        case_id: Optional[str] = None,
        filename: str = "",
        file_size: int = 0,
        content_type: str = "",
        uploaded_by: str = "",
        source_service: str = "evidence-processor"
    ) -> Event:
        """Create EvidenceUploaded event."""
        return Event(
            event_type=EventType.EVIDENCE_UPLOADED,
            data={
                "evidence_id": evidence_id,
                "case_id": case_id,
                "filename": filename,
                "file_size": file_size,
                "content_type": content_type,
                "uploaded_by": uploaded_by
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=source_service,
            correlation_id=str(uuid.uuid4())
        )
    
    @staticmethod
    def create_evidence_processed(
        evidence_id: str,
        processing_results: Dict[str, Any],
        processing_time_ms: int = 0,
        source_service: str = "evidence-processor"
    ) -> Event:
        """Create EvidenceProcessed event."""
        return Event(
            event_type=EventType.EVIDENCE_PROCESSED,
            data={
                "evidence_id": evidence_id,
                "processing_results": processing_results,
                "processing_time_ms": processing_time_ms
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=source_service,
            correlation_id=str(uuid.uuid4())
        )
    
    @staticmethod
    def create_storyboard_created(
        storyboard_id: str,
        case_id: str,
        created_by: str = "",
        source_service: str = "storyboard-service"
    ) -> Event:
        """Create StoryboardCreated event."""
        return Event(
            event_type=EventType.STORYBOARD_CREATED,
            data={
                "storyboard_id": storyboard_id,
                "case_id": case_id,
                "created_by": created_by
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=source_service,
            correlation_id=str(uuid.uuid4())
        )
    
    @staticmethod
    def create_timeline_compiled(
        timeline_id: str,
        storyboard_id: str,
        compilation_results: Dict[str, Any],
        source_service: str = "timeline-compiler"
    ) -> Event:
        """Create TimelineCompiled event."""
        return Event(
            event_type=EventType.TIMELINE_COMPILED,
            data={
                "timeline_id": timeline_id,
                "storyboard_id": storyboard_id,
                "compilation_results": compilation_results
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=source_service,
            correlation_id=str(uuid.uuid4())
        )
    
    @staticmethod
    def create_render_completed(
        render_id: str,
        storyboard_id: str,
        output_path: str = "",
        file_size: int = 0,
        render_time_ms: int = 0,
        source_service: str = "render-orchestrator"
    ) -> Event:
        """Create RenderCompleted event."""
        return Event(
            event_type=EventType.RENDER_COMPLETED,
            data={
                "render_id": render_id,
                "storyboard_id": storyboard_id,
                "output_path": output_path,
                "file_size": file_size,
                "render_time_ms": render_time_ms
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=source_service,
            correlation_id=str(uuid.uuid4())
        )
    
    @staticmethod
    def create_render_failed(
        render_id: str,
        storyboard_id: str,
        error_message: str = "",
        source_service: str = "render-orchestrator"
    ) -> Event:
        """Create RenderFailed event."""
        return Event(
            event_type=EventType.RENDER_FAILED,
            data={
                "render_id": render_id,
                "storyboard_id": storyboard_id,
                "error_message": error_message
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=source_service,
            correlation_id=str(uuid.uuid4())
        )
