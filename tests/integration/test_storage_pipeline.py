"""
Integration tests for storage pipeline.

These tests verify that the storage system properly handles file uploads,
SHA256 hashing, content-addressed storage, and deduplication.
"""

import pytest
import tempfile
import hashlib
import os
from pathlib import Path

from services.shared.implementations.storage.local import LocalStorage
from services.shared.interfaces.storage import StorageError, WormLockError, ObjectNotFoundError


class TestStoragePipeline:
    """Test suite for storage pipeline functionality."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def storage_service(self, temp_storage_dir):
        """Create storage service instance."""
        config = {"base_path": temp_storage_dir}
        return LocalStorage(config)
    
    @pytest.mark.asyncio
    async def test_store_small_file(self, storage_service):
        """Test storing a small file."""
        # Test data
        file_data = b"Hello, World! This is test evidence content."
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        metadata = {
            "filename": "test_evidence.txt",
            "content_type": "text/plain",
            "case_id": "case-123",
            "description": "Test evidence file",
            "tags": {"priority": "high", "type": "document"}
        }
        
        # Store file
        object_id = await storage_service.store_evidence(
            file_data=file_data,
            metadata=metadata,
            evidence_id="evidence-123"
        )
        
        # Verify object ID is the file hash
        assert object_id == file_hash
        
        # Verify metadata was saved
        stored_metadata = await storage_service.get_metadata(object_id)
        assert stored_metadata.object_id == file_hash
        assert stored_metadata.content_type == "text/plain"
        assert stored_metadata.size_bytes == len(file_data)
        assert stored_metadata.checksum == file_hash
        assert stored_metadata.tags["filename"] == "test_evidence.txt"
        assert stored_metadata.tags["case_id"] == "case-123"
        assert not stored_metadata.worm_locked
        
        # Verify file can be retrieved
        retrieved_data = await storage_service.get_evidence(object_id)
        assert retrieved_data == file_data
    
    @pytest.mark.asyncio
    async def test_duplicate_upload_idempotent(self, storage_service):
        """Test that duplicate uploads are idempotent by hash."""
        # Test data
        file_data = b"Duplicate test content"
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        metadata = {
            "filename": "duplicate_test.txt",
            "content_type": "text/plain"
        }
        
        # Store file first time
        object_id_1 = await storage_service.store_evidence(
            file_data=file_data,
            metadata=metadata,
            evidence_id="evidence-1"
        )
        
        # Store same file with different evidence_id (should be deduplicated)
        object_id_2 = await storage_service.store_evidence(
            file_data=file_data,
            metadata=metadata,
            evidence_id="evidence-2"
        )
        
        # Both should return the same object ID (hash)
        assert object_id_1 == object_id_2
        assert object_id_1 == file_hash
        
        # Verify only one physical file exists
        content_path = storage_service._get_content_path(file_hash)
        assert content_path.exists()
        
        # Verify file content is correct
        retrieved_data = await storage_service.get_evidence(object_id_1)
        assert retrieved_data == file_data
    
    @pytest.mark.asyncio
    async def test_worm_lock_functionality(self, storage_service):
        """Test WORM (Write Once, Read Many) lock functionality."""
        # Test data
        file_data = b"WORM locked content"
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        metadata = {
            "filename": "worm_test.txt",
            "content_type": "text/plain"
        }
        
        # Store file
        object_id = await storage_service.store_evidence(
            file_data=file_data,
            metadata=metadata,
            evidence_id="evidence-worm"
        )
        
        # Verify file is not locked initially
        stored_metadata = await storage_service.get_metadata(object_id)
        assert not stored_metadata.worm_locked
        
        # Apply WORM lock
        lock_result = await storage_service.ensure_worm_lock(object_id)
        assert lock_result is True
        
        # Verify file is now locked
        locked_metadata = await storage_service.get_metadata(object_id)
        assert locked_metadata.worm_locked
        
        # Verify file can still be read
        retrieved_data = await storage_service.get_evidence(object_id)
        assert retrieved_data == file_data
        
        # Verify trying to lock again raises error
        with pytest.raises(WormLockError):
            await storage_service.ensure_worm_lock(object_id)
        
        # Verify trying to delete locked file raises error
        with pytest.raises(WormLockError):
            await storage_service.delete_object(object_id)
    
    @pytest.mark.asyncio
    async def test_content_addressed_storage(self, storage_service):
        """Test that files are stored with content-addressed paths."""
        # Test data
        file_data = b"Content-addressed test"
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        metadata = {
            "filename": "content_test.txt",
            "content_type": "text/plain"
        }
        
        # Store file
        object_id = await storage_service.store_evidence(
            file_data=file_data,
            metadata=metadata,
            evidence_id="evidence-content"
        )
        
        # Verify content-addressed path structure
        content_path = storage_service._get_content_path(file_hash)
        expected_dir = storage_service.evidence_path / file_hash[:2]
        
        assert content_path.parent == expected_dir
        assert content_path.name == file_hash
        assert content_path.exists()
        
        # Verify metadata file exists
        metadata_path = storage_service._get_metadata_path(object_id)
        assert metadata_path.exists()
    
    @pytest.mark.asyncio
    async def test_list_objects_functionality(self, storage_service):
        """Test object listing functionality."""
        # Store multiple files
        test_files = [
            (b"File 1 content", "file1.txt", "evidence-1"),
            (b"File 2 content", "file2.txt", "evidence-2"),
            (b"File 3 content", "file3.txt", "evidence-3"),
        ]
        
        stored_objects = []
        for file_data, filename, evidence_id in test_files:
            metadata = {
                "filename": filename,
                "content_type": "text/plain"
            }
            
            object_id = await storage_service.store_evidence(
                file_data=file_data,
                metadata=metadata,
                evidence_id=evidence_id
            )
            stored_objects.append(object_id)
        
        # List all objects
        all_objects = []
        async for metadata in storage_service.list_objects():
            all_objects.append(metadata)
        
        assert len(all_objects) == 3
        
        # Verify all stored objects are in the list
        object_ids = [obj.object_id for obj in all_objects]
        for stored_id in stored_objects:
            assert stored_id in object_ids
        
        # Test prefix filtering
        prefix_objects = []
        async for metadata in storage_service.list_objects(prefix=stored_objects[0][:8]):
            prefix_objects.append(metadata)
        
        # Should find at least one object with the prefix
        assert len(prefix_objects) >= 1
    
    @pytest.mark.asyncio
    async def test_delete_unlocked_object(self, storage_service):
        """Test deleting unlocked objects."""
        # Test data
        file_data = b"Deletable content"
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        metadata = {
            "filename": "deletable.txt",
            "content_type": "text/plain"
        }
        
        # Store file
        object_id = await storage_service.store_evidence(
            file_data=file_data,
            metadata=metadata,
            evidence_id="evidence-deletable"
        )
        
        # Verify file exists
        content_path = storage_service._get_content_path(file_hash)
        metadata_path = storage_service._get_metadata_path(object_id)
        assert content_path.exists()
        assert metadata_path.exists()
        
        # Delete object
        delete_result = await storage_service.delete_object(object_id)
        assert delete_result is True
        
        # Verify files are deleted
        assert not content_path.exists()
        assert not metadata_path.exists()
        
        # Verify object cannot be retrieved
        with pytest.raises(ObjectNotFoundError):
            await storage_service.get_evidence(object_id)
    
    @pytest.mark.asyncio
    async def test_storage_health_check(self, storage_service):
        """Test storage health check functionality."""
        # Health check should pass for valid storage
        health_status = await storage_service.health_check()
        assert health_status is True
    
    @pytest.mark.asyncio
    async def test_storage_statistics(self, storage_service):
        """Test storage statistics functionality."""
        # Store some test files
        test_files = [
            (b"Small file", "small.txt", "evidence-small"),
            (b"Medium file content that is longer", "medium.txt", "evidence-medium"),
        ]
        
        for file_data, filename, evidence_id in test_files:
            metadata = {
                "filename": filename,
                "content_type": "text/plain"
            }
            
            await storage_service.store_evidence(
                file_data=file_data,
                metadata=metadata,
                evidence_id=evidence_id
            )
        
        # Get statistics
        stats = await storage_service.get_storage_stats()
        
        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["worm_locked_files"] == 0
        assert "storage_path" in stats
        assert "available_space" in stats
    
    @pytest.mark.asyncio
    async def test_error_handling(self, storage_service):
        """Test error handling for various scenarios."""
        # Test getting non-existent evidence
        with pytest.raises(ObjectNotFoundError):
            await storage_service.get_evidence("nonexistent-id")
        
        # Test getting metadata for non-existent object
        with pytest.raises(ObjectNotFoundError):
            await storage_service.get_metadata("nonexistent-id")
        
        # Test applying WORM lock to non-existent object
        with pytest.raises(ObjectNotFoundError):
            await storage_service.ensure_worm_lock("nonexistent-id")
        
        # Test deleting non-existent object
        with pytest.raises(ObjectNotFoundError):
            await storage_service.delete_object("nonexistent-id")
