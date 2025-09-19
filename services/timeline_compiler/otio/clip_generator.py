"""OpenTimelineIO clip generator."""

import time
from typing import Dict, Any, List
import opentimelineio as otio


class ClipGenerator:
    """Generator for OpenTimelineIO clips."""
    
    def __init__(self):
        self.default_fps = 30.0
        self.default_resolution = (1920, 1080)
    
    async def generate_clips(self, storyboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clips from storyboard scenes."""
        try:
            start_time = time.time()
            
            # Parse storyboard
            from ...shared.models.storyboard import Storyboard
            storyboard = Storyboard.from_dict(storyboard_data)
            
            # Generate clips for each scene
            clips = []
            for scene in storyboard.scenes:
                scene_clips = await self._generate_scene_clips(scene)
                clips.extend(scene_clips)
            
            # Generate transition clips
            transition_clips = await self._generate_transition_clips(storyboard)
            clips.extend(transition_clips)
            
            # Generate overlay clips
            overlay_clips = await self._generate_overlay_clips(storyboard)
            clips.extend(overlay_clips)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "clips": clips,
                "total_clips": len(clips),
                "scene_clips": len([c for c in clips if c["type"] == "scene"]),
                "transition_clips": len([c for c in clips if c["type"] == "transition"]),
                "overlay_clips": len([c for c in clips if c["type"] == "overlay"]),
                "processing_time_ms": processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Clip generation failed: {str(e)}")
    
    async def _generate_scene_clips(self, scene) -> List[Dict[str, Any]]:
        """Generate clips for a single scene."""
        clips = []
        
        try:
            # Create main scene clip
            scene_clip = {
                "type": "scene",
                "name": scene.title,
                "scene_id": scene.id,
                "scene_type": scene.scene_type.value,
                "duration_seconds": scene.duration_seconds,
                "start_time": scene.start_time,
                "media_reference": {
                    "target_url": f"scene://{scene.id}",
                    "metadata": {
                        "scene_type": scene.scene_type.value,
                        "title": scene.title,
                        "description": scene.description,
                        "camera_config": scene.camera_config,
                        "lighting_config": scene.lighting_config,
                        "materials": scene.materials,
                    }
                },
                "source_range": {
                    "start_time": {"value": 0, "rate": self.default_fps},
                    "duration": {"value": int(scene.duration_seconds * self.default_fps), "rate": self.default_fps},
                },
                "metadata": {
                    "scene_id": scene.id,
                    "scene_type": scene.scene_type.value,
                    "duration_seconds": scene.duration_seconds,
                }
            }
            clips.append(scene_clip)
            
            # Create evidence clips
            for anchor in scene.evidence_anchors:
                evidence_clip = await self._generate_evidence_clip(scene, anchor)
                if evidence_clip:
                    clips.append(evidence_clip)
            
            # Create audio clips if needed
            audio_clip = await self._generate_scene_audio_clip(scene)
            if audio_clip:
                clips.append(audio_clip)
            
        except Exception as e:
            print(f"Failed to generate clips for scene {scene.title}: {e}")
        
        return clips
    
    async def _generate_evidence_clip(self, scene, anchor) -> Dict[str, Any]:
        """Generate clip for evidence anchor."""
        try:
            # Determine evidence type
            evidence_type = self._determine_evidence_type(anchor.evidence_id)
            
            # Create evidence clip
            evidence_clip = {
                "type": "evidence",
                "name": f"{scene.title} - {anchor.evidence_id}",
                "scene_id": scene.id,
                "evidence_id": anchor.evidence_id,
                "evidence_type": evidence_type,
                "duration_seconds": anchor.end_time - anchor.start_time,
                "start_time": anchor.start_time,
                "media_reference": {
                    "target_url": f"evidence://{anchor.evidence_id}",
                    "metadata": {
                        "evidence_id": anchor.evidence_id,
                        "evidence_type": evidence_type,
                        "description": anchor.description,
                        "confidence": anchor.confidence,
                        "annotations": anchor.annotations,
                    }
                },
                "source_range": {
                    "start_time": {"value": int(anchor.start_time * self.default_fps), "rate": self.default_fps},
                    "duration": {"value": int((anchor.end_time - anchor.start_time) * self.default_fps), "rate": self.default_fps},
                },
                "metadata": {
                    "scene_id": scene.id,
                    "evidence_id": anchor.evidence_id,
                    "evidence_type": evidence_type,
                    "duration_seconds": anchor.end_time - anchor.start_time,
                    "confidence": anchor.confidence,
                }
            }
            
            return evidence_clip
            
        except Exception as e:
            print(f"Failed to generate evidence clip for {anchor.evidence_id}: {e}")
            return None
    
    async def _generate_scene_audio_clip(self, scene) -> Dict[str, Any]:
        """Generate audio clip for scene."""
        try:
            # Check if scene has audio evidence
            has_audio = any(
                anchor.evidence_id.startswith("audio_") or anchor.evidence_id.startswith("video_")
                for anchor in scene.evidence_anchors
            )
            
            if not has_audio:
                return None
            
            # Create audio clip
            audio_clip = {
                "type": "audio",
                "name": f"{scene.title} Audio",
                "scene_id": scene.id,
                "duration_seconds": scene.duration_seconds,
                "start_time": scene.start_time,
                "media_reference": {
                    "target_url": f"audio://{scene.id}",
                    "metadata": {
                        "scene_id": scene.id,
                        "has_audio": True,
                    }
                },
                "source_range": {
                    "start_time": {"value": 0, "rate": self.default_fps},
                    "duration": {"value": int(scene.duration_seconds * self.default_fps), "rate": self.default_fps},
                },
                "metadata": {
                    "scene_id": scene.id,
                    "duration_seconds": scene.duration_seconds,
                }
            }
            
            return audio_clip
            
        except Exception as e:
            print(f"Failed to generate audio clip for scene {scene.title}: {e}")
            return None
    
    async def _generate_transition_clips(self, storyboard) -> List[Dict[str, Any]]:
        """Generate transition clips between scenes."""
        clips = []
        
        try:
            for i in range(len(storyboard.scenes) - 1):
                current_scene = storyboard.scenes[i]
                next_scene = storyboard.scenes[i + 1]
                
                # Check if scenes have transitions
                if current_scene.transitions:
                    for transition_type, transition_config in current_scene.transitions.items():
                        transition_clip = await self._generate_transition_clip(
                            current_scene, next_scene, transition_type, transition_config
                        )
                        if transition_clip:
                            clips.append(transition_clip)
            
        except Exception as e:
            print(f"Failed to generate transition clips: {e}")
        
        return clips
    
    async def _generate_transition_clip(self, current_scene, next_scene, transition_type: str, transition_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate individual transition clip."""
        try:
            # Get transition duration
            duration = transition_config.get("duration", 1.0)
            
            # Create transition clip
            transition_clip = {
                "type": "transition",
                "name": f"{current_scene.title} -> {next_scene.title}",
                "transition_type": transition_type,
                "duration_seconds": duration,
                "start_time": current_scene.start_time + current_scene.duration_seconds - duration,
                "media_reference": {
                    "target_url": f"transition://{current_scene.id}-{next_scene.id}",
                    "metadata": {
                        "transition_type": transition_type,
                        "from_scene": current_scene.id,
                        "to_scene": next_scene.id,
                        "duration": duration,
                        "config": transition_config,
                    }
                },
                "source_range": {
                    "start_time": {"value": 0, "rate": self.default_fps},
                    "duration": {"value": int(duration * self.default_fps), "rate": self.default_fps},
                },
                "metadata": {
                    "transition_type": transition_type,
                    "from_scene": current_scene.id,
                    "to_scene": next_scene.id,
                    "duration_seconds": duration,
                }
            }
            
            return transition_clip
            
        except Exception as e:
            print(f"Failed to generate transition clip: {e}")
            return None
    
    async def _generate_overlay_clips(self, storyboard) -> List[Dict[str, Any]]:
        """Generate overlay clips (text, captions, etc.)."""
        clips = []
        
        try:
            for scene in storyboard.scenes:
                # Generate text overlay clips
                text_clips = await self._generate_text_overlay_clips(scene)
                clips.extend(text_clips)
                
                # Generate caption clips
                caption_clips = await self._generate_caption_clips(scene)
                clips.extend(caption_clips)
            
        except Exception as e:
            print(f"Failed to generate overlay clips: {e}")
        
        return clips
    
    async def _generate_text_overlay_clips(self, scene) -> List[Dict[str, Any]]:
        """Generate text overlay clips for scene."""
        clips = []
        
        try:
            # Check if scene has text overlays
            if "text_overlays" in scene.metadata:
                for overlay in scene.metadata["text_overlays"]:
                    text_clip = {
                        "type": "text_overlay",
                        "name": f"{scene.title} - Text Overlay",
                        "scene_id": scene.id,
                        "duration_seconds": overlay.get("duration", scene.duration_seconds),
                        "start_time": overlay.get("start_time", 0.0),
                        "media_reference": {
                            "target_url": f"text://{scene.id}-{overlay.get('id', 'default')}",
                            "metadata": {
                                "text": overlay.get("text", ""),
                                "position": overlay.get("position", "center"),
                                "style": overlay.get("style", {}),
                            }
                        },
                        "source_range": {
                            "start_time": {"value": int(overlay.get("start_time", 0.0) * self.default_fps), "rate": self.default_fps},
                            "duration": {"value": int(overlay.get("duration", scene.duration_seconds) * self.default_fps), "rate": self.default_fps},
                        },
                        "metadata": {
                            "scene_id": scene.id,
                            "overlay_type": "text",
                            "duration_seconds": overlay.get("duration", scene.duration_seconds),
                        }
                    }
                    clips.append(text_clip)
            
        except Exception as e:
            print(f"Failed to generate text overlay clips for scene {scene.title}: {e}")
        
        return clips
    
    async def _generate_caption_clips(self, scene) -> List[Dict[str, Any]]:
        """Generate caption clips for scene."""
        clips = []
        
        try:
            # Check if scene has captions
            if "captions" in scene.metadata:
                for caption in scene.metadata["captions"]:
                    caption_clip = {
                        "type": "caption",
                        "name": f"{scene.title} - Caption",
                        "scene_id": scene.id,
                        "duration_seconds": caption.get("duration", 2.0),
                        "start_time": caption.get("start_time", 0.0),
                        "media_reference": {
                            "target_url": f"caption://{scene.id}-{caption.get('id', 'default')}",
                            "metadata": {
                                "text": caption.get("text", ""),
                                "speaker": caption.get("speaker", ""),
                                "confidence": caption.get("confidence", 1.0),
                            }
                        },
                        "source_range": {
                            "start_time": {"value": int(caption.get("start_time", 0.0) * self.default_fps), "rate": self.default_fps},
                            "duration": {"value": int(caption.get("duration", 2.0) * self.default_fps), "rate": self.default_fps},
                        },
                        "metadata": {
                            "scene_id": scene.id,
                            "overlay_type": "caption",
                            "duration_seconds": caption.get("duration", 2.0),
                        }
                    }
                    clips.append(caption_clip)
            
        except Exception as e:
            print(f"Failed to generate caption clips for scene {scene.title}: {e}")
        
        return clips
    
    def _determine_evidence_type(self, evidence_id: str) -> str:
        """Determine evidence type from ID."""
        if evidence_id.startswith("document_"):
            return "document"
        elif evidence_id.startswith("image_"):
            return "image"
        elif evidence_id.startswith("audio_"):
            return "audio"
        elif evidence_id.startswith("video_"):
            return "video"
        elif evidence_id.startswith("object_"):
            return "object"
        elif evidence_id.startswith("testimony_"):
            return "testimony"
        else:
            return "unknown"
    
    def _validate_clip(self, clip: Dict[str, Any]) -> List[str]:
        """Validate clip for issues."""
        issues = []
        
        # Check required fields
        if "name" not in clip:
            issues.append("Clip name is required")
        
        if "type" not in clip:
            issues.append("Clip type is required")
        
        if "duration_seconds" not in clip:
            issues.append("Clip duration is required")
        
        # Check duration
        if clip.get("duration_seconds", 0) <= 0:
            issues.append("Clip duration must be positive")
        
        # Check media reference
        if "media_reference" not in clip:
            issues.append("Media reference is required")
        
        return issues
    
    def _optimize_clips(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize clips for rendering."""
        try:
            # Sort clips by start time
            clips.sort(key=lambda clip: clip.get("start_time", 0.0))
            
            # Remove duplicate clips
            unique_clips = []
            seen_clips = set()
            
            for clip in clips:
                clip_key = (clip.get("name"), clip.get("start_time"), clip.get("duration_seconds"))
                if clip_key not in seen_clips:
                    unique_clips.append(clip)
                    seen_clips.add(clip_key)
            
            return unique_clips
            
        except Exception as e:
            print(f"Failed to optimize clips: {e}")
            return clips
