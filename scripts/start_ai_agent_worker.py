#!/usr/bin/env python3
"""Startup script for the AI Agent Temporal worker.

This script starts the Temporal worker that executes AI agent workflows
and activities for evidence intake/triage and timeline reconciliation.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.shared.workers.ai_agent_worker import AIAgentWorker


def setup_logging():
    """Setup logging configuration."""
    
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ai_agent_worker.log')
        ]
    )


async def main():
    """Main function to start the AI agent worker."""
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get configuration from environment
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "legal-sim")
    task_queue = os.getenv("AI_AGENT_TASK_QUEUE", "ai-agent-queue")
    
    logger.info("Starting AI Agent Temporal Worker")
    logger.info(f"Temporal Host: {temporal_host}")
    logger.info(f"Temporal Namespace: {temporal_namespace}")
    logger.info(f"Task Queue: {task_queue}")
    
    # Create and start worker
    worker = AIAgentWorker(
        temporal_host=temporal_host,
        temporal_namespace=temporal_namespace,
        task_queue=task_queue
    )
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)
    finally:
        await worker.stop()
        logger.info("AI Agent Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
