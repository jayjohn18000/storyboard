"""Mode enforcement middleware for Sandbox vs Demonstrative modes."""

import os
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from enum import Enum


class Mode(Enum):
    """System operation modes."""
    SANDBOX = "sandbox"
    DEMONSTRATIVE = "demonstrative"


class ModeEnforcerMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce mode-specific restrictions."""
    
    def __init__(self, app):
        super().__init__(app)
        self.current_mode = Mode(os.getenv("MODE", "demonstrative"))
        self.sandbox_features = {
            "agents": os.getenv("ENABLE_AGENTS", "false").lower() == "true",
            "gpu_rendering": os.getenv("ENABLE_GPU_RENDERING", "false").lower() == "true",
            "distributed_processing": os.getenv("ENABLE_DISTRIBUTED_PROCESSING", "false").lower() == "true",
            "cinematic_rendering": True,  # Only available in sandbox
            "experimental_features": True,  # Only available in sandbox
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through mode enforcement middleware."""
        # Add mode info to request state
        request.state.current_mode = self.current_mode
        request.state.sandbox_features = self.sandbox_features
        
        # Check for mode-specific restrictions
        if self.current_mode == Mode.DEMONSTRATIVE:
            # Enforce demonstrative mode restrictions
            if self._is_sandbox_only_endpoint(request.url.path):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Feature not available in demonstrative mode"
                )
        
        # Continue to next middleware/handler
        response = await call_next(request)
        return response
    
    def _is_sandbox_only_endpoint(self, path: str) -> bool:
        """Check if endpoint is sandbox-only."""
        sandbox_endpoints = [
            "/api/v1/agents/",
            "/api/v1/renders/cinematic",
            "/api/v1/experimental/",
        ]
        
        return any(path.startswith(endpoint) for endpoint in sandbox_endpoints)


