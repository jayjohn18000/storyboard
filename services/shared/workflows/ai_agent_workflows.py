"""Temporal workflows for AI agent orchestration.

This module defines Temporal workflows that orchestrate the AI agents
for evidence intake/triage and timeline reconciliation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from temporalio import workflow
from temporalio.common import RetryPolicy

from services.shared.models.case import Case
from services.shared.models.evidence import Evidence
from services.shared.models.storyboard import Storyboard
from services.shared.security.audit import AuditLogger, AuditEventType


@dataclass
class EvidenceIntakeRequest:
    """Request for evidence intake processing."""
    evidence_id: str
    case_id: str
    filename: str
    evidence_type: str
    file_path: str
    sha256_hash: str
    case_mode: str
    available_cases: List[Dict[str, Any]]


@dataclass
class TimelineReconciliationRequest:
    """Request for timeline reconciliation."""
    storyboard_id: str
    case_id: str
    scenes: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    case_mode: str


@dataclass
class AIAgentResult:
    """Result from AI agent processing."""
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None
    processing_time: float = 0.0
    confidence_score: float = 0.0


@workflow.defn
class EvidenceIntakeWorkflow:
    """Workflow for evidence intake and triage processing."""
    
    def __init__(self):
        self.logger = workflow.logger()
    
    @workflow.run
    async def run(self, request: EvidenceIntakeRequest) -> AIAgentResult:
        """Run the evidence intake workflow."""
        
        self.logger.info(f"Starting evidence intake workflow for {request.evidence_id}")
        
        try:
            # Create evidence object
            evidence = Evidence(
                id=request.evidence_id,
                case_id=request.case_id,
                filename=request.filename,
                evidence_type=request.evidence_type,
                file_path=request.file_path,
                sha256_hash=request.sha256_hash
            )
            
            # Create case objects
            cases = []
            for case_data in request.available_cases:
                case = Case(
                    id=case_data["id"],
                    title=case_data["title"],
                    case_type=case_data["case_type"],
                    description=case_data.get("description", "")
                )
                cases.append(case)
            
            # Execute evidence intake activity
            intake_result = await workflow.execute_activity(
                process_evidence_intake,
                args=[evidence, request.case_mode, cases],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3
                )
            )
            
            # Log successful processing
            await workflow.execute_activity(
                log_ai_processing_event,
                args=[
                    "evidence_intake_completed",
                    request.evidence_id,
                    intake_result.get("ai_confidence", 0.0),
                    True
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return AIAgentResult(
                success=True,
                result=intake_result,
                processing_time=intake_result.get("processing_time", 0.0),
                confidence_score=intake_result.get("ai_confidence", 0.0)
            )
            
        except Exception as e:
            self.logger.error(f"Evidence intake workflow failed: {e}")
            
            # Log error
            await workflow.execute_activity(
                log_ai_processing_event,
                args=[
                    "evidence_intake_failed",
                    request.evidence_id,
                    0.0,
                    False,
                    str(e)
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return AIAgentResult(
                success=False,
                result={},
                error=str(e)
            )


@workflow.defn
class TimelineReconciliationWorkflow:
    """Workflow for timeline reconciliation processing."""
    
    def __init__(self):
        self.logger = workflow.logger()
    
    @workflow.run
    async def run(self, request: TimelineReconciliationRequest) -> AIAgentResult:
        """Run the timeline reconciliation workflow."""
        
        self.logger.info(f"Starting timeline reconciliation workflow for {request.storyboard_id}")
        
        try:
            # Create storyboard object
            scenes = []
            for scene_data in request.scenes:
                scene = {
                    "scene_id": scene_data["scene_id"],
                    "title": scene_data["title"],
                    "start_time": scene_data["start_time"],
                    "end_time": scene_data["end_time"],
                    "duration_seconds": scene_data["duration_seconds"],
                    "evidence_anchors": scene_data.get("evidence_anchors", [])
                }
                scenes.append(scene)
            
            storyboard = Storyboard(
                id=request.storyboard_id,
                case_id=request.case_id,
                title="Timeline Reconciliation",
                content="",
                scenes=scenes
            )
            
            # Create evidence objects
            evidence = []
            for evidence_data in request.evidence:
                evid = Evidence(
                    id=evidence_data["id"],
                    case_id=evidence_data["case_id"],
                    filename=evidence_data["filename"],
                    evidence_type=evidence_data["evidence_type"],
                    file_path=evidence_data["file_path"],
                    sha256_hash=evidence_data["sha256_hash"]
                )
                evidence.append(evid)
            
            # Execute timeline reconciliation activity
            reconciliation_result = await workflow.execute_activity(
                process_timeline_reconciliation,
                args=[storyboard, evidence, request.case_mode],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3
                )
            )
            
            # Log successful processing
            await workflow.execute_activity(
                log_ai_processing_event,
                args=[
                    "timeline_reconciliation_completed",
                    request.storyboard_id,
                    reconciliation_result.get("overall_confidence", 0.0),
                    True
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return AIAgentResult(
                success=True,
                result=reconciliation_result,
                processing_time=reconciliation_result.get("processing_time", 0.0),
                confidence_score=reconciliation_result.get("overall_confidence", 0.0)
            )
            
        except Exception as e:
            self.logger.error(f"Timeline reconciliation workflow failed: {e}")
            
            # Log error
            await workflow.execute_activity(
                log_ai_processing_event,
                args=[
                    "timeline_reconciliation_failed",
                    request.storyboard_id,
                    0.0,
                    False,
                    str(e)
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return AIAgentResult(
                success=False,
                result={},
                error=str(e)
            )


@workflow.defn
class AIAgentOrchestrationWorkflow:
    """Master workflow that orchestrates multiple AI agents."""
    
    def __init__(self):
        self.logger = workflow.logger()
    
    @workflow.run
    async def run(self, case_id: str, evidence_ids: List[str], 
                 storyboard_id: Optional[str] = None) -> Dict[str, Any]:
        """Run the AI agent orchestration workflow."""
        
        self.logger.info(f"Starting AI agent orchestration for case {case_id}")
        
        results = {
            "case_id": case_id,
            "evidence_intake_results": [],
            "timeline_reconciliation_result": None,
            "overall_success": True,
            "errors": []
        }
        
        try:
            # Process evidence intake for each evidence item
            for evidence_id in evidence_ids:
                try:
                    # Get evidence details (this would be fetched from database)
                    evidence_request = await workflow.execute_activity(
                        get_evidence_details,
                        args=[evidence_id],
                        start_to_close_timeout=timedelta(seconds=30)
                    )
                    
                    # Run evidence intake workflow
                    intake_workflow_result = await workflow.execute_child_workflow(
                        EvidenceIntakeWorkflow.run,
                        args=[evidence_request],
                        id=f"evidence-intake-{evidence_id}",
                        task_queue="ai-agent-queue"
                    )
                    
                    results["evidence_intake_results"].append({
                        "evidence_id": evidence_id,
                        "result": intake_workflow_result
                    })
                    
                except Exception as e:
                    self.logger.error(f"Evidence intake failed for {evidence_id}: {e}")
                    results["errors"].append(f"Evidence intake failed for {evidence_id}: {str(e)}")
                    results["overall_success"] = False
            
            # Process timeline reconciliation if storyboard exists
            if storyboard_id:
                try:
                    # Get storyboard details
                    reconciliation_request = await workflow.execute_activity(
                        get_storyboard_details,
                        args=[storyboard_id],
                        start_to_close_timeout=timedelta(seconds=30)
                    )
                    
                    # Run timeline reconciliation workflow
                    reconciliation_workflow_result = await workflow.execute_child_workflow(
                        TimelineReconciliationWorkflow.run,
                        args=[reconciliation_request],
                        id=f"timeline-reconciliation-{storyboard_id}",
                        task_queue="ai-agent-queue"
                    )
                    
                    results["timeline_reconciliation_result"] = reconciliation_workflow_result
                    
                except Exception as e:
                    self.logger.error(f"Timeline reconciliation failed for {storyboard_id}: {e}")
                    results["errors"].append(f"Timeline reconciliation failed for {storyboard_id}: {str(e)}")
                    results["overall_success"] = False
            
            # Generate summary report
            summary_report = await workflow.execute_activity(
                generate_ai_summary_report,
                args=[results],
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            results["summary_report"] = summary_report
            
            return results
            
        except Exception as e:
            self.logger.error(f"AI agent orchestration workflow failed: {e}")
            results["overall_success"] = False
            results["errors"].append(f"Orchestration failed: {str(e)}")
            return results


# Activity functions
@workflow.activity
async def process_evidence_intake(evidence: Evidence, case_mode: str, 
                                available_cases: List[Case]) -> Dict[str, Any]:
    """Activity to process evidence intake using AI agent."""
    
    from agents.intake_triage.main import IntakeTriageAgent
    from services.shared.interfaces.storage import StorageInterface
    from services.shared.security.audit import AuditLogger
    
    # Initialize services (in real implementation, these would be injected)
    storage_service = None  # StorageInterface implementation
    audit_logger = None     # AuditLogger implementation
    
    # Create agent
    agent = IntakeTriageAgent(storage_service, audit_logger)
    
    # Process evidence intake
    start_time = datetime.utcnow()
    result = await agent.process_evidence_intake(evidence, case_mode, available_cases)
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    
    result["processing_time"] = processing_time
    return result


@workflow.activity
async def process_timeline_reconciliation(storyboard: Storyboard, evidence: List[Evidence], 
                                        case_mode: str) -> Dict[str, Any]:
    """Activity to process timeline reconciliation using AI agent."""
    
    from agents.timeline_reconciliation.main import TimelineReconciliationAgent
    from services.shared.security.audit import AuditLogger
    
    # Initialize services (in real implementation, these would be injected)
    audit_logger = None  # AuditLogger implementation
    
    # Create agent
    agent = TimelineReconciliationAgent(audit_logger)
    
    # Process timeline reconciliation
    start_time = datetime.utcnow()
    result = await agent.reconcile_timeline(storyboard, evidence, case_mode)
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Convert result to dict
    result_dict = {
        "storyboard_id": result.storyboard_id,
        "total_conflicts": result.total_conflicts,
        "conflicts_by_type": {k.value: v for k, v in result.conflicts_by_type.items()},
        "missing_events": [
            {
                "event_id": event.event_id,
                "title": event.title,
                "description": event.description,
                "suggested_start_time": event.suggested_start_time,
                "suggested_duration": event.suggested_duration,
                "supporting_evidence": event.supporting_evidence,
                "confidence_score": event.confidence_score,
                "reasoning": event.reasoning
            }
            for event in result.missing_events
        ],
        "alternative_sequences": result.alternative_sequences,
        "overall_confidence": result.overall_confidence,
        "recommendations": result.recommendations,
        "analysis_timestamp": result.analysis_timestamp.isoformat(),
        "processing_time": processing_time
    }
    
    return result_dict


@workflow.activity
async def log_ai_processing_event(action: str, entity_id: str, confidence: float, 
                                success: bool, error: Optional[str] = None) -> None:
    """Activity to log AI processing events."""
    
    from services.shared.security.audit import AuditLogger, AuditEventType
    
    # Initialize audit logger (in real implementation, this would be injected)
    audit_logger = None  # AuditLogger implementation
    
    if audit_logger:
        audit_logger.log_event(
            AuditEventType.SYSTEM_ERROR,  # Using system event for AI processing
            {
                "action": action,
                "entity_id": entity_id,
                "ai_confidence": confidence,
                "success": success,
                "error": error
            },
            case_id=entity_id.split('-')[0] if '-' in entity_id else None
        )


@workflow.activity
async def get_evidence_details(evidence_id: str) -> EvidenceIntakeRequest:
    """Activity to get evidence details from database."""
    
    # This would fetch evidence details from the database
    # For now, return a mock request
    return EvidenceIntakeRequest(
        evidence_id=evidence_id,
        case_id="case-001",
        filename="sample_evidence.pdf",
        evidence_type="DOCUMENT",
        file_path="/path/to/evidence.pdf",
        sha256_hash="abc123",
        case_mode="SANDBOX",
        available_cases=[]
    )


@workflow.activity
async def get_storyboard_details(storyboard_id: str) -> TimelineReconciliationRequest:
    """Activity to get storyboard details from database."""
    
    # This would fetch storyboard details from the database
    # For now, return a mock request
    return TimelineReconciliationRequest(
        storyboard_id=storyboard_id,
        case_id="case-001",
        scenes=[],
        evidence=[],
        case_mode="SANDBOX"
    )


@workflow.activity
async def generate_ai_summary_report(results: Dict[str, Any]) -> Dict[str, Any]:
    """Activity to generate a summary report of AI processing results."""
    
    summary = {
        "total_evidence_processed": len(results["evidence_intake_results"]),
        "successful_evidence_processing": len([r for r in results["evidence_intake_results"] if r["result"].success]),
        "timeline_reconciliation_performed": results["timeline_reconciliation_result"] is not None,
        "overall_success": results["overall_success"],
        "total_errors": len(results["errors"]),
        "average_confidence": 0.0,
        "recommendations": []
    }
    
    # Calculate average confidence
    confidence_scores = []
    for evidence_result in results["evidence_intake_results"]:
        if evidence_result["result"].success:
            confidence_scores.append(evidence_result["result"].confidence_score)
    
    if results["timeline_reconciliation_result"] and results["timeline_reconciliation_result"].success:
        confidence_scores.append(results["timeline_reconciliation_result"].confidence_score)
    
    if confidence_scores:
        summary["average_confidence"] = sum(confidence_scores) / len(confidence_scores)
    
    # Generate recommendations
    if not results["overall_success"]:
        summary["recommendations"].append("Review and fix processing errors")
    
    if summary["average_confidence"] < 0.7:
        summary["recommendations"].append("AI confidence is low - consider manual review")
    
    if results["timeline_reconciliation_result"] and results["timeline_reconciliation_result"].success:
        reconciliation_data = results["timeline_reconciliation_result"].result
        if reconciliation_data.get("total_conflicts", 0) > 0:
            summary["recommendations"].append("Address timeline conflicts identified by AI")
    
    return summary
