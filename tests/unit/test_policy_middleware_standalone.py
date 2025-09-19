"""Standalone unit tests for policy middleware without database dependencies."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.testclient import TestClient
from starlette.responses import Response

# Import only the policy middleware components we need
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.shared.policy.middleware import (
    PolicyMiddleware,
    PolicyMode,
    requires,
    requires_permission,
    PolicyEnforcer,
    CerbosRequest,
    CerbosResponse,
)


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.post("/test-create")
    @requires("case_manager")
    async def test_create():
        return {"message": "created"}
    
    @app.get("/test-permission")
    @requires_permission("read_cases")
    async def test_permission():
        return {"message": "permission granted"}
    
    return app


@pytest.fixture
def policy_middleware(app):
    """Create policy middleware instance."""
    return PolicyMiddleware(app)


@pytest.fixture
def mock_request():
    """Create mock request."""
    request = MagicMock(spec=Request)
    request.url.path = "/test"
    request.method = "GET"
    request.query_params = {}
    request.state = MagicMock()
    request.state.user_id = "test_user"
    request.state.user_roles = ["viewer"]
    request.state.user_permissions = ["read_cases"]
    return request


class TestPolicyMiddleware:
    """Test policy middleware functionality."""
    
    def test_init_disabled_mode(self):
        """Test middleware initialization in disabled mode."""
        with patch.dict("os.environ", {"POLICY_MODE": "disabled"}):
            middleware = PolicyMiddleware(MagicMock())
            assert middleware.policy_mode == PolicyMode.DISABLED
    
    def test_init_rbac_mode(self):
        """Test middleware initialization in RBAC mode."""
        with patch.dict("os.environ", {"POLICY_MODE": "rbac"}):
            middleware = PolicyMiddleware(MagicMock())
            assert middleware.policy_mode == PolicyMode.RBAC
    
    def test_init_cerbos_mode(self):
        """Test middleware initialization in Cerbos mode."""
        with patch.dict("os.environ", {"POLICY_MODE": "cerbos"}):
            middleware = PolicyMiddleware(MagicMock())
            assert middleware.policy_mode == PolicyMode.CERBOS
    
    @pytest.mark.asyncio
    async def test_excluded_paths_skip_policy(self, policy_middleware, mock_request):
        """Test that excluded paths skip policy enforcement."""
        mock_request.url.path = "/health"
        
        async def mock_call_next(request):
            return Response("ok")
        
        # Should not raise any exceptions
        response = await policy_middleware.dispatch(mock_request, mock_call_next)
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_sandbox_mode_blocks_mutating_operations(self, mock_request):
        """Test that sandbox mode blocks mutating operations."""
        with patch.dict("os.environ", {"MODE": "sandbox"}):
            middleware = PolicyMiddleware(MagicMock())
            mock_request.url.path = "/api/v1/evidence/upload"
            mock_request.method = "POST"
            
            async def mock_call_next(request):
                return Response("ok")
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(mock_request, mock_call_next)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Mutating operations not allowed in sandbox mode" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_rbac_enforcement_missing_user(self, mock_request):
        """Test RBAC enforcement with missing user."""
        with patch.dict("os.environ", {"POLICY_MODE": "rbac"}):
            middleware = PolicyMiddleware(MagicMock())
            mock_request.state.user_id = None
            
            async def mock_call_next(request):
                return Response("ok")
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(mock_request, mock_call_next)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_rbac_enforcement_insufficient_role(self, mock_request):
        """Test RBAC enforcement with insufficient role."""
        with patch.dict("os.environ", {"POLICY_MODE": "rbac"}):
            middleware = PolicyMiddleware(MagicMock())
            mock_request.url.path = "/api/v1/cases"
            mock_request.method = "POST"
            mock_request.state.user_roles = ["viewer"]  # Missing case_manager role
            
            async def mock_call_next(request):
                return Response("ok")
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(mock_request, mock_call_next)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Required role 'case_manager' not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_cerbos_enforcement_success(self, mock_request):
        """Test Cerbos enforcement with successful authorization."""
        with patch.dict("os.environ", {"POLICY_MODE": "cerbos", "CERBOS_ENDPOINT": "http://localhost:3593"}):
            middleware = PolicyMiddleware(MagicMock())
            
            # Mock successful Cerbos response
            mock_response = httpx.Response(
                status_code=200,
                json={"allowed": True}
            )
            
            with patch("httpx.AsyncClient.post", return_value=mock_response):
                async def mock_call_next(request):
                    return Response("ok")
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                assert response is not None
    
    @pytest.mark.asyncio
    async def test_cerbos_enforcement_denied(self, mock_request):
        """Test Cerbos enforcement with denied authorization."""
        with patch.dict("os.environ", {"POLICY_MODE": "cerbos", "CERBOS_ENDPOINT": "http://localhost:3593"}):
            middleware = PolicyMiddleware(MagicMock())
            
            # Mock denied Cerbos response
            mock_response = httpx.Response(
                status_code=200,
                json={"allowed": False, "reason": "Insufficient permissions"}
            )
            
            with patch("httpx.AsyncClient.post", return_value=mock_response):
                async def mock_call_next(request):
                    return Response("ok")
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "Access denied" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_cerbos_timeout(self, mock_request):
        """Test Cerbos enforcement with timeout."""
        with patch.dict("os.environ", {"POLICY_MODE": "cerbos", "CERBOS_ENDPOINT": "http://localhost:3593"}):
            middleware = PolicyMiddleware(MagicMock())
            
            with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
                async def mock_call_next(request):
                    return Response("ok")
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Policy decision point timeout" in str(exc_info.value.detail)


class TestRequiresDecorator:
    """Test @requires decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_requires_decorator_success(self):
        """Test @requires decorator with sufficient role."""
        @requires("viewer")
        async def test_function(request):
            return {"message": "success"}
        
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_roles = ["viewer"]
        
        result = await test_function(mock_request)
        assert result["message"] == "success"
    
    @pytest.mark.asyncio
    async def test_requires_decorator_insufficient_role(self):
        """Test @requires decorator with insufficient role."""
        @requires("admin")
        async def test_function(request):
            return {"message": "success"}
        
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_roles = ["viewer"]
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required role 'admin' not found" in str(exc_info.value.detail)


