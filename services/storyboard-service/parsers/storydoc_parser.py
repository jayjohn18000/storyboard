"""StoryDoc DSL parser for storyboards."""

import re
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from services.shared.models.storyboard import Storyboard, StoryboardMetadata, Scene, SceneType, EvidenceAnchor


class StoryDocParser:
    """Parser for StoryDoc DSL format."""
    
    def __init__(self):
        self.scene_pattern = re.compile(r'scene\s+(\w+)\s*\{([^}]+)\}', re.DOTALL | re.IGNORECASE)
        self.property_pattern = re.compile(r'(\w+)\s*:\s*([^,\n]+)', re.IGNORECASE)
        self.evidence_pattern = re.compile(r'evidence[:\s]*([a-zA-Z0-9_-]+)', re.IGNORECASE)
        self.duration_pattern = re.compile(r'duration[:\s]*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)?', re.IGNORECASE)
        self.title_pattern = re.compile(r'title[:\s]*"([^"]+)"', re.IGNORECASE)
        self.description_pattern = re.compile(r'description[:\s]*"([^"]+)"', re.IGNORECASE)
    
    async def parse(self, storydoc_text: str) -> Dict[str, Any]:
        """Parse StoryDoc DSL text into storyboard."""
        try:
            # Find all scenes
            scene_matches = self.scene_pattern.findall(storydoc_text)
            scenes = []
            
            for scene_name, scene_content in scene_matches:
                scene = self._parse_scene(scene_name, scene_content)
                if scene:
                    scenes.append(scene)
            
            # Create storyboard metadata
            metadata = StoryboardMetadata(
                title="Parsed Storyboard",
                description="Storyboard parsed from StoryDoc DSL",
                case_id="",  # Would be set by caller
                created_by="storydoc_parser",
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
            raise Exception(f"StoryDoc parsing failed: {str(e)}")
    
    def _parse_scene(self, scene_name: str, scene_content: str) -> Optional[Scene]:
        """Parse individual scene from StoryDoc content."""
        try:
            # Extract properties
            properties = self._extract_properties(scene_content)
            
            # Determine scene type
            scene_type = self._parse_scene_type(scene_name, properties)
            
            # Extract title
            title = properties.get("title", scene_name.replace("_", " ").title())
            
            # Extract description
            description = properties.get("description", f"Scene: {title}")
            
            # Extract duration
            duration = float(properties.get("duration", "5.0"))
            
            # Extract evidence
            evidence_anchors = self._parse_evidence_anchors(scene_content, properties)
            
            # Extract camera config
            camera_config = self._parse_camera_config(properties)
            
            # Extract lighting config
            lighting_config = self._parse_lighting_config(properties)
            
            # Extract materials
            materials = self._parse_materials(properties)
            
            # Extract transitions
            transitions = self._parse_transitions(properties)
            
            # Create scene
            scene = Scene(
                scene_type=scene_type,
                title=title,
                description=description,
                duration_seconds=duration,
                start_time=0.0,
                evidence_anchors=evidence_anchors,
                camera_config=camera_config,
                lighting_config=lighting_config,
                materials=materials,
                transitions=transitions,
            )
            
            return scene
            
        except Exception as e:
            print(f"Failed to parse scene {scene_name}: {e}")
            return None
    
    def _extract_properties(self, content: str) -> Dict[str, str]:
        """Extract properties from scene content."""
        properties = {}
        
        # Find all property matches
        matches = self.property_pattern.findall(content)
        for key, value in matches:
            properties[key.lower()] = value.strip().strip('"')
        
        return properties
    
    def _parse_scene_type(self, scene_name: str, properties: Dict[str, str]) -> SceneType:
        """Parse scene type from scene name and properties."""
        name_lower = scene_name.lower()
        type_str = properties.get("type", "").lower()
        
        if "evidence" in name_lower or "evidence" in type_str:
            return SceneType.EVIDENCE_DISPLAY
        elif "timeline" in name_lower or "timeline" in type_str:
            return SceneType.TIMELINE_VISUALIZATION
        elif "expert" in name_lower or "expert" in type_str:
            return SceneType.EXPERT_TESTIMONY
        elif "reconstruction" in name_lower or "reconstruction" in type_str:
            return SceneType.RECONSTRUCTION
        elif "comparison" in name_lower or "comparison" in type_str:
            return SceneType.COMPARISON
        else:
            return SceneType.EVIDENCE_DISPLAY  # Default
    
    def _parse_evidence_anchors(self, content: str, properties: Dict[str, str]) -> List[EvidenceAnchor]:
        """Parse evidence anchors from scene content."""
        anchors = []
        
        # Find evidence references
        evidence_matches = self.evidence_pattern.findall(content)
        for evidence_id in evidence_matches:
            # Extract timing if specified
            start_time = 0.0
            end_time = float(properties.get("duration", "5.0"))
            
            # Look for timing specifications
            timing_match = re.search(rf'{evidence_id}[:\s]*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', content)
            if timing_match:
                start_time = float(timing_match.group(1))
                end_time = float(timing_match.group(2))
            
            # Create evidence anchor
            anchor = EvidenceAnchor(
                evidence_id=evidence_id,
                start_time=start_time,
                end_time=end_time,
                description=f"Evidence: {evidence_id}",
                confidence=1.0,
            )
            anchors.append(anchor)
        
        return anchors
    
    def _parse_camera_config(self, properties: Dict[str, str]) -> Dict[str, Any]:
        """Parse camera configuration from properties."""
        config = {}
        
        # Extract camera position
        if "camera_position" in properties:
            config["position"] = properties["camera_position"]
        
        # Extract camera rotation
        if "camera_rotation" in properties:
            config["rotation"] = properties["camera_rotation"]
        
        # Extract focal length
        if "focal_length" in properties:
            config["focal_length"] = float(properties["focal_length"])
        
        # Extract field of view
        if "fov" in properties:
            config["fov"] = float(properties["fov"])
        
        return config
    
    def _parse_lighting_config(self, properties: Dict[str, str]) -> Dict[str, Any]:
        """Parse lighting configuration from properties."""
        config = {}
        
        # Extract lighting type
        if "lighting_type" in properties:
            config["type"] = properties["lighting_type"]
        
        # Extract brightness
        if "brightness" in properties:
            config["brightness"] = float(properties["brightness"])
        
        # Extract color temperature
        if "color_temperature" in properties:
            config["color_temperature"] = int(properties["color_temperature"])
        
        # Extract shadow settings
        if "shadows" in properties:
            config["shadows"] = properties["shadows"].lower() == "true"
        
        return config
    
    def _parse_materials(self, properties: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse material configurations from properties."""
        materials = []
        
        # Look for material specifications
        for key, value in properties.items():
            if key.startswith("material_"):
                material_name = key.replace("material_", "")
                material_config = {
                    "name": material_name,
                    "properties": value,
                }
                materials.append(material_config)
        
        return materials
    
    def _parse_transitions(self, properties: Dict[str, str]) -> Dict[str, Any]:
        """Parse transition configurations from properties."""
        transitions = {}
        
        # Extract transition type
        if "transition_type" in properties:
            transitions["type"] = properties["transition_type"]
        
        # Extract transition duration
        if "transition_duration" in properties:
            transitions["duration"] = float(properties["transition_duration"])
        
        # Extract transition easing
        if "transition_easing" in properties:
            transitions["easing"] = properties["transition_easing"]
        
        return transitions
