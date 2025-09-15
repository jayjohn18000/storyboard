"""Blender local renderer implementation for shared use."""

# Import the actual implementation from render-orchestrator
import sys
from pathlib import Path

# Add the render-orchestrator path to sys.path
render_orchestrator_path = Path(__file__).parent.parent.parent.parent / "render-orchestrator"
sys.path.insert(0, str(render_orchestrator_path))

try:
    from implementations.blender.local_renderer import BlenderLocalRenderer
except ImportError:
    # Fallback implementation if render-orchestrator is not available
    from ...interfaces.renderer import RendererInterface, RenderError
    
    class BlenderLocalRenderer(RendererInterface):
        """Fallback Blender local renderer."""
        
        def __init__(self, config):
            raise RenderError("BlenderLocalRenderer not available - render-orchestrator service not found")
        
        async def render_scene(self, scene_data, config):
            raise RenderError("Not implemented")
        
        async def render_frame(self, scene_data, frame_number, config):
            raise RenderError("Not implemented")
        
        async def validate_scene(self, scene_data):
            return False
        
        async def get_render_status(self, render_id):
            return "not_available"
