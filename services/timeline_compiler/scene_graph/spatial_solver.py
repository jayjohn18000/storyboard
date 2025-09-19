"""Spatial solver for scene graph."""

import time
from typing import Dict, Any, List, Tuple
import math


class SpatialSolver:
    """Solver for spatial relationships in scene graphs."""
    
    def __init__(self):
        self.default_camera_distance = 5.0
        self.default_light_distance = 10.0
        self.default_object_scale = 1.0
    
    async def solve_spatial(self, scene_graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Solve spatial relationships in scene graph."""
        try:
            start_time = time.time()
            
            # Parse scene graph
            scene_graph = self._parse_scene_graph(scene_graph_data)
            
            # Solve spatial relationships
            solved_scene_graph = await self._solve_spatial_relationships(scene_graph)
            
            # Validate spatial solution
            validation_results = self._validate_spatial_solution(solved_scene_graph)
            
            # Optimize spatial layout
            optimized_scene_graph = self._optimize_spatial_layout(solved_scene_graph)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "scene_graph": optimized_scene_graph,
                "validation_results": validation_results,
                "processing_time_ms": processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Spatial solving failed: {str(e)}")
    
    def _parse_scene_graph(self, scene_graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse scene graph data."""
        return {
            "name": scene_graph_data.get("name", "SceneGraph"),
            "metadata": scene_graph_data.get("metadata", {}),
            "resolution": scene_graph_data.get("resolution", (1920, 1080)),
            "fps": scene_graph_data.get("fps", 30.0),
            "duration": scene_graph_data.get("duration", 0.0),
            "scenes": scene_graph_data.get("scenes", []),
            "cameras": scene_graph_data.get("cameras", []),
            "lights": scene_graph_data.get("lights", []),
            "materials": scene_graph_data.get("materials", []),
            "objects": scene_graph_data.get("objects", []),
        }
    
    async def _solve_spatial_relationships(self, scene_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Solve spatial relationships in scene graph."""
        try:
            # Solve camera positions
            scene_graph["cameras"] = await self._solve_camera_positions(scene_graph["cameras"], scene_graph["scenes"])
            
            # Solve light positions
            scene_graph["lights"] = await self._solve_light_positions(scene_graph["lights"], scene_graph["scenes"])
            
            # Solve object positions
            scene_graph["objects"] = await self._solve_object_positions(scene_graph["objects"], scene_graph["scenes"])
            
            # Solve scene transitions
            scene_graph["scenes"] = await self._solve_scene_transitions(scene_graph["scenes"])
            
            return scene_graph
            
        except Exception as e:
            raise Exception(f"Failed to solve spatial relationships: {str(e)}")
    
    async def _solve_camera_positions(self, cameras: List[Dict[str, Any]], scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Solve camera positions for scenes."""
        solved_cameras = []
        
        for camera in cameras:
            try:
                # Get scene for camera
                scene = self._get_scene_for_camera(camera, scenes)
                if not scene:
                    continue
                
                # Solve camera position based on scene type
                solved_camera = await self._solve_camera_position(camera, scene)
                solved_cameras.append(solved_camera)
                
            except Exception as e:
                print(f"Failed to solve camera position: {e}")
                solved_cameras.append(camera)
        
        return solved_cameras
    
    async def _solve_camera_position(self, camera: Dict[str, Any], scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve individual camera position."""
        try:
            # Get scene type
            scene_type = scene.get("type", "evidence_display")
            
            # Solve position based on scene type
            if scene_type == "evidence_display":
                position = await self._solve_evidence_display_camera_position(camera, scene)
            elif scene_type == "timeline_visualization":
                position = await self._solve_timeline_visualization_camera_position(camera, scene)
            elif scene_type == "expert_testimony":
                position = await self._solve_expert_testimony_camera_position(camera, scene)
            elif scene_type == "reconstruction":
                position = await self._solve_reconstruction_camera_position(camera, scene)
            elif scene_type == "comparison":
                position = await self._solve_comparison_camera_position(camera, scene)
            else:
                position = camera.get("position", [0, 0, self.default_camera_distance])
            
            # Update camera
            solved_camera = camera.copy()
            solved_camera["position"] = position
            solved_camera["solved"] = True
            
            return solved_camera
            
        except Exception as e:
            print(f"Failed to solve camera position: {e}")
            return camera
    
    async def _solve_evidence_display_camera_position(self, camera: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve camera position for evidence display scene."""
        # Position camera to view evidence objects
        # Default position: slightly elevated and angled down
        return [0, 2, self.default_camera_distance]
    
    async def _solve_timeline_visualization_camera_position(self, camera: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve camera position for timeline visualization scene."""
        # Position camera for timeline view
        # Default position: elevated and angled for timeline view
        return [0, 5, self.default_camera_distance * 1.5]
    
    async def _solve_expert_testimony_camera_position(self, camera: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve camera position for expert testimony scene."""
        # Position camera for expert testimony
        # Default position: eye level, slightly angled
        return [0, 1.7, self.default_camera_distance]
    
    async def _solve_reconstruction_camera_position(self, camera: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve camera position for reconstruction scene."""
        # Position camera for reconstruction
        # Default position: elevated for overview
        return [0, 3, self.default_camera_distance * 1.2]
    
    async def _solve_comparison_camera_position(self, camera: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve camera position for comparison scene."""
        # Position camera for comparison
        # Default position: elevated and angled for comparison view
        return [0, 4, self.default_camera_distance * 1.3]
    
    async def _solve_light_positions(self, lights: List[Dict[str, Any]], scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Solve light positions for scenes."""
        solved_lights = []
        
        for light in lights:
            try:
                # Get scene for light
                scene = self._get_scene_for_light(light, scenes)
                if not scene:
                    continue
                
                # Solve light position based on scene type
                solved_light = await self._solve_light_position(light, scene)
                solved_lights.append(solved_light)
                
            except Exception as e:
                print(f"Failed to solve light position: {e}")
                solved_lights.append(light)
        
        return solved_lights
    
    async def _solve_light_position(self, light: Dict[str, Any], scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve individual light position."""
        try:
            # Get light type
            light_type = light.get("type", "directional")
            
            # Solve position based on light type
            if light_type == "directional":
                position = await self._solve_directional_light_position(light, scene)
            elif light_type == "point":
                position = await self._solve_point_light_position(light, scene)
            elif light_type == "spot":
                position = await self._solve_spot_light_position(light, scene)
            elif light_type == "area":
                position = await self._solve_area_light_position(light, scene)
            else:
                position = light.get("position", [0, self.default_light_distance, 0])
            
            # Update light
            solved_light = light.copy()
            solved_light["position"] = position
            solved_light["solved"] = True
            
            return solved_light
            
        except Exception as e:
            print(f"Failed to solve light position: {e}")
            return light
    
    async def _solve_directional_light_position(self, light: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve directional light position."""
        # Directional lights are positioned far away
        return [0, self.default_light_distance, 0]
    
    async def _solve_point_light_position(self, light: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve point light position."""
        # Point lights are positioned near the scene
        return [0, 3, 2]
    
    async def _solve_spot_light_position(self, light: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve spot light position."""
        # Spot lights are positioned above and angled down
        return [0, 5, 3]
    
    async def _solve_area_light_position(self, light: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve area light position."""
        # Area lights are positioned above the scene
        return [0, 4, 0]
    
    async def _solve_object_positions(self, objects: List[Dict[str, Any]], scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Solve object positions for scenes."""
        solved_objects = []
        
        for obj in objects:
            try:
                # Get scene for object
                scene = self._get_scene_for_object(obj, scenes)
                if not scene:
                    continue
                
                # Solve object position based on object type
                solved_obj = await self._solve_object_position(obj, scene)
                solved_objects.append(solved_obj)
                
            except Exception as e:
                print(f"Failed to solve object position: {e}")
                solved_objects.append(obj)
        
        return solved_objects
    
    async def _solve_object_position(self, obj: Dict[str, Any], scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve individual object position."""
        try:
            # Get object type
            object_type = obj.get("type", "unknown")
            
            # Solve position based on object type
            if object_type == "document":
                position = await self._solve_document_object_position(obj, scene)
            elif object_type == "image":
                position = await self._solve_image_object_position(obj, scene)
            elif object_type == "audio":
                position = await self._solve_audio_object_position(obj, scene)
            elif object_type == "video":
                position = await self._solve_video_object_position(obj, scene)
            elif object_type == "object":
                position = await self._solve_object_object_position(obj, scene)
            elif object_type == "testimony":
                position = await self._solve_testimony_object_position(obj, scene)
            else:
                position = obj.get("position", [0, 0, 0])
            
            # Update object
            solved_obj = obj.copy()
            solved_obj["position"] = position
            solved_obj["solved"] = True
            
            return solved_obj
            
        except Exception as e:
            print(f"Failed to solve object position: {e}")
            return obj
    
    async def _solve_document_object_position(self, obj: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve document object position."""
        # Documents are positioned on a surface
        return [0, 0, 0]
    
    async def _solve_image_object_position(self, obj: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve image object position."""
        # Images are positioned on a surface
        return [0, 0, 0]
    
    async def _solve_audio_object_position(self, obj: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve audio object position."""
        # Audio objects are positioned in 3D space
        return [0, 1, 0]
    
    async def _solve_video_object_position(self, obj: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve video object position."""
        # Video objects are positioned on a surface
        return [0, 0, 0]
    
    async def _solve_object_object_position(self, obj: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve object object position."""
        # Objects are positioned on a surface
        return [0, 0, 0]
    
    async def _solve_testimony_object_position(self, obj: Dict[str, Any], scene: Dict[str, Any]) -> List[float]:
        """Solve testimony object position."""
        # Testimony objects are positioned in 3D space
        return [0, 1.7, 0]
    
    async def _solve_scene_transitions(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Solve scene transitions."""
        solved_scenes = []
        
        for i, scene in enumerate(scenes):
            try:
                # Solve transition to next scene
                if i < len(scenes) - 1:
                    next_scene = scenes[i + 1]
                    transition = await self._solve_scene_transition(scene, next_scene)
                    scene["transition"] = transition
                
                solved_scenes.append(scene)
                
            except Exception as e:
                print(f"Failed to solve scene transition: {e}")
                solved_scenes.append(scene)
        
        return solved_scenes
    
    async def _solve_scene_transition(self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve transition between scenes."""
        try:
            # Get transition type
            transition_type = current_scene.get("transition", {}).get("type", "fade")
            
            # Solve transition based on type
            if transition_type == "fade":
                transition = await self._solve_fade_transition(current_scene, next_scene)
            elif transition_type == "dissolve":
                transition = await self._solve_dissolve_transition(current_scene, next_scene)
            elif transition_type == "wipe":
                transition = await self._solve_wipe_transition(current_scene, next_scene)
            elif transition_type == "slide":
                transition = await self._solve_slide_transition(current_scene, next_scene)
            elif transition_type == "zoom":
                transition = await self._solve_zoom_transition(current_scene, next_scene)
            elif transition_type == "pan":
                transition = await self._solve_pan_transition(current_scene, next_scene)
            else:
                transition = await self._solve_fade_transition(current_scene, next_scene)
            
            return transition
            
        except Exception as e:
            print(f"Failed to solve scene transition: {e}")
            return {"type": "fade", "duration": 1.0}
    
    async def _solve_fade_transition(self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve fade transition."""
        return {
            "type": "fade",
            "duration": 1.0,
            "easing": "linear",
        }
    
    async def _solve_dissolve_transition(self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve dissolve transition."""
        return {
            "type": "dissolve",
            "duration": 1.5,
            "easing": "ease_in_out",
        }
    
    async def _solve_wipe_transition(self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve wipe transition."""
        return {
            "type": "wipe",
            "duration": 1.0,
            "direction": "left_to_right",
            "easing": "linear",
        }
    
    async def _solve_slide_transition(self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve slide transition."""
        return {
            "type": "slide",
            "duration": 1.0,
            "direction": "left_to_right",
            "easing": "ease_in_out",
        }
    
    async def _solve_zoom_transition(self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve zoom transition."""
        return {
            "type": "zoom",
            "duration": 1.0,
            "zoom_factor": 1.5,
            "easing": "ease_in_out",
        }
    
    async def _solve_pan_transition(self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> Dict[str, Any]:
        """Solve pan transition."""
        return {
            "type": "pan",
            "duration": 1.0,
            "direction": "left_to_right",
            "easing": "ease_in_out",
        }
    
    def _get_scene_for_camera(self, camera: Dict[str, Any], scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get scene for camera."""
        scene_id = camera.get("scene_id", "")
        for scene in scenes:
            if scene.get("id", "") == scene_id:
                return scene
        return None
    
    def _get_scene_for_light(self, light: Dict[str, Any], scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get scene for light."""
        scene_id = light.get("scene_id", "")
        for scene in scenes:
            if scene.get("id", "") == scene_id:
                return scene
        return None
    
    def _get_scene_for_object(self, obj: Dict[str, Any], scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get scene for object."""
        scene_id = obj.get("scene_id", "")
        for scene in scenes:
            if scene.get("id", "") == scene_id:
                return scene
        return None
    
    def _validate_spatial_solution(self, scene_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Validate spatial solution."""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "solved_cameras": 0,
            "solved_lights": 0,
            "solved_objects": 0,
        }
        
        try:
            # Count solved cameras
            for camera in scene_graph.get("cameras", []):
                if camera.get("solved", False):
                    validation_results["solved_cameras"] += 1
            
            # Count solved lights
            for light in scene_graph.get("lights", []):
                if light.get("solved", False):
                    validation_results["solved_lights"] += 1
            
            # Count solved objects
            for obj in scene_graph.get("objects", []):
                if obj.get("solved", False):
                    validation_results["solved_objects"] += 1
            
            # Check for unsolved elements
            total_cameras = len(scene_graph.get("cameras", []))
            total_lights = len(scene_graph.get("lights", []))
            total_objects = len(scene_graph.get("objects", []))
            
            if validation_results["solved_cameras"] < total_cameras:
                validation_results["warnings"].append(f"Only {validation_results['solved_cameras']}/{total_cameras} cameras solved")
            
            if validation_results["solved_lights"] < total_lights:
                validation_results["warnings"].append(f"Only {validation_results['solved_lights']}/{total_lights} lights solved")
            
            if validation_results["solved_objects"] < total_objects:
                validation_results["warnings"].append(f"Only {validation_results['solved_objects']}/{total_objects} objects solved")
            
            # Set overall validity
            validation_results["valid"] = len(validation_results["issues"]) == 0
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Validation failed: {str(e)}")
        
        return validation_results
    
    def _optimize_spatial_layout(self, scene_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize spatial layout."""
        try:
            # Optimize camera positions
            scene_graph["cameras"] = self._optimize_camera_positions(scene_graph["cameras"])
            
            # Optimize light positions
            scene_graph["lights"] = self._optimize_light_positions(scene_graph["lights"])
            
            # Optimize object positions
            scene_graph["objects"] = self._optimize_object_positions(scene_graph["objects"])
            
            return scene_graph
            
        except Exception as e:
            print(f"Failed to optimize spatial layout: {e}")
            return scene_graph
    
    def _optimize_camera_positions(self, cameras: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize camera positions."""
        optimized_cameras = []
        
        for camera in cameras:
            try:
                # Optimize camera position
                optimized_camera = camera.copy()
                
                # Ensure camera is not too close to objects
                position = optimized_camera.get("position", [0, 0, self.default_camera_distance])
                if position[2] < 1.0:
                    position[2] = self.default_camera_distance
                    optimized_camera["position"] = position
                
                optimized_cameras.append(optimized_camera)
                
            except Exception as e:
                print(f"Failed to optimize camera position: {e}")
                optimized_cameras.append(camera)
        
        return optimized_cameras
    
    def _optimize_light_positions(self, lights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize light positions."""
        optimized_lights = []
        
        for light in lights:
            try:
                # Optimize light position
                optimized_light = light.copy()
                
                # Ensure light is not too close to objects
                position = optimized_light.get("position", [0, self.default_light_distance, 0])
                if position[1] < 1.0:
                    position[1] = self.default_light_distance
                    optimized_light["position"] = position
                
                optimized_lights.append(optimized_light)
                
            except Exception as e:
                print(f"Failed to optimize light position: {e}")
                optimized_lights.append(light)
        
        return optimized_lights
    
    def _optimize_object_positions(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize object positions."""
        optimized_objects = []
        
        for obj in objects:
            try:
                # Optimize object position
                optimized_obj = obj.copy()
                
                # Ensure object is not overlapping with others
                position = optimized_obj.get("position", [0, 0, 0])
                # Simple optimization: spread objects out
                if len(optimized_objects) > 0:
                    position[0] += len(optimized_objects) * 0.5
                optimized_obj["position"] = position
                
                optimized_objects.append(optimized_obj)
                
            except Exception as e:
                print(f"Failed to optimize object position: {e}")
                optimized_objects.append(obj)
        
        return optimized_objects