class ModeEnforcer:
    """Mode enforcement utility class."""
    
    def __init__(self, request: Request):
        self.request = request
        self.current_mode = request.state.current_mode
        self.sandbox_features = request.state.sandbox_features
    
    def can_create_case(self, user_id: str) -> bool:
        """Check if user can create cases."""
        # In demonstrative mode, only authorized users can create cases
        if self.current_mode == Mode.DEMONSTRATIVE:
            # TODO: Check user permissions via Cerbos
            return True
        return True
    
    def can_list_cases(self, user_id: str) -> bool:
        """Check if user can list cases."""
        return True
    
    def can_view_case(self, user_id: str, case_id: str) -> bool:
        """Check if user can view case."""
        # TODO: Check case-specific permissions
        return True
    
    def can_edit_case(self, user_id: str, case_id: str) -> bool:
        """Check if user can edit case."""
        # TODO: Check case-specific permissions
        return True
    
    def can_delete_case(self, user_id: str, case_id: str) -> bool:
        """Check if user can delete case."""
        # TODO: Check case-specific permissions
        return True
    
    def can_upload_evidence(self, user_id: str) -> bool:
        """Check if user can upload evidence."""
        return True
    
    def can_list_evidence(self, user_id: str) -> bool:
        """Check if user can list evidence."""
        return True
    
    def can_view_evidence(self, user_id: str, evidence_id: str) -> bool:
        """Check if user can view evidence."""
        # TODO: Check evidence-specific permissions
        return True
    
    def can_edit_evidence(self, user_id: str, evidence_id: str) -> bool:
        """Check if user can edit evidence."""
        # TODO: Check evidence-specific permissions
        return True
    
    def can_delete_evidence(self, user_id: str, evidence_id: str) -> bool:
        """Check if user can delete evidence."""
        # TODO: Check evidence-specific permissions
        return True
    
    def can_lock_evidence(self, user_id: str, evidence_id: str) -> bool:
        """Check if user can apply WORM lock to evidence."""
        # TODO: Check evidence-specific permissions
        return True
    
    def can_download_evidence(self, user_id: str, evidence_id: str) -> bool:
        """Check if user can download evidence."""
        # TODO: Check evidence-specific permissions
        return True
    
    def can_create_storyboard(self, user_id: str, case_id: str) -> bool:
        """Check if user can create storyboard."""
        # TODO: Check case-specific permissions
        return True
    
    def can_list_storyboards(self, user_id: str) -> bool:
        """Check if user can list storyboards."""
        return True
    
    def can_view_storyboard(self, user_id: str, storyboard_id: str) -> bool:
        """Check if user can view storyboard."""
        # TODO: Check storyboard-specific permissions
        return True
    
    def can_edit_storyboard(self, user_id: str, storyboard_id: str) -> bool:
        """Check if user can edit storyboard."""
        # TODO: Check storyboard-specific permissions
        return True
    
    def can_delete_storyboard(self, user_id: str, storyboard_id: str) -> bool:
        """Check if user can delete storyboard."""
        # TODO: Check storyboard-specific permissions
        return True
    
    def can_validate_storyboard(self, user_id: str, storyboard_id: str) -> bool:
        """Check if user can validate storyboard."""
        # TODO: Check storyboard-specific permissions
        return True
    
    def can_compile_storyboard(self, user_id: str, storyboard_id: str) -> bool:
        """Check if user can compile storyboard."""
        # TODO: Check storyboard-specific permissions
        return True
    
    def can_create_render(self, user_id: str, case_id: str) -> bool:
        """Check if user can create render."""
        # TODO: Check case-specific permissions
        return True
    
    def can_list_renders(self, user_id: str) -> bool:
        """Check if user can list renders."""
        return True
    
    def can_view_render(self, user_id: str, render_id: str) -> bool:
        """Check if user can view render."""
        # TODO: Check render-specific permissions
        return True
    
    def can_edit_render(self, user_id: str, render_id: str) -> bool:
        """Check if user can edit render."""
        # TODO: Check render-specific permissions
        return True
    
    def can_cancel_render(self, user_id: str, render_id: str) -> bool:
        """Check if user can cancel render."""
        # TODO: Check render-specific permissions
        return True
    
    def can_download_render(self, user_id: str, render_id: str) -> bool:
        """Check if user can download render."""
        # TODO: Check render-specific permissions
        return True
    
    def can_view_queue_stats(self, user_id: str) -> bool:
        """Check if user can view queue stats."""
        return True
    
    def can_export_case(self, user_id: str, case_id: str) -> bool:
        """Check if user can export case."""
        # TODO: Check case-specific permissions
        return True
    
    def can_view_export(self, user_id: str, export_id: str) -> bool:
        """Check if user can view export."""
        # TODO: Check export-specific permissions
        return True
    
    def can_download_export(self, user_id: str, export_id: str) -> bool:
        """Check if user can download export."""
        # TODO: Check export-specific permissions
        return True
    
    def is_sandbox_mode(self) -> bool:
        """Check if system is in sandbox mode."""
        return self.current_mode == Mode.SANDBOX
    
    def is_demonstrative_mode(self) -> bool:
        """Check if system is in demonstrative mode."""
        return self.current_mode == Mode.DEMONSTRATIVE
    
    def can_use_feature(self, feature: str) -> bool:
        """Check if feature is available in current mode."""
        if self.current_mode == Mode.SANDBOX:
            return True
        
        # In demonstrative mode, check if feature is sandbox-only
        return not self.sandbox_features.get(feature, False)
    
    def get_available_render_profiles(self) -> list:
        """Get available render profiles for current mode."""
        if self.current_mode == Mode.SANDBOX:
            return ["neutral", "cinematic"]
        else:
            return ["neutral"]
    
    def get_available_engines(self) -> dict:
        """Get available engines for current mode."""
        engines = {
            "ocr": ["tesseract_local"],
            "asr": ["whisperx_local"],
            "render": ["blender_local"],
        }
        
        if self.current_mode == Mode.SANDBOX:
            engines["ocr"].extend(["tesseract_distributed", "paddleocr"])
            engines["asr"].extend(["whisperx_gpu", "pyannote_diarizer"])
            engines["render"].extend(["blender_gpu", "blender_distributed"])
        
        return engines
