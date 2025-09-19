"""USD (Universal Scene Description) builder for legal simulation scenes."""

import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class USDStageType(Enum):
    """Types of USD stages."""
    OVER = "over"
    DEF = "def"
    CLASS = "class"
    INSTANCE = "instance"


class USDDataType(Enum):
    """USD data types."""
    FLOAT = "float"
    DOUBLE = "double"
    INT = "int"
    STRING = "string"
    BOOL = "bool"
    VECTOR3F = "vector3f"
    VECTOR3D = "vector3d"
    MATRIX4D = "matrix4d"
    QUATERNIONF = "quaternionf"
    QUATERNIOND = "quaterniond"


@dataclass
class USDAttribute:
    """USD attribute definition."""
    name: str
    data_type: USDDataType
    value: Any
    variability: str = "varying"  # varying, uniform, constant
    custom: bool = False


@dataclass
class USDObject:
    """USD object definition."""
    path: str
    object_type: str  # Xform, Mesh, Camera, Light, etc.
    attributes: List[USDAttribute]
    children: List['USDObject']
    stage_type: USDStageType = USDStageType.DEF


@dataclass
class USDStage:
    """USD stage definition."""
    name: str
    objects: List[USDObject]
    metadata: Dict[str, Any]


class USDBuilder:
    """Builder for USD scene files."""
    
    def __init__(self):
        self.stage = None
        self.current_path = ""
        self.indent_level = 0
    
    def create_stage(self, name: str) -> 'USDBuilder':
        """Create a new USD stage."""
        self.stage = USDStage(name=name, objects=[], metadata={})
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'USDBuilder':
        """Add metadata to the stage."""
        if self.stage:
            self.stage.metadata[key] = value
        return self
    
    def add_object(
        self, 
        path: str, 
        object_type: str, 
        attributes: Optional[List[USDAttribute]] = None,
        stage_type: USDStageType = USDStageType.DEF
    ) -> 'USDBuilder':
        """Add an object to the stage."""
        if not self.stage:
            raise ValueError("No stage created. Call create_stage() first.")
        
        obj = USDObject(
            path=path,
            object_type=object_type,
            attributes=attributes or [],
            children=[],
            stage_type=stage_type
        )
        
        self.stage.objects.append(obj)
        return self
    
    def add_attribute(
        self, 
        object_path: str, 
        name: str, 
        data_type: USDDataType, 
        value: Any,
        variability: str = "varying",
        custom: bool = False
    ) -> 'USDBuilder':
        """Add an attribute to an object."""
        if not self.stage:
            raise ValueError("No stage created. Call create_stage() first.")
        
        # Find the object
        obj = self._find_object(object_path)
        if not obj:
            raise ValueError(f"Object not found: {object_path}")
        
        attr = USDAttribute(
            name=name,
            data_type=data_type,
            value=value,
            variability=variability,
            custom=custom
        )
        
        obj.attributes.append(attr)
        return self
    
    def add_child_object(
        self,
        parent_path: str,
        child_path: str,
        object_type: str,
        attributes: Optional[List[USDAttribute]] = None
    ) -> 'USDBuilder':
        """Add a child object to a parent."""
        if not self.stage:
            raise ValueError("No stage created. Call create_stage() first.")
        
        # Find the parent object
        parent = self._find_object(parent_path)
        if not parent:
            raise ValueError(f"Parent object not found: {parent_path}")
        
        child = USDObject(
            path=child_path,
            object_type=object_type,
            attributes=attributes or [],
            children=[]
        )
        
        parent.children.append(child)
        return self
    
    def _find_object(self, path: str) -> Optional[USDObject]:
        """Find an object by path."""
        for obj in self.stage.objects:
            if obj.path == path:
                return obj
            # Check children recursively
            found = self._find_object_in_children(obj, path)
            if found:
                return found
        return None
    
    def _find_object_in_children(self, parent: USDObject, path: str) -> Optional[USDObject]:
        """Find an object in children recursively."""
        for child in parent.children:
            if child.path == path:
                return child
            found = self._find_object_in_children(child, path)
            if found:
                return found
        return None
    
    def build(self) -> str:
        """Build the USD file content."""
        if not self.stage:
            raise ValueError("No stage created. Call create_stage() first.")
        
        lines = []
        
        # Add header
        lines.append("#usda 1.0")
        lines.append("")
        
        # Add metadata
        if self.stage.metadata:
            lines.append("def Scope \"Metadata\"")
            lines.append("{")
            for key, value in self.stage.metadata.items():
                lines.append(f"    string {key} = \"{value}\"")
            lines.append("}")
            lines.append("")
        
        # Add objects
        for obj in self.stage.objects:
            self._build_object(obj, lines, 0)
        
        return "\n".join(lines)
    
    def _build_object(self, obj: USDObject, lines: List[str], indent: int):
        """Build an object and its children."""
        indent_str = "    " * indent
        
        # Object declaration
        stage_type_str = obj.stage_type.value if obj.stage_type != USDStageType.DEF else "def"
        lines.append(f"{indent_str}{stage_type_str} {obj.object_type} \"{obj.path}\"")
        lines.append(f"{indent_str}{{")
        
        # Add attributes
        for attr in obj.attributes:
            self._build_attribute(attr, lines, indent + 1)
        
        # Add children
        for child in obj.children:
            self._build_object(child, lines, indent + 1)
        
        lines.append(f"{indent_str}}}")
    
    def _build_attribute(self, attr: USDAttribute, lines: List[str], indent: int):
        """Build an attribute."""
        indent_str = "    " * indent
        
        # Format value based on data type
        value_str = self._format_value(attr.value, attr.data_type)
        
        # Build attribute line
        custom_str = " custom " if attr.custom else " "
        variability_str = f" {attr.variability}" if attr.variability != "varying" else ""
        
        lines.append(f"{indent_str}{custom_str}{attr.data_type.value}{variability_str} {attr.name} = {value_str}")
    
    def _format_value(self, value: Any, data_type: USDDataType) -> str:
        """Format value for USD output."""
        if data_type == USDDataType.STRING:
            return f'"{value}"'
        elif data_type == USDDataType.BOOL:
            return "true" if value else "false"
        elif data_type in [USDDataType.VECTOR3F, USDDataType.VECTOR3D]:
            if isinstance(value, (list, tuple)) and len(value) == 3:
                return f"({value[0]}, {value[1]}, {value[2]})"
            else:
                return f"({value}, {value}, {value})"
        elif data_type in [USDDataType.QUATERNIONF, USDDataType.QUATERNIOND]:
            if isinstance(value, (list, tuple)) and len(value) == 4:
                return f"({value[0]}, {value[1]}, {value[2]}, {value[3]})"
            else:
                return "(0, 0, 0, 1)"  # Default quaternion
        elif data_type == USDDataType.MATRIX4D:
            if isinstance(value, (list, tuple)) and len(value) == 16:
                return f"({', '.join(map(str, value))})"
            else:
                return "(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)"  # Identity matrix
        else:
            return str(value)
    
    def save_to_file(self, filepath: str) -> None:
        """Save the USD stage to a file."""
        content = self.build()
        with open(filepath, 'w') as f:
            f.write(content)
    
    def create_camera(
        self, 
        name: str, 
        position: Tuple[float, float, float] = (0, 0, 5),
        rotation: Tuple[float, float, float] = (0, 0, 0),
        fov: float = 50.0
    ) -> 'USDBuilder':
        """Create a camera object."""
        attributes = [
            USDAttribute("xformOp:translate", USDDataType.VECTOR3F, position),
            USDAttribute("xformOp:rotateXYZ", USDDataType.VECTOR3F, rotation),
            USDAttribute("focalLength", USDDataType.FLOAT, 35.0),
            USDAttribute("horizontalAperture", USDDataType.FLOAT, 20.955),
            USDAttribute("verticalAperture", USDDataType.FLOAT, 15.955),
            USDAttribute("clippingRange", USDDataType.VECTOR2F, (0.1, 1000.0)),
        ]
        
        return self.add_object(f"/World/Camera_{name}", "Camera", attributes)
    
    def create_light(
        self, 
        name: str, 
        light_type: str = "DistantLight",
        position: Tuple[float, float, float] = (0, 10, 0),
        intensity: float = 1.0,
        color: Tuple[float, float, float] = (1, 1, 1)
    ) -> 'USDBuilder':
        """Create a light object."""
        attributes = [
            USDAttribute("xformOp:translate", USDDataType.VECTOR3F, position),
            USDAttribute("intensity", USDDataType.FLOAT, intensity),
            USDAttribute("color", USDDataType.VECTOR3F, color),
        ]
        
        return self.add_object(f"/World/Light_{name}", light_type, attributes)
    
    def create_mesh(
        self, 
        name: str, 
        position: Tuple[float, float, float] = (0, 0, 0),
        scale: Tuple[float, float, float] = (1, 1, 1),
        material: Optional[str] = None
    ) -> 'USDBuilder':
        """Create a mesh object."""
        attributes = [
            USDAttribute("xformOp:translate", USDDataType.VECTOR3F, position),
            USDAttribute("xformOp:scale", USDDataType.VECTOR3F, scale),
        ]
        
        if material:
            attributes.append(
                USDAttribute("material:binding", USDDataType.STRING, material)
            )
        
        return self.add_object(f"/World/Mesh_{name}", "Mesh", attributes)


def create_usd_builder() -> USDBuilder:
    """Create a new USD builder instance."""
    return USDBuilder()


# Example usage
if __name__ == "__main__":
    # Create a simple scene
    builder = create_usd_builder()
    
    builder.create_stage("LegalSimulation")
    builder.add_metadata("upAxis", "Y")
    builder.add_metadata("metersPerUnit", 1)
    
    # Add a camera
    builder.create_camera("Main", position=(0, 0, 5), fov=50)
    
    # Add a light
    builder.create_light("Main", "DistantLight", position=(0, 10, 0), intensity=1.5)
    
    # Add a simple mesh
    builder.create_mesh("Evidence", position=(0, 0, 0), scale=(1, 1, 1))
    
    # Build and save
    usd_content = builder.build()
    print("Generated USD content:")
    print(usd_content)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.usd', delete=False) as f:
        f.write(usd_content)
        print(f"\nSaved to: {f.name}")
