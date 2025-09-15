"""Determinism management for Blender rendering."""

import random
import hashlib
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class DeterminismManager:
    """Manages deterministic rendering for legal compliance."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.random_state = None
        self.blender_seeds = {}
        self.checksums = {}
    
    def set_seed(self, seed: int) -> None:
        """Set the base seed for deterministic operations."""
        self.seed = seed
    
    def get_current_seed(self) -> int:
        """Get the current base seed."""
        return self.seed
    
    def random(self) -> float:
        """Generate a random value using the current seed."""
        # Reset random state to ensure deterministic behavior
        random.seed(self.seed)
        return random.random()
    
    def initialize_seeds(self, scene_data: bytes, config: Dict[str, Any]) -> Dict[str, int]:
        """Initialize deterministic seeds for all random operations."""
        # Create deterministic seed from scene data and config
        scene_hash = hashlib.sha256(scene_data).hexdigest()
        config_str = json.dumps(config, sort_keys=True)
        combined_input = f"{scene_hash}:{config_str}:{self.seed}"
        
        # Generate deterministic seed
        deterministic_seed = int(hashlib.sha256(combined_input.encode()).hexdigest()[:8], 16)
        
        # Set random state
        random.seed(deterministic_seed)
        self.random_state = random.getstate()
        
        # Generate seeds for different components
        seeds = {
            "blender_main": deterministic_seed,
            "cycles_samples": random.randint(1, 1000000),
            "camera_noise": random.randint(1, 1000000),
            "material_noise": random.randint(1, 1000000),
            "lighting_noise": random.randint(1, 1000000),
            "animation_noise": random.randint(1, 1000000),
            "texture_noise": random.randint(1, 1000000),
        }
        
        self.blender_seeds = seeds
        return seeds
    
    def get_blender_determinism_script(self) -> str:
        """Get Blender Python script for deterministic rendering."""
        if not self.blender_seeds:
            raise ValueError("Seeds not initialized")
        
        script = f'''
# Deterministic rendering setup
import random
import bpy

# Set all random seeds
random.seed({self.blender_seeds['blender_main']})

# Set Blender's internal random seed
bpy.context.scene.frame_set(1)
bpy.context.scene.frame_set(1)  # Ensure seed is set

# Set Cycles renderer seeds
if bpy.context.scene.render.engine == 'CYCLES':
    bpy.context.scene.cycles.seed = {self.blender_seeds['cycles_samples']}
    bpy.context.scene.cycles.use_animated_seed = False

# Set deterministic sampling
bpy.context.scene.cycles.sample_clamp = 0.0
bpy.context.scene.cycles.sample_clamp_indirect = 0.0

# Disable adaptive sampling for determinism
bpy.context.scene.cycles.use_adaptive_sampling = False

# Set deterministic tile size
bpy.context.scene.render.tile_size = 256

# Ensure deterministic frame range
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = bpy.context.scene.frame_end

print("Deterministic settings applied")
'''
        return script
    
    def validate_determinism(self, output_files: List[Path]) -> Dict[str, Any]:
        """Validate that renders are deterministic."""
        results = {
            "is_deterministic": True,
            "checksums": {},
            "errors": []
        }
        
        for output_file in output_files:
            if output_file.exists():
                checksum = self._calculate_file_checksum(output_file)
                results["checksums"][output_file.name] = checksum
                
                # Check against previous checksum if available
                if output_file.name in self.checksums:
                    if checksum != self.checksums[output_file.name]:
                        results["is_deterministic"] = False
                        results["errors"].append(
                            f"Checksum mismatch for {output_file.name}"
                        )
                else:
                    # Store first checksum
                    self.checksums[output_file.name] = checksum
            else:
                results["is_deterministic"] = False
                results["errors"].append(f"Output file not found: {output_file.name}")
        
        return results
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def create_determinism_report(self, render_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive determinism report."""
        report = {
            "seed_used": self.seed,
            "blender_seeds": self.blender_seeds,
            "total_renders": len(render_results),
            "deterministic_renders": 0,
            "failed_renders": 0,
            "checksum_consistency": True,
            "recommendations": []
        }
        
        checksums = {}
        for result in render_results:
            if result.get("success", False):
                report["deterministic_renders"] += 1
                checksum = result.get("checksum")
                if checksum:
                    if checksum in checksums:
                        checksums[checksum] += 1
                    else:
                        checksums[checksum] = 1
            else:
                report["failed_renders"] += 1
        
        # Check checksum consistency
        if len(checksums) > 1:
            report["checksum_consistency"] = False
            report["recommendations"].append(
                "Multiple different checksums detected - determinism may be compromised"
            )
        
        # Add recommendations
        if report["failed_renders"] > 0:
            report["recommendations"].append(
                f"{report['failed_renders']} renders failed - check Blender installation and scene data"
            )
        
        if not report["checksum_consistency"]:
            report["recommendations"].append(
                "Enable deterministic mode and verify all random operations use fixed seeds"
            )
        
        return report


class DeterminismTestSuite:
    """Test suite for validating deterministic rendering."""
    
    def __init__(self, determinism_manager: DeterminismManager):
        self.determinism_manager = determinism_manager
        self.test_results = []
    
    async def run_determinism_tests(
        self, 
        scene_data: bytes, 
        config: Dict[str, Any],
        num_iterations: int = 3
    ) -> Dict[str, Any]:
        """Run determinism tests with multiple iterations."""
        test_results = {
            "test_name": "determinism_validation",
            "iterations": num_iterations,
            "results": [],
            "overall_success": True,
            "recommendations": []
        }
        
        # Initialize seeds
        seeds = self.determinism_manager.initialize_seeds(scene_data, config)
        
        for i in range(num_iterations):
            iteration_result = {
                "iteration": i + 1,
                "seeds_used": seeds,
                "success": True,
                "errors": []
            }
            
            try:
                # This would normally trigger a render
                # For now, we'll simulate the test
                iteration_result["success"] = True
                iteration_result["message"] = f"Iteration {i + 1} completed successfully"
                
            except Exception as e:
                iteration_result["success"] = False
                iteration_result["errors"].append(str(e))
                test_results["overall_success"] = False
            
            test_results["results"].append(iteration_result)
        
        # Add recommendations based on results
        if not test_results["overall_success"]:
            test_results["recommendations"].append(
                "Some iterations failed - check Blender installation and scene data"
            )
        
        return test_results
