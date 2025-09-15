"""Local filesystem storage implementation."""

import os
import hashlib
import asyncio
import aiofiles
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
from pathlib import Path

from ...interfaces.storage import StorageInterface, StorageMetadata, StorageError, WormLockError, ObjectNotFoundError


class LocalStorage(StorageInterface):
    """Local filesystem storage implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize local storage."""
        self.base_path = Path(config["base_path"])
        
        # Ensure base directory exists
        asyncio.create_task(self._ensure_base_path_exists())
    
    async def _ensure_base_path_exists(self) -> None:
        """Ensure the base path exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_object_path(self, object_id: str) -> Path:
        """Get full path for object."""
        return self.base_path / object_id
    
    def _get_metadata_path(self, object_id: str) -> Path:
        """Get metadata file path for object."""
        return self.base_path / f"{object_id}.meta"
    
    async def _read_metadata(self, object_id: str) -> Dict[str, Any]:
        """Read metadata from file."""
        metadata_path = self._get_metadata_path(object_id)
        
        if not metadata_path.exists():
            raise ObjectNotFoundError(f"Metadata not found: {object_id}")
        
        async with aiofiles.open(metadata_path, 'r') as f:
            import json
            content = await f.read()
            return json.loads(content)
    
    async def _write_metadata(self, object_id: str, metadata: Dict[str, Any]) -> None:
        """Write metadata to file."""
        metadata_path = self._get_metadata_path(object_id)
        
        async with aiofiles.open(metadata_path, 'w') as f:
            import json
            await f.write(json.dumps(metadata, indent=2))
    
    async def store_evidence(
        self, 
        file_data: bytes, 
        metadata: Dict[str, Any],
        evidence_id: str
    ) -> str:
        """Store evidence file and return object ID."""
        try:
            # Generate object key
            object_key = f"evidence/{evidence_id}"
            object_path = self._get_object_path(object_key)
            
            # Ensure directory exists
            object_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Calculate checksum
            checksum = hashlib.sha256(file_data).hexdigest()
            
            # Write file
            async with aiofiles.open(object_path, 'wb') as f:
                await f.write(file_data)
            
            # Write metadata
            metadata_dict = {
                "evidence_id": evidence_id,
                "checksum": checksum,
                "uploaded_at": datetime.utcnow().isoformat(),
                "content_type": metadata.get("content_type", "application/octet-stream"),
                "size_bytes": len(file_data),
                "worm_locked": False,
                **metadata.get("tags", {})
            }
            
            await self._write_metadata(object_key, metadata_dict)
            
            return object_key
            
        except Exception as e:
            raise StorageError(f"Failed to store evidence: {e}")
    
    async def get_evidence(self, evidence_id: str) -> bytes:
        """Retrieve evidence file by ID."""
        try:
            object_key = f"evidence/{evidence_id}"
            object_path = self._get_object_path(object_key)
            
            if not object_path.exists():
                raise ObjectNotFoundError(f"Evidence not found: {evidence_id}")
            
            async with aiofiles.open(object_path, 'rb') as f:
                return await f.read()
                
        except ObjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to retrieve evidence: {e}")
    
    async def ensure_worm_lock(self, evidence_id: str) -> bool:
        """Apply WORM lock to evidence."""
        try:
            object_key = f"evidence/{evidence_id}"
            
            # Check if object exists
            object_path = self._get_object_path(object_key)
            if not object_path.exists():
                raise ObjectNotFoundError(f"Evidence not found: {evidence_id}")
            
            # Read current metadata
            metadata = await self._read_metadata(object_key)
            
            # Check if already locked
            if metadata.get("worm_locked"):
                return True
            
            # Apply WORM lock
            metadata["worm_locked"] = True
            metadata["worm_locked_at"] = datetime.utcnow().isoformat()
            
            await self._write_metadata(object_key, metadata)
            
            return True
            
        except ObjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to apply WORM lock: {e}")
    
    async def get_metadata(self, object_id: str) -> StorageMetadata:
        """Get metadata for stored object."""
        try:
            metadata = await self._read_metadata(object_id)
            
            return StorageMetadata(
                object_id=object_id,
                content_type=metadata.get("content_type", "application/octet-stream"),
                size_bytes=metadata.get("size_bytes", 0),
                created_at=metadata.get("uploaded_at", ""),
                checksum=metadata.get("checksum", ""),
                tags={k: v for k, v in metadata.items() 
                      if k not in ["evidence_id", "checksum", "uploaded_at", 
                                  "content_type", "size_bytes", "worm_locked", "worm_locked_at"]},
                worm_locked=metadata.get("worm_locked", False)
            )
            
        except ObjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get metadata: {e}")
    
    async def list_objects(
        self, 
        prefix: str = "", 
        limit: int = 100
    ) -> AsyncGenerator[StorageMetadata, None]:
        """List objects with optional prefix filtering."""
        try:
            count = 0
            evidence_dir = self.base_path / "evidence"
            
            if not evidence_dir.exists():
                return
            
            for file_path in evidence_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.endswith('.meta'):
                    object_id = str(file_path.relative_to(self.base_path))
                    
                    if prefix and not object_id.startswith(prefix):
                        continue
                    
                    if count >= limit:
                        break
                    
                    try:
                        metadata = await self.get_metadata(object_id)
                        yield metadata
                        count += 1
                    except ObjectNotFoundError:
                        # Skip files without metadata
                        continue
                        
        except Exception as e:
            raise StorageError(f"Failed to list objects: {e}")
    
    async def delete_object(self, object_id: str) -> bool:
        """Delete object (only if not WORM locked)."""
        try:
            # Check if WORM locked first
            try:
                metadata = await self.get_metadata(object_id)
                if metadata.worm_locked:
                    raise WormLockError(f"Cannot delete WORM-locked object: {object_id}")
            except ObjectNotFoundError:
                return False
            
            # Delete files
            object_path = self._get_object_path(object_id)
            metadata_path = self._get_metadata_path(object_id)
            
            if object_path.exists():
                object_path.unlink()
            
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
            
        except WormLockError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete object: {e}")
