"""
Shared HTTP client with retries, circuit breaker, and logging.

This module provides a resilient HTTP client for inter-service communication
with automatic retries, circuit breaker pattern, and comprehensive logging.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Simple in-memory circuit breaker implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Time in seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ResilientHTTPClient:
    """HTTP client with retries, circuit breaker, and logging."""
    
    def __init__(
        self,
        timeout: float = 5.0,
        retries: int = 3,
        backoff: float = 0.25,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 30.0,
    ):
        """
        Initialize resilient HTTP client.
        
        Args:
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            backoff: Base backoff time in seconds
            circuit_breaker_threshold: Circuit breaker failure threshold
            circuit_breaker_timeout: Circuit breaker recovery timeout
        """
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Create HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )
    
    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30.0
            )
        return self.circuit_breakers[service_name]
    
    def _get_service_name_from_url(self, url: str) -> str:
        """Extract service name from URL."""
        parsed = urlparse(url)
        hostname = parsed.hostname or "unknown"
        port = parsed.port or 80
        return f"{hostname}:{port}"
    
    async def request_json(
        self,
        method: str,
        url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retries and circuit breaker.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            json: JSON payload for request body
            params: Query parameters
            headers: Request headers
            timeout: Request timeout (overrides default)
            retries: Number of retries (overrides default)
            backoff: Backoff time (overrides default)
            
        Returns:
            Response JSON data
            
        Raises:
            CircuitBreakerError: When circuit breaker is open
            httpx.HTTPError: For HTTP errors
        """
        service_name = self._get_service_name_from_url(url)
        circuit_breaker = self._get_circuit_breaker(service_name)
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            raise CircuitBreakerError(f"Circuit breaker is open for {service_name}")
        
        # Generate request ID for logging
        request_id = str(uuid.uuid4())[:8]
        
        # Use provided values or defaults
        timeout_val = timeout or self.timeout
        retries_val = retries or self.retries
        backoff_val = backoff or self.backoff
        
        # Configure retry strategy
        retry_strategy = retry(
            stop=stop_after_attempt(retries_val + 1),
            wait=wait_exponential(multiplier=backoff_val, min=backoff_val, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        
        start_time = time.time()
        
        try:
            # Make request with retries
            response = await retry_strategy(self._make_request)(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
                timeout=timeout_val,
                request_id=request_id,
                service_name=service_name,
            )
            
            # Record success
            circuit_breaker.record_success()
            
            # Log successful request
            latency = time.time() - start_time
            logger.info(
                f"HTTP request successful",
                extra={
                    "request_id": request_id,
                    "service": service_name,
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "latency_ms": round(latency * 1000, 2),
                }
            )
            
            return response.json()
            
        except Exception as e:
            # Record failure
            circuit_breaker.record_failure()
            
            # Log failed request
            latency = time.time() - start_time
            logger.error(
                f"HTTP request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "service": service_name,
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "latency_ms": round(latency * 1000, 2),
                }
            )
            
            raise
    
    async def _make_request(
        self,
        method: str,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0,
        request_id: str = "",
        service_name: str = "",
    ) -> httpx.Response:
        """Make single HTTP request."""
        # Add request ID to headers
        request_headers = headers or {}
        request_headers["X-Request-ID"] = request_id
        
        # Make request
        response = await self.client.request(
            method=method,
            url=url,
            json=json,
            params=params,
            headers=request_headers,
            timeout=timeout,
        )
        
        # Raise for HTTP errors
        response.raise_for_status()
        
        return response
    
    async def get(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        return await self.request_json(
            "GET",
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
        )
    
    async def post(
        self,
        url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        return await self.request_json(
            "POST",
            url,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
        )
    
    async def put(
        self,
        url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.request_json(
            "PUT",
            url,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
        )
    
    async def delete(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.request_json(
            "DELETE",
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
        )
    
    async def health_check(self, url: str) -> Dict[str, Any]:
        """Check service health."""
        try:
            return await self.get(f"{url}/health", timeout=2.0, retries=1)
        except Exception as e:
            logger.warning(f"Health check failed for {url}: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, 'client'):
            asyncio.create_task(self.client.aclose())


# Global HTTP client instance
_http_client: Optional[ResilientHTTPClient] = None


def get_http_client() -> ResilientHTTPClient:
    """Get global HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = ResilientHTTPClient()
    return _http_client


async def close_http_client():
    """Close global HTTP client."""
    global _http_client
    if _http_client is not None:
        await _http_client.close()
        _http_client = None


# Convenience functions for common operations
async def request_json(
    method: str,
    url: str,
    *,
    json: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 5.0,
    retries: int = 3,
    backoff: float = 0.25,
) -> Dict[str, Any]:
    """
    Convenience function to make HTTP request.
    
    Args:
        method: HTTP method
        url: Request URL
        json: JSON payload
        params: Query parameters
        headers: Request headers
        timeout: Request timeout
        retries: Number of retries
        backoff: Backoff time
        
    Returns:
        Response JSON data
    """
    client = get_http_client()
    return await client.request_json(
        method=method,
        url=url,
        json=json,
        params=params,
        headers=headers,
        timeout=timeout,
        retries=retries,
        backoff=backoff,
    )


async def get_service_health(service_url: str) -> Dict[str, Any]:
    """
    Convenience function to check service health.
    
    Args:
        service_url: Service base URL
        
    Returns:
        Health check response
    """
    client = get_http_client()
    return await client.health_check(service_url)
