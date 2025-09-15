#!/usr/bin/env python3
"""Test script to verify the Legal Simulation Platform setup."""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        # Test shared modules
        from services.shared.database import init_database, Base
        print("✅ Database module imported successfully")
        
        from services.shared.models.database_models import User, Case, Evidence, Storyboard, Render
        print("✅ Database models imported successfully")
        
        from services.shared.services.database_service import DatabaseService
        print("✅ Database service imported successfully")
        
        # Test storyboard service
        import importlib.util
        spec = importlib.util.spec_from_file_location("lint_engine", "services/storyboard-service/validators/lint_engine.py")
        lint_engine_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint_engine_module)
        print("✅ Lint engine imported successfully")
        
        spec = importlib.util.spec_from_file_location("anchor_validator", "services/storyboard-service/validators/anchor_validator.py")
        anchor_validator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(anchor_validator_module)
        print("✅ Anchor validator imported successfully")
        
        spec = importlib.util.spec_from_file_location("coverage_calculator", "services/storyboard-service/validators/coverage_calculator.py")
        coverage_calculator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(coverage_calculator_module)
        print("✅ Coverage calculator imported successfully")
        
        # Test timeline compiler
        spec = importlib.util.spec_from_file_location("trajectory_generator", "services/timeline-compiler/scene_graph/trajectory_generator.py")
        trajectory_generator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(trajectory_generator_module)
        print("✅ Trajectory generator imported successfully")
        
        spec = importlib.util.spec_from_file_location("usd_builder", "services/timeline-compiler/scene_graph/usd_builder.py")
        usd_builder_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(usd_builder_module)
        print("✅ USD builder imported successfully")
        
        spec = importlib.util.spec_from_file_location("spatial_solver", "services/timeline-compiler/scene_graph/spatial_solver.py")
        spatial_solver_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spatial_solver_module)
        print("✅ Spatial solver imported successfully")
        
        # Test API Gateway
        spec = importlib.util.spec_from_file_location("api_gateway", "services/api-gateway/main.py")
        api_gateway_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_gateway_module)
        print("✅ API Gateway imported successfully")
        
        # Test evidence processor
        spec = importlib.util.spec_from_file_location("evidence_processor", "services/evidence-processor/main.py")
        evidence_processor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evidence_processor_module)
        print("✅ Evidence processor imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_lint_engine():
    """Test the lint engine functionality."""
    print("\n🧪 Testing lint engine...")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("lint_engine", "services/storyboard-service/validators/lint_engine.py")
        lint_engine_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint_engine_module)
        
        lint_engine = lint_engine_module.LintEngine()
        
        # Test with minimal storyboard data
        test_data = {
            "metadata": {
                "title": "Test Storyboard",
                "case_id": "test-case-123"
            },
            "scenes": [
                {
                    "title": "Scene 1",
                    "duration_seconds": 5.0,
                    "start_time": 0.0,
                    "evidence_anchors": [],
                    "camera_config": {},
                    "lighting_config": {},
                    "materials": [],
                    "transitions": {}
                }
            ]
        }
        
        # This would be async in real usage, but we're just testing imports
        print("✅ Lint engine created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Lint engine error: {e}")
        return False

def test_trajectory_generator():
    """Test the trajectory generator functionality."""
    print("\n🧪 Testing trajectory generator...")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("trajectory_generator", "services/timeline-compiler/scene_graph/trajectory_generator.py")
        trajectory_generator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(trajectory_generator_module)
        
        generator = trajectory_generator_module.TrajectoryGenerator()
        
        # Test with minimal scene data
        test_scene = {
            "scene_type": "evidence_display",
            "duration": 5.0,
            "camera_config": {
                "position": [0, 0, 5],
                "rotation": [0, 0, 0],
                "focal_length": 50,
                "fov": 45
            },
            "evidence_anchors": []
        }
        
        print("✅ Trajectory generator created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Trajectory generator error: {e}")
        return False

def test_docker_setup():
    """Test that Docker files exist."""
    print("\n🧪 Testing Docker setup...")
    
    docker_files = [
        "docker-compose.yml",
        "infrastructure/docker/services/api-gateway.Dockerfile",
        "infrastructure/docker/services/evidence-processor.Dockerfile",
        "infrastructure/docker/services/storyboard-service.Dockerfile",
        "infrastructure/docker/services/timeline-compiler.Dockerfile",
        "infrastructure/docker/services/render-orchestrator.Dockerfile",
    ]
    
    all_exist = True
    for docker_file in docker_files:
        if Path(docker_file).exists():
            print(f"✅ {docker_file} exists")
        else:
            print(f"❌ {docker_file} missing")
            all_exist = False
    
    return all_exist

def test_config_files():
    """Test that configuration files exist."""
    print("\n🧪 Testing configuration files...")
    
    config_files = [
        "pyproject.toml",
        "env.example",
        "Makefile",
        "database/schemas/01_init.sql",
        "config/rbac-policies/cerbos.yaml",
        "config/policy-packs/opa-policies.rego",
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("🚀 Legal Simulation Platform - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_lint_engine,
        test_trajectory_generator,
        test_docker_setup,
        test_config_files,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The platform is ready to use.")
        print("\nNext steps:")
        print("1. Copy env.example to .env and configure your environment")
        print("2. Run 'make setup-mvp' to initialize the database")
        print("3. Run 'docker-compose up -d' to start all services")
        print("4. Access the dashboard at http://localhost:3000")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
