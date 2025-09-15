"""Case data models for legal simulation platform."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class CaseStatus(Enum):
    """Case status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"


class CaseType(Enum):
    """Case type enumeration."""
    CIVIL = "civil"
    CRIMINAL = "criminal"
    ADMINISTRATIVE = "administrative"
    APPELLATE = "appellate"


class CaseMode(Enum):
    """Case mode enumeration."""
    DEMONSTRATIVE = "demonstrative"
    SANDBOX = "sandbox"


@dataclass
class CaseMetadata:
    """Metadata for a legal case."""
    case_number: str
    title: str
    case_type: CaseType
    jurisdiction: str
    court: str
    judge: Optional[str] = None
    attorneys: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Case:
    """Main case data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: CaseMetadata = field(default_factory=CaseMetadata)
    status: CaseStatus = CaseStatus.DRAFT
    evidence_ids: List[str] = field(default_factory=list)
    storyboard_ids: List[str] = field(default_factory=list)
    render_ids: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    
    def add_evidence(self, evidence_id: str) -> None:
        """Add evidence to case."""
        if evidence_id not in self.evidence_ids:
            self.evidence_ids.append(evidence_id)
            self.metadata.updated_at = datetime.utcnow()
    
    def add_storyboard(self, storyboard_id: str) -> None:
        """Add storyboard to case."""
        if storyboard_id not in self.storyboard_ids:
            self.storyboard_ids.append(storyboard_id)
            self.metadata.updated_at = datetime.utcnow()
    
    def add_render(self, render_id: str) -> None:
        """Add render to case."""
        if render_id not in self.render_ids:
            self.render_ids.append(render_id)
            self.metadata.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert case to dictionary."""
        return {
            "id": self.id,
            "metadata": {
                "case_number": self.metadata.case_number,
                "title": self.metadata.title,
                "case_type": self.metadata.case_type.value,
                "jurisdiction": self.metadata.jurisdiction,
                "court": self.metadata.court,
                "judge": self.metadata.judge,
                "attorneys": self.metadata.attorneys,
                "created_by": self.metadata.created_by,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
            },
            "status": self.status.value,
            "evidence_ids": self.evidence_ids,
            "storyboard_ids": self.storyboard_ids,
            "render_ids": self.render_ids,
            "tags": self.tags,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Case":
        """Create case from dictionary."""
        metadata = CaseMetadata(
            case_number=data["metadata"]["case_number"],
            title=data["metadata"]["title"],
            case_type=CaseType(data["metadata"]["case_type"]),
            jurisdiction=data["metadata"]["jurisdiction"],
            court=data["metadata"]["court"],
            judge=data["metadata"].get("judge"),
            attorneys=data["metadata"].get("attorneys", []),
            created_by=data["metadata"].get("created_by", ""),
            created_at=datetime.fromisoformat(data["metadata"]["created_at"]),
            updated_at=datetime.fromisoformat(data["metadata"]["updated_at"]),
        )
        
        return cls(
            id=data["id"],
            metadata=metadata,
            status=CaseStatus(data["status"]),
            evidence_ids=data.get("evidence_ids", []),
            storyboard_ids=data.get("storyboard_ids", []),
            render_ids=data.get("render_ids", []),
            tags=data.get("tags", {}),
            notes=data.get("notes", ""),
        )
