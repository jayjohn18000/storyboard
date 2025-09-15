"""Redis-based event bus implementation."""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import redis.asyncio as redis
from redis.asyncio import Redis

from ...interfaces.event_bus import EventBusInterface, Event, EventType, EventBusError

logger = logging.getLogger(__name__)


class RedisEventBus(EventBusInterface):
    """Redis-based event bus implementation."""
    
    def __init__(self, redis_url: str, redis_password: Optional[str] = None):
        """
        Initialize Redis event bus.
        
        Args:
            redis_url: Redis connection URL
            redis_password: Optional Redis password
        """
        self.redis_url = redis_url
        self.redis_password = redis_password
        self.redis_client: Optional[Redis] = None
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self._running = False
        self._subscription_tasks: List[asyncio.Task] = []
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            # Parse Redis URL
            if self.redis_password:
                # Replace password in URL
                self.redis_url = self.redis_url.replace("redis://", f"redis://:{self.redis_password}@")
            
            # Create Redis client
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis event bus initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis event bus: {e}")
            raise EventBusError(f"Failed to initialize Redis event bus: {e}")
    
    async def publish(self, event: Event) -> None:
        """
        Publish event to Redis.
        
        Args:
            event: Event to publish
        """
        if not self.redis_client:
            raise EventBusError("Redis client not initialized")
        
        try:
            # Convert event to JSON
            event_data = {
                "event_type": event.event_type.value,
                "data": event.data,
                "timestamp": event.timestamp,
                "source_service": event.source_service,
                "correlation_id": event.correlation_id,
                "version": event.version
            }
            
            # Publish to Redis channel
            channel = f"events:{event.event_type.value}"
            await self.redis_client.publish(channel, json.dumps(event_data))
            
            logger.debug(f"Published event {event.event_type.value} to channel {channel}")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type.value}: {e}")
            raise EventBusError(f"Failed to publish event: {e}")
    
    async def subscribe(
        self, 
        event_type: EventType, 
        handler: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Handler function for the event
        """
        if not self.redis_client:
            raise EventBusError("Redis client not initialized")
        
        # Add handler to subscribers
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        
        # Start subscription task if not already running
        if not self._running:
            await self._start_subscriptions()
        
        logger.info(f"Subscribed to event type {event_type.value}")
    
    async def unsubscribe(
        self, 
        event_type: EventType, 
        handler: Callable[[Event], None]
    ) -> None:
        """
        Unsubscribe from event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from event type {event_type.value}")
            except ValueError:
                logger.warning(f"Handler not found for event type {event_type.value}")
    
    async def _start_subscriptions(self) -> None:
        """Start Redis subscription tasks."""
        if self._running:
            return
        
        self._running = True
        
        # Create subscription task for each event type
        for event_type in self.subscribers.keys():
            task = asyncio.create_task(self._subscribe_to_channel(event_type))
            self._subscription_tasks.append(task)
        
        logger.info("Started Redis event subscriptions")
    
    async def _subscribe_to_channel(self, event_type: EventType) -> None:
        """Subscribe to a specific Redis channel."""
        channel = f"events:{event_type.value}"
        
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            logger.info(f"Subscribing to Redis channel: {channel}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse event data
                        event_data = json.loads(message["data"])
                        
                        # Create Event object
                        event = Event(
                            event_type=EventType(event_data["event_type"]),
                            data=event_data["data"],
                            timestamp=event_data["timestamp"],
                            source_service=event_data["source_service"],
                            correlation_id=event_data.get("correlation_id"),
                            version=event_data.get("version", "1.0")
                        )
                        
                        # Call all handlers for this event type
                        if event_type in self.subscribers:
                            for handler in self.subscribers[event_type]:
                                try:
                                    if asyncio.iscoroutinefunction(handler):
                                        await handler(event)
                                    else:
                                        handler(event)
                                except Exception as e:
                                    logger.error(f"Error in event handler for {event_type.value}: {e}")
                        
                    except Exception as e:
                        logger.error(f"Error processing message from channel {channel}: {e}")
        
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
            raise EventBusError(f"Failed to subscribe to channel {channel}: {e}")
    
    async def close(self) -> None:
        """Close Redis connection and stop subscriptions."""
        self._running = False
        
        # Cancel subscription tasks
        for task in self._subscription_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._subscription_tasks:
            await asyncio.gather(*self._subscription_tasks, return_exceptions=True)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Redis event bus closed")


# Global event bus instance
_event_bus: Optional[RedisEventBus] = None


async def get_event_bus() -> RedisEventBus:
    """Get global event bus instance."""
    global _event_bus
    
    if _event_bus is None:
        from ...config import config
        _event_bus = RedisEventBus(
            redis_url=config.redis.redis_url,
            redis_password=config.redis.redis_password
        )
        await _event_bus.initialize()
    
    return _event_bus


async def close_event_bus() -> None:
    """Close global event bus."""
    global _event_bus
    
    if _event_bus is not None:
        await _event_bus.close()
        _event_bus = None
