#!/usr/bin/env python3
"""Startup script for the Temporal Event Bridge.

This script starts the event bridge service that listens to Redis events
and triggers Temporal workflows for AI agent processing.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.shared.events.temporal_event_bridge import TemporalEventBridge


def setup_logging():
    """Setup logging configuration."""
    
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('event_bridge.log')
        ]
    )


async def main():
    """Main function to start the event bridge service."""
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get configuration from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "legal-sim")
    
    logger.info("Starting Temporal Event Bridge")
    logger.info(f"Redis URL: {redis_url}")
    logger.info(f"Temporal Host: {temporal_host}")
    logger.info(f"Temporal Namespace: {temporal_namespace}")
    
    # Create and start event bridge
    bridge = TemporalEventBridge(
        redis_url=redis_url,
        temporal_host=temporal_host,
        temporal_namespace=temporal_namespace
    )
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Event bridge failed: {e}")
        sys.exit(1)
    finally:
        await bridge.stop()
        logger.info("Event Bridge stopped")


if __name__ == "__main__":
    asyncio.run(main())
