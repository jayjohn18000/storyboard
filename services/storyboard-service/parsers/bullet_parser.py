"""Bullet point storyboard parser."""

import re
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from services.shared.models.storyboard import Storyboard, StoryboardMetadata, Scene, SceneType, EvidenceAnchor


class BulletParser:
    """Parser for bullet point storyboard format."""
    
    def __init__(self):
        self.scene_pattern = re.compile(r'^•\s*Scene\s+(\d+):\s*(.+)$', re.IGNORECASE)
        self.evidence_pattern = re.compile(r'^-\s*(.+)$')
        self.duration_pattern = re.compile(r'duration:\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)?', re.IGNORECASE)
        self.evidence_id_pattern = re.compile(r'evidence[_\s]*id[:\s]*([a-zA-Z0-9_-]+)', re.IGNORECASE)
    
    async def parse(self, bullet_text: str) -> Dict[str, Any]:
        """Parse bullet point text into storyboard."""
        try:
            lines = bullet_text.strip().split('\n')
            scenes = []
            current_scene = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for scene header
                scene_match = self.scene_pattern.match(line)
                if scene_match:
                    # Save previous scene
                    if current_scene:
                        scenes.append(current_scene)
                    
                    # Start new scene
                    scene_number = int(scene_match.group(1))
                    scene_title = scene_match.group(2).strip()
                    
                    current_scene = Scene(
                        scene_type=SceneType.EVIDENCE_DISPLAY,
                        title=scene_title,
                        description=f"Scene {scene_number}: {scene_title}",
                        duration_seconds=5.0,  # Default duration
                        start_time=0.0,
                        evidence_anchors=[],
                    )
                    continue
                
                # Check for evidence item
                if current_scene and line.startswith('-'):
                    evidence_match = self.evidence_pattern.match(line)
                    if evidence_match:
                        evidence_text = evidence_match.group(1).strip()
                        
                        # Extract evidence ID if present
                        evidence_id_match = self.evidence_id_pattern.search(evidence_text)
                        if evidence_id_match:
                            evidence_id = evidence_id_match.group(1)
                        else:
                            # Generate evidence ID from text
                            evidence_id = self._generate_evidence_id(evidence_text)
                        
                        # Extract duration if present
                        duration_match = self.duration_pattern.search(evidence_text)
                        duration = float(duration_match.group(1)) if duration_match else 2.0
                        
                        # Create evidence anchor
                        anchor = EvidenceAnchor(
                            evidence_id=evidence_id,
                            start_time=0.0,
                            end_time=duration,
                            description=evidence_text,
                            confidence=1.0,
                        )
                        
                        current_scene.evidence_anchors.append(anchor)
                        continue
                
                # Check for duration specification
                if current_scene:
                    duration_match = self.duration_pattern.search(line)
                    if duration_match:
                        current_scene.duration_seconds = float(duration_match.group(1))
                        continue
            
            # Add last scene
            if current_scene:
                scenes.append(current_scene)
            
            # Create storyboard metadata
            metadata = StoryboardMetadata(
                title="Parsed Storyboard",
                description="Storyboard parsed from bullet points",
                case_id="",  # Would be set by caller
                created_by="bullet_parser",
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
            raise Exception(f"Bullet parsing failed: {str(e)}")
    
    def _generate_evidence_id(self, text: str) -> str:
        """Generate evidence ID from text."""
        # Simple ID generation
        # In production, you might want more sophisticated ID generation
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    def _extract_scene_info(self, line: str) -> Dict[str, Any]:
        """Extract scene information from line."""
        info = {}
        
        # Extract duration
        duration_match = self.duration_pattern.search(line)
        if duration_match:
            info["duration"] = float(duration_match.group(1))
        
        # Extract evidence ID
        evidence_id_match = self.evidence_id_pattern.search(line)
        if evidence_id_match:
            info["evidence_id"] = evidence_id_match.group(1)
        
        return info
    
    def _parse_scene_type(self, title: str) -> SceneType:
        """Parse scene type from title."""
        title_lower = title.lower()
        
        if "evidence" in title_lower or "document" in title_lower:
            return SceneType.EVIDENCE_DISPLAY
        elif "timeline" in title_lower or "chronology" in title_lower:
            return SceneType.TIMELINE_VISUALIZATION
        elif "expert" in title_lower or "testimony" in title_lower:
            return SceneType.EXPERT_TESTIMONY
        elif "reconstruction" in title_lower or "recreate" in title_lower:
            return SceneType.RECONSTRUCTION
        elif "comparison" in title_lower or "compare" in title_lower:
            return SceneType.COMPARISON
        else:
            return SceneType.EVIDENCE_DISPLAY  # Default
    
    def _parse_camera_config(self, line: str) -> Dict[str, Any]:
        """Parse camera configuration from line."""
        config = {}
        
        # Extract camera position
        position_match = re.search(r'camera[_\s]*position[:\s]*([^,\n]+)', line, re.IGNORECASE)
        if position_match:
            config["position"] = position_match.group(1).strip()
        
        # Extract camera angle
        angle_match = re.search(r'camera[_\s]*angle[:\s]*([^,\n]+)', line, re.IGNORECASE)
        if angle_match:
            config["angle"] = angle_match.group(1).strip()
        
        # Extract zoom level
        zoom_match = re.search(r'zoom[:\s]*(\d+(?:\.\d+)?)', line, re.IGNORECASE)
        if zoom_match:
            config["zoom"] = float(zoom_match.group(1))
        
        return config
    
    def _parse_lighting_config(self, line: str) -> Dict[str, Any]:
        """Parse lighting configuration from line."""
        config = {}
        
        # Extract lighting type
        lighting_match = re.search(r'lighting[:\s]*([^,\n]+)', line, re.IGNORECASE)
        if lighting_match:
            config["type"] = lighting_match.group(1).strip()
        
        # Extract brightness
        brightness_match = re.search(r'brightness[:\s]*(\d+(?:\.\d+)?)', line, re.IGNORECASE)
        if brightness_match:
            config["brightness"] = float(brightness_match.group(1))
        
        # Extract color temperature
        color_match = re.search(r'color[_\s]*temp[:\s]*(\d+)', line, re.IGNORECASE)
        if color_match:
            config["color_temperature"] = int(color_match.group(1))
        
        return config
