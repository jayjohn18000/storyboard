"""Trajectory generator for camera movements."""

import numpy as np
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class TrajectoryGenerator:
    """Generates camera trajectories for scenes."""
    
    def __init__(self):
        """Initialize trajectory generator."""
        self.default_speed = 1.0  # units per second
        self.default_acceleration = 0.5  # units per second squared
        self.default_jerk = 0.1  # units per second cubed
    
    async def generate_trajectory(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate camera trajectory for scene."""
        try:
            # Extract scene information
            scene_type = scene_data.get("scene_type", "evidence_display")
            duration = scene_data.get("duration", 5.0)
            camera_config = scene_data.get("camera_config", {})
            evidence_anchors = scene_data.get("evidence_anchors", [])
            
            # Generate trajectory based on scene type
            if scene_type == "evidence_display":
                trajectory = await self._generate_evidence_trajectory(
                    duration, camera_config, evidence_anchors
                )
            elif scene_type == "transition":
                trajectory = await self._generate_transition_trajectory(
                    duration, camera_config
                )
            elif scene_type == "overview":
                trajectory = await self._generate_overview_trajectory(
                    duration, camera_config
                )
            else:
                trajectory = await self._generate_default_trajectory(
                    duration, camera_config
                )
            
            return {
                "trajectory_type": scene_type,
                "duration": duration,
                "keyframes": trajectory["keyframes"],
                "smooth_curves": trajectory["smooth_curves"],
                "interpolation_method": trajectory["interpolation_method"],
                "total_distance": trajectory["total_distance"],
                "average_speed": trajectory["average_speed"],
            }
            
        except Exception as e:
            logger.error(f"Trajectory generation failed: {e}")
            raise Exception(f"Trajectory generation failed: {str(e)}")
    
    async def _generate_evidence_trajectory(
        self, 
        duration: float, 
        camera_config: Dict[str, Any], 
        evidence_anchors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trajectory for evidence display scene."""
        keyframes = []
        
        # Start position
        start_pos = camera_config.get("position", [0, 0, 5])
        start_rot = camera_config.get("rotation", [0, 0, 0])
        
        keyframes.append({
            "time": 0.0,
            "position": start_pos,
            "rotation": start_rot,
            "focal_length": camera_config.get("focal_length", 50),
            "fov": camera_config.get("fov", 45),
        })
        
        # Generate keyframes for each evidence anchor
        for i, anchor in enumerate(evidence_anchors):
            anchor_time = anchor.get("start_time", 0.0)
            anchor_duration = anchor.get("end_time", duration) - anchor_time
            
            # Calculate focus position based on anchor
            focus_pos = self._calculate_focus_position(anchor)
            
            # Add keyframe for evidence focus
            keyframes.append({
                "time": anchor_time,
                "position": focus_pos,
                "rotation": self._calculate_focus_rotation(focus_pos, start_pos),
                "focal_length": camera_config.get("focal_length", 50),
                "fov": camera_config.get("fov", 45),
                "evidence_id": anchor.get("evidence_id"),
            })
        
        # End position
        end_pos = camera_config.get("end_position", start_pos)
        end_rot = camera_config.get("end_rotation", start_rot)
        
        keyframes.append({
            "time": duration,
            "position": end_pos,
            "rotation": end_rot,
            "focal_length": camera_config.get("focal_length", 50),
            "fov": camera_config.get("fov", 45),
        })
        
        # Sort keyframes by time
        keyframes.sort(key=lambda x: x["time"])
        
        # Generate smooth curves
        smooth_curves = self._generate_smooth_curves(keyframes, duration)
        
        # Calculate trajectory metrics
        total_distance = self._calculate_total_distance(keyframes)
        average_speed = total_distance / duration if duration > 0 else 0
        
        return {
            "keyframes": keyframes,
            "smooth_curves": smooth_curves,
            "interpolation_method": "bezier",
            "total_distance": total_distance,
            "average_speed": average_speed,
        }
    
    async def _generate_transition_trajectory(
        self, 
        duration: float, 
        camera_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trajectory for transition scene."""
        keyframes = []
        
        # Start position
        start_pos = camera_config.get("start_position", [0, 0, 5])
        start_rot = camera_config.get("start_rotation", [0, 0, 0])
        
        keyframes.append({
            "time": 0.0,
            "position": start_pos,
            "rotation": start_rot,
            "focal_length": camera_config.get("focal_length", 50),
            "fov": camera_config.get("fov", 45),
        })
        
        # End position
        end_pos = camera_config.get("end_position", [0, 0, 5])
        end_rot = camera_config.get("end_rotation", [0, 0, 0])
        
        keyframes.append({
            "time": duration,
            "position": end_pos,
            "rotation": end_rot,
            "focal_length": camera_config.get("focal_length", 50),
            "fov": camera_config.get("fov", 45),
        })
        
        # Generate smooth curves
        smooth_curves = self._generate_smooth_curves(keyframes, duration)
        
        # Calculate trajectory metrics
        total_distance = self._calculate_total_distance(keyframes)
        average_speed = total_distance / duration if duration > 0 else 0
        
        return {
            "keyframes": keyframes,
            "smooth_curves": smooth_curves,
            "interpolation_method": "linear",
            "total_distance": total_distance,
            "average_speed": average_speed,
        }
    
    async def _generate_overview_trajectory(
        self, 
        duration: float, 
        camera_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trajectory for overview scene."""
        keyframes = []
        
        # Start position (wide view)
        start_pos = camera_config.get("position", [0, 0, 10])
        start_rot = camera_config.get("rotation", [0, 0, 0])
        
        keyframes.append({
            "time": 0.0,
            "position": start_pos,
            "rotation": start_rot,
            "focal_length": camera_config.get("focal_length", 35),
            "fov": camera_config.get("fov", 60),
        })
        
        # End position (closer view)
        end_pos = camera_config.get("end_position", [0, 0, 7])
        end_rot = camera_config.get("end_rotation", [0, 0, 0])
        
        keyframes.append({
            "time": duration,
            "position": end_pos,
            "rotation": end_rot,
            "focal_length": camera_config.get("focal_length", 50),
            "fov": camera_config.get("fov", 45),
        })
        
        # Generate smooth curves
        smooth_curves = self._generate_smooth_curves(keyframes, duration)
        
        # Calculate trajectory metrics
        total_distance = self._calculate_total_distance(keyframes)
        average_speed = total_distance / duration if duration > 0 else 0
        
        return {
            "keyframes": keyframes,
            "smooth_curves": smooth_curves,
            "interpolation_method": "bezier",
            "total_distance": total_distance,
            "average_speed": average_speed,
        }
    
    async def _generate_default_trajectory(
        self, 
        duration: float, 
        camera_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate default trajectory."""
        keyframes = []
        
        # Static position
        pos = camera_config.get("position", [0, 0, 5])
        rot = camera_config.get("rotation", [0, 0, 0])
        
        keyframes.append({
            "time": 0.0,
            "position": pos,
            "rotation": rot,
            "focal_length": camera_config.get("focal_length", 50),
            "fov": camera_config.get("fov", 45),
        })
        
        keyframes.append({
            "time": duration,
            "position": pos,
            "rotation": rot,
            "focal_length": camera_config.get("focal_length", 50),
            "fov": camera_config.get("fov", 45),
        })
        
        return {
            "keyframes": keyframes,
            "smooth_curves": [],
            "interpolation_method": "static",
            "total_distance": 0.0,
            "average_speed": 0.0,
        }
    
    def _calculate_focus_position(self, anchor: Dict[str, Any]) -> List[float]:
        """Calculate camera position to focus on evidence anchor."""
        # Default focus position
        focus_pos = [0, 0, 3]
        
        # Adjust based on anchor properties
        if "position" in anchor:
            anchor_pos = anchor["position"]
            # Position camera to view the evidence
            focus_pos = [
                anchor_pos[0],
                anchor_pos[1],
                anchor_pos[2] + 2  # 2 units above the evidence
            ]
        
        return focus_pos
    
    def _calculate_focus_rotation(
        self, 
        focus_pos: List[float], 
        start_pos: List[float]
    ) -> List[float]:
        """Calculate camera rotation to focus on position."""
        # Calculate rotation to look at focus position
        dx = focus_pos[0] - start_pos[0]
        dy = focus_pos[1] - start_pos[1]
        dz = focus_pos[2] - start_pos[2]
        
        # Calculate yaw (rotation around Y axis)
        yaw = np.arctan2(dx, dz)
        
        # Calculate pitch (rotation around X axis)
        distance = np.sqrt(dx**2 + dz**2)
        pitch = np.arctan2(-dy, distance)
        
        return [np.degrees(pitch), np.degrees(yaw), 0]
    
    def _generate_smooth_curves(
        self, 
        keyframes: List[Dict[str, Any]], 
        duration: float
    ) -> List[Dict[str, Any]]:
        """Generate smooth curves between keyframes."""
        curves = []
        
        for i in range(len(keyframes) - 1):
            current_frame = keyframes[i]
            next_frame = keyframes[i + 1]
            
            # Generate curve points
            curve_points = self._interpolate_bezier(
                current_frame, 
                next_frame, 
                duration
            )
            
            curves.append({
                "start_time": current_frame["time"],
                "end_time": next_frame["time"],
                "points": curve_points,
                "curve_type": "bezier",
            })
        
        return curves
    
    def _interpolate_bezier(
        self, 
        start_frame: Dict[str, Any], 
        end_frame: Dict[str, Any], 
        duration: float
    ) -> List[Dict[str, Any]]:
        """Interpolate Bezier curve between keyframes."""
        points = []
        
        # Generate 10 points between keyframes
        num_points = 10
        for i in range(num_points + 1):
            t = i / num_points
            
            # Interpolate position
            start_pos = np.array(start_frame["position"])
            end_pos = np.array(end_frame["position"])
            pos = start_pos + t * (end_pos - start_pos)
            
            # Interpolate rotation
            start_rot = np.array(start_frame["rotation"])
            end_rot = np.array(end_frame["rotation"])
            rot = start_rot + t * (end_rot - start_rot)
            
            # Interpolate focal length
            start_focal = start_frame.get("focal_length", 50)
            end_focal = end_frame.get("focal_length", 50)
            focal = start_focal + t * (end_focal - start_focal)
            
            # Interpolate FOV
            start_fov = start_frame.get("fov", 45)
            end_fov = end_frame.get("fov", 45)
            fov = start_fov + t * (end_fov - start_fov)
            
            points.append({
                "time": start_frame["time"] + t * (end_frame["time"] - start_frame["time"]),
                "position": pos.tolist(),
                "rotation": rot.tolist(),
                "focal_length": focal,
                "fov": fov,
            })
        
        return points
    
    def _calculate_total_distance(self, keyframes: List[Dict[str, Any]]) -> float:
        """Calculate total distance traveled by camera."""
        total_distance = 0.0
        
        for i in range(len(keyframes) - 1):
            current_pos = np.array(keyframes[i]["position"])
            next_pos = np.array(keyframes[i + 1]["position"])
            distance = np.linalg.norm(next_pos - current_pos)
            total_distance += distance
        
        return total_distance
