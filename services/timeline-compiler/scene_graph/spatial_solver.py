"""Spatial solver for legal simulation scene layout and positioning."""

import math
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class SpatialConstraintType(Enum):
    """Types of spatial constraints."""
    POSITION = "position"
    DISTANCE = "distance"
    ANGLE = "angle"
    ALIGNMENT = "alignment"
    BOUNDARY = "boundary"
    COLLISION = "collision"


class SpatialObjectType(Enum):
    """Types of spatial objects."""
    CAMERA = "camera"
    LIGHT = "light"
    MESH = "mesh"
    EVIDENCE = "evidence"
    TEXT = "text"
    ANNOTATION = "annotation"


@dataclass
class SpatialObject:
    """Spatial object in the scene."""
    id: str
    object_type: SpatialObjectType
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float] = (0, 0, 0)
    scale: Tuple[float, float, float] = (1, 1, 1)
    bounds: Optional[Tuple[float, float, float, float, float, float]] = None  # min_x, min_y, min_z, max_x, max_y, max_z
    properties: Dict[str, Any] = None


@dataclass
class SpatialConstraint:
    """Spatial constraint between objects."""
    id: str
    constraint_type: SpatialConstraintType
    objects: List[str]  # Object IDs involved in constraint
    target_value: Any  # Target value for the constraint
    weight: float = 1.0  # Constraint weight for optimization
    enabled: bool = True


@dataclass
class SpatialSolution:
    """Solution to spatial constraints."""
    objects: Dict[str, SpatialObject]
    constraints_satisfied: List[str]
    constraints_violated: List[str]
    total_error: float
    iterations: int


