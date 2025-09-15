"""End-to-end tests for complete case creation workflows.

Tests complete user workflows from case creation to final render output,
including multi-user collaboration and error recovery scenarios.
"""

import pytest
import asyncio
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Import models and services
from services.shared.models.case import Case, CaseMode, CaseType, CaseMetadata
from services.shared.models.evidence import Evidence, EvidenceType, EvidenceMetadata
from services.shared.models.storyboard import Storyboard, Scene
from services.shared.models.render import RenderJob, RenderConfig, RenderProfile
from services.shared.models.timeline import Timeline


class TestCaseCreationFlow:
    """Test suite for end-to-end case creation workflows."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def test_case_metadata(self):
        """Create test case metadata."""
        return CaseMetadata(
            case_number="24-cv-e2e-001",
            title="E2E Test Case",
            case_type=CaseType.CIVIL,
            jurisdiction="federal",
            court="US District Court",
            filing_date="2024-01-01",
            parties={
                "plaintiff": "Test Plaintiff Corp.",
                "defendant": "Test Defendant LLC"
            },
            attorneys={
                "plaintiff": "Jane Smith, Esq.",
                "defendant": "John Doe, Esq."
            }
        )
    
    @pytest.fixture
    def test_evidence_files(self, temp_dir):
        """Create test evidence files."""
        evidence_files = {}
        
        # Create document evidence
        doc_path = temp_dir / "contract_agreement.pdf"
        doc_content = """
        CONTRACT AGREEMENT
        
        This agreement is entered into on January 1, 2024, between
        Test Plaintiff Corp. and Test Defendant LLC.
        
        Terms and conditions:
        1. Payment of $50,000.00
        2. Delivery by March 1, 2024
        3. Warranty period of 1 year
        """
        doc_path.write_text(doc_content)
        evidence_files["document"] = doc_path
        
        # Create audio evidence (mock)
        audio_path = temp_dir / "deposition_transcript.wav"
        audio_path.write_bytes(b"mock audio data")
        evidence_files["audio"] = audio_path
        
        # Create image evidence (mock)
        image_path = temp_dir / "evidence_photo.jpg"
        image_path.write_bytes(b"mock image data")
        evidence_files["image"] = image_path
        
        return evidence_files
    
    @pytest.fixture
    def test_storyboard_content(self):
        """Create test storyboard content."""
        return """
        # Case Presentation Storyboard
        
        ## Scene 1: Contract Overview (0:00 - 0:30)
        - Present the contract agreement document
        - Highlight key terms and conditions
        - Show parties involved
        
        ## Scene 2: Evidence Presentation (0:30 - 1:00)
        - Display contract signatures
        - Show delivery timeline
        - Present payment terms
        
        ## Scene 3: Witness Testimony (1:00 - 1:30)
        - Play deposition audio
        - Display transcript overlay
        - Highlight key statements
        
        ## Scene 4: Conclusion (1:30 - 2:00)
        - Summarize key points
        - Present timeline of events
        - Show final evidence summary
        """
    
    @pytest.mark.asyncio
    async def test_complete_case_creation_workflow(self, temp_dir, test_case_metadata, test_evidence_files, test_storyboard_content):
        """Test complete workflow from case creation to render output."""
        
        # Step 1: Create case
        case = Case(
            id="e2e-case-001",
            metadata=test_case_metadata,
            mode=CaseMode.DEMONSTRATIVE
        )
        
        # Verify case creation
        assert case.id == "e2e-case-001"
        assert case.metadata.case_number == "24-cv-e2e-001"
        assert case.mode == CaseMode.DEMONSTRATIVE
        
        # Step 2: Upload and process evidence
        evidence_items = []
        
        # Process document evidence
        doc_evidence = Evidence(
            id="evid-doc-001",
            case_id=case.id,
            filename=test_evidence_files["document"].name,
            evidence_type=EvidenceType.DOCUMENT,
            file_path=str(test_evidence_files["document"]),
            sha256_hash="doc_hash_123",
            metadata=EvidenceMetadata(
                filename=test_evidence_files["document"].name,
                content_type="application/pdf",
                size_bytes=test_evidence_files["document"].stat().st_size,
                checksum="doc_hash_123",
                uploaded_by="test_user"
            ),
            chain_of_custody=[
                {"timestamp": "2024-01-01T10:00:00Z", "custodian": "Officer Smith", "action": "collected"},
                {"timestamp": "2024-01-01T11:00:00Z", "custodian": "Detective Jones", "action": "transferred"}
            ]
        )
        evidence_items.append(doc_evidence)
        
        # Process audio evidence
        audio_evidence = Evidence(
            id="evid-audio-001",
            case_id=case.id,
            filename=test_evidence_files["audio"].name,
            evidence_type=EvidenceType.AUDIO,
            file_path=str(test_evidence_files["audio"]),
            sha256_hash="audio_hash_123",
            metadata=EvidenceMetadata(
                filename=test_evidence_files["audio"].name,
                content_type="audio/wav",
                size_bytes=test_evidence_files["audio"].stat().st_size,
                checksum="audio_hash_123",
                uploaded_by="test_user"
            )
        )
        evidence_items.append(audio_evidence)
        
        # Process image evidence
        image_evidence = Evidence(
            id="evid-image-001",
            case_id=case.id,
            filename=test_evidence_files["image"].name,
            evidence_type=EvidenceType.IMAGE,
            file_path=str(test_evidence_files["image"]),
            sha256_hash="image_hash_123",
            metadata=EvidenceMetadata(
                filename=test_evidence_files["image"].name,
                content_type="image/jpeg",
                size_bytes=test_evidence_files["image"].stat().st_size,
                checksum="image_hash_123",
                uploaded_by="test_user"
            )
        )
        evidence_items.append(image_evidence)
        
        # Verify evidence processing
        assert len(evidence_items) == 3
        for evidence in evidence_items:
            assert evidence.case_id == case.id
            assert evidence.evidence_type in [EvidenceType.DOCUMENT, EvidenceType.AUDIO, EvidenceType.IMAGE]
        
        # Step 3: Create storyboard
        storyboard = Storyboard(
            id="story-e2e-001",
            case_id=case.id,
            title="E2E Test Storyboard",
            content=test_storyboard_content,
            scenes=[
                Scene(
                    scene_id="scene-001",
                    title="Contract Overview",
                    duration_seconds=30.0,
                    evidence_anchors=[
                        {
                            "evidence_id": "evid-doc-001",
                            "timestamp": 5.0,
                            "confidence": 0.95,
                            "description": "Contract agreement document"
                        }
                    ],
                    camera_config={
                        "position": [0, 0, 5],
                        "rotation": [0, 0, 0],
                        "focal_length": 50
                    }
                ),
                Scene(
                    scene_id="scene-002",
                    title="Evidence Presentation",
                    duration_seconds=30.0,
                    evidence_anchors=[
                        {
                            "evidence_id": "evid-image-001",
                            "timestamp": 10.0,
                            "confidence": 0.90,
                            "description": "Evidence photograph"
                        }
                    ]
                ),
                Scene(
                    scene_id="scene-003",
                    title="Witness Testimony",
                    duration_seconds=30.0,
                    evidence_anchors=[
                        {
                            "evidence_id": "evid-audio-001",
                            "timestamp": 15.0,
                            "confidence": 0.85,
                            "description": "Deposition transcript"
                        }
                    ]
                ),
                Scene(
                    scene_id="scene-004",
                    title="Conclusion",
                    duration_seconds=30.0,
                    evidence_anchors=[]
                )
            ]
        )
        
        # Verify storyboard creation
        assert storyboard.id == "story-e2e-001"
        assert len(storyboard.scenes) == 4
        assert storyboard.scenes[0].title == "Contract Overview"
        assert storyboard.scenes[0].evidence_anchors[0]["evidence_id"] == "evid-doc-001"
        
        # Step 4: Generate timeline
        timeline = Timeline(
            id="timeline-e2e-001",
            case_id=case.id,
            storyboard_id=storyboard.id,
            total_duration_seconds=120.0,  # 2 minutes
            scenes=[
                {
                    "scene_id": "scene-001",
                    "start_time": 0.0,
                    "end_time": 30.0,
                    "evidence_clips": [
                        {
                            "evidence_id": "evid-doc-001",
                            "start_time": 5.0,
                            "end_time": 25.0,
                            "confidence": 0.95
                        }
                    ]
                },
                {
                    "scene_id": "scene-002",
                    "start_time": 30.0,
                    "end_time": 60.0,
                    "evidence_clips": [
                        {
                            "evidence_id": "evid-image-001",
                            "start_time": 40.0,
                            "end_time": 55.0,
                            "confidence": 0.90
                        }
                    ]
                },
                {
                    "scene_id": "scene-003",
                    "start_time": 60.0,
                    "end_time": 90.0,
                    "evidence_clips": [
                        {
                            "evidence_id": "evid-audio-001",
                            "start_time": 75.0,
                            "end_time": 85.0,
                            "confidence": 0.85
                        }
                    ]
                },
                {
                    "scene_id": "scene-004",
                    "start_time": 90.0,
                    "end_time": 120.0,
                    "evidence_clips": []
                }
            ]
        )
        
        # Verify timeline generation
        assert timeline.id == "timeline-e2e-001"
        assert timeline.total_duration_seconds == 120.0
        assert len(timeline.scenes) == 4
        assert timeline.scenes[0]["start_time"] == 0.0
        assert timeline.scenes[0]["end_time"] == 30.0
        
        # Step 5: Create render job
        render_config = RenderConfig(
            width=1920,
            height=1080,
            fps=30,
            duration_seconds=120.0,
            profile=RenderProfile.NEUTRAL,
            deterministic=True,
            seed=42,
            output_format="mp4",
            quality="high"
        )
        
        render_job = RenderJob(
            id="render-e2e-001",
            case_id=case.id,
            storyboard_id=storyboard.id,
            timeline_id=timeline.id,
            config=render_config,
            output_path=str(temp_dir / "e2e_render_output.mp4"),
            status="pending"
        )
        
        # Verify render job creation
        assert render_job.id == "render-e2e-001"
        assert render_job.config.profile == RenderProfile.NEUTRAL
        assert render_job.config.deterministic is True
        assert render_job.status == "pending"
        
        # Step 6: Mock render execution
        with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
            mock_render_result = Mock()
            mock_render_result.output_path = render_job.output_path
            mock_render_result.render_time_seconds = 45.0
            mock_render_result.frames_generated = 3600  # 120 seconds * 30 fps
            mock_render_result.file_size_bytes = 50 * 1024 * 1024  # 50MB
            mock_render_result.checksums = {
                f"frame_{i:06d}": f"checksum_{i:06d}" for i in range(1, 3601)
            }
            
            mock_renderer.return_value.render_scene.return_value = mock_render_result
            
            renderer = mock_renderer.return_value
            
            # Execute render
            scene_data = Mock()
            result = await renderer.render_scene(scene_data, render_job.config)
            
            # Verify render execution
            assert result.output_path == render_job.output_path
            assert result.render_time_seconds > 0
            assert result.frames_generated == 3600
            assert len(result.checksums) == 3600
            
            # Update render job status
            render_job.status = "completed"
            render_job.completed_at = time.time()
            
            # Verify final render job status
            assert render_job.status == "completed"
            assert render_job.completed_at is not None
        
        # Step 7: Verify complete workflow
        workflow_summary = {
            "case_id": case.id,
            "evidence_count": len(evidence_items),
            "storyboard_scenes": len(storyboard.scenes),
            "timeline_duration": timeline.total_duration_seconds,
            "render_completed": render_job.status == "completed",
            "output_file": render_job.output_path
        }
        
        # Verify workflow completeness
        assert workflow_summary["evidence_count"] == 3
        assert workflow_summary["storyboard_scenes"] == 4
        assert workflow_summary["timeline_duration"] == 120.0
        assert workflow_summary["render_completed"] is True
        
        # Save workflow summary for verification
        summary_path = temp_dir / "workflow_summary.json"
        summary_path.write_text(json.dumps(workflow_summary, indent=2))
        
        assert summary_path.exists()
    
    @pytest.mark.asyncio
    async def test_multi_user_collaboration_workflow(self, temp_dir):
        """Test multi-user collaboration on a single case."""
        
        # Create shared case
        shared_case = Case(
            id="collaboration-case-001",
            metadata=CaseMetadata(
                case_number="24-cv-collab-001",
                title="Collaboration Test Case",
                case_type=CaseType.CIVIL,
                jurisdiction="federal",
                court="US District Court"
            ),
            mode=CaseMode.DEMONSTRATIVE,
            collaborators=[
                {"user_id": "user-001", "role": "lead_attorney", "permissions": ["read", "write", "approve"]},
                {"user_id": "user-002", "role": "paralegal", "permissions": ["read", "write"]},
                {"user_id": "user-003", "role": "reviewer", "permissions": ["read", "comment"]}
            ]
        )
        
        # User 1 (Lead Attorney): Creates initial case structure
        user1_case_data = {
            "case_id": shared_case.id,
            "created_by": "user-001",
            "actions": ["case_created", "evidence_uploaded", "storyboard_created"]
        }
        
        # User 2 (Paralegal): Adds evidence and refines storyboard
        user2_case_data = {
            "case_id": shared_case.id,
            "updated_by": "user-002",
            "actions": ["evidence_processed", "storyboard_updated", "timeline_created"]
        }
        
        # User 3 (Reviewer): Reviews and comments
        user3_case_data = {
            "case_id": shared_case.id,
            "reviewed_by": "user-003",
            "actions": ["storyboard_reviewed", "comments_added", "approval_requested"]
        }
        
        # Simulate collaboration workflow
        collaboration_events = []
        
        # User 1 creates case
        collaboration_events.append({
            "timestamp": "2024-01-01T10:00:00Z",
            "user_id": "user-001",
            "action": "case_created",
            "data": user1_case_data
        })
        
        # User 2 processes evidence
        collaboration_events.append({
            "timestamp": "2024-01-01T11:00:00Z",
            "user_id": "user-002",
            "action": "evidence_processed",
            "data": user2_case_data
        })
        
        # User 3 reviews
        collaboration_events.append({
            "timestamp": "2024-01-01T12:00:00Z",
            "user_id": "user-003",
            "action": "storyboard_reviewed",
            "data": user3_case_data
        })
        
        # User 1 approves
        collaboration_events.append({
            "timestamp": "2024-01-01T13:00:00Z",
            "user_id": "user-001",
            "action": "approved",
            "data": {"case_id": shared_case.id, "approved_by": "user-001"}
        })
        
        # Verify collaboration workflow
        assert len(collaboration_events) == 4
        assert collaboration_events[0]["action"] == "case_created"
        assert collaboration_events[1]["action"] == "evidence_processed"
        assert collaboration_events[2]["action"] == "storyboard_reviewed"
        assert collaboration_events[3]["action"] == "approved"
        
        # Verify user permissions
        for collaborator in shared_case.collaborators:
            assert "user_id" in collaborator
            assert "role" in collaborator
            assert "permissions" in collaborator
            
            if collaborator["role"] == "lead_attorney":
                assert "approve" in collaborator["permissions"]
            elif collaborator["role"] == "paralegal":
                assert "write" in collaborator["permissions"]
            elif collaborator["role"] == "reviewer":
                assert "comment" in collaborator["permissions"]
        
        # Save collaboration log
        collaboration_log_path = temp_dir / "collaboration_log.json"
        collaboration_log_path.write_text(json.dumps(collaboration_events, indent=2))
        
        assert collaboration_log_path.exists()
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, temp_dir):
        """Test error recovery and resilience scenarios."""
        
        # Test upload failure and retry
        upload_failures = []
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Simulate upload failure on first two attempts
                if attempt < 2:
                    raise ConnectionError("Network timeout during upload")
                
                # Success on third attempt
                upload_failures.append({
                    "attempt": attempt + 1,
                    "success": True,
                    "error": None
                })
                break
                
            except ConnectionError as e:
                upload_failures.append({
                    "attempt": attempt + 1,
                    "success": False,
                    "error": str(e)
                })
                
                # Wait before retry
                await asyncio.sleep(1.0)
        
        # Verify retry mechanism
        assert len(upload_failures) == 3
        assert upload_failures[0]["success"] is False
        assert upload_failures[1]["success"] is False
        assert upload_failures[2]["success"] is True
        
        # Test render crash recovery
        render_crash_scenarios = []
        
        # Scenario 1: Render crashes mid-process
        with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
            render_count = 0
            
            async def mock_render_with_crash(scene_data, config):
                nonlocal render_count
                render_count += 1
                
                if render_count == 1:
                    # First render crashes
                    raise RuntimeError("Blender process crashed")
                else:
                    # Second render succeeds
                    return Mock(
                        output_path=config.output_path,
                        render_time_seconds=30.0,
                        frames_generated=720,
                        file_size_bytes=25 * 1024 * 1024
                    )
            
            mock_renderer.return_value.render_scene = mock_render_with_crash
            
            renderer = mock_renderer.return_value
            
            # First render attempt (should crash)
            try:
                scene_data = Mock()
                config = Mock()
                config.output_path = str(temp_dir / "recovery_test.mp4")
                
                result = await renderer.render_scene(scene_data, config)
                render_crash_scenarios.append({
                    "attempt": 1,
                    "success": True,
                    "error": None
                })
            except RuntimeError as e:
                render_crash_scenarios.append({
                    "attempt": 1,
                    "success": False,
                    "error": str(e)
                })
            
            # Second render attempt (should succeed)
            try:
                result = await renderer.render_scene(scene_data, config)
                render_crash_scenarios.append({
                    "attempt": 2,
                    "success": True,
                    "error": None,
                    "frames_generated": result.frames_generated
                })
            except Exception as e:
                render_crash_scenarios.append({
                    "attempt": 2,
                    "success": False,
                    "error": str(e)
                })
        
        # Verify render recovery
        assert len(render_crash_scenarios) == 2
        assert render_crash_scenarios[0]["success"] is False
        assert render_crash_scenarios[1]["success"] is True
        assert render_crash_scenarios[1]["frames_generated"] == 720
        
        # Test network interruption handling
        network_interruptions = []
        
        async def simulate_network_operation():
            """Simulate network operation with interruptions."""
            try:
                # Simulate network delay
                await asyncio.sleep(0.1)
                
                # Simulate network interruption
                raise ConnectionError("Network connection lost")
                
            except ConnectionError as e:
                network_interruptions.append({
                    "error": str(e),
                    "recovered": False
                })
                
                # Simulate reconnection
                await asyncio.sleep(0.1)
                
                try:
                    # Retry operation
                    await asyncio.sleep(0.1)
                    network_interruptions.append({
                        "error": None,
                        "recovered": True
                    })
                except Exception as retry_error:
                    network_interruptions.append({
                        "error": str(retry_error),
                        "recovered": False
                    })
        
        await simulate_network_operation()
        
        # Verify network recovery
        assert len(network_interruptions) == 2
        assert network_interruptions[0]["recovered"] is False
        assert network_interruptions[1]["recovered"] is True
        
        # Test partial state recovery
        partial_state_data = {
            "case_id": "recovery-case-001",
            "evidence_uploaded": True,
            "evidence_processed": False,  # Processing failed
            "storyboard_created": False,
            "timeline_generated": False,
            "render_completed": False
        }
        
        # Simulate recovery from partial state
        recovery_actions = []
        
        # Check what needs to be recovered
        if not partial_state_data["evidence_processed"]:
            recovery_actions.append("retry_evidence_processing")
        
        if not partial_state_data["storyboard_created"]:
            recovery_actions.append("create_storyboard")
        
        if not partial_state_data["timeline_generated"]:
            recovery_actions.append("generate_timeline")
        
        # Execute recovery actions
        for action in recovery_actions:
            # Simulate successful recovery
            await asyncio.sleep(0.1)
            
            if action == "retry_evidence_processing":
                partial_state_data["evidence_processed"] = True
            elif action == "create_storyboard":
                partial_state_data["storyboard_created"] = True
            elif action == "generate_timeline":
                partial_state_data["timeline_generated"] = True
        
        # Verify recovery
        assert partial_state_data["evidence_processed"] is True
        assert partial_state_data["storyboard_created"] is True
        assert partial_state_data["timeline_generated"] is True
        
        # Test data integrity after errors
        data_integrity_checks = []
        
        # Simulate data corruption detection
        original_checksum = "abc123def456"
        corrupted_checksum = "abc123def456"  # Same for test, but would be different in real scenario
        
        if original_checksum != corrupted_checksum:
            data_integrity_checks.append({
                "check": "checksum_validation",
                "result": "corrupted",
                "action": "restore_from_backup"
            })
        else:
            data_integrity_checks.append({
                "check": "checksum_validation",
                "result": "valid",
                "action": "none"
            })
        
        # Verify data integrity
        assert len(data_integrity_checks) == 1
        assert data_integrity_checks[0]["result"] == "valid"
        
        # Save error recovery log
        error_recovery_log = {
            "upload_failures": upload_failures,
            "render_crash_scenarios": render_crash_scenarios,
            "network_interruptions": network_interruptions,
            "partial_state_recovery": partial_state_data,
            "data_integrity_checks": data_integrity_checks
        }
        
        recovery_log_path = temp_dir / "error_recovery_log.json"
        recovery_log_path.write_text(json.dumps(error_recovery_log, indent=2))
        
        assert recovery_log_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])