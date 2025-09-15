"""Compliance tests for policy engine and jurisdiction rules.

Tests each jurisdiction's rules, validation violations, edge cases,
and remediation suggestions to ensure legal compliance.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Import policy and compliance modules
from services.shared.interfaces.policy import PolicyService, PolicyViolation
from services.shared.models.case import Case, CaseMode, CaseType
from services.shared.models.evidence import Evidence, EvidenceType
from services.shared.models.storyboard import Storyboard
from services.shared.models.render import RenderJob


class TestPolicyCompliance:
    """Test suite for policy compliance and jurisdiction rules."""
    
    @pytest.fixture
    def federal_policy_service(self):
        """Create federal jurisdiction policy service."""
        with patch('services.shared.interfaces.policy.PolicyService') as mock_service:
            mock_service.return_value.jurisdiction = "federal"
            mock_service.return_value.rules = self._get_federal_rules()
            return mock_service.return_value
    
    @pytest.fixture
    def state_california_policy_service(self):
        """Create California state jurisdiction policy service."""
        with patch('services.shared.interfaces.policy.PolicyService') as mock_service:
            mock_service.return_value.jurisdiction = "california"
            mock_service.return_value.rules = self._get_california_rules()
            return mock_service.return_value
    
    @pytest.fixture
    def test_case_demonstrative(self):
        """Create test case in demonstrative mode."""
        from services.shared.models.case import CaseMetadata
        metadata = CaseMetadata(
            case_number="24-cv-001",
            title="Test Demonstrative Case",
            case_type=CaseType.CIVIL,
            jurisdiction="federal",
            court="US District Court"
        )
        return Case(
            id="case-001",
            metadata=metadata
        )
    
    @pytest.fixture
    def test_case_sandbox(self):
        """Create test case in sandbox mode."""
        from services.shared.models.case import CaseMetadata
        metadata = CaseMetadata(
            case_number="24-cr-001",
            title="Test Sandbox Case",
            case_type=CaseType.CRIMINAL,
            jurisdiction="federal",
            court="US District Court"
        )
        return Case(
            id="case-002",
            metadata=metadata
        )
    
    @pytest.fixture
    def test_evidence(self):
        """Create test evidence."""
        return Evidence(
            id="evid-001",
            case_id="case-001",
            filename="test_document.pdf",
            evidence_type=EvidenceType.DOCUMENT,
            file_path="/path/to/test_document.pdf",
            sha256_hash="abcd1234",
            chain_of_custody=[
                {"timestamp": "2024-01-01T10:00:00Z", "custodian": "Officer Smith", "action": "collected"},
                {"timestamp": "2024-01-01T11:00:00Z", "custodian": "Detective Jones", "action": "transferred"}
            ]
        )
    
    @pytest.fixture
    def test_storyboard(self):
        """Create test storyboard."""
        return Storyboard(
            id="story-001",
            case_id="case-001",
            title="Test Storyboard",
            content="Scene 1: Evidence presentation\nScene 2: Witness testimony",
            scenes=[
                {
                    "scene_id": "scene-001",
                    "title": "Evidence Presentation",
                    "duration_seconds": 30.0,
                    "evidence_anchors": [
                        {
                            "evidence_id": "evid-001",
                            "timestamp": 10.0,
                            "confidence": 0.95
                        }
                    ],
                    "camera_config": {
                        "position": [0, 0, 5],
                        "rotation": [0, 0, 0]
                    }
                }
            ]
        )
    
    def _get_federal_rules(self) -> Dict[str, Any]:
        """Get federal jurisdiction rules."""
        return {
            "evidence_requirements": {
                "chain_of_custody": True,
                "authentication": True,
                "best_evidence_rule": True,
                "hearsay_exceptions": ["business_records", "public_records"]
            },
            "demonstrative_standards": {
                "accuracy_required": 0.95,
                "dispute_marking": True,
                "uncertainty_display": True,
                "neutral_rendering": True
            },
            "sandbox_restrictions": {
                "allow_ai_assistance": True,
                "allow_speculation": True,
                "allow_cinematic_rendering": True,
                "require_disclaimers": True
            },
            "render_requirements": {
                "deterministic": True,
                "audit_trail": True,
                "watermark_required": True,
                "export_controls": True
            }
        }
    
    def _get_california_rules(self) -> Dict[str, Any]:
        """Get California state jurisdiction rules."""
        return {
            "evidence_requirements": {
                "chain_of_custody": True,
                "authentication": True,
                "best_evidence_rule": True,
                "california_evidence_code": True,
                "hearsay_exceptions": ["business_records", "public_records", "dying_declarations"]
            },
            "demonstrative_standards": {
                "accuracy_required": 0.98,  # Higher standard than federal
                "dispute_marking": True,
                "uncertainty_display": True,
                "neutral_rendering": True,
                "california_specific_requirements": True
            },
            "sandbox_restrictions": {
                "allow_ai_assistance": True,
                "allow_speculation": True,
                "allow_cinematic_rendering": True,
                "require_disclaimers": True,
                "privacy_protections": True  # California-specific
            },
            "render_requirements": {
                "deterministic": True,
                "audit_trail": True,
                "watermark_required": True,
                "export_controls": True,
                "california_compliance": True
            }
        }
    
    @pytest.mark.asyncio
    async def test_federal_jurisdiction_rules(self, federal_policy_service, test_case_demonstrative, test_evidence):
        """Test federal jurisdiction policy compliance."""
        # Test evidence compliance
        violations = await federal_policy_service.validate_evidence(test_evidence)
        
        # Should have no violations for properly formatted evidence
        assert len(violations) == 0
        
        # Test case compliance
        case_violations = await federal_policy_service.validate_case(test_case_demonstrative)
        assert len(case_violations) == 0
        
        # Test jurisdiction-specific rules
        rules = federal_policy_service.get_jurisdiction_rules("federal")
        assert rules["evidence_requirements"]["chain_of_custody"] is True
        assert rules["demonstrative_standards"]["accuracy_required"] == 0.95
    
    @pytest.mark.asyncio
    async def test_california_state_rules(self, state_california_policy_service, test_case_demonstrative, test_evidence):
        """Test California state jurisdiction policy compliance."""
        # Test stricter California standards
        violations = await state_california_policy_service.validate_evidence(test_evidence)
        assert len(violations) == 0
        
        # Test California-specific requirements
        rules = state_california_policy_service.get_jurisdiction_rules("california")
        assert rules["demonstrative_standards"]["accuracy_required"] == 0.98  # Stricter than federal
        assert rules["sandbox_restrictions"]["privacy_protections"] is True  # California-specific
    
    @pytest.mark.asyncio
    async def test_validation_catches_violations(self, federal_policy_service):
        """Test that validation catches policy violations."""
        # Create evidence with missing chain of custody
        from services.shared.models.evidence import EvidenceMetadata
        metadata = EvidenceMetadata(
            filename="invalid_document.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="invalid123",
            uploaded_by="test_user"
        )
        invalid_evidence = Evidence(
            id="evid-invalid",
            case_id="case-001",
            evidence_type=EvidenceType.DOCUMENT,
            metadata=metadata,
            chain_of_custody=[]  # Missing chain of custody
        )
        
        violations = federal_policy_service.validate_evidence(invalid_evidence)
        
        # Should catch chain of custody violation
        assert len(violations) > 0
        assert any(v.rule_id == "chain_of_custody_required" for v in violations)
        
        # Test evidence with insufficient accuracy
        low_accuracy_evidence = Evidence(
            id="evid-low-accuracy",
            case_id="case-001",
            filename="low_accuracy.pdf",
            evidence_type=EvidenceType.DOCUMENT,
            file_path="/path/to/low_accuracy.pdf",
            sha256_hash="lowacc123",
            chain_of_custody=[{"timestamp": "2024-01-01T10:00:00Z", "custodian": "Officer Smith", "action": "collected"}],
            confidence_score=0.90  # Below 0.95 requirement
        )
        
        violations = await federal_policy_service.validate_evidence(low_accuracy_evidence)
        assert any(v.rule_id == "insufficient_accuracy" for v in violations)
    
    @pytest.mark.asyncio
    async def test_edge_cases_and_boundaries(self, federal_policy_service):
        """Test policy validation with edge cases and boundary conditions."""
        # Test evidence at exactly the accuracy threshold
        from services.shared.models.evidence import EvidenceMetadata
        metadata = EvidenceMetadata(
            filename="threshold.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="threshold123",
            uploaded_by="test_user"
        )
        threshold_evidence = Evidence(
            id="evid-threshold",
            case_id="case-001",
            evidence_type=EvidenceType.DOCUMENT,
            metadata=metadata,
            chain_of_custody=[{"timestamp": "2024-01-01T10:00:00Z", "custodian": "Officer Smith", "action": "collected"}],                                                                                              
        )
        
        violations = federal_policy_service.validate_evidence(threshold_evidence)
        assert len(violations) == 0  # Should pass at threshold
        
        # Test evidence just below threshold
        below_threshold_evidence = threshold_evidence.copy()
        below_threshold_evidence.confidence_score = 0.949  # Just below threshold
        
        violations = await federal_policy_service.validate_evidence(below_threshold_evidence)
        assert any(v.rule_id == "insufficient_accuracy" for v in violations)
        
        # Test with maximum allowed duration
        max_duration_storyboard = Storyboard(
            id="story-max-duration",
            case_id="case-001",
            title="Max Duration Storyboard",
            content="Long storyboard content",
            scenes=[{
                "scene_id": "scene-long",
                "title": "Long Scene",
                "duration_seconds": 300.0,  # 5 minutes - should be allowed
                "evidence_anchors": []
            }]
        )
        
        violations = await federal_policy_service.validate_storyboard(max_duration_storyboard)
        assert len(violations) == 0
        
        # Test with excessive duration
        excessive_duration_storyboard = max_duration_storyboard.copy()
        excessive_duration_storyboard.scenes[0]["duration_seconds"] = 3600.0  # 1 hour - should be flagged
        
        violations = await federal_policy_service.validate_storyboard(excessive_duration_storyboard)
        assert any(v.rule_id == "excessive_duration" for v in violations)
    
    @pytest.mark.asyncio
    async def test_remediation_suggestions(self, federal_policy_service):
        """Test that policy violations include helpful remediation suggestions."""
        # Create evidence with multiple violations
        from services.shared.models.evidence import EvidenceMetadata
        metadata = EvidenceMetadata(
            filename="problematic.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="problem123",
            uploaded_by="test_user",
            tags={"authentication": "missing"}  # Missing authentication
        )
        problematic_evidence = Evidence(
            id="evid-problematic",
            case_id="case-001",
            evidence_type=EvidenceType.DOCUMENT,
            metadata=metadata,
            chain_of_custody=[],  # Missing
        )
        
        violations = federal_policy_service.validate_evidence(problematic_evidence)
        
        # Check that violations include remediation suggestions
        for violation in violations:
            assert violation.remediation_suggestion is not None
            assert len(violation.remediation_suggestion) > 0
            
            # Verify specific suggestions
            if violation.rule_id == "chain_of_custody_required":
                assert "chain of custody" in violation.remediation_suggestion.lower()
            elif violation.rule_id == "insufficient_accuracy":
                assert "improve accuracy" in violation.remediation_suggestion.lower()
            elif violation.rule_id == "authentication_required":
                assert "authentication" in violation.remediation_suggestion.lower()
    
    @pytest.mark.asyncio
    async def test_policy_versioning(self, federal_policy_service):
        """Test policy versioning and updates."""
        # Get current policy version
        current_version = federal_policy_service.get_policy_version()
        assert current_version is not None
        assert isinstance(current_version, str)
        
        # Test policy update detection
        has_updates = await federal_policy_service.check_for_updates()
        assert isinstance(has_updates, bool)
        
        # Test policy migration
        if has_updates:
            migration_result = await federal_policy_service.migrate_policies()
            assert migration_result.success is True
            assert migration_result.updated_rules is not None
        
        # Test backward compatibility
        old_case = Case(
            id="old-case",
            title="Old Case",
            jurisdiction="federal",
            case_type="civil",
            mode=CaseMode.DEMONSTRATIVE,
            policy_version="1.0.0"  # Older version
        )
        
        compatibility_result = await federal_policy_service.check_compatibility(old_case)
        assert compatibility_result.is_compatible is True
    
    @pytest.mark.asyncio
    async def test_sandbox_mode_restrictions(self, federal_policy_service, test_case_sandbox):
        """Test sandbox mode specific restrictions and allowances."""
        # Test sandbox mode validation
        violations = await federal_policy_service.validate_case(test_case_sandbox)
        
        # Sandbox mode should have different validation rules
        sandbox_rules = federal_policy_service.get_mode_rules(CaseMode.SANDBOX)
        assert sandbox_rules["allow_ai_assistance"] is True
        assert sandbox_rules["allow_speculation"] is True
        assert sandbox_rules["allow_cinematic_rendering"] is True
        
        # Test render job in sandbox mode
        sandbox_render = RenderJob(
            id="render-sandbox",
            case_id=test_case_sandbox.id,
            storyboard_id="story-sandbox",
            profile="cinematic",  # Should be allowed in sandbox
            mode=CaseMode.SANDBOX
        )
        
        render_violations = await federal_policy_service.validate_render_job(sandbox_render)
        assert len(render_violations) == 0  # Cinematic should be allowed in sandbox
        
        # Test render job in demonstrative mode
        demonstrative_render = RenderJob(
            id="render-demo",
            case_id="case-001",
            storyboard_id="story-demo",
            profile="cinematic",  # Should be restricted in demonstrative
            mode=CaseMode.DEMONSTRATIVE
        )
        
        render_violations = await federal_policy_service.validate_render_job(demonstrative_render)
        assert any(v.rule_id == "cinematic_not_allowed_demonstrative" for v in render_violations)
    
    @pytest.mark.asyncio
    async def test_cross_jurisdiction_compliance(self):
        """Test compliance across multiple jurisdictions."""
        jurisdictions = ["federal", "california", "texas", "new_york"]
        
        for jurisdiction in jurisdictions:
            with patch('services.shared.interfaces.policy.PolicyService') as mock_service:
                mock_service.return_value.jurisdiction = jurisdiction
                mock_service.return_value.rules = self._get_jurisdiction_rules(jurisdiction)
                
                policy_service = mock_service.return_value
                
                # Test basic compliance for each jurisdiction
                from services.shared.models.evidence import EvidenceMetadata
                metadata = EvidenceMetadata(
                    filename="test.pdf",
                    content_type="application/pdf",
                    size_bytes=1024,
                    checksum="test123",
                    uploaded_by="test_user"
                )
                test_evidence = Evidence(
                    id=f"evid-{jurisdiction}",
                    case_id="case-001",
                    evidence_type=EvidenceType.DOCUMENT,
                    metadata=metadata,
                    chain_of_custody=[{"timestamp": "2024-01-01T10:00:00Z", "custodian": "Officer Smith", "action": "collected"}]                                                                                       
                )
                
                violations = policy_service.validate_evidence(test_evidence)
                
                # Each jurisdiction should have its own validation rules
                rules = policy_service.get_jurisdiction_rules(jurisdiction)
                assert rules is not None
                assert "evidence_requirements" in rules
    
    def _get_jurisdiction_rules(self, jurisdiction: str) -> Dict[str, Any]:
        """Get rules for a specific jurisdiction."""
        base_rules = {
            "evidence_requirements": {
                "chain_of_custody": True,
                "authentication": True,
                "best_evidence_rule": True
            },
            "demonstrative_standards": {
                "accuracy_required": 0.95,
                "dispute_marking": True,
                "uncertainty_display": True
            },
            "sandbox_restrictions": {
                "allow_ai_assistance": True,
                "allow_speculation": True,
                "require_disclaimers": True
            }
        }
        
        # Add jurisdiction-specific rules
        if jurisdiction == "california":
            base_rules["demonstrative_standards"]["accuracy_required"] = 0.98
            base_rules["sandbox_restrictions"]["privacy_protections"] = True
        elif jurisdiction == "texas":
            base_rules["evidence_requirements"]["texas_rules"] = True
        elif jurisdiction == "new_york":
            base_rules["evidence_requirements"]["new_york_evidence_code"] = True
        
        return base_rules
    
    @pytest.mark.asyncio
    async def test_audit_trail_compliance(self, federal_policy_service):
        """Test audit trail requirements and compliance."""
        # Test case creation audit trail
        from services.shared.models.case import CaseMetadata
        metadata = CaseMetadata(
            case_number="audit-case-001",
            title="Audit Test Case",
            case_type=CaseType.CIVIL,
            jurisdiction="federal",
            court="US District Court"
        )
        test_case = Case(
            id="audit-case-001",
            metadata=metadata
        )
        
        audit_events = await federal_policy_service.validate_audit_trail(test_case.id)
        
        # Should have creation event
        assert len(audit_events) > 0
        assert any(event.event_type == "case_created" for event in audit_events)
        
        # Test evidence processing audit trail
        test_evidence = Evidence(
            id="audit-evid-001",
            case_id=test_case.id,
            filename="audit_test.pdf",
            evidence_type=EvidenceType.DOCUMENT,
            file_path="/path/to/audit_test.pdf",
            sha256_hash="audit123",
            chain_of_custody=[{"timestamp": "2024-01-01T10:00:00Z", "custodian": "Officer Smith", "action": "collected"}]
        )
        
        evidence_audit = await federal_policy_service.validate_audit_trail(test_evidence.id)
        
        # Should have evidence processing events
        assert len(evidence_audit) > 0
        assert any(event.event_type == "evidence_processed" for event in evidence_audit)
        
        # Test audit trail integrity
        for event in evidence_audit:
            assert event.timestamp is not None
            assert event.user_id is not None
            assert event.event_type is not None
            assert event.checksum is not None  # For tamper detection


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