class SpatialSolver:
    """Solver for spatial constraints in legal simulation scenes."""
    
    def __init__(self):
        self.objects: Dict[str, SpatialObject] = {}
        self.constraints: Dict[str, SpatialConstraint] = {}
        self.max_iterations = 100
        self.convergence_threshold = 1e-6
        self.damping_factor = 0.1
    
    def add_object(self, obj: SpatialObject) -> None:
        """Add a spatial object to the scene."""
        self.objects[obj.id] = obj
    
    def add_constraint(self, constraint: SpatialConstraint) -> None:
        """Add a spatial constraint."""
        self.constraints[constraint.id] = constraint
    
    def remove_object(self, obj_id: str) -> None:
        """Remove an object and its constraints."""
        if obj_id in self.objects:
            del self.objects[obj_id]
        
        # Remove constraints involving this object
        constraints_to_remove = []
        for constraint_id, constraint in self.constraints.items():
            if obj_id in constraint.objects:
                constraints_to_remove.append(constraint_id)
        
        for constraint_id in constraints_to_remove:
            del self.constraints[constraint_id]
    
    def solve(self) -> SpatialSolution:
        """Solve spatial constraints using iterative optimization."""
        if not self.objects or not self.constraints:
            return SpatialSolution(
                objects=self.objects.copy(),
                constraints_satisfied=[],
                constraints_violated=[],
                total_error=0.0,
                iterations=0
            )
        
        # Initialize solution
        solution_objects = {obj_id: SpatialObject(
            id=obj.id,
            object_type=obj.object_type,
            position=obj.position,
            rotation=obj.rotation,
            scale=obj.scale,
            bounds=obj.bounds,
            properties=obj.properties.copy() if obj.properties else {}
        ) for obj_id, obj in self.objects.items()}
        
        # Iterative optimization
        iteration = 0
        total_error = float('inf')
        
        while iteration < self.max_iterations and total_error > self.convergence_threshold:
            total_error = 0.0
            
            # Apply constraints
            for constraint_id, constraint in self.constraints.items():
                if not constraint.enabled:
                    continue
                
                error = self._apply_constraint(constraint, solution_objects)
                total_error += error * constraint.weight
            
            iteration += 1
        
        # Evaluate final solution
        satisfied_constraints = []
        violated_constraints = []
        
        for constraint_id, constraint in self.constraints.items():
            if constraint.enabled:
                error = self._evaluate_constraint(constraint, solution_objects)
                if error < self.convergence_threshold:
                    satisfied_constraints.append(constraint_id)
                else:
                    violated_constraints.append(constraint_id)
        
        return SpatialSolution(
            objects=solution_objects,
            constraints_satisfied=satisfied_constraints,
            constraints_violated=violated_constraints,
            total_error=total_error,
            iterations=iteration
        )
    
    def _apply_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Apply a single constraint and return the error."""
        if constraint.constraint_type == SpatialConstraintType.POSITION:
            return self._apply_position_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.DISTANCE:
            return self._apply_distance_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.ANGLE:
            return self._apply_angle_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.ALIGNMENT:
            return self._apply_alignment_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.BOUNDARY:
            return self._apply_boundary_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.COLLISION:
            return self._apply_collision_constraint(constraint, objects)
        else:
            return 0.0
    
    def _apply_position_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Apply position constraint."""
        if len(constraint.objects) != 1:
            return 0.0
        
        obj_id = constraint.objects[0]
        if obj_id not in objects:
            return 0.0
        
        target_pos = constraint.target_value
        obj = objects[obj_id]
        
        # Calculate error
        error = math.sqrt(
            (obj.position[0] - target_pos[0])**2 +
            (obj.position[1] - target_pos[1])**2 +
            (obj.position[2] - target_pos[2])**2
        )
        
        # Apply correction
        correction = [
            (target_pos[0] - obj.position[0]) * self.damping_factor,
            (target_pos[1] - obj.position[1]) * self.damping_factor,
            (target_pos[2] - obj.position[2]) * self.damping_factor
        ]
        
        obj.position = (
            obj.position[0] + correction[0],
            obj.position[1] + correction[1],
            obj.position[2] + correction[2]
        )
        
        return error
    
    def _apply_distance_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Apply distance constraint between two objects."""
        if len(constraint.objects) != 2:
            return 0.0
        
        obj1_id, obj2_id = constraint.objects
        if obj1_id not in objects or obj2_id not in objects:
            return 0.0
        
        obj1 = objects[obj1_id]
        obj2 = objects[obj2_id]
        target_distance = constraint.target_value
        
        # Calculate current distance
        current_distance = math.sqrt(
            (obj1.position[0] - obj2.position[0])**2 +
            (obj1.position[1] - obj2.position[1])**2 +
            (obj1.position[2] - obj2.position[2])**2
        )
        
        error = abs(current_distance - target_distance)
        
        if current_distance > 0:
            # Calculate direction vector
            direction = [
                (obj2.position[0] - obj1.position[0]) / current_distance,
                (obj2.position[1] - obj1.position[1]) / current_distance,
                (obj2.position[2] - obj1.position[2]) / current_distance
            ]
            
            # Apply correction
            correction = (current_distance - target_distance) * self.damping_factor
            
            # Move objects apart or together
            obj1.position = (
                obj1.position[0] - direction[0] * correction * 0.5,
                obj1.position[1] - direction[1] * correction * 0.5,
                obj1.position[2] - direction[2] * correction * 0.5
            )
            
            obj2.position = (
                obj2.position[0] + direction[0] * correction * 0.5,
                obj2.position[1] + direction[1] * correction * 0.5,
                obj2.position[2] + direction[2] * correction * 0.5
            )
        
        return error
    
    def _apply_angle_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Apply angle constraint between three objects."""
        if len(constraint.objects) != 3:
            return 0.0
        
        obj1_id, obj2_id, obj3_id = constraint.objects
        if any(obj_id not in objects for obj_id in [obj1_id, obj2_id, obj3_id]):
            return 0.0
        
        obj1 = objects[obj1_id]
        obj2 = objects[obj2_id]
        obj3 = objects[obj3_id]
        target_angle = constraint.target_value
        
        # Calculate vectors
        v1 = [
            obj1.position[0] - obj2.position[0],
            obj1.position[1] - obj2.position[1],
            obj1.position[2] - obj2.position[2]
        ]
        v2 = [
            obj3.position[0] - obj2.position[0],
            obj3.position[1] - obj2.position[1],
            obj3.position[2] - obj2.position[2]
        ]
        
        # Calculate current angle
        dot_product = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
        v1_length = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
        v2_length = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)
        
        if v1_length > 0 and v2_length > 0:
            current_angle = math.acos(max(-1, min(1, dot_product / (v1_length * v2_length))))
            error = abs(current_angle - target_angle)
        else:
            error = target_angle
        
        return error
    
    def _apply_alignment_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Apply alignment constraint."""
        if len(constraint.objects) < 2:
            return 0.0
        
        alignment_axis = constraint.target_value  # 'x', 'y', 'z', or 'xy', 'xz', 'yz'
        objects_to_align = [objects[obj_id] for obj_id in constraint.objects if obj_id in objects]
        
        if len(objects_to_align) < 2:
            return 0.0
        
        # Calculate average position for alignment axis
        avg_positions = [0, 0, 0]
        for obj in objects_to_align:
            avg_positions[0] += obj.position[0]
            avg_positions[1] += obj.position[1]
            avg_positions[2] += obj.position[2]
        
        avg_positions = [pos / len(objects_to_align) for pos in avg_positions]
        
        # Apply alignment
        error = 0.0
        for obj in objects_to_align:
            new_position = list(obj.position)
            
            if 'x' in alignment_axis:
                error += abs(obj.position[0] - avg_positions[0])
                new_position[0] = avg_positions[0]
            
            if 'y' in alignment_axis:
                error += abs(obj.position[1] - avg_positions[1])
                new_position[1] = avg_positions[1]
            
            if 'z' in alignment_axis:
                error += abs(obj.position[2] - avg_positions[2])
                new_position[2] = avg_positions[2]
            
            obj.position = tuple(new_position)
        
        return error
    
    def _apply_boundary_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Apply boundary constraint."""
        if len(constraint.objects) != 1:
            return 0.0
        
        obj_id = constraint.objects[0]
        if obj_id not in objects:
            return 0.0
        
        obj = objects[obj_id]
        boundary = constraint.target_value  # (min_x, min_y, min_z, max_x, max_y, max_z)
        
        error = 0.0
        new_position = list(obj.position)
        
        # Check and correct X boundary
        if obj.position[0] < boundary[0]:
            error += boundary[0] - obj.position[0]
            new_position[0] = boundary[0]
        elif obj.position[0] > boundary[3]:
            error += obj.position[0] - boundary[3]
            new_position[0] = boundary[3]
        
        # Check and correct Y boundary
        if obj.position[1] < boundary[1]:
            error += boundary[1] - obj.position[1]
            new_position[1] = boundary[1]
        elif obj.position[1] > boundary[4]:
            error += obj.position[1] - boundary[4]
            new_position[1] = boundary[4]
        
        # Check and correct Z boundary
        if obj.position[2] < boundary[2]:
            error += boundary[2] - obj.position[2]
            new_position[2] = boundary[2]
        elif obj.position[2] > boundary[5]:
            error += obj.position[2] - boundary[5]
            new_position[2] = boundary[5]
        
        obj.position = tuple(new_position)
        return error
    
    def _apply_collision_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Apply collision avoidance constraint."""
        if len(constraint.objects) != 2:
            return 0.0
        
        obj1_id, obj2_id = constraint.objects
        if obj1_id not in objects or obj2_id not in objects:
            return 0.0
        
        obj1 = objects[obj1_id]
        obj2 = objects[obj2_id]
        min_distance = constraint.target_value
        
        # Calculate current distance
        current_distance = math.sqrt(
            (obj1.position[0] - obj2.position[0])**2 +
            (obj1.position[1] - obj2.position[1])**2 +
            (obj1.position[2] - obj2.position[2])**2
        )
        
        if current_distance < min_distance:
            # Objects are too close, push them apart
            if current_distance > 0:
                direction = [
                    (obj2.position[0] - obj1.position[0]) / current_distance,
                    (obj2.position[1] - obj1.position[1]) / current_distance,
                    (obj2.position[2] - obj1.position[2]) / current_distance
                ]
                
                separation = (min_distance - current_distance) * self.damping_factor
                
                # Move objects apart
                obj1.position = (
                    obj1.position[0] - direction[0] * separation * 0.5,
                    obj1.position[1] - direction[1] * separation * 0.5,
                    obj1.position[2] - direction[2] * separation * 0.5
                )
                
                obj2.position = (
                    obj2.position[0] + direction[0] * separation * 0.5,
                    obj2.position[1] + direction[1] * separation * 0.5,
                    obj2.position[2] + direction[2] * separation * 0.5
                )
            
            return min_distance - current_distance
        
        return 0.0
    
    def _evaluate_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Evaluate constraint error without applying corrections."""
        if constraint.constraint_type == SpatialConstraintType.POSITION:
            return self._evaluate_position_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.DISTANCE:
            return self._evaluate_distance_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.ANGLE:
            return self._evaluate_angle_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.ALIGNMENT:
            return self._evaluate_alignment_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.BOUNDARY:
            return self._evaluate_boundary_constraint(constraint, objects)
        elif constraint.constraint_type == SpatialConstraintType.COLLISION:
            return self._evaluate_collision_constraint(constraint, objects)
        else:
            return 0.0
    
    def _evaluate_position_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Evaluate position constraint error."""
        if len(constraint.objects) != 1:
            return 0.0
        
        obj_id = constraint.objects[0]
        if obj_id not in objects:
            return 0.0
        
        obj = objects[obj_id]
        target_pos = constraint.target_value
        
        return math.sqrt(
            (obj.position[0] - target_pos[0])**2 +
            (obj.position[1] - target_pos[1])**2 +
            (obj.position[2] - target_pos[2])**2
        )
    
    def _evaluate_distance_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Evaluate distance constraint error."""
        if len(constraint.objects) != 2:
            return 0.0
        
        obj1_id, obj2_id = constraint.objects
        if obj1_id not in objects or obj2_id not in objects:
            return 0.0
        
        obj1 = objects[obj1_id]
        obj2 = objects[obj2_id]
        target_distance = constraint.target_value
        
        current_distance = math.sqrt(
            (obj1.position[0] - obj2.position[0])**2 +
            (obj1.position[1] - obj2.position[1])**2 +
            (obj1.position[2] - obj2.position[2])**2
        )
        
        return abs(current_distance - target_distance)
    
    def _evaluate_angle_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Evaluate angle constraint error."""
        if len(constraint.objects) != 3:
            return 0.0
        
        obj1_id, obj2_id, obj3_id = constraint.objects
        if any(obj_id not in objects for obj_id in [obj1_id, obj2_id, obj3_id]):
            return 0.0
        
        obj1 = objects[obj1_id]
        obj2 = objects[obj2_id]
        obj3 = objects[obj3_id]
        target_angle = constraint.target_value
        
        # Calculate vectors
        v1 = [
            obj1.position[0] - obj2.position[0],
            obj1.position[1] - obj2.position[1],
            obj1.position[2] - obj2.position[2]
        ]
        v2 = [
            obj3.position[0] - obj2.position[0],
            obj3.position[1] - obj2.position[1],
            obj3.position[2] - obj2.position[2]
        ]
        
        # Calculate current angle
        dot_product = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
        v1_length = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
        v2_length = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)
        
        if v1_length > 0 and v2_length > 0:
            current_angle = math.acos(max(-1, min(1, dot_product / (v1_length * v2_length))))
            return abs(current_angle - target_angle)
        else:
            return target_angle
    
    def _evaluate_alignment_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Evaluate alignment constraint error."""
        if len(constraint.objects) < 2:
            return 0.0
        
        alignment_axis = constraint.target_value
        objects_to_align = [objects[obj_id] for obj_id in constraint.objects if obj_id in objects]
        
        if len(objects_to_align) < 2:
            return 0.0
        
        # Calculate average position for alignment axis
        avg_positions = [0, 0, 0]
        for obj in objects_to_align:
            avg_positions[0] += obj.position[0]
            avg_positions[1] += obj.position[1]
            avg_positions[2] += obj.position[2]
        
        avg_positions = [pos / len(objects_to_align) for pos in avg_positions]
        
        # Calculate error
        error = 0.0
        for obj in objects_to_align:
            if 'x' in alignment_axis:
                error += abs(obj.position[0] - avg_positions[0])
            if 'y' in alignment_axis:
                error += abs(obj.position[1] - avg_positions[1])
            if 'z' in alignment_axis:
                error += abs(obj.position[2] - avg_positions[2])
        
        return error
    
    def _evaluate_boundary_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Evaluate boundary constraint error."""
        if len(constraint.objects) != 1:
            return 0.0
        
        obj_id = constraint.objects[0]
        if obj_id not in objects:
            return 0.0
        
        obj = objects[obj_id]
        boundary = constraint.target_value  # (min_x, min_y, min_z, max_x, max_y, max_z)
        
        error = 0.0
        
        # Check X boundary
        if obj.position[0] < boundary[0]:
            error += boundary[0] - obj.position[0]
        elif obj.position[0] > boundary[3]:
            error += obj.position[0] - boundary[3]
        
        # Check Y boundary
        if obj.position[1] < boundary[1]:
            error += boundary[1] - obj.position[1]
        elif obj.position[1] > boundary[4]:
            error += obj.position[1] - boundary[4]
        
        # Check Z boundary
        if obj.position[2] < boundary[2]:
            error += boundary[2] - obj.position[2]
        elif obj.position[2] > boundary[5]:
            error += obj.position[2] - boundary[5]
        
        return error
    
    def _evaluate_collision_constraint(self, constraint: SpatialConstraint, objects: Dict[str, SpatialObject]) -> float:
        """Evaluate collision constraint error."""
        if len(constraint.objects) != 2:
            return 0.0
        
        obj1_id, obj2_id = constraint.objects
        if obj1_id not in objects or obj2_id not in objects:
            return 0.0
        
        obj1 = objects[obj1_id]
        obj2 = objects[obj2_id]
        min_distance = constraint.target_value
        
        current_distance = math.sqrt(
            (obj1.position[0] - obj2.position[0])**2 +
            (obj1.position[1] - obj2.position[1])**2 +
            (obj1.position[2] - obj2.position[2])**2
        )
        
        if current_distance < min_distance:
            return min_distance - current_distance
        
        return 0.0


def create_spatial_solver() -> SpatialSolver:
    """Create a new spatial solver instance."""
    return SpatialSolver()


# Example usage
if __name__ == "__main__":
    # Create a spatial solver
    solver = create_spatial_solver()
    
    # Add some objects
    camera = SpatialObject(
        id="camera_1",
        object_type=SpatialObjectType.CAMERA,
        position=(0, 0, 5)
    )
    
    evidence = SpatialObject(
        id="evidence_1",
        object_type=SpatialObjectType.EVIDENCE,
        position=(0, 0, 0)
    )
    
    light = SpatialObject(
        id="light_1",
        object_type=SpatialObjectType.LIGHT,
        position=(2, 2, 2)
    )
    
    solver.add_object(camera)
    solver.add_object(evidence)
    solver.add_object(light)
    
    # Add constraints
    distance_constraint = SpatialConstraint(
        id="camera_evidence_distance",
        constraint_type=SpatialConstraintType.DISTANCE,
        objects=["camera_1", "evidence_1"],
        target_value=5.0
    )
    
    collision_constraint = SpatialConstraint(
        id="evidence_light_collision",
        constraint_type=SpatialConstraintType.COLLISION,
        objects=["evidence_1", "light_1"],
        target_value=1.0
    )
    
    solver.add_constraint(distance_constraint)
    solver.add_constraint(collision_constraint)
    
    # Solve constraints
    solution = solver.solve()
    
    print(f"Solution found in {solution.iterations} iterations")
    print(f"Total error: {solution.total_error:.6f}")
    print(f"Satisfied constraints: {len(solution.constraints_satisfied)}")
    print(f"Violated constraints: {len(solution.constraints_violated)}")
    
    # Print final positions
    for obj_id, obj in solution.objects.items():
        print(f"{obj_id}: position {obj.position}")
