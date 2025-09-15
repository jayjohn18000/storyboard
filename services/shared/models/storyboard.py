"""Storyboard data models for legal simulation platform."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class StoryboardStatus(Enum):
    """Storyboard status enumeration."""
    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    COMPILING = "compiling"
    COMPILED = "compiled"
    FAILED = "failed"


class SceneType(Enum):
    """Scene type enumeration."""
    EVIDENCE_DISPLAY = "evidence_display"
    TIMELINE_VISUALIZATION = "timeline_visualization"
    EXPERT_TESTIMONY = "expert_testimony"
    RECONSTRUCTION = "reconstruction"
    COMPARISON = "comparison"


@dataclass
class EvidenceAnchor:
    """Anchor linking evidence to storyboard elements."""
    evidence_id: str
    start_time: float
    end_time: float
    description: str
    confidence: float = 1.0
    annotations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    """Individual scene in storyboard."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scene_type: SceneType = SceneType.EVIDENCE_DISPLAY
    title: str = ""
    description: str = ""
    duration_seconds: float = 5.0
    start_time: float = 0.0
    evidence_anchors: List[EvidenceAnchor] = field(default_factory=list)
    camera_config: Dict[str, Any] = field(default_factory=dict)
    lighting_config: Dict[str, Any] = field(default_factory=dict)
    materials: List[Dict[str, Any]] = field(default_factory=list)
    transitions: Dict[str, Any] = field(default_factory=dict)
    
    def add_evidence_anchor(self, anchor: EvidenceAnchor) -> None:
        """Add evidence anchor to scene."""
        self.evidence_anchors.append(anchor)
    
    def get_total_duration(self) -> float:
        """Get total duration including transitions."""
        transition_time = sum(
            transition.get("duration", 0) 
            for transition in self.transitions.values()
        )
        return self.duration_seconds + transition_time


