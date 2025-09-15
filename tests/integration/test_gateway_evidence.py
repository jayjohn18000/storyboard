"""
Integration tests for API Gateway evidence routes.

Tests the integration between API Gateway and Evidence service,
including happy path scenarios and error handling.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the modules we need to test
from services.shared.http_client import CircuitBreakerError, ResilientHTTPClient
from services.shared.config import get_service_url


class TestEvidenceGatewayIntegration:
    """Test API Gateway evidence integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.evidence_url = "http://localhost:8001"
    
    @pytest.mark.asyncio
    async def test_http_client_happy_path(self):
        """Test HTTP client making successful requests to evidence service."""
        # Mock evidence service response
        mock_response = {
            "evidence": [
                {
                    "evidence_id": "test-evidence-1",
                    "filename": "test-document.pdf",
                    "content_type": "application/pdf",
                    "size_bytes": 1024,
                    "checksum": "abc123",
                    "created_at": "2024-01-01T00:00:00Z",
                    "worm_locked": False,
                    "case_id": "test-case-1",
                    "status": "uploaded",
                    "uploaded_by": "test-user"
                }
            ],
            "total_count": 1,
            "skip": 0,
            "limit": 100
        }
        
        # Create HTTP client
        client = ResilientHTTPClient()
        
        # Mock the httpx client
        with patch.object(client.client, 'request') as mock_request:
            mock_response_obj = httpx.Response(200, json=mock_response)
            mock_request.return_value = mock_response_obj
            
            # Make request
            response = await client.get(f"{self.evidence_url}/evidence")
            
            # Assertions
            assert response == mock_response
            assert "evidence" in response
            assert len(response["evidence"]) == 1
            assert response["evidence"][0]["evidence_id"] == "test-evidence-1"
    
    @pytest.mark.asyncio
    async def test_http_client_upstream_500(self):
        """Test HTTP client handling upstream service error (500)."""
        # Create HTTP client
        client = ResilientHTTPClient()
        
        # Mock the httpx client to raise 500 error
        with patch.object(client.client, 'request') as mock_request:
            mock_response_obj = httpx.Response(500, text="Internal Server Error")
            mock_request.return_value = mock_response_obj
            
            # Make request and expect exception
            with pytest.raises(httpx.HTTPStatusError):
                await client.get(f"{self.evidence_url}/evidence")
    
    @pytest.mark.asyncio
    async def test_http_client_circuit_breaker(self):
        """Test HTTP client circuit breaker functionality."""
        # Create HTTP client with low threshold for testing
        client = ResilientHTTPClient(circuit_breaker_threshold=2)
        
        # Mock the httpx client to fail multiple times
        with patch.object(client.client, 'request') as mock_request:
            mock_response_obj = httpx.Response(500, text="Internal Server Error")
            mock_request.return_value = mock_response_obj
            
            # Make multiple failing requests to trigger circuit breaker
            for _ in range(3):
                with pytest.raises(httpx.HTTPStatusError):
                    await client.get(f"{self.evidence_url}/evidence")
            
            # Circuit breaker should now be open
            circuit_breaker = client._get_circuit_breaker("localhost:8001")
            assert circuit_breaker.state == "OPEN"
            
            # Next request should raise CircuitBreakerError
            with pytest.raises(CircuitBreakerError):
                await client.get(f"{self.evidence_url}/evidence")
    
    @pytest.mark.asyncio
    async def test_http_client_retry_mechanism(self):
        """Test HTTP client retry mechanism."""
        # Create HTTP client with retries
        client = ResilientHTTPClient(retries=2)
        
        # Mock the httpx client to fail then succeed
        call_count = 0
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # First two calls fail
                raise httpx.HTTPStatusError("Server Error", request=None, response=httpx.Response(500))
            else:
                # Third call succeeds
                return httpx.Response(200, json={"status": "ok"})
        
        with patch.object(client.client, 'request', side_effect=mock_request):
            response = await client.get(f"{self.evidence_url}/evidence")
            
            # Should succeed after retries
            assert response == {"status": "ok"}
            assert call_count == 3  # Initial + 2 retries
    
    def test_service_url_configuration(self):
        """Test service URL configuration."""
        # Test getting evidence service URL
        evidence_url = get_service_url("evidence")
        assert str(evidence_url) == "http://localhost:8001"
        
        # Test getting storyboard service URL
        storyboard_url = get_service_url("storyboard")
        assert str(storyboard_url) == "http://localhost:8002"
        
        # Test getting timeline service URL
        timeline_url = get_service_url("timeline")
        assert str(timeline_url) == "http://localhost:8003"
        
        # Test getting render service URL
        render_url = get_service_url("render")
        assert str(render_url) == "http://localhost:8004"
    
    def test_service_url_invalid_service(self):
        """Test service URL configuration with invalid service."""
        with pytest.raises(ValueError, match="Unknown service"):
            get_service_url("invalid-service")
    
    @pytest.mark.asyncio
    async def test_health_check_functionality(self):
        """Test health check functionality."""
        client = ResilientHTTPClient()
        
        # Mock successful health check
        with patch.object(client.client, 'request') as mock_request:
            mock_response_obj = httpx.Response(200, json={"status": "ok", "service": "evidence-processor"})
            mock_request.return_value = mock_response_obj
            
            response = await client.health_check(f"{self.evidence_url}")
            
            assert response["status"] == "ok"
            assert response["service"] == "evidence-processor"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure handling."""
        client = ResilientHTTPClient()
        
        # Mock failed health check
        with patch.object(client.client, 'request') as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError("Service Unavailable", request=None, response=httpx.Response(503))
            
            response = await client.health_check(f"{self.evidence_url}")
            
            assert response["status"] == "unhealthy"
            assert "error" in response
    
    @pytest.mark.asyncio
    async def test_request_with_headers(self):
        """Test HTTP client with custom headers."""
        client = ResilientHTTPClient()
        
        # Mock successful request
        with patch.object(client.client, 'request') as mock_request:
            mock_response_obj = httpx.Response(200, json={"status": "ok"})
            mock_request.return_value = mock_response_obj
            
            headers = {"X-User-ID": "test-user", "Authorization": "Bearer token"}
            response = await client.get(f"{self.evidence_url}/evidence", headers=headers)
            
            # Verify headers were passed
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["headers"]["X-User-ID"] == "test-user"
            assert call_args[1]["headers"]["Authorization"] == "Bearer token"
    
    @pytest.mark.asyncio
    async def test_request_with_params(self):
        """Test HTTP client with query parameters."""
        client = ResilientHTTPClient()
        
        # Mock successful request
        with patch.object(client.client, 'request') as mock_request:
            mock_response_obj = httpx.Response(200, json={"status": "ok"})
            mock_request.return_value = mock_response_obj
            
            params = {"skip": 0, "limit": 10, "status_filter": "uploaded"}
            response = await client.get(f"{self.evidence_url}/evidence", params=params)
            
            # Verify params were passed
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["params"]["skip"] == 0
            assert call_args[1]["params"]["limit"] == 10
            assert call_args[1]["params"]["status_filter"] == "uploaded"