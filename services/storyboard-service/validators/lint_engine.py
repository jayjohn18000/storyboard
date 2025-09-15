"""Lint engine for storyboard validation."""

from typing import List, Dict, Any, Set
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from services.shared.models.storyboard import Storyboard, Scene, EvidenceAnchor, SceneType


class LintEngine:
    """Lint engine for storyboard validation."""
    
    def __init__(self):
        self.rules = [
            self._check_required_fields,
            self._check_scene_duration,
            self._check_evidence_anchors,
            self._check_camera_config,
            self._check_lighting_config,
            self._check_materials,
            self._check_transitions,
            self._check_scene_ordering,
            self._check_timing_consistency,
            self._check_naming_conventions,
        ]
    
    async def lint(self, storyboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Lint storyboard for issues."""
        try:
            # Parse storyboard
            storyboard = Storyboard.from_dict(storyboard_data)
            
            # Run all lint rules
            issues = []
            warnings = []
            
            for rule in self.rules:
                rule_issues, rule_warnings = rule(storyboard)
                issues.extend(rule_issues)
                warnings.extend(rule_warnings)
            
            # Calculate severity
            severity = self._calculate_severity(issues, warnings)
            
            # Generate summary
            summary = self._generate_summary(issues, warnings)
            
            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "severity": severity,
                "summary": summary,
                "total_issues": len(issues),
                "total_warnings": len(warnings),
            }
            
        except Exception as e:
            raise Exception(f"Linting failed: {str(e)}")
    
    def _check_required_fields(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check for required fields."""
        issues = []
        warnings = []
        
        # Check storyboard metadata
        if not storyboard.metadata.title:
            issues.append({
                "type": "missing_field",
                "severity": "error",
                "message": "Storyboard title is required",
                "field": "metadata.title",
            })
        
        if not storyboard.metadata.description:
            warnings.append({
                "type": "missing_field",
                "severity": "warning",
                "message": "Storyboard description is recommended",
                "field": "metadata.description",
            })
        
        if not storyboard.metadata.case_id:
            issues.append({
                "type": "missing_field",
                "severity": "error",
                "message": "Case ID is required",
                "field": "metadata.case_id",
            })
        
        # Check scenes
        if not storyboard.scenes:
            issues.append({
                "type": "missing_field",
                "severity": "error",
                "message": "At least one scene is required",
                "field": "scenes",
            })
        
        return issues, warnings
    
    def _check_scene_duration(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check scene duration validity."""
        issues = []
        warnings = []
        
        for i, scene in enumerate(storyboard.scenes):
            # Check duration
            if scene.duration_seconds <= 0:
                issues.append({
                    "type": "invalid_duration",
                    "severity": "error",
                    "message": f"Scene {i+1} duration must be positive",
                    "scene": scene.title,
                    "value": scene.duration_seconds,
                })
            
            if scene.duration_seconds > 60:
                warnings.append({
                    "type": "long_duration",
                    "severity": "warning",
                    "message": f"Scene {i+1} duration is very long ({scene.duration_seconds}s)",
                    "scene": scene.title,
                    "value": scene.duration_seconds,
                })
            
            if scene.duration_seconds < 1:
                warnings.append({
                    "type": "short_duration",
                    "severity": "warning",
                    "message": f"Scene {i+1} duration is very short ({scene.duration_seconds}s)",
                    "scene": scene.title,
                    "value": scene.duration_seconds,
                })
        
        return issues, warnings
    
    def _check_evidence_anchors(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check evidence anchors validity."""
        issues = []
        warnings = []
        
        for i, scene in enumerate(storyboard.scenes):
            # Check for evidence anchors
            if not scene.evidence_anchors:
                warnings.append({
                    "type": "no_evidence",
                    "severity": "warning",
                    "message": f"Scene {i+1} has no evidence anchors",
                    "scene": scene.title,
                })
            
            # Check individual anchors
            for j, anchor in enumerate(scene.evidence_anchors):
                # Check evidence ID
                if not anchor.evidence_id:
                    issues.append({
                        "type": "missing_evidence_id",
                        "severity": "error",
                        "message": f"Scene {i+1}, Anchor {j+1}: Evidence ID is required",
                        "scene": scene.title,
                        "anchor_index": j,
                    })
                
                # Check timing
                if anchor.start_time < 0:
                    issues.append({
                        "type": "invalid_start_time",
                        "severity": "error",
                        "message": f"Scene {i+1}, Anchor {j+1}: Start time must be non-negative",
                        "scene": scene.title,
                        "anchor_index": j,
                        "value": anchor.start_time,
                    })
                
                if anchor.end_time <= anchor.start_time:
                    issues.append({
                        "type": "invalid_end_time",
                        "severity": "error",
                        "message": f"Scene {i+1}, Anchor {j+1}: End time must be greater than start time",
                        "scene": scene.title,
                        "anchor_index": j,
                        "value": anchor.end_time,
                    })
                
                if anchor.end_time > scene.duration_seconds:
                    issues.append({
                        "type": "anchor_exceeds_scene",
                        "severity": "error",
                        "message": f"Scene {i+1}, Anchor {j+1}: Anchor extends beyond scene duration",
                        "scene": scene.title,
                        "anchor_index": j,
                        "value": anchor.end_time,
                        "scene_duration": scene.duration_seconds,
                    })
                
                # Check confidence
                if not (0.0 <= anchor.confidence <= 1.0):
                    issues.append({
                        "type": "invalid_confidence",
                        "severity": "error",
                        "message": f"Scene {i+1}, Anchor {j+1}: Confidence must be between 0.0 and 1.0",
                        "scene": scene.title,
                        "anchor_index": j,
                        "value": anchor.confidence,
                    })
                
                # Check description
                if not anchor.description:
                    warnings.append({
                        "type": "missing_description",
                        "severity": "warning",
                        "message": f"Scene {i+1}, Anchor {j+1}: Description is recommended",
                        "scene": scene.title,
                        "anchor_index": j,
                    })
        
        return issues, warnings
    
    def _check_camera_config(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check camera configuration validity."""
        issues = []
        warnings = []
        
        for i, scene in enumerate(storyboard.scenes):
            camera_config = scene.camera_config
            
            # Check for required camera fields
            if "position" in camera_config:
                position = camera_config["position"]
                if not isinstance(position, (list, tuple)) or len(position) != 3:
                    issues.append({
                        "type": "invalid_camera_position",
                        "severity": "error",
                        "message": f"Scene {i+1}: Camera position must be a 3-element array",
                        "scene": scene.title,
                        "value": position,
                    })
            
            if "rotation" in camera_config:
                rotation = camera_config["rotation"]
                if not isinstance(rotation, (list, tuple)) or len(rotation) != 3:
                    issues.append({
                        "type": "invalid_camera_rotation",
                        "severity": "error",
                        "message": f"Scene {i+1}: Camera rotation must be a 3-element array",
                        "scene": scene.title,
                        "value": rotation,
                    })
            
            if "focal_length" in camera_config:
                focal_length = camera_config["focal_length"]
                if not isinstance(focal_length, (int, float)) or focal_length <= 0:
                    issues.append({
                        "type": "invalid_focal_length",
                        "severity": "error",
                        "message": f"Scene {i+1}: Focal length must be a positive number",
                        "scene": scene.title,
                        "value": focal_length,
                    })
            
            if "fov" in camera_config:
                fov = camera_config["fov"]
                if not isinstance(fov, (int, float)) or not (0 < fov < 180):
                    issues.append({
                        "type": "invalid_fov",
                        "severity": "error",
                        "message": f"Scene {i+1}: Field of view must be between 0 and 180 degrees",
                        "scene": scene.title,
                        "value": fov,
                    })
        
        return issues, warnings
    
    def _check_lighting_config(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check lighting configuration validity."""
        issues = []
        warnings = []
        
        for i, scene in enumerate(storyboard.scenes):
            lighting_config = scene.lighting_config
            
            # Check brightness
            if "brightness" in lighting_config:
                brightness = lighting_config["brightness"]
                if not isinstance(brightness, (int, float)) or not (0 <= brightness <= 10):
                    issues.append({
                        "type": "invalid_brightness",
                        "severity": "error",
                        "message": f"Scene {i+1}: Brightness must be between 0 and 10",
                        "scene": scene.title,
                        "value": brightness,
                    })
            
            # Check color temperature
            if "color_temperature" in lighting_config:
                color_temp = lighting_config["color_temperature"]
                if not isinstance(color_temp, (int, float)) or not (1000 <= color_temp <= 10000):
                    issues.append({
                        "type": "invalid_color_temperature",
                        "severity": "error",
                        "message": f"Scene {i+1}: Color temperature must be between 1000 and 10000K",
                        "scene": scene.title,
                        "value": color_temp,
                    })
            
            # Check color
            if "color" in lighting_config:
                color = lighting_config["color"]
                if not isinstance(color, (list, tuple)) or len(color) != 3:
                    issues.append({
                        "type": "invalid_color",
                        "severity": "error",
                        "message": f"Scene {i+1}: Color must be a 3-element RGB array",
                        "scene": scene.title,
                        "value": color,
                    })
        
        return issues, warnings
    
    def _check_materials(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check materials configuration validity."""
        issues = []
        warnings = []
        
        for i, scene in enumerate(storyboard.scenes):
            materials = scene.materials
            
            for j, material in enumerate(materials):
                if not isinstance(material, dict):
                    issues.append({
                        "type": "invalid_material",
                        "severity": "error",
                        "message": f"Scene {i+1}, Material {j+1}: Material must be an object",
                        "scene": scene.title,
                        "material_index": j,
                    })
                    continue
                
                # Check material name
                if "name" not in material:
                    issues.append({
                        "type": "missing_material_name",
                        "severity": "error",
                        "message": f"Scene {i+1}, Material {j+1}: Material name is required",
                        "scene": scene.title,
                        "material_index": j,
                    })
                
                # Check material properties
                if "properties" in material:
                    properties = material["properties"]
                    if not isinstance(properties, dict):
                        issues.append({
                            "type": "invalid_material_properties",
                            "severity": "error",
                            "message": f"Scene {i+1}, Material {j+1}: Material properties must be an object",
                            "scene": scene.title,
                            "material_index": j,
                        })
        
        return issues, warnings
    
    def _check_transitions(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check transitions configuration validity."""
        issues = []
        warnings = []
        
        for i, scene in enumerate(storyboard.scenes):
            transitions = scene.transitions
            
            # Check transition type
            if "type" in transitions:
                transition_type = transitions["type"]
                valid_types = ["fade", "cut", "dissolve", "wipe", "slide"]
                if transition_type not in valid_types:
                    issues.append({
                        "type": "invalid_transition_type",
                        "severity": "error",
                        "message": f"Scene {i+1}: Invalid transition type '{transition_type}'",
                        "scene": scene.title,
                        "value": transition_type,
                        "valid_types": valid_types,
                    })
            
            # Check transition duration
            if "duration" in transitions:
                duration = transitions["duration"]
                if not isinstance(duration, (int, float)) or duration < 0:
                    issues.append({
                        "type": "invalid_transition_duration",
                        "severity": "error",
                        "message": f"Scene {i+1}: Transition duration must be non-negative",
                        "scene": scene.title,
                        "value": duration,
                    })
                
                if duration > 5.0:
                    warnings.append({
                        "type": "long_transition",
                        "severity": "warning",
                        "message": f"Scene {i+1}: Transition duration is very long ({duration}s)",
                        "scene": scene.title,
                        "value": duration,
                    })
        
        return issues, warnings
    
    def _check_scene_ordering(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check scene ordering validity."""
        issues = []
        warnings = []
        
        for i in range(len(storyboard.scenes) - 1):
            current_scene = storyboard.scenes[i]
            next_scene = storyboard.scenes[i + 1]
            
            # Check start time ordering
            if current_scene.start_time >= next_scene.start_time:
                issues.append({
                    "type": "invalid_scene_ordering",
                    "severity": "error",
                    "message": f"Scene {i+1} start time must be less than scene {i+2} start time",
                    "scene1": current_scene.title,
                    "scene2": next_scene.title,
                    "scene1_start": current_scene.start_time,
                    "scene2_start": next_scene.start_time,
                })
            
            # Check for overlapping scenes
            current_end = current_scene.start_time + current_scene.duration_seconds
            if current_end > next_scene.start_time:
                warnings.append({
                    "type": "overlapping_scenes",
                    "severity": "warning",
                    "message": f"Scene {i+1} and scene {i+2} overlap in time",
                    "scene1": current_scene.title,
                    "scene2": next_scene.title,
                    "overlap_duration": current_end - next_scene.start_time,
                })
        
        return issues, warnings
    
    def _check_timing_consistency(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check timing consistency."""
        issues = []
        warnings = []
        
        total_duration = storyboard.get_total_duration()
        if total_duration <= 0:
            issues.append({
                "type": "invalid_total_duration",
                "severity": "error",
                "message": "Total storyboard duration must be positive",
                "value": total_duration,
            })
        
        if total_duration > 3600:  # 1 hour
            warnings.append({
                "type": "very_long_storyboard",
                "severity": "warning",
                "message": f"Storyboard is very long ({total_duration}s)",
                "value": total_duration,
            })
        
        return issues, warnings
    
    def _check_naming_conventions(self, storyboard: Storyboard) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check naming conventions."""
        issues = []
        warnings = []
        
        # Check storyboard title
        if storyboard.metadata.title:
            title = storyboard.metadata.title
            if len(title) < 3:
                warnings.append({
                    "type": "short_title",
                    "severity": "warning",
                    "message": "Storyboard title is very short",
                    "value": title,
                })
            
            if len(title) > 100:
                warnings.append({
                    "type": "long_title",
                    "severity": "warning",
                    "message": "Storyboard title is very long",
                    "value": title,
                })
        
        # Check scene titles
        for i, scene in enumerate(storyboard.scenes):
            if scene.title:
                title = scene.title
                if len(title) < 3:
                    warnings.append({
                        "type": "short_scene_title",
                        "severity": "warning",
                        "message": f"Scene {i+1} title is very short",
                        "scene": scene.title,
                        "value": title,
                    })
                
                if len(title) > 50:
                    warnings.append({
                        "type": "long_scene_title",
                        "severity": "warning",
                        "message": f"Scene {i+1} title is very long",
                        "scene": scene.title,
                        "value": title,
                    })
        
        return issues, warnings
    
    def _calculate_severity(self, issues: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> str:
        """Calculate overall severity."""
        if issues:
            return "error"
        elif warnings:
            return "warning"
        else:
            return "info"
    
    def _generate_summary(self, issues: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate lint summary."""
        issue_types = {}
        warning_types = {}
        
        for issue in issues:
            issue_type = issue["type"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        for warning in warnings:
            warning_type = warning["type"]
            warning_types[warning_type] = warning_types.get(warning_type, 0) + 1
        
        return {
            "issue_types": issue_types,
            "warning_types": warning_types,
            "most_common_issue": max(issue_types.items(), key=lambda x: x[1])[0] if issue_types else None,
            "most_common_warning": max(warning_types.items(), key=lambda x: x[1])[0] if warning_types else None,
        }
