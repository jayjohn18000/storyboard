"""Policy engine middleware for RBAC and Cerbos integration."""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from enum import Enum
from fastapi import Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class PolicyMode(Enum):
    """Policy enforcement modes."""
    DISABLED = "disabled"
    RBAC = "rbac"
    CERBOS = "cerbos"


class CerbosRequest(BaseModel):
    """Cerbos authorization request model."""
    principal: Dict[str, Any]
    resource: Dict[str, Any]
    actions: List[str]


class CerbosResponse(BaseModel):
    """Cerbos authorization response model."""
    allowed: bool
    reason: Optional[str] = None


class PolicyMiddleware(BaseHTTPMiddleware):
    """Policy enforcement middleware with RBAC and Cerbos support."""
    
    def __init__(self, app):
        super().__init__(app)
        self.policy_mode = PolicyMode(os.getenv("POLICY_MODE", "rbac"))
        self.cerbos_endpoint = os.getenv("CERBOS_ENDPOINT", "http://localhost:3593")
        self.sandbox_mode = os.getenv("MODE", "demonstrative") == "sandbox"
        
        # Excluded paths that don't require policy enforcement
        self.excluded_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
            "/ready",
        }
        
        # Mutating endpoints that should be blocked in sandbox mode
        self.mutating_endpoints = {
            "/api/v1/evidence/upload",
            "/api/v1/evidence/{id}/commit",
            "/api/v1/cases",
            "/api/v1/storyboards/{id}/compile",
            "/api/v1/renders",
            "/api/v1/export",
        }
        
        logger.info(f"Policy middleware initialized with mode: {self.policy_mode.value}")
    
    async def dispatch(self, request: Request, call_next):
        """Process request through policy enforcement middleware."""
        # Skip policy enforcement for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Add policy context to request state
        request.state.policy_mode = self.policy_mode
        request.state.sandbox_mode = self.sandbox_mode
        
        # Check sandbox mode restrictions
        if self.sandbox_mode and self._is_mutating_endpoint(request.url.path, request.method):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mutating operations not allowed in sandbox mode"
            )
        
        # Apply policy enforcement based on mode
        if self.policy_mode == PolicyMode.DISABLED:
            # No policy enforcement
            pass
        elif self.policy_mode == PolicyMode.RBAC:
            await self._enforce_rbac(request)
        elif self.policy_mode == PolicyMode.CERBOS:
            await self._enforce_cerbos(request)
        
        # Continue to next middleware/handler
        response = await call_next(request)
        return response
    
    def _is_mutating_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint performs mutating operations."""
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            return any(path.startswith(endpoint.replace("{id}", "")) for endpoint in self.mutating_endpoints)
        return False
    
    async def _enforce_rbac(self, request: Request):
        """Enforce RBAC-based authorization."""
        # Get user roles from request state (set by auth middleware)
        user_roles = getattr(request.state, "user_roles", [])
        user_id = getattr(request.state, "user_id", None)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Check if user has required role for the endpoint
        required_role = self._get_required_role(request.url.path, request.method)
        if required_role and required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role '{required_role}' not found"
            )
    
    async def _enforce_cerbos(self, request: Request):
        """Enforce Cerbos-based authorization."""
        user_id = getattr(request.state, "user_id", None)
        user_roles = getattr(request.state, "user_roles", [])
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Prepare Cerbos request
        principal = {
            "id": user_id,
            "roles": user_roles,
            "attr": {
                "department": getattr(request.state, "user_department", "default"),
                "region": getattr(request.state, "user_region", "default"),
            }
        }
        
        resource = self._build_resource_context(request)
        actions = [self._get_action_from_method(request.method)]
        
        # Call Cerbos PDP
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.cerbos_endpoint}/api/check",
                    json={
                        "principal": principal,
                        "resource": resource,
                        "actions": actions
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not result.get("allowed", False):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Access denied: {result.get('reason', 'Insufficient permissions')}"
                        )
                else:
                    logger.error(f"Cerbos PDP error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Policy decision point unavailable"
                    )
        
        except httpx.TimeoutException:
            logger.error("Cerbos PDP timeout")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Policy decision point timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"Cerbos PDP request error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Policy decision point unavailable"
            )
    
    def _get_required_role(self, path: str, method: str) -> Optional[str]:
        """Get required role for endpoint based on path and method."""
        # Define role requirements for different endpoints
        role_requirements = {
            ("/api/v1/cases", "POST"): "case_manager",
            ("/api/v1/cases", "GET"): "viewer",
            ("/api/v1/evidence/upload", "POST"): "evidence_manager",
            ("/api/v1/evidence", "GET"): "viewer",
            ("/api/v1/evidence/{id}/commit", "POST"): "evidence_manager",
            ("/api/v1/storyboards", "GET"): "viewer",
            ("/api/v1/storyboards/{id}/compile", "POST"): "storyboard_manager",
            ("/api/v1/renders", "POST"): "render_manager",
            ("/api/v1/renders", "GET"): "viewer",
            ("/api/v1/export", "POST"): "export_manager",
        }
        
        # Find matching requirement
        for (endpoint_pattern, req_method), role in role_requirements.items():
            if method == req_method and self._path_matches_pattern(path, endpoint_pattern):
                return role
        
        return None
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches endpoint pattern."""
        # Simple pattern matching - replace {id} with wildcard
        pattern_parts = pattern.replace("{id}", "*").split("/")
        path_parts = path.split("/")
        
        if len(pattern_parts) != len(path_parts):
            return False
        
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part != "*" and pattern_part != path_part:
                return False
        
        return True
    
    def _build_resource_context(self, request: Request) -> Dict[str, Any]:
        """Build resource context for Cerbos request."""
        path_parts = request.url.path.split("/")
        
        # Extract resource information from path
        resource = {
            "kind": "api_endpoint",
            "id": request.url.path,
            "attr": {
                "path": request.url.path,
                "method": request.method,
                "query_params": dict(request.query_params),
            }
        }
        
        # Add specific resource context based on path
        if "/cases/" in request.url.path:
            case_id = self._extract_id_from_path(request.url.path, "/cases/")
            if case_id:
                resource["kind"] = "case"
                resource["id"] = case_id
        
        elif "/evidence/" in request.url.path:
            evidence_id = self._extract_id_from_path(request.url.path, "/evidence/")
            if evidence_id:
                resource["kind"] = "evidence"
                resource["id"] = evidence_id
        
        elif "/storyboards/" in request.url.path:
            storyboard_id = self._extract_id_from_path(request.url.path, "/storyboards/")
            if storyboard_id:
                resource["kind"] = "storyboard"
                resource["id"] = storyboard_id
        
        elif "/renders/" in request.url.path:
            render_id = self._extract_id_from_path(request.url.path, "/renders/")
            if render_id:
                resource["kind"] = "render"
                resource["id"] = render_id
        
        return resource
    
    def _extract_id_from_path(self, path: str, prefix: str) -> Optional[str]:
        """Extract ID from path after given prefix."""
        try:
            start_idx = path.find(prefix) + len(prefix)
            end_idx = path.find("/", start_idx)
            if end_idx == -1:
                end_idx = len(path)
            return path[start_idx:end_idx]
        except (ValueError, IndexError):
            return None
    
    def _get_action_from_method(self, method: str) -> str:
        """Map HTTP method to Cerbos action."""
        action_mapping = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        return action_mapping.get(method.upper(), "read")


