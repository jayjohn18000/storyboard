"""Unit tests for data models."""

import pytest
from datetime import datetime

from services.shared.models.case import Case, CaseMode, CaseType, CaseStatus, CaseMetadata
from services.shared.models.evidence import Evidence, EvidenceType, EvidenceStatus, EvidenceMetadata
from services.shared.models.storyboard import Storyboard, StoryboardStatus, StoryboardMetadata
from services.shared.models.timeline import Timeline, TimelineStatus, TimelineMetadata
from services.shared.models.render import RenderJob, RenderStatus


class TestCaseModels:
    """Test case data models."""
    
    def test_case_creation(self):
        """Test basic case creation."""
        metadata = CaseMetadata(
            case_number="24-cv-001",
            title="Test Case",
            case_type=CaseType.CIVIL,
            jurisdiction="federal",
            court="US District Court",
            created_by="test_user"
        )
        
        case = Case(
            id="test-case-001",
            metadata=metadata,
            status=CaseStatus.ACTIVE
        )
        
        assert case.id == "test-case-001"
        assert case.metadata.title == "Test Case"
        assert case.metadata.case_type == CaseType.CIVIL
        assert case.status == CaseStatus.ACTIVE
        assert len(case.evidence_ids) == 0
        assert len(case.storyboard_ids) == 0
    
    def test_case_modes(self):
        """Test case mode enumeration."""
        assert CaseMode.DEMONSTRATIVE.value == "demonstrative"
        assert CaseMode.SANDBOX.value == "sandbox"
    
    def test_add_evidence(self):
        """Test adding evidence to case."""
        metadata = CaseMetadata(
            case_number="24-cv-001",
            title="Test Case",
            case_type=CaseType.CIVIL,
            jurisdiction="federal",
            court="US District Court",
            created_by="test_user"
        )
        
        case = Case(metadata=metadata)
        
        # Add evidence
        case.add_evidence("evidence-001")
        assert "evidence-001" in case.evidence_ids
        assert len(case.evidence_ids) == 1
        
        # Adding same evidence again should not duplicate
        case.add_evidence("evidence-001")
        assert len(case.evidence_ids) == 1


class TestEvidenceModels:
    """Test evidence data models."""
    
    def test_evidence_creation(self):
        """Test basic evidence creation."""
        metadata = EvidenceMetadata(
            filename="test_document.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="test_hash",
            uploaded_by="test_user"
        )
        
        evidence = Evidence(
            id="test-evidence-001",
            evidence_type=EvidenceType.DOCUMENT,
            metadata=metadata,
            status=EvidenceStatus.UPLOADED,
            case_id="test-case-001"
        )
        
        assert evidence.id == "test-evidence-001"
        assert evidence.evidence_type == EvidenceType.DOCUMENT
        assert evidence.metadata.filename == "test_document.pdf"
        assert evidence.status == EvidenceStatus.UPLOADED
        assert evidence.case_id == "test-case-001"
    
    def test_chain_of_custody(self):
        """Test chain of custody functionality."""
        metadata = EvidenceMetadata(
            filename="test_document.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="test_hash",
            uploaded_by="test_user"
        )
        
        evidence = Evidence(metadata=metadata)
        
        # Add custody entry
        evidence.add_custody_entry("collected", "Officer Smith")
        assert len(evidence.chain_of_custody) == 1
        
        entry = evidence.chain_of_custody[0]
        assert entry["action"] == "collected"
        assert entry["user"] == "Officer Smith"
        assert "timestamp" in entry


class TestStoryboardModels:
    """Test storyboard data models."""
    
    def test_storyboard_creation(self):
        """Test basic storyboard creation."""
        metadata = StoryboardMetadata(
            title="Test Storyboard",
            description="Test description",
            case_id="test-case-001",
            created_by="test_user"
        )
        
        storyboard = Storyboard(
            id="test-storyboard-001",
            metadata=metadata,
            status=StoryboardStatus.DRAFT
        )
        
        assert storyboard.id == "test-storyboard-001"
        assert storyboard.metadata.title == "Test Storyboard"
        assert storyboard.status == StoryboardStatus.DRAFT
        assert len(storyboard.scenes) == 0


class TestTimelineModels:
    """Test timeline data models."""
    
    def test_timeline_creation(self):
        """Test basic timeline creation."""
        metadata = TimelineMetadata(
            title="Test Timeline",
            description="Test description",
            storyboard_id="test-storyboard-001",
            created_by="test_user"
        )
        
        timeline = Timeline(
            id="test-timeline-001",
            metadata=metadata,
            status=TimelineStatus.DRAFT
        )
        
        assert timeline.id == "test-timeline-001"
        assert timeline.metadata.title == "Test Timeline"
        assert timeline.status == TimelineStatus.DRAFT
        assert len(timeline.tracks) == 0


class TestRenderModels:
    """Test render data models."""
    
    def test_render_job_creation(self):
        """Test basic render job creation."""
        job = RenderJob(
            id="test-render-001",
            timeline_id="test-timeline-001",
            storyboard_id="test-storyboard-001",
            case_id="test-case-001",
            status=RenderStatus.QUEUED
        )
        
        assert job.id == "test-render-001"
        assert job.timeline_id == "test-timeline-001"
        assert job.status == RenderStatus.QUEUED
        assert job.deterministic is True
        assert job.quality.value == "standard"
    
    def test_render_progress(self):
        """Test render progress tracking."""
        job = RenderJob()
        
        # Start processing
        job.start_processing()
        assert job.status == RenderStatus.PROCESSING
        assert job.started_at is not None
        
        # Update progress
        job.update_progress(30, 100)
        assert job.frames_rendered == 30
        assert job.total_frames == 100
        assert job.progress_percentage == 30.0
        
        # Complete processing
        job.complete_processing("/path/to/output.mp4", 1024, 10.0)
        assert job.status == RenderStatus.COMPLETED
        assert job.output_path == "/path/to/output.mp4"
        assert job.progress_percentage == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
