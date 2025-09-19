"""Camera trajectory generator for legal simulation scenes."""

import math
import random
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TrajectoryType(Enum):
    """Types of camera trajectories."""
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    ZOOM = "zoom"
    DOLLY = "dolly"
    TRACKING = "tracking"
    ORBIT = "orbit"
    KEN_BURNS = "ken_burns"
    CUSTOM = "custom"


class EasingType(Enum):
    """Easing types for smooth animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"


@dataclass
class CameraPosition:
    """Camera position in 3D space."""
    x: float
    y: float
    z: float
    rotation_x: float = 0.0  # Pitch
    rotation_y: float = 0.0  # Yaw
    rotation_z: float = 0.0  # Roll
    fov: float = 50.0  # Field of view in degrees


@dataclass
class TrajectoryKeyframe:
    """Keyframe for camera trajectory."""
    time: float  # Time in seconds
    position: CameraPosition
    easing: EasingType = EasingType.LINEAR


@dataclass
class TrajectoryConfig:
    """Configuration for trajectory generation."""
    duration: float = 10.0  # Duration in seconds
    fps: int = 30  # Frames per second
    trajectory_type: TrajectoryType = TrajectoryType.STATIC
    start_position: Optional[CameraPosition] = None
    end_position: Optional[CameraPosition] = None
    target_position: Optional[Tuple[float, float, float]] = None
    easing: EasingType = EasingType.EASE_IN_OUT
    random_seed: Optional[int] = None


class TrajectoryGenerator:
    """Generator for camera trajectories in legal simulations."""
    
    def __init__(self, config: TrajectoryConfig):
        self.config = config
        if config.random_seed is not None:
            random.seed(config.random_seed)
    
    def generate_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate camera trajectory based on configuration."""
        if self.config.trajectory_type == TrajectoryType.STATIC:
            return self._generate_static_trajectory()
        elif self.config.trajectory_type == TrajectoryType.PAN:
            return self._generate_pan_trajectory()
        elif self.config.trajectory_type == TrajectoryType.TILT:
            return self._generate_tilt_trajectory()
        elif self.config.trajectory_type == TrajectoryType.ZOOM:
            return self._generate_zoom_trajectory()
        elif self.config.trajectory_type == TrajectoryType.DOLLY:
            return self._generate_dolly_trajectory()
        elif self.config.trajectory_type == TrajectoryType.TRACKING:
            return self._generate_tracking_trajectory()
        elif self.config.trajectory_type == TrajectoryType.ORBIT:
            return self._generate_orbit_trajectory()
        elif self.config.trajectory_type == TrajectoryType.KEN_BURNS:
            return self._generate_ken_burns_trajectory()
        else:
            return self._generate_custom_trajectory()
    
    def _generate_static_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate static camera trajectory."""
        start_pos = self.config.start_position or CameraPosition(0, 0, 5)
        
        return [
            TrajectoryKeyframe(
                time=0.0,
                position=start_pos,
                easing=self.config.easing
            ),
            TrajectoryKeyframe(
                time=self.config.duration,
                position=start_pos,
                easing=self.config.easing
            )
        ]
    
    def _generate_pan_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate panning camera trajectory."""
        start_pos = self.config.start_position or CameraPosition(0, 0, 5)
        end_pos = self.config.end_position or CameraPosition(0, 0, 5)
        
        # Pan horizontally
        end_pos.rotation_y = start_pos.rotation_y + 30.0  # 30 degree pan
        
        return [
            TrajectoryKeyframe(
                time=0.0,
                position=start_pos,
                easing=self.config.easing
            ),
            TrajectoryKeyframe(
                time=self.config.duration,
                position=end_pos,
                easing=self.config.easing
            )
        ]
    
    def _generate_tilt_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate tilting camera trajectory."""
        start_pos = self.config.start_position or CameraPosition(0, 0, 5)
        end_pos = self.config.end_position or CameraPosition(0, 0, 5)
        
        # Tilt vertically
        end_pos.rotation_x = start_pos.rotation_x + 20.0  # 20 degree tilt
        
        return [
            TrajectoryKeyframe(
                time=0.0,
                position=start_pos,
                easing=self.config.easing
            ),
            TrajectoryKeyframe(
                time=self.config.duration,
                position=end_pos,
                easing=self.config.easing
            )
        ]
    
    def _generate_zoom_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate zooming camera trajectory."""
        start_pos = self.config.start_position or CameraPosition(0, 0, 5)
        end_pos = self.config.end_position or CameraPosition(0, 0, 5)
        
        # Zoom in/out
        end_pos.fov = start_pos.fov * 0.5  # Zoom in by 50%
        
        return [
            TrajectoryKeyframe(
                time=0.0,
                position=start_pos,
                easing=self.config.easing
            ),
            TrajectoryKeyframe(
                time=self.config.duration,
                position=end_pos,
                easing=self.config.easing
            )
        ]
    
    def _generate_dolly_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate dollying camera trajectory."""
        start_pos = self.config.start_position or CameraPosition(0, 0, 5)
        end_pos = self.config.end_position or CameraPosition(0, 0, 5)
        
        # Move camera forward/backward
        end_pos.z = start_pos.z - 2.0  # Move closer
        
        return [
            TrajectoryKeyframe(
                time=0.0,
                position=start_pos,
                easing=self.config.easing
            ),
            TrajectoryKeyframe(
                time=self.config.duration,
                position=end_pos,
                easing=self.config.easing
            )
        ]
    
    def _generate_tracking_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate tracking camera trajectory."""
        start_pos = self.config.start_position or CameraPosition(0, 0, 5)
        end_pos = self.config.end_position or CameraPosition(0, 0, 5)
        
        # Move camera sideways while keeping target in view
        end_pos.x = start_pos.x + 3.0
        end_pos.rotation_y = start_pos.rotation_y - 15.0  # Compensate for movement
        
        return [
            TrajectoryKeyframe(
                time=0.0,
                position=start_pos,
                easing=self.config.easing
            ),
            TrajectoryKeyframe(
                time=self.config.duration,
                position=end_pos,
                easing=self.config.easing
            )
        ]
    
    def _generate_orbit_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate orbital camera trajectory."""
        start_pos = self.config.start_position or CameraPosition(3, 0, 5)
        target = self.config.target_position or (0, 0, 0)
        
        keyframes = []
        num_frames = int(self.config.duration * self.config.fps)
        
        for i in range(num_frames + 1):
            t = i / num_frames
            angle = t * 2 * math.pi  # Full circle
            
            # Calculate orbital position
            radius = math.sqrt(start_pos.x**2 + start_pos.z**2)
            x = target[0] + radius * math.cos(angle)
            z = target[2] + radius * math.sin(angle)
            y = start_pos.y
            
            # Calculate rotation to look at target
            dx = target[0] - x
            dz = target[2] - z
            rotation_y = math.degrees(math.atan2(dx, dz))
            
            position = CameraPosition(
                x=x, y=y, z=z,
                rotation_x=start_pos.rotation_x,
                rotation_y=rotation_y,
                rotation_z=start_pos.rotation_z,
                fov=start_pos.fov
            )
            
            keyframes.append(TrajectoryKeyframe(
                time=t * self.config.duration,
                position=position,
                easing=self.config.easing
            ))
        
        return keyframes
    
    def _generate_ken_burns_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate Ken Burns effect trajectory."""
        start_pos = self.config.start_position or CameraPosition(0, 0, 5)
        end_pos = self.config.end_position or CameraPosition(0, 0, 5)
        
        # Ken Burns: slow zoom + pan
        end_pos.fov = start_pos.fov * 0.8  # Slight zoom
        end_pos.x = start_pos.x + 1.0  # Slight pan
        end_pos.rotation_y = start_pos.rotation_y + 5.0  # Slight rotation
        
        return [
            TrajectoryKeyframe(
                time=0.0,
                position=start_pos,
                easing=EasingType.EASE_IN_OUT
            ),
            TrajectoryKeyframe(
                time=self.config.duration,
                position=end_pos,
                easing=EasingType.EASE_IN_OUT
            )
        ]
    
    def _generate_custom_trajectory(self) -> List[TrajectoryKeyframe]:
        """Generate custom trajectory based on multiple keyframes."""
        # Default to static if no custom configuration
        return self._generate_static_trajectory()
    
    def interpolate_position(self, keyframes: List[TrajectoryKeyframe], time: float) -> CameraPosition:
        """Interpolate camera position at given time."""
        if not keyframes:
            return CameraPosition(0, 0, 5)
        
        if len(keyframes) == 1:
            return keyframes[0].position
        
        # Find surrounding keyframes
        for i in range(len(keyframes) - 1):
            if keyframes[i].time <= time <= keyframes[i + 1].time:
                return self._interpolate_between_keyframes(
                    keyframes[i], keyframes[i + 1], time
                )
        
        # Clamp to first or last keyframe
        if time <= keyframes[0].time:
            return keyframes[0].position
        else:
            return keyframes[-1].position
    
    def _interpolate_between_keyframes(
        self, 
        kf1: TrajectoryKeyframe, 
        kf2: TrajectoryKeyframe, 
        time: float
    ) -> CameraPosition:
        """Interpolate between two keyframes."""
        if kf1.time == kf2.time:
            return kf1.position
        
        # Normalize time between keyframes
        t = (time - kf1.time) / (kf2.time - kf1.time)
        
        # Apply easing
        t_eased = self._apply_easing(t, kf1.easing)
        
        # Interpolate position
        pos1 = kf1.position
        pos2 = kf2.position
        
        return CameraPosition(
            x=self._lerp(pos1.x, pos2.x, t_eased),
            y=self._lerp(pos1.y, pos2.y, t_eased),
            z=self._lerp(pos1.z, pos2.z, t_eased),
            rotation_x=self._lerp(pos1.rotation_x, pos2.rotation_x, t_eased),
            rotation_y=self._lerp(pos1.rotation_y, pos2.rotation_y, t_eased),
            rotation_z=self._lerp(pos1.rotation_z, pos2.rotation_z, t_eased),
            fov=self._lerp(pos1.fov, pos2.fov, t_eased)
        )
    
    def _apply_easing(self, t: float, easing: EasingType) -> float:
        """Apply easing function to normalized time."""
        if easing == EasingType.LINEAR:
            return t
        elif easing == EasingType.EASE_IN:
            return t * t
        elif easing == EasingType.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif easing == EasingType.EASE_IN_OUT:
            return 3 * t * t - 2 * t * t * t
        elif easing == EasingType.EASE_IN_CUBIC:
            return t * t * t
        elif easing == EasingType.EASE_OUT_CUBIC:
            return 1 - (1 - t) * (1 - t) * (1 - t)
        elif easing == EasingType.EASE_IN_OUT_CUBIC:
            return t < 0.5 and 4 * t * t * t or 1 - 4 * (1 - t) * (1 - t) * (1 - t)
        else:
            return t
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation between two values."""
        return a + (b - a) * t
    
    def generate_deterministic_trajectory(self, seed: int) -> List[TrajectoryKeyframe]:
        """Generate deterministic trajectory with given seed."""
        original_seed = self.config.random_seed
        self.config.random_seed = seed
        random.seed(seed)
        
        trajectory = self.generate_trajectory()
        
        # Restore original seed
        self.config.random_seed = original_seed
        if original_seed is not None:
            random.seed(original_seed)
        
        return trajectory


def create_trajectory_generator(
    trajectory_type: TrajectoryType,
    duration: float = 10.0,
    start_position: Optional[CameraPosition] = None,
    end_position: Optional[CameraPosition] = None,
    **kwargs
) -> TrajectoryGenerator:
    """Create trajectory generator with specified parameters."""
    config = TrajectoryConfig(
        duration=duration,
        trajectory_type=trajectory_type,
        start_position=start_position,
        end_position=end_position,
        **kwargs
    )
    return TrajectoryGenerator(config)


# Example usage and testing
if __name__ == "__main__":
    # Test trajectory generation
    config = TrajectoryConfig(
        duration=5.0,
        trajectory_type=TrajectoryType.ORBIT,
        start_position=CameraPosition(3, 0, 5),
        target_position=(0, 0, 0),
        easing=EasingType.EASE_IN_OUT
    )
    
    generator = TrajectoryGenerator(config)
    trajectory = generator.generate_trajectory()
    
    print(f"Generated {len(trajectory)} keyframes for {config.trajectory_type.value} trajectory")
    for kf in trajectory[:3]:  # Show first 3 keyframes
        print(f"  Time: {kf.time:.2f}s, Position: ({kf.position.x:.2f}, {kf.position.y:.2f}, {kf.position.z:.2f})")
