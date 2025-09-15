"""Neutral render profile for court-appropriate settings."""

from typing import Dict, Any


class NeutralProfile:
    """Neutral render profile for court-admissible content."""
    
    def __init__(self):
        self.name = "neutral"
        self.description = "Court-appropriate render settings with neutral lighting and materials"
    
    def get_blender_script(self) -> str:
        """Get Blender Python script for neutral profile."""
        return '''
# Neutral Profile Settings
scene = bpy.context.scene

# Render engine settings
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128  # Moderate quality
scene.cycles.use_denoising = True

# Lighting - flat, neutral lighting
scene.world.use_nodes = True
world_nodes = scene.world.node_tree.nodes
world_nodes.clear()

# Add environment texture
env_node = world_nodes.new(type='ShaderNodeTexEnvironment')
background_node = world_nodes.new(type='ShaderNodeBackground')
output_node = world_nodes.new(type='ShaderNodeOutputWorld')

# Connect nodes
scene.world.node_tree.links.new(env_node.outputs['Color'], background_node.inputs['Color'])
scene.world.node_tree.links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

# Set neutral environment strength
background_node.inputs['Strength'].default_value = 1.0

# Camera settings - fixed, neutral angles
camera = scene.camera
if camera:
    camera.data.lens = 50.0  # Standard lens
    camera.data.sensor_width = 36.0  # Full frame
    camera.data.clip_start = 0.1
    camera.data.clip_end = 1000.0
    
    # Disable depth of field
    camera.data.dof.use_dof = False
    
    # Disable motion blur
    scene.render.motion_blur_shutter = 0.0

# Material settings - neutral colors
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
            # Set neutral material properties
            principled.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)  # Light gray
            principled.inputs['Metallic'].default_value = 0.0
            principled.inputs['Roughness'].default_value = 0.5
            principled.inputs['Specular'].default_value = 0.5

# Disable all effects that could be dramatic
scene.render.use_motion_blur = False
scene.render.use_antialiasing = True
scene.render.filter_size = 1.5  # Moderate anti-aliasing

# Color management - neutral
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0

# Output settings
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 15  # Moderate compression

print("Neutral profile applied successfully")
'''
    
    def get_settings(self) -> Dict[str, Any]:
        """Get profile settings as dictionary."""
        return {
            "lighting": "flat",
            "materials": "neutral",
            "camera_movement": False,
            "dramatic_effects": False,
            "motion_blur": False,
            "depth_of_field": False,
            "color_saturation": 1.0,
            "contrast": 1.0,
            "brightness": 1.0,
            "samples": 128,
            "denoising": True,
            "compression": 15
        }