@dataclass
class StoryboardMetadata:
    """Metadata for storyboard."""
    title: str
    description: str
    case_id: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of storyboard validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    coverage_percentage: float = 0.0
    evidence_coverage: Dict[str, float] = field(default_factory=dict)
    validated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Storyboard:
    """Main storyboard data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: StoryboardMetadata = field(default_factory=StoryboardMetadata)
    status: StoryboardStatus = StoryboardStatus.DRAFT
    scenes: List[Scene] = field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    timeline_id: Optional[str] = None
    render_config: Dict[str, Any] = field(default_factory=dict)
    
    def add_scene(self, scene: Scene) -> None:
        """Add scene to storyboard."""
        self.scenes.append(scene)
        self.metadata.updated_at = datetime.utcnow()
    
    def remove_scene(self, scene_id: str) -> bool:
        """Remove scene from storyboard."""
        for i, scene in enumerate(self.scenes):
            if scene.id == scene_id:
                del self.scenes[i]
                self.metadata.updated_at = datetime.utcnow()
                return True
        return False
    
    def get_total_duration(self) -> float:
        """Get total duration of storyboard."""
        return sum(scene.get_total_duration() for scene in self.scenes)
    
    def get_evidence_ids(self) -> List[str]:
        """Get all evidence IDs referenced in storyboard."""
        evidence_ids = set()
        for scene in self.scenes:
            for anchor in scene.evidence_anchors:
                evidence_ids.add(anchor.evidence_id)
        return list(evidence_ids)
    
    def validate_coverage(self, evidence_ids: List[str]) -> ValidationResult:
        """Validate evidence coverage."""
        referenced_ids = set(self.get_evidence_ids())
        provided_ids = set(evidence_ids)
        
        missing_evidence = referenced_ids - provided_ids
        unused_evidence = provided_ids - referenced_ids
        
        errors = []
        warnings = []
        
        if missing_evidence:
            errors.append(f"Missing evidence: {', '.join(missing_evidence)}")
        
        if unused_evidence:
            warnings.append(f"Unused evidence: {', '.join(unused_evidence)}")
        
        coverage_percentage = len(referenced_ids) / len(provided_ids) * 100 if provided_ids else 0
        
        evidence_coverage = {
            evidence_id: 1.0 if evidence_id in referenced_ids else 0.0
            for evidence_id in evidence_ids
        }
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            coverage_percentage=coverage_percentage,
            evidence_coverage=evidence_coverage,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert storyboard to dictionary."""
        result = {
            "id": self.id,
            "metadata": {
                "title": self.metadata.title,
                "description": self.metadata.description,
                "case_id": self.metadata.case_id,
                "created_by": self.metadata.created_by,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "version": self.metadata.version,
                "tags": self.metadata.tags,
            },
            "status": self.status.value,
            "scenes": [
                {
                    "id": scene.id,
                    "scene_type": scene.scene_type.value,
                    "title": scene.title,
                    "description": scene.description,
                    "duration_seconds": scene.duration_seconds,
                    "start_time": scene.start_time,
                    "evidence_anchors": [
                        {
                            "evidence_id": anchor.evidence_id,
                            "start_time": anchor.start_time,
                            "end_time": anchor.end_time,
                            "description": anchor.description,
                            "confidence": anchor.confidence,
                            "annotations": anchor.annotations,
                        }
                        for anchor in scene.evidence_anchors
                    ],
                    "camera_config": scene.camera_config,
                    "lighting_config": scene.lighting_config,
                    "materials": scene.materials,
                    "transitions": scene.transitions,
                }
                for scene in self.scenes
            ],
            "timeline_id": self.timeline_id,
            "render_config": self.render_config,
        }
        
        if self.validation_result:
            result["validation_result"] = {
                "is_valid": self.validation_result.is_valid,
                "errors": self.validation_result.errors,
                "warnings": self.validation_result.warnings,
                "coverage_percentage": self.validation_result.coverage_percentage,
                "evidence_coverage": self.validation_result.evidence_coverage,
                "validated_at": self.validation_result.validated_at.isoformat(),
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Storyboard":
        """Create storyboard from dictionary."""
        metadata = StoryboardMetadata(
            title=data["metadata"]["title"],
            description=data["metadata"]["description"],
            case_id=data["metadata"]["case_id"],
            created_by=data["metadata"]["created_by"],
            created_at=datetime.fromisoformat(data["metadata"]["created_at"]),
            updated_at=datetime.fromisoformat(data["metadata"]["updated_at"]),
            version=data["metadata"].get("version", "1.0"),
            tags=data["metadata"].get("tags", {}),
        )
        
        scenes = []
        for scene_data in data.get("scenes", []):
            evidence_anchors = [
                EvidenceAnchor(
                    evidence_id=anchor["evidence_id"],
                    start_time=anchor["start_time"],
                    end_time=anchor["end_time"],
                    description=anchor["description"],
                    confidence=anchor.get("confidence", 1.0),
                    annotations=anchor.get("annotations", {}),
                )
                for anchor in scene_data.get("evidence_anchors", [])
            ]
            
            scene = Scene(
                id=scene_data["id"],
                scene_type=SceneType(scene_data["scene_type"]),
                title=scene_data.get("title", ""),
                description=scene_data.get("description", ""),
                duration_seconds=scene_data.get("duration_seconds", 5.0),
                start_time=scene_data.get("start_time", 0.0),
                evidence_anchors=evidence_anchors,
                camera_config=scene_data.get("camera_config", {}),
                lighting_config=scene_data.get("lighting_config", {}),
                materials=scene_data.get("materials", []),
                transitions=scene_data.get("transitions", {}),
            )
            scenes.append(scene)
        
        validation_result = None
        if "validation_result" in data:
            vr_data = data["validation_result"]
            validation_result = ValidationResult(
                is_valid=vr_data["is_valid"],
                errors=vr_data.get("errors", []),
                warnings=vr_data.get("warnings", []),
                coverage_percentage=vr_data.get("coverage_percentage", 0.0),
                evidence_coverage=vr_data.get("evidence_coverage", {}),
                validated_at=datetime.fromisoformat(vr_data["validated_at"]),
            )
        
        return cls(
            id=data["id"],
            metadata=metadata,
            status=StoryboardStatus(data["status"]),
            scenes=scenes,
            validation_result=validation_result,
            timeline_id=data.get("timeline_id"),
            render_config=data.get("render_config", {}),
        )
