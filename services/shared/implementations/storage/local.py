"""
Local file system storage implementation.

This module provides a local file system implementation of the storage interface
with SHA256 hashing, content-addressed storage, and WORM lock support.
"""

import os
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
from pathlib import Path
import aiofiles

from ...interfaces.storage import StorageInterface, StorageMetadata, StorageError, WormLockError, ObjectNotFoundError

logger = logging.getLogger(__name__)


class LocalStorage(StorageInterface):
    """Local file system storage implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize local storage.
        
        Args:
            config: Configuration dictionary with 'base_path' key
        """
        self.base_path = Path(config.get("base_path", "/tmp/legal-sim-storage"))
        self.evidence_path = self.base_path / "evidence"
        self.renders_path = self.base_path / "renders"
        self.metadata_path = self.base_path / "metadata"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure storage directories exist."""
        for path in [self.evidence_path, self.renders_path, self.metadata_path]:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")
    
    def _get_content_path(self, file_hash: str) -> Path:
        """
        Get content-addressed file path.
        
        Args:
            file_hash: SHA256 hash of file content
            
        Returns:
            Path object for the file
        """
        # Use first 2 chars for directory, full hash for filename
        dir_path = self.evidence_path / file_hash[:2]
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / file_hash
    
    def _get_metadata_path(self, object_id: str) -> Path:
        """
        Get metadata file path.
        
        Args:
            object_id: Object identifier
            
        Returns:
            Path object for metadata file
        """
        return self.metadata_path / f"{object_id}.json"
    
    async def _save_metadata(self, object_id: str, metadata: StorageMetadata):
        """
        Save metadata to file.
        
        Args:
            object_id: Object identifier
            metadata: Metadata to save
        """
        metadata_path = self._get_metadata_path(object_id)
        metadata_dict = {
            "object_id": metadata.object_id,
            "content_type": metadata.content_type,
            "size_bytes": metadata.size_bytes,
            "created_at": metadata.created_at,
            "checksum": metadata.checksum,
            "tags": metadata.tags,
            "worm_locked": metadata.worm_locked,
        }
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata_dict, indent=2))
    
    async def _load_metadata(self, object_id: str) -> StorageMetadata:
        """
        Load metadata from file.
        
        Args:
            object_id: Object identifier
            
        Returns:
            StorageMetadata object
            
        Raises:
            ObjectNotFoundError: If metadata file doesn't exist
        """
        metadata_path = self._get_metadata_path(object_id)
        
        if not metadata_path.exists():
            raise ObjectNotFoundError(f"Metadata not found for object: {object_id}")
        
        async with aiofiles.open(metadata_path, 'r') as f:
            content = await f.read()
            metadata_dict = json.loads(content)
            
            return StorageMetadata(
                object_id=metadata_dict["object_id"],
                content_type=metadata_dict["content_type"],
                size_bytes=metadata_dict["size_bytes"],
                created_at=metadata_dict["created_at"],
                checksum=metadata_dict["checksum"],
                tags=metadata_dict["tags"],
                worm_locked=metadata_dict.get("worm_locked", False)
            )
    
    async def store_evidence(
        self, 
        file_data: bytes, 
        metadata: Dict[str, Any],
        evidence_id: str
    ) -> str:
        """
        Store evidence file with SHA256 hashing and content addressing.
        
        Args:
            file_data: File content as bytes
            metadata: File metadata
            evidence_id: Evidence identifier
            
        Returns:
            Object ID (content hash)
            
        Raises:
            StorageError: If storage operation fails
        """
        try:
            # Calculate SHA256 hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Get content-addressed path
            content_path = self._get_content_path(file_hash)
            
            # Check if file already exists (deduplication)
            if content_path.exists():
                logger.info(f"File with hash {file_hash} already exists, skipping storage")
            else:
                # Write file data
                async with aiofiles.open(content_path, 'wb') as f:
                    await f.write(file_data)
                logger.debug(f"Stored file at {content_path}")
            
            # Create storage metadata
            storage_metadata = StorageMetadata(
                object_id=file_hash,
                content_type=metadata.get("content_type", "application/octet-stream"),
                size_bytes=len(file_data),
                created_at=datetime.utcnow().isoformat() + "Z",
                checksum=file_hash,
                tags={
                    "filename": metadata.get("filename", ""),
                    "case_id": metadata.get("case_id", ""),
                    "description": metadata.get("description", ""),
                    **metadata.get("tags", {})
                },
                worm_locked=False
            )
            
            # Save metadata
            await self._save_metadata(file_hash, storage_metadata)
            
            logger.info(f"Stored evidence {evidence_id} with hash {file_hash}")
            return file_hash
            
        except Exception as e:
            logger.error(f"Failed to store evidence {evidence_id}: {e}")
            raise StorageError(f"Failed to store evidence: {e}")
    
    async def get_evidence(self, evidence_id: str) -> bytes:
        """
        Retrieve evidence file by ID.
        
        Args:
            evidence_id: Evidence identifier (content hash)
            
        Returns:
            File content as bytes
            
        Raises:
            ObjectNotFoundError: If evidence doesn't exist
            StorageError: If retrieval fails
        """
        try:
            # Load metadata to verify existence
            metadata = await self._load_metadata(evidence_id)
            
            # Get content path
            content_path = self._get_content_path(evidence_id)
            
            if not content_path.exists():
                raise ObjectNotFoundError(f"Evidence file not found: {evidence_id}")
            
            # Read file data
            async with aiofiles.open(content_path, 'rb') as f:
                file_data = await f.read()
            
            # Verify checksum
            calculated_hash = hashlib.sha256(file_data).hexdigest()
            if calculated_hash != evidence_id:
                raise StorageError(f"Checksum mismatch for evidence {evidence_id}")
            
            logger.debug(f"Retrieved evidence {evidence_id}")
            return file_data
            
        except ObjectNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve evidence {evidence_id}: {e}")
            raise StorageError(f"Failed to retrieve evidence: {e}")
    
    async def ensure_worm_lock(self, evidence_id: str) -> bool:
        """
        Apply WORM (Write Once, Read Many) lock to evidence.
        
        Args:
            evidence_id: Evidence identifier
            
        Returns:
            True if lock was applied successfully
            
        Raises:
            ObjectNotFoundError: If evidence doesn't exist
            WormLockError: If evidence is already locked
        """
        try:
            # Load metadata
            metadata = await self._load_metadata(evidence_id)
            
            if metadata.worm_locked:
                raise WormLockError(f"Evidence {evidence_id} is already WORM locked")
            
            # Update metadata with WORM lock
            metadata.worm_locked = True
            await self._save_metadata(evidence_id, metadata)
            
            logger.info(f"Applied WORM lock to evidence {evidence_id}")
            return True
            
        except (ObjectNotFoundError, WormLockError):
            raise
        except Exception as e:
            logger.error(f"Failed to apply WORM lock to evidence {evidence_id}: {e}")
            raise StorageError(f"Failed to apply WORM lock: {e}")
    
    async def get_metadata(self, object_id: str) -> StorageMetadata:
        """
        Get metadata for stored object.
        
        Args:
            object_id: Object identifier
            
        Returns:
            StorageMetadata object
            
        Raises:
            ObjectNotFoundError: If object doesn't exist
        """
        try:
            return await self._load_metadata(object_id)
        except ObjectNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get metadata for object {object_id}: {e}")
            raise StorageError(f"Failed to get metadata: {e}")
    
    async def list_objects(
        self, 
        prefix: str = "", 
        limit: int = 100
    ) -> AsyncGenerator[StorageMetadata, None]:
        """
        List objects with optional prefix filtering.
        
        Args:
            prefix: Prefix to filter by
            limit: Maximum number of objects to return
            
        Yields:
            StorageMetadata objects
        """
        try:
            count = 0
            metadata_files = list(self.metadata_path.glob("*.json"))
            
            for metadata_file in sorted(metadata_files):
                if count >= limit:
                    break
                
                try:
                    object_id = metadata_file.stem
                    
                    # Check prefix filter
                    if prefix and not object_id.startswith(prefix):
                        continue
                    
                    metadata = await self._load_metadata(object_id)
                    yield metadata
                    count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to list objects: {e}")
            raise StorageError(f"Failed to list objects: {e}")
    
    async def delete_object(self, object_id: str) -> bool:
        """
        Delete object (only if not WORM locked).
        
        Args:
            object_id: Object identifier
            
        Returns:
            True if deleted successfully
            
        Raises:
            ObjectNotFoundError: If object doesn't exist
            WormLockError: If object is WORM locked
        """
        try:
            # Load metadata to check WORM lock
            metadata = await self._load_metadata(object_id)
            
            if metadata.worm_locked:
                raise WormLockError(f"Cannot delete WORM-locked object: {object_id}")
            
            # Delete content file
            content_path = self._get_content_path(object_id)
            if content_path.exists():
                content_path.unlink()
                logger.debug(f"Deleted content file: {content_path}")
            
            # Delete metadata file
            metadata_path = self._get_metadata_path(object_id)
            if metadata_path.exists():
                metadata_path.unlink()
                logger.debug(f"Deleted metadata file: {metadata_path}")
            
            logger.info(f"Deleted object {object_id}")
            return True
            
        except (ObjectNotFoundError, WormLockError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete object {object_id}: {e}")
            raise StorageError(f"Failed to delete object: {e}")
    
    async def health_check(self) -> bool:
        """
        Check storage health.
        
        Returns:
            True if storage is healthy
        """
        try:
            # Check if base directory is writable
            test_file = self.base_path / ".health_check"
            test_file.write_text("health check")
            test_file.unlink()
            
            return True
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_files = 0
            total_size = 0
            worm_locked_count = 0
            
            async for metadata in self.list_objects(limit=10000):
                total_files += 1
                total_size += metadata.size_bytes
                if metadata.worm_locked:
                    worm_locked_count += 1
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "worm_locked_files": worm_locked_count,
                "storage_path": str(self.base_path),
                "available_space": self._get_available_space()
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "worm_locked_files": 0,
                "storage_path": str(self.base_path),
                "available_space": 0
            }
    
    def _get_available_space(self) -> int:
        """Get available disk space in bytes."""
        try:
            statvfs = os.statvfs(self.base_path)
            return statvfs.f_frsize * statvfs.f_bavail
        except Exception:
            return 0
