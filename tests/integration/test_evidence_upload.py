"""
Integration tests for evidence upload functionality.

Tests the upload pipeline including file validation, hashing,
storage, and deduplication.
"""

import pytest
import hashlib
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from io import BytesIO

from services.evidence_processor.main import app


class TestEvidenceUpload:
    """Test evidence upload functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_file_data(self):
        """Sample file data for testing."""
        return b"This is a test document content for evidence upload."
    
    @pytest.fixture
    def sample_file_hash(self, sample_file_data):
        """SHA256 hash of sample file data."""
        return hashlib.sha256(sample_file_data).hexdigest()
    
    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service."""
        mock_service = AsyncMock()
        mock_service.store_evidence.return_value = "evidence/test-evidence-id"
        mock_service.get_evidence.return_value = b"test file data"
        mock_service.get_metadata.return_value = AsyncMock(
            content_type="text/plain",
            size_bytes=100,
            checksum="test-checksum",
            created_at="2024-01-01T00:00:00Z",
            worm_locked=False,
            tags={"filename": "test.txt", "case_id": "case-123"}
        )
        return mock_service
    
    @pytest.mark.asyncio
    async def test_upload_small_file_success(self, client, sample_file_data, sample_file_hash, mock_storage_service):
        """Test successful upload of small file."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            with patch('services.evidence_processor.main.metrics') as mock_metrics:
                # Create file upload
                files = {"file": ("test.txt", BytesIO(sample_file_data), "text/plain")}
                data = {
                    "case_id": "case-123",
                    "description": "Test evidence file",
                    "tags": json.dumps({"category": "document"})
                }
                
                # Make request
                response = client.post("/evidence/upload", files=files, data=data)
                
                # Assertions
                assert response.status_code == 200
                result = response.json()
                
                assert result["evidence_id"] == sample_file_hash[:16]
                assert result["file_hash"] == sample_file_hash
                assert result["filename"] == "test.txt"
                assert result["content_type"] == "text/plain"
                assert result["size_bytes"] == len(sample_file_data)
                assert result["status"] == "uploaded"
                
                # Verify storage service was called
                mock_storage_service.store_evidence.assert_called_once()
                call_args = mock_storage_service.store_evidence.call_args
                assert call_args[0][0] == sample_file_data  # file_data
                assert call_args[0][2] == sample_file_hash[:16]  # evidence_id
                
                # Verify metrics were recorded
                mock_metrics.record_evidence_uploaded.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, client, mock_storage_service):
        """Test upload rejection for file exceeding size limit."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            with patch.dict('os.environ', {'MAX_UPLOAD_MB': '1'}):  # 1MB limit
                # Create large file (2MB)
                large_data = b"x" * (2 * 1024 * 1024)
                files = {"file": ("large.txt", BytesIO(large_data), "text/plain")}
                
                # Make request
                response = client.post("/evidence/upload", files=files)
                
                # Assertions
                assert response.status_code == 413
                result = response.json()
                assert "File size exceeds limit" in result["detail"]
                assert "1MB" in result["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_no_filename(self, client, mock_storage_service):
        """Test upload rejection when no filename provided."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            # Create file upload without filename
            files = {"file": ("", BytesIO(b"test"), "text/plain")}
            
            # Make request
            response = client.post("/evidence/upload", files=files)
            
            # Assertions
            assert response.status_code == 400
            result = response.json()
            assert "No filename provided" in result["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_invalid_tags_json(self, client, sample_file_data, mock_storage_service):
        """Test upload rejection with invalid tags JSON."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            files = {"file": ("test.txt", BytesIO(sample_file_data), "text/plain")}
            data = {"tags": "invalid json"}
            
            # Make request
            response = client.post("/evidence/upload", files=files, data=data)
            
            # Assertions
            assert response.status_code == 400
            result = response.json()
            assert "Invalid tags JSON format" in result["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_deduplication(self, client, sample_file_data, sample_file_hash, mock_storage_service):
        """Test that duplicate files are deduplicated by hash."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            # Upload same file twice
            files1 = {"file": ("test1.txt", BytesIO(sample_file_data), "text/plain")}
            files2 = {"file": ("test2.txt", BytesIO(sample_file_data), "text/plain")}
            
            # First upload
            response1 = client.post("/evidence/upload", files=files1)
            assert response1.status_code == 200
            result1 = response1.json()
            
            # Second upload
            response2 = client.post("/evidence/upload", files=files2)
            assert response2.status_code == 200
            result2 = response2.json()
            
            # Both should have same evidence_id (deduplication)
            assert result1["evidence_id"] == result2["evidence_id"]
            assert result1["file_hash"] == result2["file_hash"]
            assert result1["file_hash"] == sample_file_hash
    
    @pytest.mark.asyncio
    async def test_get_evidence_success(self, client, mock_storage_service):
        """Test successful evidence retrieval."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            # Make request
            response = client.get("/evidence/test-evidence-id")
            
            # Assertions
            assert response.status_code == 200
            result = response.json()
            
            assert result["evidence_id"] == "test-evidence-id"
            assert "file_data" in result
            assert "metadata" in result
            
            metadata = result["metadata"]
            assert metadata["filename"] == "test.txt"
            assert metadata["content_type"] == "text/plain"
            assert metadata["size_bytes"] == 100
            assert metadata["checksum"] == "test-checksum"
            assert metadata["worm_locked"] is False
    
    @pytest.mark.asyncio
    async def test_get_evidence_not_found(self, client, mock_storage_service):
        """Test evidence retrieval when not found."""
        # Mock storage service to raise exception
        mock_storage_service.get_evidence.side_effect = Exception("Not found")
        
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            # Make request
            response = client.get("/evidence/nonexistent-id")
            
            # Assertions
            assert response.status_code == 404
            result = response.json()
            assert "Evidence not found" in result["detail"]
    
    @pytest.mark.asyncio
    async def test_list_evidence_success(self, client, mock_storage_service):
        """Test successful evidence listing."""
        # Mock list_objects to return test data
        async def mock_list_objects(prefix="", limit=100):
            metadata = AsyncMock(
                object_id="evidence/test-id",
                content_type="text/plain",
                size_bytes=100,
                checksum="test-checksum",
                created_at="2024-01-01T00:00:00Z",
                worm_locked=False,
                tags={"filename": "test.txt", "case_id": "case-123"}
            )
            yield metadata
        
        mock_storage_service.list_objects = mock_list_objects
        
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            # Make request
            response = client.get("/evidence")
            
            # Assertions
            assert response.status_code == 200
            result = response.json()
            
            assert "evidence" in result
            assert "total_count" in result
            assert len(result["evidence"]) == 1
            
            evidence = result["evidence"][0]
            assert evidence["evidence_id"] == "test-id"
            assert evidence["filename"] == "test.txt"
            assert evidence["content_type"] == "text/plain"
            assert evidence["case_id"] == "case-123"
    
    @pytest.mark.asyncio
    async def test_list_evidence_with_case_filter(self, client, mock_storage_service):
        """Test evidence listing with case ID filter."""
        # Mock list_objects to return test data
        async def mock_list_objects(prefix="", limit=100):
            metadata = AsyncMock(
                object_id="evidence/test-id",
                content_type="text/plain",
                size_bytes=100,
                checksum="test-checksum",
                created_at="2024-01-01T00:00:00Z",
                worm_locked=False,
                tags={"filename": "test.txt", "case_id": "case-123"}
            )
            yield metadata
        
        mock_storage_service.list_objects = mock_list_objects
        
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            # Make request with case filter
            response = client.get("/evidence?case_id=case-123")
            
            # Assertions
            assert response.status_code == 200
            result = response.json()
            
            assert len(result["evidence"]) == 1
            assert result["evidence"][0]["case_id"] == "case-123"
    
    @pytest.mark.asyncio
    async def test_mime_type_detection(self, client, sample_file_data, mock_storage_service):
        """Test MIME type detection for various file types."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            # Test PDF file
            files = {"file": ("document.pdf", BytesIO(sample_file_data), None)}
            
            response = client.post("/evidence/upload", files=files)
            assert response.status_code == 200
            
            result = response.json()
            assert result["content_type"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_virus_scan_hook_placeholder(self, client, sample_file_data, mock_storage_service):
        """Test that virus scan hook placeholder is present."""
        with patch('services.evidence_processor.main.storage_service', mock_storage_service):
            files = {"file": ("test.txt", BytesIO(sample_file_data), "text/plain")}
            
            response = client.post("/evidence/upload", files=files)
            assert response.status_code == 200
            
            # Verify storage service was called (virus scan would be called here in real implementation)
            mock_storage_service.store_evidence.assert_called_once()
