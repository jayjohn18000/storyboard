#!/usr/bin/env python3
"""Startup script for Temporal Event Bridge.

This script starts the event bridge service that connects Redis events
to Temporal workflows for AI agent processing.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.shared.events.temporal_event_bridge import TemporalEventBridge


async def main():
    """Main function to start the event bridge service."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Get configuration from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "legal-sim")
    
    logger.info(f"Starting Temporal Event Bridge")
    logger.info(f"Redis URL: {redis_url}")
    logger.info(f"Temporal Host: {temporal_host}")
    logger.info(f"Namespace: {temporal_namespace}")
    
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


if __name__ == "__main__":
    asyncio.run(main())
