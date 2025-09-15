"""USD scene graph builder."""

import time
from typing import Dict, Any, List
import json


class USDBuilder:
    """Builder for USD scene graphs."""
    
    def __init__(self):
        self.default_resolution = (1920, 1080)
        self.default_fps = 30.0
    
    async def build_scene_graph(self, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build USD scene graph from timeline."""
        try:
            start_time = time.time()
            
            # Parse timeline
            timeline = self._parse_timeline(timeline_data)
            
            # Build scene graph
            scene_graph = await self._build_scene_graph(timeline)
            
            # Validate scene graph
            validation_results = self._validate_scene_graph(scene_graph)
            
            # Convert to USD format
            usd_data = self._convert_to_usd(scene_graph)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "scene_graph": scene_graph,
                "usd_data": usd_data,
                "validation_results": validation_results,
                "processing_time_ms": processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Scene graph building failed: {str(e)}")
    
    def _parse_timeline(self, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse timeline data."""
        return {
            "name": timeline_data.get("name", "Timeline"),
            "metadata": timeline_data.get("metadata", {}),
            "tracks": timeline_data.get("tracks", []),
        }
    
    async def _build_scene_graph(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Build scene graph from timeline."""
        try:
            # Create root scene graph
            scene_graph = {
                "name": timeline["name"],
                "metadata": timeline["metadata"],
                "resolution": self.default_resolution,
                "fps": self.default_fps,
                "duration": 0.0,
                "scenes": [],
                "cameras": [],
                "lights": [],
                "materials": [],
                "objects": [],
            }
            
            # Process tracks
            for track in timeline["tracks"]:
                await self._process_track(track, scene_graph)
            
            # Calculate total duration
            scene_graph["duration"] = max(
                scene.get("end_time", 0.0) for scene in scene_graph["scenes"]
            ) if scene_graph["scenes"] else 0.0
            
            return scene_graph
            
        except Exception as e:
            raise Exception(f"Failed to build scene graph: {str(e)}")
    
    async def _process_track(self, track: Dict[str, Any], scene_graph: Dict[str, Any]):
        """Process track and add to scene graph."""
        try:
            track_name = track.get("name", "Track")
            track_kind = track.get("kind", "Video")
            
            # Process clips in track
            for clip in track.get("clips", []):
                await self._process_clip(clip, scene_graph, track_name, track_kind)
            
        except Exception as e:
            print(f"Failed to process track: {e}")
    
    async def _process_clip(self, clip: Dict[str, Any], scene_graph: Dict[str, Any], track_name: str, track_kind: str):
        """Process clip and add to scene graph."""
        try:
            clip_type = clip.get("type", "clip")
            clip_name = clip.get("name", "Clip")
            
            if clip_type == "scene":
                await self._process_scene_clip(clip, scene_graph)
            elif clip_type == "evidence":
                await self._process_evidence_clip(clip, scene_graph)
            elif clip_type == "transition":
                await self._process_transition_clip(clip, scene_graph)
            elif clip_type == "audio":
                await self._process_audio_clip(clip, scene_graph)
            elif clip_type == "text_overlay":
                await self._process_text_overlay_clip(clip, scene_graph)
            elif clip_type == "caption":
                await self._process_caption_clip(clip, scene_graph)
            
        except Exception as e:
            print(f"Failed to process clip {clip.get('name', 'Unknown')}: {e}")
    
    async def _process_scene_clip(self, clip: Dict[str, Any], scene_graph: Dict[str, Any]):
        """Process scene clip."""
        try:
            # Extract scene information
            scene_info = {
                "id": clip.get("scene_id", ""),
                "name": clip.get("name", ""),
                "type": clip.get("scene_type", "evidence_display"),
                "duration": clip.get("duration_seconds", 0.0),
                "start_time": clip.get("start_time", 0.0),
                "end_time": clip.get("start_time", 0.0) + clip.get("duration_seconds", 0.0),
                "camera_config": clip.get("media_reference", {}).get("metadata", {}).get("camera_config", {}),
                "lighting_config": clip.get("media_reference", {}).get("metadata", {}).get("lighting_config", {}),
                "materials": clip.get("media_reference", {}).get("metadata", {}).get("materials", []),
            }
            
            # Add scene to scene graph
            scene_graph["scenes"].append(scene_info)
            
            # Add camera if configured
            if scene_info["camera_config"]:
                camera = await self._create_camera(scene_info)
                scene_graph["cameras"].append(camera)
            
            # Add lights if configured
            if scene_info["lighting_config"]:
                lights = await self._create_lights(scene_info)
                scene_graph["lights"].extend(lights)
            
            # Add materials if configured
            if scene_info["materials"]:
                for material in scene_info["materials"]:
                    material_obj = await self._create_material(material)
                    scene_graph["materials"].append(material_obj)
            
        except Exception as e:
            print(f"Failed to process scene clip: {e}")
    
    async def _process_evidence_clip(self, clip: Dict[str, Any], scene_graph: Dict[str, Any]):
        """Process evidence clip."""
        try:
            # Extract evidence information
            evidence_info = {
                "id": clip.get("evidence_id", ""),
                "name": clip.get("name", ""),
                "type": clip.get("evidence_type", "unknown"),
                "duration": clip.get("duration_seconds", 0.0),
                "start_time": clip.get("start_time", 0.0),
                "end_time": clip.get("start_time", 0.0) + clip.get("duration_seconds", 0.0),
                "confidence": clip.get("metadata", {}).get("confidence", 1.0),
                "description": clip.get("media_reference", {}).get("metadata", {}).get("description", ""),
            }
            
            # Create evidence object
            evidence_obj = await self._create_evidence_object(evidence_info)
            scene_graph["objects"].append(evidence_obj)
            
        except Exception as e:
            print(f"Failed to process evidence clip: {e}")
    
    async def _process_transition_clip(self, clip: Dict[str, Any], scene_graph: Dict[str, Any]):
        """Process transition clip."""
        try:
            # Extract transition information
            transition_info = {
                "name": clip.get("name", ""),
                "type": clip.get("transition_type", "fade"),
                "duration": clip.get("duration_seconds", 0.0),
                "start_time": clip.get("start_time", 0.0),
                "end_time": clip.get("start_time", 0.0) + clip.get("duration_seconds", 0.0),
                "config": clip.get("media_reference", {}).get("metadata", {}).get("config", {}),
            }
            
            # Add transition to scene graph
            scene_graph["transitions"] = scene_graph.get("transitions", [])
            scene_graph["transitions"].append(transition_info)
            
        except Exception as e:
            print(f"Failed to process transition clip: {e}")
    
    async def _process_audio_clip(self, clip: Dict[str, Any], scene_graph: Dict[str, Any]):
        """Process audio clip."""
        try:
            # Extract audio information
            audio_info = {
                "id": clip.get("scene_id", ""),
                "name": clip.get("name", ""),
                "duration": clip.get("duration_seconds", 0.0),
                "start_time": clip.get("start_time", 0.0),
                "end_time": clip.get("start_time", 0.0) + clip.get("duration_seconds", 0.0),
            }
            
            # Add audio to scene graph
            scene_graph["audio"] = scene_graph.get("audio", [])
            scene_graph["audio"].append(audio_info)
            
        except Exception as e:
            print(f"Failed to process audio clip: {e}")
    
    async def _process_text_overlay_clip(self, clip: Dict[str, Any], scene_graph: Dict[str, Any]):
        """Process text overlay clip."""
        try:
            # Extract text overlay information
            text_info = {
                "name": clip.get("name", ""),
                "text": clip.get("media_reference", {}).get("metadata", {}).get("text", ""),
                "position": clip.get("media_reference", {}).get("metadata", {}).get("position", "center"),
                "style": clip.get("media_reference", {}).get("metadata", {}).get("style", {}),
                "duration": clip.get("duration_seconds", 0.0),
                "start_time": clip.get("start_time", 0.0),
                "end_time": clip.get("start_time", 0.0) + clip.get("duration_seconds", 0.0),
            }
            
            # Add text overlay to scene graph
            scene_graph["text_overlays"] = scene_graph.get("text_overlays", [])
            scene_graph["text_overlays"].append(text_info)
            
        except Exception as e:
            print(f"Failed to process text overlay clip: {e}")
    
    async def _process_caption_clip(self, clip: Dict[str, Any], scene_graph: Dict[str, Any]):
        """Process caption clip."""
        try:
            # Extract caption information
            caption_info = {
                "name": clip.get("name", ""),
                "text": clip.get("media_reference", {}).get("metadata", {}).get("text", ""),
                "speaker": clip.get("media_reference", {}).get("metadata", {}).get("speaker", ""),
                "confidence": clip.get("media_reference", {}).get("metadata", {}).get("confidence", 1.0),
                "duration": clip.get("duration_seconds", 0.0),
                "start_time": clip.get("start_time", 0.0),
                "end_time": clip.get("start_time", 0.0) + clip.get("duration_seconds", 0.0),
            }
            
            # Add caption to scene graph
            scene_graph["captions"] = scene_graph.get("captions", [])
            scene_graph["captions"].append(caption_info)
            
        except Exception as e:
            print(f"Failed to process caption clip: {e}")
    
    async def _create_camera(self, scene_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create camera object."""
        camera_config = scene_info["camera_config"]
        
        return {
            "name": f"Camera_{scene_info['id']}",
            "type": "perspective",
            "position": camera_config.get("position", [0, 0, 5]),
            "rotation": camera_config.get("rotation", [0, 0, 0]),
            "focal_length": camera_config.get("focal_length", 50.0),
            "fov": camera_config.get("fov", 45.0),
            "zoom": camera_config.get("zoom", 1.0),
            "scene_id": scene_info["id"],
            "start_time": scene_info["start_time"],
            "end_time": scene_info["end_time"],
        }
    
    async def _create_lights(self, scene_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create light objects."""
        lights = []
        lighting_config = scene_info["lighting_config"]
        
        # Create main light
        main_light = {
            "name": f"MainLight_{scene_info['id']}",
            "type": lighting_config.get("type", "directional"),
            "position": lighting_config.get("position", [0, 10, 0]),
            "rotation": lighting_config.get("rotation", [0, 0, 0]),
            "brightness": lighting_config.get("brightness", 1.0),
            "color": lighting_config.get("color", [1, 1, 1]),
            "color_temperature": lighting_config.get("color_temperature", 6500),
            "shadows": lighting_config.get("shadows", True),
            "scene_id": scene_info["id"],
            "start_time": scene_info["start_time"],
            "end_time": scene_info["end_time"],
        }
        lights.append(main_light)
        
        # Create fill light
        fill_light = {
            "name": f"FillLight_{scene_info['id']}",
            "type": "directional",
            "position": lighting_config.get("fill_position", [5, 5, 5]),
            "rotation": lighting_config.get("fill_rotation", [0, 0, 0]),
            "brightness": lighting_config.get("fill_brightness", 0.3),
            "color": lighting_config.get("fill_color", [1, 1, 1]),
            "shadows": False,
            "scene_id": scene_info["id"],
            "start_time": scene_info["start_time"],
            "end_time": scene_info["end_time"],
        }
        lights.append(fill_light)
        
        return lights
    
    async def _create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create material object."""
        return {
            "name": material_data.get("name", "DefaultMaterial"),
            "type": "standard",
            "properties": material_data.get("properties", {}),
            "diffuse_color": material_data.get("properties", {}).get("diffuse_color", [0.8, 0.8, 0.8]),
            "specular_color": material_data.get("properties", {}).get("specular_color", [1, 1, 1]),
            "roughness": material_data.get("properties", {}).get("roughness", 0.5),
            "metallic": material_data.get("properties", {}).get("metallic", 0.0),
            "emission": material_data.get("properties", {}).get("emission", [0, 0, 0]),
        }
    
    async def _create_evidence_object(self, evidence_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create evidence object."""
        return {
            "name": evidence_info["name"],
            "type": evidence_info["type"],
            "evidence_id": evidence_info["id"],
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "material": f"Material_{evidence_info['id']}",
            "start_time": evidence_info["start_time"],
            "end_time": evidence_info["end_time"],
            "confidence": evidence_info["confidence"],
            "description": evidence_info["description"],
        }
    
    def _validate_scene_graph(self, scene_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scene graph."""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "scene_count": len(scene_graph.get("scenes", [])),
            "camera_count": len(scene_graph.get("cameras", [])),
            "light_count": len(scene_graph.get("lights", [])),
            "material_count": len(scene_graph.get("materials", [])),
            "object_count": len(scene_graph.get("objects", [])),
        }
        
        try:
            # Check for scenes
            if not scene_graph.get("scenes"):
                validation_results["issues"].append("No scenes found in scene graph")
            
            # Check for cameras
            if not scene_graph.get("cameras"):
                validation_results["warnings"].append("No cameras found in scene graph")
            
            # Check for lights
            if not scene_graph.get("lights"):
                validation_results["warnings"].append("No lights found in scene graph")
            
            # Check scene duration
            duration = scene_graph.get("duration", 0.0)
            if duration <= 0:
                validation_results["issues"].append("Invalid scene graph duration")
            
            # Check for overlapping scenes
            scenes = scene_graph.get("scenes", [])
            for i in range(len(scenes) - 1):
                current_scene = scenes[i]
                next_scene = scenes[i + 1]
                
                if current_scene["end_time"] > next_scene["start_time"]:
                    validation_results["issues"].append(
                        f"Overlapping scenes: {current_scene['name']} and {next_scene['name']}"
                    )
            
            # Set overall validity
            validation_results["valid"] = len(validation_results["issues"]) == 0
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Validation failed: {str(e)}")
        
        return validation_results
    
    def _convert_to_usd(self, scene_graph: Dict[str, Any]) -> str:
        """Convert scene graph to USD format."""
        try:
            # Create USD header
            usd_header = f"""#usda 1.0
(
    defaultPrim = "Scene"
    metersPerUnit = 1
    upAxis = "Y"
    framesPerSecond = {scene_graph.get('fps', self.default_fps)}
    timeCodesPerSecond = {scene_graph.get('fps', self.default_fps)}
)

def "Scene" (
    kind = "group"
)
{{
    def Camera "MainCamera"
    {{
        float focalLength = 50.0
        float focusDistance = 5.0
        float fStop = 5.6
        float horizontalAperture = 20.955
        float horizontalApertureOffset = 0
        float verticalAperture = 15.955
        float verticalApertureOffset = 0
        matrix4d xformOp:transform = ( (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 5, 1) )
        uniform token[] xformOpOrder = ["xformOp:transform"]
    }}
    
    def DirectionalLight "MainLight"
    {{
        float intensity = 1.0
        color3f color = (1, 1, 1)
        float3 xformOp:rotateXYZ = (0, 0, 0)
        matrix4d xformOp:transform = ( (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 10, 0, 1) )
        uniform token[] xformOpOrder = ["xformOp:transform"]
    }}
"""
            
            # Add scenes
            usd_scenes = ""
            for scene in scene_graph.get("scenes", []):
                usd_scenes += f"""
    def "Scene_{scene['id']}" (
        kind = "group"
    )
    {{
        def "Evidence_Objects"
        {{
            # Evidence objects for scene {scene['name']}
        }}
    }}
"""
            
            # Add materials
            usd_materials = ""
            for material in scene_graph.get("materials", []):
                usd_materials += f"""
    def Material "Material_{material['name']}"
    {{
        def Shader "Diffuse"
        {{
            uniform token info:id = "UsdPreviewSurface"
            color3f diffuseColor = {material.get('diffuse_color', [0.8, 0.8, 0.8])}
            float roughness = {material.get('roughness', 0.5)}
            float metallic = {material.get('metallic', 0.0)}
        }}
    }}
"""
            
            # Combine USD components
            usd_content = usd_header + usd_scenes + usd_materials + "}"
            
            return usd_content
            
        except Exception as e:
            return f"# USD generation failed: {str(e)}"
