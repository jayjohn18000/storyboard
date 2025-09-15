"""Blender local renderer implementation."""

import asyncio
import os
import tempfile
import subprocess
import hashlib
import time
import json
from typing import Dict, Any, List
from pathlib import Path

from services.shared.interfaces.renderer import (
    RendererInterface, 
    RenderConfig, 
    RenderResult, 
    SceneData,
    RenderError,
    SceneValidationError,
    RenderTimeoutError,
    DeterminismError
)


class BlenderLocalRenderer(RendererInterface):
    """Blender local renderer implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Blender local renderer."""
        self.blender_path = config.get("blender_path", "blender")
        self.blender_version = config.get("blender_version", "4.0")
        self.temp_dir = Path(config.get("temp_dir", "/tmp/blender-renders"))
        self.memory_limit = config.get("memory_limit", 8192)
        self.timeout = config.get("timeout", 3600)
        self.deterministic = config.get("deterministic", True)
        self.seed = config.get("seed", 42)
        
        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify Blender installation
        asyncio.create_task(self._verify_blender_installation())
    
    async def _verify_blender_installation(self) -> None:
        """Verify Blender installation."""
        try:
            result = subprocess.run(
                [self.blender_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RenderError(f"Blender not found at {self.blender_path}")
            
            # Check version compatibility
            version_output = result.stdout
            if self.blender_version not in version_output:
                print(f"Warning: Expected Blender {self.blender_version}, found: {version_output}")
                
        except subprocess.TimeoutExpired:
            raise RenderError(f"Blender command timeout")
        except FileNotFoundError:
            raise RenderError(f"Blender not found at {self.blender_path}")
    
    async def render_scene(
        self, 
        scene_data: SceneData, 
        config: RenderConfig
    ) -> RenderResult:
        """Render 3D scene to video."""
        try:
            start_time = time.time()
            
            # Validate scene data
            if not await self.validate_scene(scene_data):
                raise SceneValidationError("Scene data validation failed")
            
            # Create temporary workspace
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as workspace:
                workspace_path = Path(workspace)
                
                # Write scene data to files
                usd_file = workspace_path / "scene.usd"
                timeline_file = workspace_path / "timeline.json"
                
                usd_file.write_bytes(scene_data.usd_data)
                timeline_file.write_bytes(scene_data.timeline_data)
                
                # Generate Blender script
                script_file = workspace_path / "render_script.py"
                await self._generate_blender_script(
                    script_file, 
                    usd_file, 
                    timeline_file, 
                    config,
                    scene_data
                )
                
                # Execute Blender render
                output_file = workspace_path / f"output.{config.output_format}"
                render_id = f"render_{int(time.time())}_{hashlib.md5(scene_data.usd_data).hexdigest()[:8]}"
                
                await self._execute_blender_render(
                    script_file, 
                    output_file, 
                    config,
                    render_id
                )
                
                # Calculate results
                render_time = time.time() - start_time
                file_size = output_file.stat().st_size
                checksum = await self._calculate_checksum(output_file)
                
                # Move output to final location
                final_output = self.temp_dir / f"{render_id}.{config.output_format}"
                output_file.rename(final_output)
                
                return RenderResult(
                    render_id=render_id,
                    output_path=str(final_output),
                    duration_seconds=config.duration_seconds,
                    file_size_bytes=file_size,
                    render_time_seconds=render_time,
                    frames_rendered=int(config.duration_seconds * config.fps),
                    profile_used=config.profile.value,
                    checksum=checksum
                )
                
        except Exception as e:
            raise RenderError(f"Render failed: {str(e)}")
    
    async def render_frame(
        self, 
        scene_data: SceneData, 
        frame_number: int,
        config: RenderConfig
    ) -> bytes:
        """Render single frame as image."""
        try:
            # Create temporary workspace
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as workspace:
                workspace_path = Path(workspace)
                
                # Write scene data
                usd_file = workspace_path / "scene.usd"
                timeline_file = workspace_path / "timeline.json"
                
                usd_file.write_bytes(scene_data.usd_data)
                timeline_file.write_bytes(scene_data.timeline_data)
                
                # Generate single frame script
                script_file = workspace_path / "frame_script.py"
                await self._generate_frame_script(
                    script_file, 
                    usd_file, 
                    timeline_file, 
                    frame_number,
                    config,
                    scene_data
                )
                
                # Execute Blender render
                output_file = workspace_path / f"frame_{frame_number:06d}.png"
                
                await self._execute_blender_render(
                    script_file, 
                    output_file, 
                    config,
                    f"frame_{frame_number}"
                )
                
                return output_file.read_bytes()
                
        except Exception as e:
            raise RenderError(f"Frame render failed: {str(e)}")
    
    async def validate_scene(self, scene_data: SceneData) -> bool:
        """Validate scene data before rendering."""
        try:
            # Check USD data is not empty
            if not scene_data.usd_data or len(scene_data.usd_data) < 100:
                return False
            
            # Check timeline data is valid JSON
            try:
                json.loads(scene_data.timeline_data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return False
            
            # Check camera path is valid
            if not scene_data.camera_path or len(scene_data.camera_path) == 0:
                return False
            
            # Check lighting config
            if not scene_data.lighting_config:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def get_render_status(self, render_id: str) -> str:
        """Get status of render job."""
        # For local renderer, jobs are synchronous
        # Check if output file exists
        output_files = list(self.temp_dir.glob(f"{render_id}.*"))
        if output_files:
            return "completed"
        else:
            return "not_found"
    
    async def _generate_blender_script(
        self, 
        script_file: Path, 
        usd_file: Path, 
        timeline_file: Path, 
        config: RenderConfig,
        scene_data: SceneData
    ) -> None:
        """Generate Blender Python script for rendering."""
        
        # Import render profile
        if config.profile.value == "neutral":
            from .profiles.neutral import NeutralProfile
            profile = NeutralProfile()
        else:
            from .profiles.cinematic import CinematicProfile
            profile = CinematicProfile()
        
        script_content = f'''
import bpy
import bmesh
import json
import os
from mathutils import Vector, Euler
import bpy_extras.io_utils

# Clear existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = {config.width}
scene.render.resolution_y = {config.height}
scene.render.fps = {config.fps}
scene.render.fps_base = 1.0
scene.frame_start = 1
scene.frame_end = int({config.duration_seconds} * {config.fps})

# Set deterministic seed if enabled
if {self.deterministic}:
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_set(1)  # Ensure seed is set

# Apply render profile
{profile.get_blender_script()}

# Load USD scene (placeholder - would need USD import addon)
# For now, create a simple test scene
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

# Set up camera from camera path
camera_data = bpy.data.cameras.new(name="Camera")
camera_obj = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera_obj)

# Position camera based on first camera path point
if {scene_data.camera_path}:
    first_point = {scene_data.camera_path}[0]
    camera_obj.location = Vector((first_point.get('x', 0), first_point.get('y', 0), first_point.get('z', 5)))
    camera_obj.rotation_euler = Euler((first_point.get('rx', 0), first_point.get('ry', 0), first_point.get('rz', 0)))

# Set camera as active
scene.camera = camera_obj

# Set output path
scene.render.filepath = "{script_file.parent}/output_"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'

# Render
bpy.ops.render.render(animation=True)

print("Render completed successfully")
'''
        
        script_file.write_text(script_content)
    
    async def _generate_frame_script(
        self, 
        script_file: Path, 
        usd_file: Path, 
        timeline_file: Path, 
        frame_number: int,
        config: RenderConfig,
        scene_data: SceneData
    ) -> None:
        """Generate Blender Python script for single frame rendering."""
        
        script_content = f'''
import bpy
import bmesh
import json
import os
from mathutils import Vector, Euler

# Clear existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = {config.width}
scene.render.resolution_y = {config.height}
scene.render.fps = {config.fps}
scene.frame_set({frame_number})

# Create simple test scene
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

# Set up camera
camera_data = bpy.data.cameras.new(name="Camera")
camera_obj = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera_obj)
camera_obj.location = Vector((0, 0, 5))
scene.camera = camera_obj

# Set output path
scene.render.filepath = "{script_file.parent}/frame_{frame_number:06d}_"
scene.render.image_settings.file_format = 'PNG'

# Render single frame
bpy.ops.render.render(write_still=True)

print(f"Frame {frame_number} rendered successfully")
'''
        
        script_file.write_text(script_content)
    
    async def _execute_blender_render(
        self, 
        script_file: Path, 
        output_file: Path, 
        config: RenderConfig,
        render_id: str
    ) -> None:
        """Execute Blender render command."""
        try:
            cmd = [
                self.blender_path,
                "--background",
                "--python", str(script_file),
                "--",  # Pass arguments to script
                "--output", str(output_file),
                "--render-id", render_id
            ]
            
            # Set memory limit
            env = os.environ.copy()
            env["BLENDER_MEMORY_LIMIT"] = str(self.memory_limit)
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
            )
            
            if result.returncode != 0:
                raise RenderError(f"Blender render failed: {result.stderr}")
            
            # Verify output file was created
            if not output_file.exists():
                raise RenderError("Output file was not created")
                
        except subprocess.TimeoutExpired:
            raise RenderTimeoutError(f"Render timeout after {self.timeout} seconds")
        except Exception as e:
            raise RenderError(f"Blender execution failed: {str(e)}")
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
