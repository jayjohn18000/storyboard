"""Authentication middleware for API Gateway."""

import os
import jwt
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API Gateway."""
    
    def __init__(self, app):
        super().__init__(app)
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.excluded_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through authentication middleware."""
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )
        
        # Verify JWT token
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Add user info to request state
            request.state.user_id = user_id
            request.state.user_roles = payload.get("roles", [])
            request.state.user_permissions = payload.get("permissions", [])
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Continue to next middleware/handler
        response = await call_next(request)
        return response


def get_current_user(request: Request) -> str:
    """Get current user from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user_id


def get_user_roles(request: Request) -> list:
    """Get user roles from request state."""
    if not hasattr(request.state, "user_roles"):
        return []
    return request.state.user_roles


def get_user_permissions(request: Request) -> list:
    """Get user permissions from request state."""
    if not hasattr(request.state, "user_permissions"):
        return []
    return request.state.user_permissions


def require_role(required_role: str):
    """Decorator to require specific role."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_roles = get_user_roles(request)
            if required_role not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role '{required_role}' not found"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(required_permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_permissions = get_user_permissions(request)
            if required_permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required permission '{required_permission}' not found"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
