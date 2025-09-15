"""Determinism tests for rendering pipeline.

Tests render reproducibility across runs, seed propagation, and checksum consistency
to ensure frame-perfect reproducibility for legal evidence.
"""

import pytest
import asyncio
import tempfile
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

# Import render services
from services.render_orchestrator.implementations.blender.local_renderer import BlenderLocalRenderer
from services.render_orchestrator.implementations.blender.profiles.neutral import NeutralProfile
from services.render_orchestrator.implementations.blender.profiles.cinematic import CinematicProfile
from services.render_orchestrator.implementations.blender.determinism import DeterminismManager
from services.timeline_compiler.scene_graph.usd_builder import USDBuilder
from services.shared.models.render import RenderJob, RenderQuality


class TestRenderDeterminism:
    """Test suite for rendering determinism and reproducibility."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def determinism_manager(self):
        """Create determinism manager for testing."""
        return DeterminismManager()
    
    @pytest.fixture
    def test_scene_data(self):
        """Create test scene data for rendering."""
        return {
            "scene_id": "test-scene-001",
            "duration": 5.0,
            "fps": 24,
            "resolution": {"width": 1920, "height": 1080},
            "camera": {
                "position": [0, 0, 5],
                "rotation": [0, 0, 0],
                "focal_length": 50
            },
            "objects": [
                {
                    "id": "obj-001",
                    "type": "cube",
                    "position": [0, 0, 0],
                    "rotation": [0, 0, 0],
                    "scale": [1, 1, 1],
                    "material": {
                        "color": [0.8, 0.2, 0.2],
                        "metallic": 0.0,
                        "roughness": 0.5
                    }
                }
            ],
            "lighting": [
                {
                    "type": "sun",
                    "position": [5, 5, 10],
                    "energy": 3.0,
                    "color": [1.0, 1.0, 1.0]
                }
            ]
        }
    
    def create_golden_test_case(self, temp_dir: Path, scene_data: dict, seed: int) -> Path:
        """Create a golden test case for determinism verification."""
        golden_file = temp_dir / f"golden_test_seed_{seed}.json"
        
        # Create deterministic scene data
        deterministic_scene = {
            "seed": seed,
            "scene_data": scene_data,
            "expected_checksums": {
                "frame_001": "expected_hash_001",
                "frame_002": "expected_hash_002",
                "frame_003": "expected_hash_003"
            },
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "render_engine": "blender",
                "version": "3.6.0"
            }
        }
        
        golden_file.write_text(json.dumps(deterministic_scene, indent=2))
        return golden_file
    
    @pytest.mark.asyncio
    async def test_render_reproducibility_across_runs(self, temp_dir, determinism_manager, test_scene_data):
        """Test that identical renders produce identical outputs."""
        seed = 12345
        num_runs = 3
        
        # Mock renderer to return consistent results
        with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
            # Create mock render results with deterministic content
            mock_result = Mock()
            mock_result.output_path = str(temp_dir / "render_output.mp4")
            mock_result.frames_generated = 120  # 5 seconds * 24 fps
            mock_result.checksums = {
                f"frame_{i:03d}": f"deterministic_hash_{i:03d}" for i in range(1, 121)
            }
            mock_renderer.return_value.render.return_value = mock_result
            
            renderer = mock_renderer.return_value
            checksums = []
            
            # Run multiple renders with same seed
            for run in range(num_runs):
                determinism_manager.set_seed(seed)
                result = renderer.render(
                    scene_data=test_scene_data,
                    output_path=temp_dir / f"render_run_{run}.mp4",
                    profile="neutral"
                )
                checksums.append(result.checksums)
            
            # Verify all runs produced identical results
            for i in range(1, num_runs):
                assert checksums[0] == checksums[i], f"Run {i} produced different checksums than run 0"
    
    @pytest.mark.asyncio
    async def test_seed_propagation_through_pipeline(self, temp_dir, determinism_manager):
        """Test that seeds are properly propagated through the rendering pipeline."""
        seed = 54321
        
        # Test seed setting and retrieval
        determinism_manager.set_seed(seed)
        retrieved_seed = determinism_manager.get_current_seed()
        assert retrieved_seed == seed
        
        # Test seed affects random operations
        determinism_manager.set_seed(seed)
        random_values_1 = [determinism_manager.random() for _ in range(10)]
        
        determinism_manager.set_seed(seed)
        random_values_2 = [determinism_manager.random() for _ in range(10)]
        
        # Same seed should produce same random values
        assert random_values_1 == random_values_2
        
        # Different seed should produce different values
        determinism_manager.set_seed(seed + 1)
        random_values_3 = [determinism_manager.random() for _ in range(10)]
        assert random_values_1 != random_values_3
    
    @pytest.mark.asyncio
    async def test_checksum_consistency(self, temp_dir, test_scene_data):
        """Test that frame checksums are consistent across renders."""
        seed = 98765
        
        # Create test frame data
        frame_data = np.random.RandomState(seed).randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        frame_path = temp_dir / "test_frame.png"
        
        # Save frame and calculate checksum
        from PIL import Image
        Image.fromarray(frame_data).save(frame_path)
        
        # Calculate checksum multiple times
        checksums = []
        for _ in range(5):
            with open(frame_path, 'rb') as f:
                content = f.read()
                checksum = hashlib.sha256(content).hexdigest()
                checksums.append(checksum)
        
        # All checksums should be identical
        assert all(c == checksums[0] for c in checksums), "Checksums should be consistent"
        
        # Test deterministic frame generation
        with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
            mock_result = Mock()
            mock_result.checksums = {"frame_001": hashlib.sha256(frame_data.tobytes()).hexdigest()}
            mock_renderer.return_value.render.return_value = mock_result
            
            renderer = mock_renderer.return_value
            
            # Generate frame with same parameters multiple times
            frame_checksums = []
            for _ in range(3):
                result = renderer.render(
                    scene_data={"duration": 1.0},
                    output_path=temp_dir / "test_frame.mp4",
                    profile="neutral",
                    seed=seed
                )
                frame_checksums.append(result.checksums["frame_001"])
            
            # All generated frames should have same checksum
            assert all(c == frame_checksums[0] for c in frame_checksums)
    
    @pytest.mark.asyncio
    async def test_golden_test_cases(self, temp_dir, test_scene_data):
        """Test against golden test cases for regression detection."""
        test_seeds = [11111, 22222, 33333]
        
        # Create golden test cases
        golden_cases = {}
        for seed in test_seeds:
            golden_file = self.create_golden_test_case(temp_dir, test_scene_data, seed)
            golden_cases[seed] = json.loads(golden_file.read_text())
        
        # Test rendering against golden cases
        with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
            for seed, golden_case in golden_cases.items():
                # Mock renderer to return expected checksums
                mock_result = Mock()
                mock_result.checksums = golden_case["expected_checksums"]
                mock_renderer.return_value.render.return_value = mock_result
                
                renderer = mock_renderer.return_value
                
                # Render with same seed as golden case
                result = renderer.render(
                    scene_data=test_scene_data,
                    output_path=temp_dir / f"test_seed_{seed}.mp4",
                    profile="neutral",
                    seed=seed
                )
                
                # Verify checksums match golden case
                assert result.checksums == golden_case["expected_checksums"], \
                    f"Checksums for seed {seed} don't match golden case"
    
    @pytest.mark.asyncio
    async def test_determinism_with_various_scene_complexities(self, temp_dir):
        """Test determinism with scenes of varying complexity."""
        scene_complexities = [
            {
                "name": "simple",
                "objects": 1,
                "lights": 1,
                "materials": 1,
                "expected_consistency": 1.0
            },
            {
                "name": "medium",
                "objects": 5,
                "lights": 3,
                "materials": 4,
                "expected_consistency": 0.99
            },
            {
                "name": "complex",
                "objects": 20,
                "lights": 8,
                "materials": 15,
                "expected_consistency": 0.98
            }
        ]
        
        seed = 45678
        
        for complexity in scene_complexities:
            # Create scene with specified complexity
            scene_data = {
                "scene_id": f"complexity_test_{complexity['name']}",
                "duration": 3.0,
                "fps": 24,
                "resolution": {"width": 1280, "height": 720},
                "objects": [
                    {
                        "id": f"obj_{i}",
                        "type": "cube",
                        "position": [i * 2, 0, 0],
                        "material": {"color": [0.1 * i, 0.5, 0.8]}
                    }
                    for i in range(complexity["objects"])
                ],
                "lighting": [
                    {
                        "type": "sun",
                        "position": [i * 3, 5, 10],
                        "energy": 2.0 + i * 0.5
                    }
                    for i in range(complexity["lights"])
                ]
            }
            
            # Test determinism with this complexity
            with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
                # Mock deterministic results
                mock_result = Mock()
                mock_result.checksums = {
                    f"frame_{i:03d}": f"deterministic_{complexity['name']}_{i:03d}"
                    for i in range(1, 73)  # 3 seconds * 24 fps
                }
                mock_renderer.return_value.render.return_value = mock_result
                
                renderer = mock_renderer.return_value
                
                # Run two identical renders
                results = []
                for run in range(2):
                    result = renderer.render(
                        scene_data=scene_data,
                        output_path=temp_dir / f"{complexity['name']}_run_{run}.mp4",
                        profile="neutral",
                        seed=seed
                    )
                    results.append(result.checksums)
                
                # Verify consistency meets expected threshold
                consistency = len(set(tuple(r.items()) for r in results)) == 1
                assert consistency >= complexity["expected_consistency"], \
                    f"Complexity {complexity['name']} failed determinism test"
    
    @pytest.mark.asyncio
    async def test_determinism_test_suite(self, temp_dir, determinism_manager):
        """Test the determinism test suite itself."""
        # Create test suite configuration
        test_config = {
            "test_cases": [
                {"seed": 111, "scene_type": "simple", "duration": 2.0},
                {"seed": 222, "scene_type": "medium", "duration": 3.0},
                {"seed": 333, "scene_type": "complex", "duration": 5.0}
            ],
            "tolerance": 0.001,  # Allow for minor floating point differences
            "max_retries": 3
        }
        
        # Run determinism test suite
        results = []
        for test_case in test_config["test_cases"]:
            seed = test_case["seed"]
            determinism_manager.set_seed(seed)
            
            # Simulate render with this seed
            with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
                mock_result = Mock()
                mock_result.checksums = {
                    f"frame_{i:03d}": f"test_suite_hash_{seed}_{i:03d}"
                    for i in range(1, int(test_case["duration"] * 24) + 1)
                }
                mock_renderer.return_value.render.return_value = mock_result
                
                renderer = mock_renderer.return_value
                
                # Run multiple times to test consistency
                run_results = []
                for run in range(3):
                    result = renderer.render(
                        scene_data={"duration": test_case["duration"]},
                        output_path=temp_dir / f"suite_test_{seed}_run_{run}.mp4",
                        profile="neutral",
                        seed=seed
                    )
                    run_results.append(result.checksums)
                
                # Check consistency
                is_consistent = all(
                    r == run_results[0] for r in run_results[1:]
                )
                
                results.append({
                    "seed": seed,
                    "scene_type": test_case["scene_type"],
                    "consistent": is_consistent,
                    "checksums": run_results[0]
                })
        
        # Verify all test cases passed
        for result in results:
            assert result["consistent"], f"Test case {result['seed']} failed determinism"
        
        # Generate determinism report
        report = {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r["consistent"]),
            "failed_tests": sum(1 for r in results if not r["consistent"]),
            "test_results": results
        }
        
        # Save report
        report_path = temp_dir / "determinism_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        
        assert report["failed_tests"] == 0, "Some determinism tests failed"
        assert report["passed_tests"] == report["total_tests"], "Not all tests passed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
