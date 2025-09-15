"""Abstract event bus interface for service communication."""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import asyncio


class EventType(Enum):
    """Types of events in the system."""
    EVIDENCE_UPLOADED = "evidence.uploaded"
    EVIDENCE_PROCESSED = "evidence.processed"
    STORYBOARD_CREATED = "storyboard.created"
    STORYBOARD_UPDATED = "storyboard.updated"
    TIMELINE_COMPILED = "timeline.compiled"
    RENDER_STARTED = "render.started"
    RENDER_COMPLETED = "render.completed"
    RENDER_FAILED = "render.failed"
    POLICY_EVALUATED = "policy.evaluated"
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"


@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: str
    source_service: str
    correlation_id: Optional[str] = None
    version: str = "1.0"


class EventHandler(Protocol):
    """Protocol for event handlers."""
    
    async def handle(self, event: Event) -> None:
        """Handle incoming event."""
        ...


class EventBusService(Protocol):
    """Protocol for event bus service implementations."""
    
    async def publish(self, event: Event) -> None:
        """Publish event to bus."""
        ...
    
    async def subscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """Subscribe to event type."""
        ...
    
    async def unsubscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """Unsubscribe from event type."""
        ...


class EventBusInterface(ABC):
    """Abstract base class for event bus implementations."""
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish event to bus."""
        pass
    
    @abstractmethod
    async def subscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """Subscribe to event type."""
        pass
    
    @abstractmethod
    async def unsubscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """Unsubscribe from event type."""
        pass


class EventBusError(Exception):
    """Base exception for event bus operations."""
    pass


class SubscriptionError(EventBusError):
    """Raised when subscription fails."""
    pass


class PublishError(EventBusError):
    """Raised when event publishing fails."""
    pass
