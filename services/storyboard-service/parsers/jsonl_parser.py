"""JSONL storyboard parser."""

import json
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from services.shared.models.storyboard import Storyboard, StoryboardMetadata, Scene, SceneType, EvidenceAnchor


class JSONLParser:
    """Parser for JSON Lines storyboard format."""
    
    def __init__(self):
        pass
    
    async def parse(self, jsonl_data: str) -> Dict[str, Any]:
        """Parse JSONL text into storyboard."""
        try:
            # Split into lines and parse each line
            lines = jsonl_data.strip().split('\n')
            scenes = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse JSON line
                    scene_data = json.loads(line)
                    
                    # Parse scene
                    scene = self._parse_scene(scene_data)
                    if scene:
                        scenes.append(scene)
                        
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON line: {line}, error: {e}")
                    continue
            
            # Create storyboard metadata
            metadata = StoryboardMetadata(
                title="Parsed Storyboard",
                description="Storyboard parsed from JSONL format",
                case_id="",  # Would be set by caller
                created_by="jsonl_parser",
            )
            
            # Create storyboard
            storyboard = Storyboard(
                metadata=metadata,
                scenes=scenes,
            )
            
            return {
                "storyboard": storyboard.to_dict(),
                "scenes_count": len(scenes),
                "total_duration": storyboard.get_total_duration(),
                "evidence_ids": storyboard.get_evidence_ids(),
            }
            
        except Exception as e:
            raise Exception(f"JSONL parsing failed: {str(e)}")
    
    def _parse_scene(self, scene_data: Dict[str, Any]) -> Optional[Scene]:
        """Parse individual scene from JSON data."""
        try:
            # Extract basic scene information
            scene_type = self._parse_scene_type(scene_data.get("scene_type", "evidence_display"))
            title = scene_data.get("title", "Untitled Scene")
            description = scene_data.get("description", f"Scene: {title}")
            duration = float(scene_data.get("duration", 5.0))
            start_time = float(scene_data.get("start_time", 0.0))
            
            # Parse evidence anchors
            evidence_anchors = self._parse_evidence_anchors(scene_data.get("evidence_anchors", []))
            
            # Parse camera configuration
            camera_config = scene_data.get("camera_config", {})
            
            # Parse lighting configuration
            lighting_config = scene_data.get("lighting_config", {})
            
            # Parse materials
            materials = scene_data.get("materials", [])
            
            # Parse transitions
            transitions = scene_data.get("transitions", {})
            
            # Create scene
            scene = Scene(
                scene_type=scene_type,
                title=title,
                description=description,
                duration_seconds=duration,
                start_time=start_time,
                evidence_anchors=evidence_anchors,
                camera_config=camera_config,
                lighting_config=lighting_config,
                materials=materials,
                transitions=transitions,
            )
            
            return scene
            
        except Exception as e:
            print(f"Failed to parse scene: {e}")
            return None
    
    def _parse_scene_type(self, type_str: str) -> SceneType:
        """Parse scene type from string."""
        type_mapping = {
            "evidence_display": SceneType.EVIDENCE_DISPLAY,
            "timeline_visualization": SceneType.TIMELINE_VISUALIZATION,
            "expert_testimony": SceneType.EXPERT_TESTIMONY,
            "reconstruction": SceneType.RECONSTRUCTION,
            "comparison": SceneType.COMPARISON,
        }
        
        return type_mapping.get(type_str.lower(), SceneType.EVIDENCE_DISPLAY)
    
    def _parse_evidence_anchors(self, anchors_data: List[Dict[str, Any]]) -> List[EvidenceAnchor]:
        """Parse evidence anchors from JSON data."""
        anchors = []
        
        for anchor_data in anchors_data:
            try:
                anchor = EvidenceAnchor(
                    evidence_id=anchor_data.get("evidence_id", ""),
                    start_time=float(anchor_data.get("start_time", 0.0)),
                    end_time=float(anchor_data.get("end_time", 2.0)),
                    description=anchor_data.get("description", ""),
                    confidence=float(anchor_data.get("confidence", 1.0)),
                    annotations=anchor_data.get("annotations", {}),
                )
                anchors.append(anchor)
                
            except Exception as e:
                print(f"Failed to parse evidence anchor: {e}")
                continue
        
        return anchors
    
    def _validate_scene_data(self, scene_data: Dict[str, Any]) -> List[str]:
        """Validate scene data and return list of errors."""
        errors = []
        
        # Check required fields
        if "title" not in scene_data:
            errors.append("Missing required field: title")
        
        if "duration" not in scene_data:
            errors.append("Missing required field: duration")
        
        # Validate duration
        try:
            duration = float(scene_data.get("duration", 0))
            if duration <= 0:
                errors.append("Duration must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid duration value")
        
        # Validate evidence anchors
        if "evidence_anchors" in scene_data:
            for i, anchor in enumerate(scene_data["evidence_anchors"]):
                if not isinstance(anchor, dict):
                    errors.append(f"Evidence anchor {i} must be an object")
                    continue
                
                if "evidence_id" not in anchor:
                    errors.append(f"Evidence anchor {i} missing evidence_id")
                
                if "start_time" in anchor and "end_time" in anchor:
                    try:
                        start_time = float(anchor["start_time"])
                        end_time = float(anchor["end_time"])
                        if start_time >= end_time:
                            errors.append(f"Evidence anchor {i}: start_time must be less than end_time")
                    except (ValueError, TypeError):
                        errors.append(f"Evidence anchor {i}: invalid timing values")
        
        return errors
    
    def _parse_camera_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse camera configuration from JSON data."""
        config = {}
        
        # Extract position
        if "position" in config_data:
            config["position"] = config_data["position"]
        
        # Extract rotation
        if "rotation" in config_data:
            config["rotation"] = config_data["rotation"]
        
        # Extract focal length
        if "focal_length" in config_data:
            config["focal_length"] = float(config_data["focal_length"])
        
        # Extract field of view
        if "fov" in config_data:
            config["fov"] = float(config_data["fov"])
        
        # Extract zoom
        if "zoom" in config_data:
            config["zoom"] = float(config_data["zoom"])
        
        return config
    
    def _parse_lighting_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse lighting configuration from JSON data."""
        config = {}
        
        # Extract lighting type
        if "type" in config_data:
            config["type"] = config_data["type"]
        
        # Extract brightness
        if "brightness" in config_data:
            config["brightness"] = float(config_data["brightness"])
        
        # Extract color temperature
        if "color_temperature" in config_data:
            config["color_temperature"] = int(config_data["color_temperature"])
        
        # Extract shadow settings
        if "shadows" in config_data:
            config["shadows"] = bool(config_data["shadows"])
        
        # Extract color
        if "color" in config_data:
            config["color"] = config_data["color"]
        
        return config
    
    def _parse_materials(self, materials_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse material configurations from JSON data."""
        materials = []
        
        for material_data in materials_data:
            try:
                material = {
                    "name": material_data.get("name", "default"),
                    "properties": material_data.get("properties", {}),
                }
                materials.append(material)
                
            except Exception as e:
                print(f"Failed to parse material: {e}")
                continue
        
        return materials
    
    def _parse_transitions(self, transitions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse transition configurations from JSON data."""
        transitions = {}
        
        # Extract transition type
        if "type" in transitions_data:
            transitions["type"] = transitions_data["type"]
        
        # Extract transition duration
        if "duration" in transitions_data:
            transitions["duration"] = float(transitions_data["duration"])
        
        # Extract transition easing
        if "easing" in transitions_data:
            transitions["easing"] = transitions_data["easing"]
        
        # Extract transition parameters
        if "parameters" in transitions_data:
            transitions["parameters"] = transitions_data["parameters"]
        
        return transitions
