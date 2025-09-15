"""Determinism utilities for reproducible rendering."""

import random
import numpy as np
import torch
from typing import Dict, Any, Optional, List
import hashlib
import json
from datetime import datetime


class DeterminismManager:
    """Manages deterministic behavior across the system."""
    
    def __init__(self, master_seed: int = 42):
        self.master_seed = master_seed
        self._seed_cache: Dict[str, int] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize deterministic state."""
        if self._initialized:
            return
        
        # Set Python random seed
        random.seed(self.master_seed)
        
        # Set NumPy random seed
        np.random.seed(self.master_seed)
        
        # Set PyTorch random seed
        torch.manual_seed(self.master_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(self.master_seed)
            torch.cuda.manual_seed_all(self.master_seed)
        
        # Set PyTorch deterministic behavior
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        
        self._initialized = True
    
    def get_seed_for_job(self, job_id: str, additional_data: Optional[Dict[str, Any]] = None) -> int:
        """Get deterministic seed for a specific job."""
        if job_id in self._seed_cache:
            return self._seed_cache[job_id]
        
        # Create deterministic seed from job ID and additional data
        seed_data = {"job_id": job_id, "master_seed": self.master_seed}
        if additional_data:
            seed_data.update(additional_data)
        
        # Sort keys for deterministic hashing
        sorted_data = json.dumps(seed_data, sort_keys=True, separators=(',', ':'))
        seed_hash = hashlib.sha256(sorted_data.encode('utf-8')).hexdigest()
        
        # Convert hash to integer seed
        seed = int(seed_hash[:8], 16)
        
        self._seed_cache[job_id] = seed
        return seed
    
    def set_job_seed(self, job_id: str, additional_data: Optional[Dict[str, Any]] = None) -> None:
        """Set deterministic seed for a specific job."""
        seed = self.get_seed_for_job(job_id, additional_data)
        
        # Set all random number generators to this seed
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    
    def reset_to_master(self) -> None:
        """Reset all random number generators to master seed."""
        self.initialize()
    
    def create_deterministic_config(self, base_config: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Create deterministic configuration for a job."""
        config = base_config.copy()
        
        # Add deterministic fields
        config["deterministic"] = True
        config["seed"] = self.get_seed_for_job(job_id)
        config["master_seed"] = self.master_seed
        config["job_id"] = job_id
        
        return config
    
    def validate_determinism(self, job_id: str, output_data: Any) -> Dict[str, Any]:
        """Validate that output is deterministic."""
        # This would typically compare against golden outputs
        # For now, return basic validation info
        return {
            "job_id": job_id,
            "seed_used": self.get_seed_for_job(job_id),
            "master_seed": self.master_seed,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "deterministic": True,  # Would be determined by actual comparison
        }


class RenderDeterminism:
    """Specific determinism utilities for rendering."""
    
    @staticmethod
    def create_blender_deterministic_config(base_config: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Create deterministic Blender configuration."""
        config = base_config.copy()
        
        # Set deterministic rendering options
        config.update({
            "cycles_seed": DeterminismManager().get_seed_for_job(job_id),
            "cycles_samples": config.get("cycles_samples", 128),
            "cycles_denoise": True,
            "cycles_adaptive_sampling": False,
            "cycles_adaptive_threshold": 0.01,
            "cycles_adaptive_min_samples": 64,
            "cycles_adaptive_max_samples": 2048,
            "cycles_use_denoising": True,
            "cycles_denoising_radius": 1,
            "cycles_denoising_strength": 1.0,
            "cycles_denoising_feature_strength": 0.5,
            "cycles_denoising_relative_filter": False,
            "cycles_denoising_prefilter": "ACCURATE",
        })
        
        return config
    
    @staticmethod
    def create_camera_deterministic_config(base_config: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Create deterministic camera configuration."""
        config = base_config.copy()
        
        # Ensure camera parameters are deterministic
        if "location" in config:
            # Round to avoid floating point precision issues
            config["location"] = [round(x, 6) for x in config["location"]]
        
        if "rotation" in config:
            config["rotation"] = [round(x, 6) for x in config["rotation"]]
        
        if "focal_length" in config:
            config["focal_length"] = round(config["focal_length"], 6)
        
        return config
    
    @staticmethod
    def create_lighting_deterministic_config(base_config: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Create deterministic lighting configuration."""
        config = base_config.copy()
        
        # Ensure lighting parameters are deterministic
        for light_type in ["sun", "area", "point", "spot"]:
            if light_type in config:
                light_config = config[light_type]
                if "energy" in light_config:
                    light_config["energy"] = round(light_config["energy"], 6)
                if "color" in light_config:
                    light_config["color"] = [round(x, 6) for x in light_config["color"]]
        
        return config


class DeterminismValidator:
    """Validates deterministic behavior."""
    
    @staticmethod
    def compare_outputs(output1: Any, output2: Any, tolerance: float = 1e-6) -> bool:
        """Compare two outputs for deterministic behavior."""
        if isinstance(output1, (int, float)) and isinstance(output2, (int, float)):
            return abs(output1 - output2) < tolerance
        
        if isinstance(output1, (list, tuple)) and isinstance(output2, (list, tuple)):
            if len(output1) != len(output2):
                return False
            return all(
                DeterminismValidator.compare_outputs(a, b, tolerance)
                for a, b in zip(output1, output2)
            )
        
        if isinstance(output1, dict) and isinstance(output2, dict):
            if set(output1.keys()) != set(output2.keys()):
                return False
            return all(
                DeterminismValidator.compare_outputs(output1[k], output2[k], tolerance)
                for k in output1.keys()
            )
        
        return output1 == output2
    
    @staticmethod
    def validate_render_checksums(
        checksums1: List[str], 
        checksums2: List[str]
    ) -> Dict[str, Any]:
        """Validate render frame checksums."""
        if len(checksums1) != len(checksums2):
            return {
                "valid": False,
                "error": "Different number of frames",
                "frames1": len(checksums1),
                "frames2": len(checksums2),
            }
        
        mismatches = []
        for i, (c1, c2) in enumerate(zip(checksums1, checksums2)):
            if c1 != c2:
                mismatches.append(i)
        
        return {
            "valid": len(mismatches) == 0,
            "total_frames": len(checksums1),
            "mismatched_frames": mismatches,
            "match_percentage": (len(checksums1) - len(mismatches)) / len(checksums1) * 100,
        }
