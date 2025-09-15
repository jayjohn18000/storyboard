"""MinIO storage implementation."""

import os
import hashlib
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
import minio
from minio.error import S3Error

from ...interfaces.storage import StorageInterface, StorageMetadata, StorageError, WormLockError, ObjectNotFoundError


class MinioStorage(StorageInterface):
    """MinIO storage implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MinIO storage."""
        self.endpoint = config["endpoint"]
        self.access_key = config["access_key"]
        self.secret_key = config["secret_key"]
        self.bucket = config["bucket"]
        self.secure = config["secure"]
        
        # Initialize MinIO client
        self.client = minio.Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # Ensure bucket exists
        asyncio.create_task(self._ensure_bucket_exists())
    
    async def _ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            raise StorageError(f"Failed to create bucket: {e}")
    
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
            
            # Calculate checksum
            checksum = hashlib.sha256(file_data).hexdigest()
            
            # Upload file
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_key,
                data=file_data,
                length=len(file_data),
                content_type=metadata.get("content_type", "application/octet-stream"),
                metadata={
                    "evidence_id": evidence_id,
                    "checksum": checksum,
                    "uploaded_at": datetime.utcnow().isoformat(),
                    **metadata.get("tags", {})
                }
            )
            
            return object_key
            
        except S3Error as e:
            raise StorageError(f"Failed to store evidence: {e}")
    
    async def get_evidence(self, evidence_id: str) -> bytes:
        """Retrieve evidence file by ID."""
        try:
            object_key = f"evidence/{evidence_id}"
            
            # Get object
            response = self.client.get_object(self.bucket, object_key)
            data = response.read()
            response.close()
            response.release_conn()
            
            return data
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(f"Evidence not found: {evidence_id}")
            raise StorageError(f"Failed to retrieve evidence: {e}")
    
    async def ensure_worm_lock(self, evidence_id: str) -> bool:
        """Apply WORM lock to evidence."""
        try:
            object_key = f"evidence/{evidence_id}"
            
            # Get current metadata
            stat = self.client.stat_object(self.bucket, object_key)
            
            # Check if already locked
            if stat.metadata.get("worm_locked") == "true":
                return True
            
            # Apply WORM lock by updating metadata
            self.client.copy_object(
                bucket_name=self.bucket,
                object_name=object_key,
                source=f"{self.bucket}/{object_key}",
                metadata={
                    **stat.metadata,
                    "worm_locked": "true",
                    "worm_locked_at": datetime.utcnow().isoformat()
                },
                metadata_directive="REPLACE"
            )
            
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(f"Evidence not found: {evidence_id}")
            raise StorageError(f"Failed to apply WORM lock: {e}")
    
    async def get_metadata(self, object_id: str) -> StorageMetadata:
        """Get metadata for stored object."""
        try:
            stat = self.client.stat_object(self.bucket, object_id)
            
            return StorageMetadata(
                object_id=object_id,
                content_type=stat.content_type,
                size_bytes=stat.size,
                created_at=stat.last_modified.isoformat(),
                checksum=stat.etag.strip('"'),
                tags=stat.metadata,
                worm_locked=stat.metadata.get("worm_locked") == "true"
            )
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(f"Object not found: {object_id}")
            raise StorageError(f"Failed to get metadata: {e}")
    
    async def list_objects(
        self, 
        prefix: str = "", 
        limit: int = 100
    ) -> AsyncGenerator[StorageMetadata, None]:
        """List objects with optional prefix filtering."""
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket,
                prefix=prefix,
                recursive=True
            )
            
            count = 0
            for obj in objects:
                if count >= limit:
                    break
                
                yield StorageMetadata(
                    object_id=obj.object_name,
                    content_type="application/octet-stream",  # MinIO doesn't provide this in list
                    size_bytes=obj.size,
                    created_at=obj.last_modified.isoformat(),
                    checksum=obj.etag.strip('"'),
                    tags={},
                    worm_locked=False  # Would need separate stat call to get this
                )
                
                count += 1
                
        except S3Error as e:
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
            
            # Delete object
            self.client.remove_object(self.bucket, object_id)
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise StorageError(f"Failed to delete object: {e}")
        except WormLockError:
            raise