def requires(role: str):
    """Decorator to require specific role for endpoint."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request object in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if request:
                user_roles = getattr(request.state, "user_roles", [])
                if role not in user_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required role '{role}' not found"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def requires_permission(permission: str):
    """Decorator to require specific permission for endpoint."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request object in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if request:
                user_permissions = getattr(request.state, "user_permissions", [])
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required permission '{permission}' not found"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PolicyEnforcer:
    """Policy enforcement utility class."""
    
    def __init__(self, request: Request):
        self.request = request
        self.policy_mode = request.state.policy_mode
        self.sandbox_mode = request.state.sandbox_mode
    
    def can_perform_action(self, action: str, resource_id: Optional[str] = None) -> bool:
        """Check if user can perform action on resource."""
        if self.policy_mode == PolicyMode.DISABLED:
            return True
        
        if self.sandbox_mode and action in ["create", "update", "delete"]:
            return False
        
        # Additional checks can be added here
        return True
    
    def get_user_context(self) -> Dict[str, Any]:
        """Get user context for policy decisions."""
        return {
            "user_id": getattr(self.request.state, "user_id", None),
            "user_roles": getattr(self.request.state, "user_roles", []),
            "user_permissions": getattr(self.request.state, "user_permissions", []),
            "policy_mode": self.policy_mode.value,
            "sandbox_mode": self.sandbox_mode,
        }
