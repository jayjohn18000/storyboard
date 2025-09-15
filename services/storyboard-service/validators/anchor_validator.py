"""Evidence anchor validator for storyboards."""

from typing import List, Dict, Any, Set
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from services.shared.models.storyboard import Storyboard, Scene, EvidenceAnchor


class AnchorValidator:
    """Validator for evidence anchors in storyboards."""
    
    def __init__(self):
        pass
    
    async def validate(self, storyboard_data: Dict[str, Any], evidence_ids: List[str]) -> Dict[str, Any]:
        """Validate evidence anchors in storyboard."""
        try:
            # Parse storyboard
            storyboard = Storyboard.from_dict(storyboard_data)
            
            # Get all evidence IDs referenced in storyboard
            referenced_ids = set(storyboard.get_evidence_ids())
            
            # Get provided evidence IDs
            provided_ids = set(evidence_ids)
            
            # Find missing evidence
            missing_evidence = referenced_ids - provided_ids
            
            # Find unused evidence
            unused_evidence = provided_ids - referenced_ids
            
            # Validate individual anchors
            anchor_errors = []
            for scene in storyboard.scenes:
                for anchor in scene.evidence_anchors:
                    errors = self._validate_anchor(anchor)
                    if errors:
                        anchor_errors.extend([
                            f"Scene '{scene.title}', Anchor '{anchor.evidence_id}': {error}"
                            for error in errors
                        ])
            
            # Check for timing conflicts
            timing_conflicts = self._check_timing_conflicts(storyboard)
            
            # Calculate coverage
            coverage_percentage = self._calculate_coverage(referenced_ids, provided_ids)
            
            # Determine overall validity
            is_valid = (
                len(missing_evidence) == 0 and
                len(anchor_errors) == 0 and
                len(timing_conflicts) == 0
            )
            
            return {
                "is_valid": is_valid,
                "missing_evidence": list(missing_evidence),
                "unused_evidence": list(unused_evidence),
                "anchor_errors": anchor_errors,
                "timing_conflicts": timing_conflicts,
                "coverage_percentage": coverage_percentage,
                "referenced_evidence_count": len(referenced_ids),
                "provided_evidence_count": len(provided_ids),
            }
            
        except Exception as e:
            raise Exception(f"Anchor validation failed: {str(e)}")
    
    def _validate_anchor(self, anchor: EvidenceAnchor) -> List[str]:
        """Validate individual evidence anchor."""
        errors = []
        
        # Check evidence ID
        if not anchor.evidence_id:
            errors.append("Evidence ID is required")
        
        # Check timing
        if anchor.start_time < 0:
            errors.append("Start time must be non-negative")
        
        if anchor.end_time <= anchor.start_time:
            errors.append("End time must be greater than start time")
        
        # Check confidence
        if not (0.0 <= anchor.confidence <= 1.0):
            errors.append("Confidence must be between 0.0 and 1.0")
        
        # Check description
        if not anchor.description:
            errors.append("Description is required")
        
        return errors
    
    def _check_timing_conflicts(self, storyboard: Storyboard) -> List[str]:
        """Check for timing conflicts between anchors."""
        conflicts = []
        
        for scene in storyboard.scenes:
            # Group anchors by evidence ID
            evidence_anchors = {}
            for anchor in scene.evidence_anchors:
                if anchor.evidence_id not in evidence_anchors:
                    evidence_anchors[anchor.evidence_id] = []
                evidence_anchors[anchor.evidence_id].append(anchor)
            
            # Check for overlaps within each evidence ID
            for evidence_id, anchors in evidence_anchors.items():
                if len(anchors) > 1:
                    # Sort by start time
                    sorted_anchors = sorted(anchors, key=lambda a: a.start_time)
                    
                    # Check for overlaps
                    for i in range(len(sorted_anchors) - 1):
                        current = sorted_anchors[i]
                        next_anchor = sorted_anchors[i + 1]
                        
                        if current.end_time > next_anchor.start_time:
                            conflicts.append(
                                f"Scene '{scene.title}', Evidence '{evidence_id}': "
                                f"Overlapping anchors at {current.start_time}-{current.end_time} "
                                f"and {next_anchor.start_time}-{next_anchor.end_time}"
                            )
        
        return conflicts
    
    def _calculate_coverage(self, referenced_ids: Set[str], provided_ids: Set[str]) -> float:
        """Calculate evidence coverage percentage."""
        if not provided_ids:
            return 0.0
        
        covered_ids = referenced_ids & provided_ids
        return len(covered_ids) / len(provided_ids) * 100.0
    
    def _validate_evidence_references(self, storyboard: Storyboard, evidence_ids: List[str]) -> List[str]:
        """Validate that all evidence references are valid."""
        errors = []
        provided_ids = set(evidence_ids)
        
        for scene in storyboard.scenes:
            for anchor in scene.evidence_anchors:
                if anchor.evidence_id not in provided_ids:
                    errors.append(
                        f"Scene '{scene.title}': Evidence ID '{anchor.evidence_id}' not found"
                    )
        
        return errors
    
    def _check_anchor_consistency(self, storyboard: Storyboard) -> List[str]:
        """Check for consistency issues in anchors."""
        issues = []
        
        for scene in storyboard.scenes:
            # Check for duplicate evidence IDs in same scene
            evidence_ids = [anchor.evidence_id for anchor in scene.evidence_anchors]
            if len(evidence_ids) != len(set(evidence_ids)):
                issues.append(
                    f"Scene '{scene.title}': Duplicate evidence IDs found"
                )
            
            # Check for anchors that exceed scene duration
            for anchor in scene.evidence_anchors:
                if anchor.end_time > scene.duration_seconds:
                    issues.append(
                        f"Scene '{scene.title}': Anchor '{anchor.evidence_id}' "
                        f"extends beyond scene duration ({anchor.end_time} > {scene.duration_seconds})"
                    )
        
        return issues
    
    def _validate_anchor_annotations(self, storyboard: Storyboard) -> List[str]:
        """Validate anchor annotations."""
        issues = []
        
        for scene in storyboard.scenes:
            for anchor in scene.evidence_anchors:
                # Check for required annotations
                if "highlight" in anchor.annotations:
                    highlight = anchor.annotations["highlight"]
                    if not isinstance(highlight, (str, list)):
                        issues.append(
                            f"Scene '{scene.title}', Anchor '{anchor.evidence_id}': "
                            "Invalid highlight annotation"
                        )
                
                # Check for valid annotation types
                valid_types = {"highlight", "note", "marker", "emphasis"}
                for key in anchor.annotations.keys():
                    if key not in valid_types:
                        issues.append(
                            f"Scene '{scene.title}', Anchor '{anchor.evidence_id}': "
                            f"Unknown annotation type '{key}'"
                        )
        
        return issues
    
    def _check_scene_consistency(self, storyboard: Storyboard) -> List[str]:
        """Check for scene-level consistency issues."""
        issues = []
        
        # Check for scene duration consistency
        total_duration = sum(scene.duration_seconds for scene in storyboard.scenes)
        if total_duration <= 0:
            issues.append("Total storyboard duration must be positive")
        
        # Check for scene ordering
        for i in range(len(storyboard.scenes) - 1):
            current_scene = storyboard.scenes[i]
            next_scene = storyboard.scenes[i + 1]
            
            if current_scene.start_time >= next_scene.start_time:
                issues.append(
                    f"Scene '{current_scene.title}' start time must be less than "
                    f"scene '{next_scene.title}' start time"
                )
        
        return issues
