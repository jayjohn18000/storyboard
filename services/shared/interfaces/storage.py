"""Abstract storage interface for evidence and render artifacts."""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


class StorageType(Enum):
    """Supported storage backends."""
    MINIO = "minio"
    S3 = "s3"
    LOCAL = "local"


@dataclass
class StorageMetadata:
    """Metadata for stored objects."""
    object_id: str
    content_type: str
    size_bytes: int
    created_at: str
    checksum: str
    tags: Dict[str, str]
    worm_locked: bool = False


class StorageService(Protocol):
    """Protocol for storage service implementations."""
    
    async def store_evidence(
        self, 
        file_data: bytes, 
        metadata: Dict[str, Any],
        evidence_id: str
    ) -> str:
        """Store evidence file and return object ID."""
        ...
    
    async def get_evidence(self, evidence_id: str) -> bytes:
        """Retrieve evidence file by ID."""
        ...
    
    async def ensure_worm_lock(self, evidence_id: str) -> bool:
        """Apply WORM (Write Once, Read Many) lock to evidence."""
        ...
    
    async def get_metadata(self, object_id: str) -> StorageMetadata:
        """Get metadata for stored object."""
        ...
    
    async def list_objects(
        self, 
        prefix: str = "", 
        limit: int = 100
    ) -> AsyncGenerator[StorageMetadata, None]:
        """List objects with optional prefix filtering."""
        ...
    
    async def delete_object(self, object_id: str) -> bool:
        """Delete object (only if not WORM locked)."""
        ...


class StorageInterface(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    async def store_evidence(
        self, 
        file_data: bytes, 
        metadata: Dict[str, Any],
        evidence_id: str
    ) -> str:
        """Store evidence file and return object ID."""
        pass
    
    @abstractmethod
    async def get_evidence(self, evidence_id: str) -> bytes:
        """Retrieve evidence file by ID."""
        pass
    
    @abstractmethod
    async def ensure_worm_lock(self, evidence_id: str) -> bool:
        """Apply WORM lock to evidence."""
        pass
    
    @abstractmethod
    async def get_metadata(self, object_id: str) -> StorageMetadata:
        """Get metadata for stored object."""
        pass
    
    @abstractmethod
    async def list_objects(
        self, 
        prefix: str = "", 
        limit: int = 100
    ) -> AsyncGenerator[StorageMetadata, None]:
        """List objects with optional prefix filtering."""
        pass
    
    @abstractmethod
    async def delete_object(self, object_id: str) -> bool:
        """Delete object (only if not WORM locked)."""
        pass


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class WormLockError(StorageError):
    """Raised when attempting to modify WORM-locked content."""
    pass


class ObjectNotFoundError(StorageError):
    """Raised when requested object doesn't exist."""
    pass


# Note: Concrete implementations are imported separately to avoid circular imports
