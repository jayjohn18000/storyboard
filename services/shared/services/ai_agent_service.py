"""AI Agent service for integrating Temporal workflows with the API Gateway.

This service provides a high-level interface for triggering AI agent workflows
from the API Gateway endpoints.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.shared.workers.ai_agent_worker import AIAgentClient


class AIAgentService:
    """Service for managing AI agent workflows."""
    
    def __init__(self, temporal_host: str = "localhost:7233",
                 temporal_namespace: str = "legal-sim"):
        self.temporal_host = temporal_host
        self.temporal_namespace = temporal_namespace
        self.client: Optional[AIAgentClient] = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize the AI agent service."""
        
        try:
            self.client = AIAgentClient(
                temporal_host=self.temporal_host,
                temporal_namespace=self.temporal_namespace
            )
            await self.client.connect()
            self.logger.info("AI Agent service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Agent service: {e}")
            raise
    
    async def process_evidence_intake(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process evidence intake using AI agent."""
        
        try:
            # Extract required fields
            evidence_id = evidence_data.get("id")
            case_id = evidence_data.get("case_id")
            filename = evidence_data.get("filename")
            evidence_type = evidence_data.get("evidence_type")
            file_path = evidence_data.get("file_path")
            sha256_hash = evidence_data.get("sha256_hash")
            case_mode = evidence_data.get("case_mode", "SANDBOX")
            available_cases = evidence_data.get("available_cases", [])
            
            if not all([evidence_id, case_id, filename, evidence_type, file_path, sha256_hash]):
                raise ValueError("Missing required fields for evidence intake")
            
            # Start evidence intake workflow
            workflow_id = await self.client.start_evidence_intake_workflow(
                evidence_id=evidence_id,
                case_id=case_id,
                filename=filename,
                evidence_type=evidence_type,
                file_path=file_path,
                sha256_hash=sha256_hash,
                case_mode=case_mode,
                available_cases=available_cases
            )
            
            self.logger.info(f"Started evidence intake workflow: {workflow_id}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "message": "Evidence intake workflow started",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing evidence intake: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def process_timeline_reconciliation(self, storyboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process timeline reconciliation using AI agent."""
        
        try:
            # Extract required fields
            storyboard_id = storyboard_data.get("id")
            case_id = storyboard_data.get("case_id")
            scenes = storyboard_data.get("scenes", [])
            evidence = storyboard_data.get("evidence", [])
            case_mode = storyboard_data.get("case_mode", "SANDBOX")
            
            if not all([storyboard_id, case_id]):
                raise ValueError("Missing required fields for timeline reconciliation")
            
            # Start timeline reconciliation workflow
            workflow_id = await self.client.start_timeline_reconciliation_workflow(
                storyboard_id=storyboard_id,
                case_id=case_id,
                scenes=scenes,
                evidence=evidence,
                case_mode=case_mode
            )
            
            self.logger.info(f"Started timeline reconciliation workflow: {workflow_id}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "message": "Timeline reconciliation workflow started",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing timeline reconciliation: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def orchestrate_ai_processing(self, case_id: str, evidence_ids: List[str],
                                      storyboard_id: Optional[str] = None) -> Dict[str, Any]:
        """Orchestrate AI processing for a case."""
        
        try:
            # Start AI agent orchestration workflow
            workflow_id = await self.client.start_ai_agent_orchestration_workflow(
                case_id=case_id,
                evidence_ids=evidence_ids,
                storyboard_id=storyboard_id
            )
            
            self.logger.info(f"Started AI agent orchestration workflow: {workflow_id}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "message": "AI agent orchestration workflow started",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error orchestrating AI processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_workflow_result(self, workflow_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Get workflow result."""
        
        try:
            result = await self.client.get_workflow_result(workflow_id, timeout)
            
            return {
                "success": True,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting workflow result: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        
        try:
            if self.client:
                # Try to get workflow info to check connection
                await self.client.client.list_workflows()
                
                return {
                    "healthy": True,
                    "temporal_connected": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "healthy": False,
                    "temporal_connected": False,
                    "error": "Client not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "temporal_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close the service."""
        
        if self.client:
            await self.client.close()


# Global service instance
ai_agent_service: Optional[AIAgentService] = None


async def get_ai_agent_service() -> AIAgentService:
    """Get the global AI agent service instance."""
    
    global ai_agent_service
    
    if ai_agent_service is None:
        ai_agent_service = AIAgentService()
        await ai_agent_service.initialize()
    
    return ai_agent_service


async def initialize_ai_agent_service():
    """Initialize the global AI agent service."""
    
    global ai_agent_service
    
    if ai_agent_service is None:
        ai_agent_service = AIAgentService()
        await ai_agent_service.initialize()
    
    return ai_agent_service


async def close_ai_agent_service():
    """Close the global AI agent service."""
    
    global ai_agent_service
    
    if ai_agent_service:
        await ai_agent_service.close()
        ai_agent_service = None
