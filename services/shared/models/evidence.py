"""Evidence data models for legal simulation platform."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class EvidenceType(Enum):
    """Evidence type enumeration."""
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    OBJECT = "object"
    TESTIMONY = "testimony"


class EvidenceStatus(Enum):
    """Evidence processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class EvidenceMetadata:
    """Metadata for evidence items."""
    filename: str
    content_type: str
    size_bytes: int
    checksum: str
    uploaded_by: str
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of evidence processing."""
    ocr_text: Optional[str] = None
    asr_transcript: Optional[str] = None
    extracted_entities: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    processing_time_ms: int = 0
    engine_used: str = ""


@dataclass
class Evidence:
    """Main evidence data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    metadata: EvidenceMetadata = field(default_factory=EvidenceMetadata)
    status: EvidenceStatus = EvidenceStatus.UPLOADED
    storage_id: str = ""
    processing_result: Optional[ProcessingResult] = None
    case_id: Optional[str] = None
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)
    worm_locked: bool = False
    
    def add_custody_entry(self, action: str, user: str, timestamp: Optional[datetime] = None) -> None:
        """Add chain of custody entry."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        entry = {
            "action": action,
            "user": user,
            "timestamp": timestamp.isoformat(),
            "checksum": self.metadata.checksum,
        }
        self.chain_of_custody.append(entry)
    
    def mark_processed(self, result: ProcessingResult) -> None:
        """Mark evidence as processed."""
        self.status = EvidenceStatus.PROCESSED
        self.processing_result = result
    
    def mark_failed(self, error: str) -> None:
        """Mark evidence processing as failed."""
        self.status = EvidenceStatus.FAILED
        if self.processing_result is None:
            self.processing_result = ProcessingResult()
        self.processing_result.confidence_scores["error"] = 0.0
    
    def apply_worm_lock(self) -> None:
        """Apply WORM lock to evidence."""
        self.worm_locked = True
        self.add_custody_entry("WORM_LOCK_APPLIED", "system")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence to dictionary."""
        result = {
            "id": self.id,
            "evidence_type": self.evidence_type.value,
            "metadata": {
                "filename": self.metadata.filename,
                "content_type": self.metadata.content_type,
                "size_bytes": self.metadata.size_bytes,
                "checksum": self.metadata.checksum,
                "uploaded_by": self.metadata.uploaded_by,
                "uploaded_at": self.metadata.uploaded_at.isoformat(),
                "description": self.metadata.description,
                "tags": self.metadata.tags,
            },
            "status": self.status.value,
            "storage_id": self.storage_id,
            "case_id": self.case_id,
            "chain_of_custody": self.chain_of_custody,
            "worm_locked": self.worm_locked,
        }
        
        if self.processing_result:
            result["processing_result"] = {
                "ocr_text": self.processing_result.ocr_text,
                "asr_transcript": self.processing_result.asr_transcript,
                "extracted_entities": self.processing_result.extracted_entities,
                "confidence_scores": self.processing_result.confidence_scores,
                "processing_time_ms": self.processing_result.processing_time_ms,
                "engine_used": self.processing_result.engine_used,
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        """Create evidence from dictionary."""
        metadata = EvidenceMetadata(
            filename=data["metadata"]["filename"],
            content_type=data["metadata"]["content_type"],
            size_bytes=data["metadata"]["size_bytes"],
            checksum=data["metadata"]["checksum"],
            uploaded_by=data["metadata"]["uploaded_by"],
            uploaded_at=datetime.fromisoformat(data["metadata"]["uploaded_at"]),
            description=data["metadata"].get("description", ""),
            tags=data["metadata"].get("tags", {}),
        )
        
        processing_result = None
        if "processing_result" in data:
            pr_data = data["processing_result"]
            processing_result = ProcessingResult(
                ocr_text=pr_data.get("ocr_text"),
                asr_transcript=pr_data.get("asr_transcript"),
                extracted_entities=pr_data.get("extracted_entities", []),
                confidence_scores=pr_data.get("confidence_scores", {}),
                processing_time_ms=pr_data.get("processing_time_ms", 0),
                engine_used=pr_data.get("engine_used", ""),
            )
        
        return cls(
            id=data["id"],
            evidence_type=EvidenceType(data["evidence_type"]),
            metadata=metadata,
            status=EvidenceStatus(data["status"]),
            storage_id=data.get("storage_id", ""),
            processing_result=processing_result,
            case_id=data.get("case_id"),
            chain_of_custody=data.get("chain_of_custody", []),
            worm_locked=data.get("worm_locked", False),
        )
