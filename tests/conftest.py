"""Pytest configuration and fixtures for the Legal Simulation Platform test suite.

This module provides shared fixtures, test configuration, and utilities
for all test modules in the project.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, List
import json

# Import models
from services.shared.models.case import Case, CaseMode, CaseType, CaseStatus
from services.shared.models.evidence import Evidence, EvidenceType, EvidenceStatus
from services.shared.models.storyboard import Storyboard, StoryboardStatus
from services.shared.models.timeline import Timeline, TimelineStatus
from services.shared.models.render import RenderJob, RenderStatus


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_case_data():
    """Provide test case data."""
    return {
        "id": "test-case-001",
        "metadata": {
            "case_number": "24-cv-001",
            "title": "Test Legal Case",
            "case_type": CaseType.CIVIL,
            "jurisdiction": "federal",
            "court": "US District Court",
            "created_by": "test_user"
        },
        "status": CaseStatus.ACTIVE
    }


@pytest.fixture
def test_evidence_data():
    """Provide test evidence data."""
    return {
        "id": "test-evidence-001",
        "evidence_type": EvidenceType.DOCUMENT,
        "metadata": {
            "filename": "test_document.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024,
            "checksum": "test_hash_123",
            "uploaded_by": "test_user"
        },
        "status": EvidenceStatus.UPLOADED,
        "case_id": "test-case-001",
        "chain_of_custody": [
            {
                "action": "collected",
                "user": "Officer Smith",
                "timestamp": "2024-01-01T10:00:00Z",
                "checksum": "test_hash_123"
            },
            {
                "action": "transferred",
                "user": "Detective Jones", 
                "timestamp": "2024-01-01T11:00:00Z",
                "checksum": "test_hash_123"
            }
        ]
    }


@pytest.fixture
def test_storyboard_data():
    """Provide test storyboard data."""
    return {
        "id": "test-storyboard-001",
        "metadata": {
            "title": "Test Storyboard",
            "description": "Test storyboard content with evidence references",
            "case_id": "test-case-001",
            "created_by": "test_user"
        },
        "status": StoryboardStatus.DRAFT,
        "scenes": []
    }


@pytest.fixture
def test_case(test_case_data):
    """Create a test case instance."""
    from services.shared.models.case import CaseMetadata
    metadata = CaseMetadata(**test_case_data["metadata"])
    return Case(
        id=test_case_data["id"],
        metadata=metadata,
        status=test_case_data["status"]
    )


@pytest.fixture
def test_evidence(test_evidence_data):
    """Create a test evidence instance."""
    from services.shared.models.evidence import EvidenceMetadata
    metadata = EvidenceMetadata(**test_evidence_data["metadata"])
    return Evidence(
        id=test_evidence_data["id"],
        evidence_type=test_evidence_data["evidence_type"],
        metadata=metadata,
        status=test_evidence_data["status"],
        case_id=test_evidence_data["case_id"],
        chain_of_custody=test_evidence_data["chain_of_custody"]
    )


@pytest.fixture
def test_storyboard(test_storyboard_data):
    """Create a test storyboard instance."""
    from services.shared.models.storyboard import StoryboardMetadata
    metadata = StoryboardMetadata(**test_storyboard_data["metadata"])
    return Storyboard(
        id=test_storyboard_data["id"],
        metadata=metadata,
        status=test_storyboard_data["status"],
        scenes=test_storyboard_data["scenes"]
    )


@pytest.fixture
def mock_database_service():
    """Create a mock database service."""
    with patch('services.shared.services.database_service.DatabaseService') as mock_db:
        mock_db.return_value.connection = Mock()
        mock_db.return_value.create_case.return_value = Mock(success=True)
        mock_db.return_value.get_case.return_value = Mock(id="test-case-001")
        mock_db.return_value.create_evidence.return_value = Mock(success=True)
        mock_db.return_value.create_storyboard.return_value = Mock(success=True)
        mock_db.return_value.create_timeline.return_value = Mock(success=True)
        mock_db.return_value.create_render_job.return_value = Mock(success=True)
        yield mock_db.return_value


@pytest.fixture
def mock_storage_service(temp_dir):
    """Create a mock storage service."""
    with patch('services.shared.implementations.storage.local_storage.LocalStorage') as mock_storage:
        mock_storage.return_value.base_path = temp_dir
        mock_storage.return_value.write.return_value = Mock(success=True)
        mock_storage.return_value.read.return_value = b"test content"
        mock_storage.return_value.exists.return_value = True
        yield mock_storage.return_value


@pytest.fixture
def mock_ocr_service():
    """Create a mock OCR service."""
    with patch('services.shared.implementations.ocr.tesseract_local.TesseractLocalOCR') as mock_ocr:
        mock_ocr.return_value.extract_text.return_value = Mock(
            extracted_text="Extracted text content",
            confidence_score=0.95,
            processing_time=2.5
        )
        yield mock_ocr.return_value


@pytest.fixture
def mock_asr_service():
    """Create a mock ASR service."""
    with patch('services.shared.implementations.asr.whisperx_local.WhisperXLocalASR') as mock_asr:
        mock_asr.return_value.extract_text.return_value = Mock(
            transcript="This is a test transcript",
            confidence_score=0.92,
            segments=[
                {"start": 0.0, "end": 2.0, "text": "This is a test", "confidence": 0.95},
                {"start": 2.0, "end": 4.0, "text": "transcript", "confidence": 0.89}
            ]
        )
        yield mock_asr.return_value


@pytest.fixture
def mock_renderer_service():
    """Create a mock renderer service."""
    with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
        mock_renderer.return_value.render.return_value = Mock(
            output_path="/path/to/render.mp4",
            success=True,
            render_time=30.0,
            frames_generated=720,
            checksums={"frame_001": "hash_001", "frame_002": "hash_002"}
        )
        yield mock_renderer.return_value


@pytest.fixture
def mock_policy_service():
    """Create a mock policy service."""
    with patch('services.shared.interfaces.policy.PolicyService') as mock_policy:
        mock_policy.return_value.validate_case.return_value = []
        mock_policy.return_value.validate_evidence.return_value = []
        mock_policy.return_value.validate_storyboard.return_value = []
        mock_policy.return_value.validate_render_job.return_value = []
        mock_policy.return_value.get_jurisdiction_rules.return_value = {
            "evidence_requirements": {"chain_of_custody": True},
            "demonstrative_standards": {"accuracy_required": 0.95}
        }
        yield mock_policy.return_value


@pytest.fixture
def test_data_directory(temp_dir):
    """Create a test data directory with sample files."""
    data_dir = temp_dir / "test_data"
    data_dir.mkdir()
    
    # Create sample document
    doc_file = data_dir / "sample_document.txt"
    doc_file.write_text("This is a sample legal document for testing.")
    
    # Create sample audio file (minimal WAV)
    audio_file = data_dir / "sample_audio.wav"
    audio_file.write_bytes(
        b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00' + 
        b'\x00' * 2048
    )
    
    # Create sample image
    from PIL import Image
    img = Image.new('RGB', (800, 600), color='white')
    img_file = data_dir / "sample_image.png"
    img.save(img_file)
    
    # Create test configuration
    config_file = data_dir / "test_config.json"
    config_file.write_text(json.dumps({
        "test_mode": True,
        "jurisdiction": "federal",
        "render_profile": "neutral",
        "timeout": 30
    }))
    
    return data_dir


@pytest.fixture
def performance_monitor():
    """Create a performance monitoring fixture."""
    import time
    import psutil
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.measurements = []
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        def stop(self):
            if self.start_time is None:
                return None
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            measurement = {
                "duration": end_time - self.start_time,
                "memory_start": self.start_memory,
                "memory_end": end_memory,
                "memory_increase": end_memory - self.start_memory
            }
            
            self.measurements.append(measurement)
            return measurement
        
        def get_summary(self):
            if not self.measurements:
                return None
            
            return {
                "total_measurements": len(self.measurements),
                "avg_duration": sum(m["duration"] for m in self.measurements) / len(self.measurements),
                "max_duration": max(m["duration"] for m in self.measurements),
                "avg_memory_increase": sum(m["memory_increase"] for m in self.measurements) / len(self.measurements),
                "max_memory_increase": max(m["memory_increase"] for m in self.measurements)
            }
    
    return PerformanceMonitor()


@pytest.fixture
def test_scenarios():
    """Provide test scenarios for different use cases."""
    return {
        "simple_case": {
            "case_type": "civil",
            "jurisdiction": "federal",
            "evidence_count": 2,
            "scene_count": 1,
            "expected_duration": 10.0
        },
        "complex_case": {
            "case_type": "criminal",
            "jurisdiction": "california",
            "evidence_count": 10,
            "scene_count": 5,
            "expected_duration": 60.0
        },
        "demonstrative_case": {
            "case_type": "civil",
            "jurisdiction": "federal",
            "mode": CaseMode.DEMONSTRATIVE,
            "evidence_count": 5,
            "scene_count": 3,
            "expected_duration": 30.0,
            "accuracy_required": 0.95
        },
        "sandbox_case": {
            "case_type": "criminal",
            "jurisdiction": "texas",
            "mode": CaseMode.SANDBOX,
            "evidence_count": 8,
            "scene_count": 4,
            "expected_duration": 45.0,
            "allow_speculation": True
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Mock external dependencies
    with patch('services.shared.database.init_database') as mock_init:
        mock_init.return_value = Mock()
        yield
    
    # Cleanup after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]


@pytest.fixture
def deterministic_seed():
    """Provide a deterministic seed for testing."""
    return 12345


@pytest.fixture
def mock_determinism_manager(deterministic_seed):
    """Create a mock determinism manager."""
    with patch('services.render_orchestrator.implementations.blender.determinism.DeterminismManager') as mock_dm:
        mock_dm.return_value.get_current_seed.return_value = deterministic_seed
        mock_dm.return_value.set_seed.return_value = None
        mock_dm.return_value.random.return_value = 0.5  # Deterministic random value
        yield mock_dm.return_value


# Test markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "determinism: mark test as determinism test")
    config.addinivalue_line("markers", "compliance: mark test as compliance test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "determinism" in str(item.fspath):
            item.add_marker(pytest.mark.determinism)
        elif "compliance" in str(item.fspath):
            item.add_marker(pytest.mark.compliance)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)


# Test reporting
def pytest_html_report_title(report):
    """Set the title of the HTML report."""
    report.title = "Legal Simulation Platform Test Report"


def pytest_html_results_summary(prefix, summary, postfix):
    """Add custom summary to HTML report."""
    prefix.extend([
        "<p><strong>Legal Simulation Platform</strong></p>",
        "<p>Comprehensive test suite for evidence processing, rendering, and compliance validation.</p>"
    ])
