"""Temporal worker for AI agent orchestration.

This module defines the Temporal worker that executes AI agent workflows
and activities for evidence intake/triage and timeline reconciliation.
"""

import asyncio
import logging
import os
from typing import Optional

from temporalio.client import Client
from temporalio.worker import Worker

from services.shared.workflows.ai_agent_workflows import (
    EvidenceIntakeWorkflow,
    TimelineReconciliationWorkflow,
    AIAgentOrchestrationWorkflow,
    process_evidence_intake,
    process_timeline_reconciliation,
    log_ai_processing_event,
    get_evidence_details,
    get_storyboard_details,
    generate_ai_summary_report
)


class AIAgentWorker:
    """Temporal worker for AI agent orchestration."""
    
    def __init__(self, temporal_host: str = "localhost:7233", 
                 temporal_namespace: str = "legal-sim",
                 task_queue: str = "ai-agent-queue"):
        self.temporal_host = temporal_host
        self.temporal_namespace = temporal_namespace
        self.task_queue = task_queue
        self.client: Optional[Client] = None
        self.worker: Optional[Worker] = None
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the Temporal worker."""
        
        try:
            # Create Temporal client
            self.client = await Client.connect(
                self.temporal_host,
                namespace=self.temporal_namespace
            )
            
            self.logger.info(f"Connected to Temporal at {self.temporal_host}")
            
            # Create worker
            self.worker = Worker(
                self.client,
                task_queue=self.task_queue,
                workflows=[
                    EvidenceIntakeWorkflow,
                    TimelineReconciliationWorkflow,
                    AIAgentOrchestrationWorkflow
                ],
                activities=[
                    process_evidence_intake,
                    process_timeline_reconciliation,
                    log_ai_processing_event,
                    get_evidence_details,
                    get_storyboard_details,
                    generate_ai_summary_report
                ]
            )
            
            self.logger.info(f"Starting AI agent worker on task queue: {self.task_queue}")
            
            # Start worker
            await self.worker.run()
            
        except Exception as e:
            self.logger.error(f"Failed to start AI agent worker: {e}")
            raise
    
    async def stop(self):
        """Stop the Temporal worker."""
        
        if self.worker:
            self.logger.info("Stopping AI agent worker")
            self.worker.shutdown()
        
        if self.client:
            await self.client.close()
    
    async def health_check(self) -> bool:
        """Check if the worker is healthy."""
        
        try:
            if self.client:
                # Try to get workflow info to check connection
                await self.client.list_workflows()
                return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
        
        return False


class AIAgentClient:
    """Client for starting AI agent workflows."""
    
    def __init__(self, temporal_host: str = "localhost:7233", 
                 temporal_namespace: str = "legal-sim"):
        self.temporal_host = temporal_host
        self.temporal_namespace = temporal_namespace
        self.client: Optional[Client] = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self):
        """Connect to Temporal."""
        
        try:
            self.client = await Client.connect(
                self.temporal_host,
                namespace=self.temporal_namespace
            )
            
            self.logger.info(f"Connected to Temporal at {self.temporal_host}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Temporal: {e}")
            raise
    
    async def start_evidence_intake_workflow(self, evidence_id: str, case_id: str,
                                           filename: str, evidence_type: str,
                                           file_path: str, sha256_hash: str,
                                           case_mode: str = "SANDBOX",
                                           available_cases: list = None) -> str:
        """Start evidence intake workflow."""
        
        if not self.client:
            await self.connect()
        
        from services.shared.workflows.ai_agent_workflows import EvidenceIntakeRequest
        
        request = EvidenceIntakeRequest(
            evidence_id=evidence_id,
            case_id=case_id,
            filename=filename,
            evidence_type=evidence_type,
            file_path=file_path,
            sha256_hash=sha256_hash,
            case_mode=case_mode,
            available_cases=available_cases or []
        )
        
        workflow_id = f"evidence-intake-{evidence_id}"
        
        handle = await self.client.start_workflow(
            EvidenceIntakeWorkflow.run,
            args=[request],
            id=workflow_id,
            task_queue="ai-agent-queue"
        )
        
        self.logger.info(f"Started evidence intake workflow: {workflow_id}")
        return workflow_id
    
    async def start_timeline_reconciliation_workflow(self, storyboard_id: str,
                                                    case_id: str, scenes: list,
                                                    evidence: list,
                                                    case_mode: str = "SANDBOX") -> str:
        """Start timeline reconciliation workflow."""
        
        if not self.client:
            await self.connect()
        
        from services.shared.workflows.ai_agent_workflows import TimelineReconciliationRequest
        
        request = TimelineReconciliationRequest(
            storyboard_id=storyboard_id,
            case_id=case_id,
            scenes=scenes,
            evidence=evidence,
            case_mode=case_mode
        )
        
        workflow_id = f"timeline-reconciliation-{storyboard_id}"
        
        handle = await self.client.start_workflow(
            TimelineReconciliationWorkflow.run,
            args=[request],
            id=workflow_id,
            task_queue="ai-agent-queue"
        )
        
        self.logger.info(f"Started timeline reconciliation workflow: {workflow_id}")
        return workflow_id
    
    async def start_ai_agent_orchestration_workflow(self, case_id: str,
                                                 evidence_ids: list,
                                                 storyboard_id: str = None) -> str:
        """Start AI agent orchestration workflow."""
        
        if not self.client:
            await self.connect()
        
        workflow_id = f"ai-orchestration-{case_id}"
        
        handle = await self.client.start_workflow(
            AIAgentOrchestrationWorkflow.run,
            args=[case_id, evidence_ids, storyboard_id],
            id=workflow_id,
            task_queue="ai-agent-queue"
        )
        
        self.logger.info(f"Started AI agent orchestration workflow: {workflow_id}")
        return workflow_id
    
    async def get_workflow_result(self, workflow_id: str, timeout: int = 300):
        """Get workflow result."""
        
        if not self.client:
            await self.connect()
        
        handle = self.client.get_workflow_handle(workflow_id)
        result = await handle.result(timeout=timeout)
        
        return result
    
    async def close(self):
        """Close the client connection."""
        
        if self.client:
            await self.client.close()


async def main():
    """Main function to run the AI agent worker."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "legal-sim")
    task_queue = os.getenv("AI_AGENT_TASK_QUEUE", "ai-agent-queue")
    
    # Create and start worker
    worker = AIAgentWorker(
        temporal_host=temporal_host,
        temporal_namespace=temporal_namespace,
        task_queue=task_queue
    )
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logging.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logging.error(f"Worker failed: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