class TestRequiresPermissionDecorator:
    """Test @requires_permission decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_requires_permission_decorator_success(self):
        """Test @requires_permission decorator with sufficient permission."""
        @requires_permission("read_cases")
        async def test_function(request):
            return {"message": "success"}
        
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_permissions = ["read_cases"]
        
        result = await test_function(mock_request)
        assert result["message"] == "success"
    
    @pytest.mark.asyncio
    async def test_requires_permission_decorator_insufficient_permission(self):
        """Test @requires_permission decorator with insufficient permission."""
        @requires_permission("write_cases")
        async def test_function(request):
            return {"message": "success"}
        
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_permissions = ["read_cases"]
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Required permission 'write_cases' not found" in str(exc_info.value.detail)


class TestPolicyEnforcer:
    """Test PolicyEnforcer utility class."""
    
    def test_can_perform_action_disabled_mode(self, mock_request):
        """Test action permission in disabled mode."""
        with patch.dict("os.environ", {"POLICY_MODE": "disabled"}):
            mock_request.state.policy_mode = PolicyMode.DISABLED
            mock_request.state.sandbox_mode = False
            
            enforcer = PolicyEnforcer(mock_request)
            assert enforcer.can_perform_action("create") is True
    
    def test_can_perform_action_sandbox_mode(self, mock_request):
        """Test action permission in sandbox mode."""
        with patch.dict("os.environ", {"POLICY_MODE": "rbac"}):
            mock_request.state.policy_mode = PolicyMode.RBAC
            mock_request.state.sandbox_mode = True
            
            enforcer = PolicyEnforcer(mock_request)
            assert enforcer.can_perform_action("create") is False
            assert enforcer.can_perform_action("read") is True
    
    def test_get_user_context(self, mock_request):
        """Test getting user context."""
        mock_request.state.policy_mode = PolicyMode.RBAC
        mock_request.state.sandbox_mode = False
        
        enforcer = PolicyEnforcer(mock_request)
        context = enforcer.get_user_context()
        
        assert context["user_id"] == "test_user"
        assert context["user_roles"] == ["viewer"]
        assert context["user_permissions"] == ["read_cases"]
        assert context["policy_mode"] == "rbac"
        assert context["sandbox_mode"] is False


class TestCerbosModels:
    """Test Cerbos request/response models."""
    
    def test_cerbos_request_model(self):
        """Test Cerbos request model."""
        request = CerbosRequest(
            principal={"id": "user1", "roles": ["viewer"]},
            resource={"kind": "case", "id": "case1"},
            actions=["read"]
        )
        
        assert request.principal["id"] == "user1"
        assert request.resource["kind"] == "case"
        assert request.actions == ["read"]
    
    def test_cerbos_response_model(self):
        """Test Cerbos response model."""
        response = CerbosResponse(
            allowed=True,
            reason="User has sufficient permissions"
        )
        
        assert response.allowed is True
        assert response.reason == "User has sufficient permissions"


class TestIntegration:
    """Integration tests for policy middleware with FastAPI."""
    
    def test_middleware_integration_disabled_mode(self):
        """Test middleware integration in disabled mode."""
        with patch.dict("os.environ", {"POLICY_MODE": "disabled"}):
            app = FastAPI()
            app.add_middleware(PolicyMiddleware)
            
            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}
            
            client = TestClient(app)
            response = client.get("/test")
            assert response.status_code == 200
    
    def test_middleware_integration_rbac_mode(self):
        """Test middleware integration in RBAC mode."""
        with patch.dict("os.environ", {"POLICY_MODE": "rbac"}):
            app = FastAPI()
            app.add_middleware(PolicyMiddleware)
            
            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}
            
            client = TestClient(app)
            # Should fail without authentication
            response = client.get("/test")
            assert response.status_code == 401
