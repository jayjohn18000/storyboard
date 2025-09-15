"""AWS S3 storage implementation."""

import os
import hashlib
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, UnknownKeyError

from ...interfaces.storage import StorageInterface, StorageMetadata, StorageError, WormLockError, ObjectNotFoundError


class S3Storage(StorageInterface):
    """AWS S3 storage implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize S3 storage."""
        self.access_key_id = config["access_key_id"]
        self.secret_access_key = config["secret_access_key"]
        self.region = config["region"]
        self.bucket = config["bucket"]
        
        # Initialize S3 client
        self.client = boto3.client(
            's3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region
        )
        
        # Ensure bucket exists
        asyncio.create_task(self._ensure_bucket_exists())
    
    async def _ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Create bucket
                if self.region == 'us-east-1':
                    self.client.create_bucket(Bucket=self.bucket)
                else:
                    self.client.create_bucket(
                        Bucket=self.bucket,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
            else:
                raise StorageError(f"Failed to access bucket: {e}")
    
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
                Bucket=self.bucket,
                Key=object_key,
                Body=file_data,
                ContentType=metadata.get("content_type", "application/octet-stream"),
                Metadata={
                    "evidence_id": evidence_id,
                    "checksum": checksum,
                    "uploaded_at": datetime.utcnow().isoformat(),
                    **metadata.get("tags", {})
                }
            )
            
            return object_key
            
        except ClientError as e:
            raise StorageError(f"Failed to store evidence: {e}")
    
    async def get_evidence(self, evidence_id: str) -> bytes:
        """Retrieve evidence file by ID."""
        try:
            object_key = f"evidence/{evidence_id}"
            
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return response['Body'].read()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ObjectNotFoundError(f"Evidence not found: {evidence_id}")
            raise StorageError(f"Failed to retrieve evidence: {e}")
    
    async def ensure_worm_lock(self, evidence_id: str) -> bool:
        """Apply WORM lock to evidence."""
        try:
            object_key = f"evidence/{evidence_id}"
            
            # Get current metadata
            response = self.client.head_object(Bucket=self.bucket, Key=object_key)
            current_metadata = response.get('Metadata', {})
            
            # Check if already locked
            if current_metadata.get("worm_locked") == "true":
                return True
            
            # Apply WORM lock by updating metadata
            self.client.copy_object(
                Bucket=self.bucket,
                Key=object_key,
                CopySource={'Bucket': self.bucket, 'Key': object_key},
                Metadata={
                    **current_metadata,
                    "worm_locked": "true",
                    "worm_locked_at": datetime.utcnow().isoformat()
                },
                MetadataDirective='REPLACE'
            )
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ObjectNotFoundError(f"Evidence not found: {evidence_id}")
            raise StorageError(f"Failed to apply WORM lock: {e}")
    
    async def get_metadata(self, object_id: str) -> StorageMetadata:
        """Get metadata for stored object."""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=object_id)
            
            return StorageMetadata(
                object_id=object_id,
                content_type=response.get('ContentType', 'application/octet-stream'),
                size_bytes=response['ContentLength'],
                created_at=response['LastModified'].isoformat(),
                checksum=response.get('ETag', '').strip('"'),
                tags=response.get('Metadata', {}),
                worm_locked=response.get('Metadata', {}).get("worm_locked") == "true"
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ObjectNotFoundError(f"Object not found: {object_id}")
            raise StorageError(f"Failed to get metadata: {e}")
    
    async def list_objects(
        self, 
        prefix: str = "", 
        limit: int = 100
    ) -> AsyncGenerator[StorageMetadata, None]:
        """List objects with optional prefix filtering."""
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=prefix,
                PaginationConfig={'MaxItems': limit}
            )
            
            for page in page_iterator:
                for obj in page.get('Contents', []):
                    yield StorageMetadata(
                        object_id=obj['Key'],
                        content_type="application/octet-stream",  # Would need separate head call
                        size_bytes=obj['Size'],
                        created_at=obj['LastModified'].isoformat(),
                        checksum=obj['ETag'].strip('"'),
                        tags={},  # Would need separate head call
                        worm_locked=False  # Would need separate head call
                    )
                    
        except ClientError as e:
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
            self.client.delete_object(Bucket=self.bucket, Key=object_id)
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return False
            raise StorageError(f"Failed to delete object: {e}")
        except WormLockError:
            raise
