"""Cinematic render profile for sandbox mode only."""

from typing import Dict, Any


class CinematicProfile:
    """Cinematic render profile for sandbox mode with enhanced visuals."""
    
    def __init__(self):
        self.name = "cinematic"
        self.description = "Enhanced render settings with dramatic lighting and effects (Sandbox only)"
    
    def get_blender_script(self) -> str:
        """Get Blender Python script for cinematic profile."""
        return '''
# Cinematic Profile Settings
scene = bpy.context.scene

# Render engine settings
scene.render.engine = 'CYCLES'
scene.cycles.samples = 512  # High quality
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPTIX'  # Use OptiX denoiser if available

# Enhanced lighting setup
scene.world.use_nodes = True
world_nodes = scene.world.node_tree.nodes
world_nodes.clear()

# Create HDRI environment
env_node = world_nodes.new(type='ShaderNodeTexEnvironment')
background_node = world_nodes.new(type='ShaderNodeBackground')
output_node = world_nodes.new(type='ShaderNodeOutputWorld')
mix_node = world_nodes.new(type='ShaderNodeMix')

# Connect nodes for dynamic lighting
scene.world.node_tree.links.new(env_node.outputs['Color'], mix_node.inputs['Color1'])
scene.world.node_tree.links.new(background_node.outputs['Background'], mix_node.inputs['Color2'])
scene.world.node_tree.links.new(mix_node.outputs['Color'], output_node.inputs['Surface'])

# Set enhanced environment strength
background_node.inputs['Strength'].default_value = 1.5
mix_node.inputs['Fac'].default_value = 0.7

# Camera settings - allow dynamic movement
camera = scene.camera
if camera:
    camera.data.lens = 35.0  # Slightly wider for cinematic feel
    camera.data.sensor_width = 36.0
    camera.data.clip_start = 0.1
    camera.data.clip_end = 1000.0
    
    # Enable depth of field for cinematic effect
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 10.0
    camera.data.dof.aperture_fstop = 2.8
    
    # Enable motion blur
    scene.render.motion_blur_shutter = 0.5

# Enhanced material settings
for material in bpy.data.materials:
    if material.use_nodes:
        material_nodes = material.node_tree.nodes
        principled = None
        
        # Find principled BSDF
        for node in material_nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        
        if principled:
            # Enhanced material properties
            principled.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1.0)  # Brighter base
            principled.inputs['Metallic'].default_value = 0.1  # Slight metallic
            principled.inputs['Roughness'].default_value = 0.3  # Smoother surfaces
            principled.inputs['Specular'].default_value = 0.7  # More specular
            principled.inputs['Emission Strength'].default_value = 0.1  # Subtle emission

# Enable cinematic effects
scene.render.use_motion_blur = True
scene.render.use_antialiasing = True
scene.render.filter_size = 2.0  # Higher quality anti-aliasing

# Enhanced color management
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium Contrast'
scene.view_settings.exposure = 0.2  # Slightly brighter
scene.view_settings.gamma = 1.1  # Slightly more contrast

# High quality output settings
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '16'  # Higher bit depth
scene.render.image_settings.compression = 0  # No compression for quality

# Add volumetric effects if available
scene.world.cycles_visibility.volume = True

print("Cinematic profile applied successfully")
'''
    
    def get_settings(self) -> Dict[str, Any]:
        """Get profile settings as dictionary."""
        return {
            "lighting": "dramatic",
            "materials": "enhanced",
            "camera_movement": True,
            "dramatic_effects": True,
            "motion_blur": True,
            "depth_of_field": True,
            "color_saturation": 1.2,
            "contrast": 1.1,
            "brightness": 1.1,
            "samples": 512,
            "denoising": True,
            "compression": 0,
            "color_depth": 16,
            "volumetric_effects": True
        }
