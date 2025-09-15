"""Evidence coverage calculator for storyboards."""

from typing import List, Dict, Any, Set
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from services.shared.models.storyboard import Storyboard, Scene, EvidenceAnchor


class CoverageCalculator:
    """Calculator for evidence coverage in storyboards."""
    
    def __init__(self):
        pass
    
    async def calculate_coverage(self, storyboard_data: Dict[str, Any], evidence_ids: List[str]) -> Dict[str, Any]:
        """Calculate evidence coverage for storyboard."""
        try:
            # Parse storyboard
            storyboard = Storyboard.from_dict(storyboard_data)
            
            # Get all evidence IDs referenced in storyboard
            referenced_ids = set(storyboard.get_evidence_ids())
            
            # Get provided evidence IDs
            provided_ids = set(evidence_ids)
            
            # Calculate overall coverage
            overall_coverage = self._calculate_overall_coverage(referenced_ids, provided_ids)
            
            # Calculate per-evidence coverage
            evidence_coverage = self._calculate_per_evidence_coverage(storyboard, provided_ids)
            
            # Calculate scene coverage
            scene_coverage = self._calculate_scene_coverage(storyboard, provided_ids)
            
            # Calculate temporal coverage
            temporal_coverage = self._calculate_temporal_coverage(storyboard, provided_ids)
            
            # Calculate coverage gaps
            coverage_gaps = self._identify_coverage_gaps(storyboard, provided_ids)
            
            # Calculate coverage quality metrics
            quality_metrics = self._calculate_quality_metrics(storyboard, provided_ids)
            
            return {
                "overall_coverage": overall_coverage,
                "evidence_coverage": evidence_coverage,
                "scene_coverage": scene_coverage,
                "temporal_coverage": temporal_coverage,
                "coverage_gaps": coverage_gaps,
                "quality_metrics": quality_metrics,
                "referenced_evidence_count": len(referenced_ids),
                "provided_evidence_count": len(provided_ids),
                "total_scenes": len(storyboard.scenes),
                "total_duration": storyboard.get_total_duration(),
            }
            
        except Exception as e:
            raise Exception(f"Coverage calculation failed: {str(e)}")
    
    def _calculate_overall_coverage(self, referenced_ids: Set[str], provided_ids: Set[str]) -> Dict[str, Any]:
        """Calculate overall evidence coverage."""
        if not provided_ids:
            return {
                "percentage": 0.0,
                "covered_count": 0,
                "total_count": 0,
                "missing_evidence": list(referenced_ids),
                "unused_evidence": [],
            }
        
        covered_ids = referenced_ids & provided_ids
        missing_evidence = referenced_ids - provided_ids
        unused_evidence = provided_ids - referenced_ids
        
        return {
            "percentage": len(covered_ids) / len(provided_ids) * 100.0,
            "covered_count": len(covered_ids),
            "total_count": len(provided_ids),
            "missing_evidence": list(missing_evidence),
            "unused_evidence": list(unused_evidence),
        }
    
    def _calculate_per_evidence_coverage(self, storyboard: Storyboard, provided_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
        """Calculate coverage for each evidence item."""
        evidence_coverage = {}
        
        for evidence_id in provided_ids:
            # Find all references to this evidence
            references = []
            total_duration = 0.0
            
            for scene in storyboard.scenes:
                for anchor in scene.evidence_anchors:
                    if anchor.evidence_id == evidence_id:
                        references.append({
                            "scene_title": scene.title,
                            "start_time": anchor.start_time,
                            "end_time": anchor.end_time,
                            "duration": anchor.end_time - anchor.start_time,
                            "confidence": anchor.confidence,
                        })
                        total_duration += anchor.end_time - anchor.start_time
            
            # Calculate coverage metrics
            coverage_percentage = (total_duration / storyboard.get_total_duration() * 100.0) if storyboard.get_total_duration() > 0 else 0.0
            
            evidence_coverage[evidence_id] = {
                "references_count": len(references),
                "total_duration": total_duration,
                "coverage_percentage": coverage_percentage,
                "references": references,
                "is_covered": len(references) > 0,
            }
        
        return evidence_coverage
    
    def _calculate_scene_coverage(self, storyboard: Storyboard, provided_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
        """Calculate coverage for each scene."""
        scene_coverage = {}
        
        for scene in storyboard.scenes:
            # Count evidence references in scene
            evidence_count = len(scene.evidence_anchors)
            covered_evidence = set(anchor.evidence_id for anchor in scene.evidence_anchors if anchor.evidence_id in provided_ids)
            
            # Calculate coverage metrics
            coverage_percentage = (len(covered_evidence) / len(provided_ids) * 100.0) if provided_ids else 0.0
            
            # Calculate temporal coverage within scene
            temporal_coverage = self._calculate_scene_temporal_coverage(scene, provided_ids)
            
            scene_coverage[scene.title] = {
                "evidence_count": evidence_count,
                "covered_evidence_count": len(covered_evidence),
                "coverage_percentage": coverage_percentage,
                "temporal_coverage": temporal_coverage,
                "duration": scene.duration_seconds,
                "evidence_ids": list(covered_evidence),
            }
        
        return scene_coverage
    
    def _calculate_scene_temporal_coverage(self, scene: Scene, provided_ids: Set[str]) -> Dict[str, Any]:
        """Calculate temporal coverage within a scene."""
        if not scene.evidence_anchors:
            return {
                "percentage": 0.0,
                "covered_duration": 0.0,
                "total_duration": scene.duration_seconds,
            }
        
        # Calculate total covered duration
        covered_duration = 0.0
        for anchor in scene.evidence_anchors:
            if anchor.evidence_id in provided_ids:
                covered_duration += anchor.end_time - anchor.start_time
        
        # Calculate percentage
        coverage_percentage = (covered_duration / scene.duration_seconds * 100.0) if scene.duration_seconds > 0 else 0.0
        
        return {
            "percentage": coverage_percentage,
            "covered_duration": covered_duration,
            "total_duration": scene.duration_seconds,
        }
    
    def _calculate_temporal_coverage(self, storyboard: Storyboard, provided_ids: Set[str]) -> Dict[str, Any]:
        """Calculate temporal coverage across the entire storyboard."""
        total_duration = storyboard.get_total_duration()
        if total_duration <= 0:
            return {
                "percentage": 0.0,
                "covered_duration": 0.0,
                "total_duration": 0.0,
            }
        
        # Calculate total covered duration
        covered_duration = 0.0
        for scene in storyboard.scenes:
            for anchor in scene.evidence_anchors:
                if anchor.evidence_id in provided_ids:
                    covered_duration += anchor.end_time - anchor.start_time
        
        # Calculate percentage
        coverage_percentage = (covered_duration / total_duration * 100.0) if total_duration > 0 else 0.0
        
        return {
            "percentage": coverage_percentage,
            "covered_duration": covered_duration,
            "total_duration": total_duration,
        }
    
    def _identify_coverage_gaps(self, storyboard: Storyboard, provided_ids: Set[str]) -> List[Dict[str, Any]]:
        """Identify gaps in evidence coverage."""
        gaps = []
        
        for scene in storyboard.scenes:
            # Find time ranges without evidence coverage
            covered_ranges = []
            for anchor in scene.evidence_anchors:
                if anchor.evidence_id in provided_ids:
                    covered_ranges.append((anchor.start_time, anchor.end_time))
            
            # Sort ranges by start time
            covered_ranges.sort(key=lambda x: x[0])
            
            # Find gaps
            current_time = 0.0
            for start_time, end_time in covered_ranges:
                if start_time > current_time:
                    gaps.append({
                        "scene_title": scene.title,
                        "start_time": current_time,
                        "end_time": start_time,
                        "duration": start_time - current_time,
                        "gap_type": "uncovered",
                    })
                current_time = max(current_time, end_time)
            
            # Check for gap at end of scene
            if current_time < scene.duration_seconds:
                gaps.append({
                    "scene_title": scene.title,
                    "start_time": current_time,
                    "end_time": scene.duration_seconds,
                    "duration": scene.duration_seconds - current_time,
                    "gap_type": "uncovered",
                })
        
        return gaps
    
    def _calculate_quality_metrics(self, storyboard: Storyboard, provided_ids: Set[str]) -> Dict[str, Any]:
        """Calculate quality metrics for evidence coverage."""
        metrics = {
            "average_confidence": 0.0,
            "confidence_distribution": {},
            "evidence_diversity": 0.0,
            "temporal_distribution": {},
            "scene_distribution": {},
        }
        
        # Calculate average confidence
        confidences = []
        for scene in storyboard.scenes:
            for anchor in scene.evidence_anchors:
                if anchor.evidence_id in provided_ids:
                    confidences.append(anchor.confidence)
        
        if confidences:
            metrics["average_confidence"] = sum(confidences) / len(confidences)
            
            # Calculate confidence distribution
            high_confidence = sum(1 for c in confidences if c >= 0.8)
            medium_confidence = sum(1 for c in confidences if 0.5 <= c < 0.8)
            low_confidence = sum(1 for c in confidences if c < 0.5)
            
            metrics["confidence_distribution"] = {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence,
            }
        
        # Calculate evidence diversity
        unique_evidence = set()
        for scene in storyboard.scenes:
            for anchor in scene.evidence_anchors:
                if anchor.evidence_id in provided_ids:
                    unique_evidence.add(anchor.evidence_id)
        
        metrics["evidence_diversity"] = len(unique_evidence) / len(provided_ids) * 100.0 if provided_ids else 0.0
        
        # Calculate temporal distribution
        temporal_distribution = {}
        for scene in storyboard.scenes:
            scene_duration = 0.0
            for anchor in scene.evidence_anchors:
                if anchor.evidence_id in provided_ids:
                    scene_duration += anchor.end_time - anchor.start_time
            
            temporal_distribution[scene.title] = {
                "duration": scene_duration,
                "percentage": (scene_duration / storyboard.get_total_duration() * 100.0) if storyboard.get_total_duration() > 0 else 0.0,
            }
        
        metrics["temporal_distribution"] = temporal_distribution
        
        # Calculate scene distribution
        scene_distribution = {}
        for scene in storyboard.scenes:
            evidence_count = len([anchor for anchor in scene.evidence_anchors if anchor.evidence_id in provided_ids])
            scene_distribution[scene.title] = {
                "evidence_count": evidence_count,
                "percentage": (evidence_count / len(provided_ids) * 100.0) if provided_ids else 0.0,
            }
        
        metrics["scene_distribution"] = scene_distribution
        
        return metrics
