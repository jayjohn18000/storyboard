"""Event bridge service for Redis to Temporal integration.

This service listens to Redis events and triggers Temporal workflows
for AI agent processing.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import redis.asyncio as redis
from temporalio.client import Client

from services.shared.workers.ai_agent_worker import AIAgentClient


class TemporalEventBridge:
    """Bridge service that connects Redis events to Temporal workflows."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379",
                 temporal_host: str = "localhost:7233",
                 temporal_namespace: str = "legal-sim"):
        self.redis_url = redis_url
        self.temporal_host = temporal_host
        self.temporal_namespace = temporal_namespace
        
        self.redis_client: Optional[redis.Redis] = None
        self.temporal_client: Optional[AIAgentClient] = None
        self.logger = logging.getLogger(__name__)
        
        # Event channels to listen to
        self.event_channels = [
            "evidence:uploaded",
            "evidence:processed",
            "storyboard:created",
            "storyboard:updated",
            "case:created",
            "case:updated"
        ]
    
    async def start(self):
        """Start the event bridge service."""
        
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.logger.info(f"Connected to Redis at {self.redis_url}")
            
            # Connect to Temporal
            self.temporal_client = AIAgentClient(
                temporal_host=self.temporal_host,
                temporal_namespace=self.temporal_namespace
            )
            await self.temporal_client.connect()
            self.logger.info(f"Connected to Temporal at {self.temporal_host}")
            
            # Start listening to events
            await self._listen_to_events()
            
        except Exception as e:
            self.logger.error(f"Failed to start event bridge: {e}")
            raise
    
    async def stop(self):
        """Stop the event bridge service."""
        
        if self.redis_client:
            await self.redis_client.close()
        
        if self.temporal_client:
            await self.temporal_client.close()
    
    async def _listen_to_events(self):
        """Listen to Redis events and trigger Temporal workflows."""
        
        self.logger.info(f"Listening to events on channels: {self.event_channels}")
        
        try:
            # Subscribe to event channels
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(*self.event_channels)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self._handle_event(message["channel"], message["data"])
                    
        except Exception as e:
            self.logger.error(f"Error listening to events: {e}")
            raise
    
    async def _handle_event(self, channel: str, data: bytes):
        """Handle incoming Redis event."""
        
        try:
            # Parse event data
            event_data = json.loads(data.decode('utf-8'))
            self.logger.info(f"Received event on {channel}: {event_data}")
            
            # Route event to appropriate handler
            if channel == "evidence:uploaded":
                await self._handle_evidence_uploaded(event_data)
            elif channel == "evidence:processed":
                await self._handle_evidence_processed(event_data)
            elif channel == "storyboard:created":
                await self._handle_storyboard_created(event_data)
            elif channel == "storyboard:updated":
                await self._handle_storyboard_updated(event_data)
            elif channel == "case:created":
                await self._handle_case_created(event_data)
            elif channel == "case:updated":
                await self._handle_case_updated(event_data)
            else:
                self.logger.warning(f"Unknown event channel: {channel}")
                
        except Exception as e:
            self.logger.error(f"Error handling event from {channel}: {e}")
    
    async def _handle_evidence_uploaded(self, event_data: Dict[str, Any]):
        """Handle evidence uploaded event."""
        
        try:
            evidence_id = event_data.get("evidence_id")
            case_id = event_data.get("case_id")
            filename = event_data.get("filename")
            evidence_type = event_data.get("evidence_type")
            file_path = event_data.get("file_path")
            sha256_hash = event_data.get("sha256_hash")
            case_mode = event_data.get("case_mode", "SANDBOX")
            
            if not all([evidence_id, case_id, filename, evidence_type, file_path, sha256_hash]):
                self.logger.error("Missing required fields in evidence uploaded event")
                return
            
            # Get available cases for association
            available_cases = await self._get_available_cases(case_id)
            
            # Start evidence intake workflow
            workflow_id = await self.temporal_client.start_evidence_intake_workflow(
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
            
            # Publish workflow started event
            await self._publish_event("ai:workflow:started", {
                "workflow_id": workflow_id,
                "workflow_type": "evidence_intake",
                "evidence_id": evidence_id,
                "case_id": case_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error handling evidence uploaded event: {e}")
    
    async def _handle_evidence_processed(self, event_data: Dict[str, Any]):
        """Handle evidence processed event."""
        
        try:
            evidence_id = event_data.get("evidence_id")
            case_id = event_data.get("case_id")
            
            if not evidence_id or not case_id:
                self.logger.error("Missing required fields in evidence processed event")
                return
            
            # Check if there are any storyboards for this case that need reconciliation
            storyboards = await self._get_case_storyboards(case_id)
            
            for storyboard in storyboards:
                # Start timeline reconciliation workflow
                workflow_id = await self.temporal_client.start_timeline_reconciliation_workflow(
                    storyboard_id=storyboard["id"],
                    case_id=case_id,
                    scenes=storyboard.get("scenes", []),
                    evidence=[event_data],
                    case_mode=event_data.get("case_mode", "SANDBOX")
                )
                
                self.logger.info(f"Started timeline reconciliation workflow: {workflow_id}")
                
                # Publish workflow started event
                await self._publish_event("ai:workflow:started", {
                    "workflow_id": workflow_id,
                    "workflow_type": "timeline_reconciliation",
                    "storyboard_id": storyboard["id"],
                    "case_id": case_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Error handling evidence processed event: {e}")
    
    async def _handle_storyboard_created(self, event_data: Dict[str, Any]):
        """Handle storyboard created event."""
        
        try:
            storyboard_id = event_data.get("storyboard_id")
            case_id = event_data.get("case_id")
            
            if not storyboard_id or not case_id:
                self.logger.error("Missing required fields in storyboard created event")
                return
            
            # Get case evidence for reconciliation
            evidence = await self._get_case_evidence(case_id)
            
            if evidence:
                # Start timeline reconciliation workflow
                workflow_id = await self.temporal_client.start_timeline_reconciliation_workflow(
                    storyboard_id=storyboard_id,
                    case_id=case_id,
                    scenes=event_data.get("scenes", []),
                    evidence=evidence,
                    case_mode=event_data.get("case_mode", "SANDBOX")
                )
                
                self.logger.info(f"Started timeline reconciliation workflow: {workflow_id}")
                
                # Publish workflow started event
                await self._publish_event("ai:workflow:started", {
                    "workflow_id": workflow_id,
                    "workflow_type": "timeline_reconciliation",
                    "storyboard_id": storyboard_id,
                    "case_id": case_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Error handling storyboard created event: {e}")
    
    async def _handle_storyboard_updated(self, event_data: Dict[str, Any]):
        """Handle storyboard updated event."""
        
        # Same as storyboard created
        await self._handle_storyboard_created(event_data)
    
    async def _handle_case_created(self, event_data: Dict[str, Any]):
        """Handle case created event."""
        
        try:
            case_id = event_data.get("case_id")
            
            if not case_id:
                self.logger.error("Missing case_id in case created event")
                return
            
            # Log case creation for AI processing context
            self.logger.info(f"Case created: {case_id}")
            
            # Publish case context event
            await self._publish_event("ai:case:context", {
                "case_id": case_id,
                "action": "created",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error handling case created event: {e}")
    
    async def _handle_case_updated(self, event_data: Dict[str, Any]):
        """Handle case updated event."""
        
        try:
            case_id = event_data.get("case_id")
            
            if not case_id:
                self.logger.error("Missing case_id in case updated event")
                return
            
            # Log case update for AI processing context
            self.logger.info(f"Case updated: {case_id}")
            
            # Publish case context event
            await self._publish_event("ai:case:context", {
                "case_id": case_id,
                "action": "updated",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error handling case updated event: {e}")
    
    async def _get_available_cases(self, current_case_id: str) -> list:
        """Get available cases for evidence association."""
        
        # This would query the database for available cases
        # For now, return empty list
        return []
    
    async def _get_case_storyboards(self, case_id: str) -> list:
        """Get storyboards for a case."""
        
        # This would query the database for case storyboards
        # For now, return empty list
        return []
    
    async def _get_case_evidence(self, case_id: str) -> list:
        """Get evidence for a case."""
        
        # This would query the database for case evidence
        # For now, return empty list
        return []
    
    async def _publish_event(self, channel: str, event_data: Dict[str, Any]):
        """Publish event to Redis."""
        
        try:
            await self.redis_client.publish(channel, json.dumps(event_data))
            self.logger.debug(f"Published event to {channel}: {event_data}")
        except Exception as e:
            self.logger.error(f"Error publishing event to {channel}: {e}")


async def main():
    """Main function to run the event bridge service."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "legal-sim")
    
    # Create and start event bridge
    bridge = TemporalEventBridge(
        redis_url=redis_url,
        temporal_host=temporal_host,
        temporal_namespace=temporal_namespace
    )
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logging.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logging.error(f"Event bridge failed: {e}")
    finally:
        await bridge.stop()


if __name__ == "__main__":
    import os
    asyncio.run(main())
