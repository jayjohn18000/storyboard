"""Abstract renderer interface for 3D scene generation."""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RenderEngine(Enum):
    """Supported render engines."""
    BLENDER_LOCAL = "blender_local"
    BLENDER_DISTRIBUTED = "blender_distributed"
    BLENDER_GPU = "blender_gpu"


class RenderProfile(Enum):
    """Render quality profiles."""
    NEUTRAL = "neutral"  # Court-safe settings
    CINEMATIC = "cinematic"  # Sandbox only


@dataclass
class RenderConfig:
    """Configuration for rendering."""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration_seconds: float = 10.0
    profile: RenderProfile = RenderProfile.NEUTRAL
    engine: RenderEngine = RenderEngine.BLENDER_LOCAL
    deterministic: bool = True
    seed: Optional[int] = None
    output_format: str = "mp4"
    quality: str = "high"


@dataclass
class RenderResult:
    """Result of render operation."""
    render_id: str
    output_path: str
    duration_seconds: float
    file_size_bytes: int
    render_time_seconds: float
    frames_rendered: int
    profile_used: str
    checksum: str


@dataclass
class SceneData:
    """3D scene data for rendering."""
    usd_data: bytes
    timeline_data: bytes
    camera_path: List[Dict[str, Any]]
    lighting_config: Dict[str, Any]
    materials: List[Dict[str, Any]]


class RendererService(Protocol):
    """Protocol for renderer service implementations."""
    
    async def render_scene(
        self, 
        scene_data: SceneData, 
        config: RenderConfig
    ) -> RenderResult:
        """Render 3D scene to video."""
        ...
    
    async def render_frame(
        self, 
        scene_data: SceneData, 
        frame_number: int,
        config: RenderConfig
    ) -> bytes:
        """Render single frame as image."""
        ...
    
    async def validate_scene(self, scene_data: SceneData) -> bool:
        """Validate scene data before rendering."""
        ...
    
    async def get_render_status(self, render_id: str) -> str:
        """Get status of render job."""
        ...


class RendererInterface(ABC):
    """Abstract base class for renderer implementations."""
    
    @abstractmethod
    async def render_scene(
        self, 
        scene_data: SceneData, 
        config: RenderConfig
    ) -> RenderResult:
        """Render 3D scene to video."""
        pass
    
    @abstractmethod
    async def render_frame(
        self, 
        scene_data: SceneData, 
        frame_number: int,
        config: RenderConfig
    ) -> bytes:
        """Render single frame as image."""
        pass
    
    @abstractmethod
    async def validate_scene(self, scene_data: SceneData) -> bool:
        """Validate scene data before rendering."""
        pass
    
    @abstractmethod
    async def get_render_status(self, render_id: str) -> str:
        """Get status of render job."""
        pass


class RenderError(Exception):
    """Base exception for render operations."""
    pass


class SceneValidationError(RenderError):
    """Raised when scene data is invalid."""
    pass


class RenderTimeoutError(RenderError):
    """Raised when render operation times out."""
    pass


class DeterminismError(RenderError):
    """Raised when deterministic rendering fails."""
    pass
