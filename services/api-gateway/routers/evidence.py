"""Evidence management API routes."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from datetime import datetime

from ...shared.models.evidence import Evidence, EvidenceMetadata, EvidenceType, EvidenceStatus
from ...shared.services.evidence_service import EvidenceService
from ...shared.services.database_service import DatabaseService
from ...shared.http_client import get_http_client
from ...shared.config import get_service_url
from ...shared.policy.middleware import requires
from ..middleware.auth import get_current_user
from ..middleware.mode_enforcer import ModeEnforcer

logger = logging.getLogger(__name__)


router = APIRouter()


async def get_evidence_service() -> EvidenceService:
    """Get evidence service instance."""
    db_service = DatabaseService()
    return EvidenceService(db_service)


class EvidenceUploadRequest(BaseModel):
    """Request model for uploading evidence."""
    evidence_type: EvidenceType = Field(..., description="Type of evidence")
    case_id: Optional[str] = Field(None, description="Associated case ID")
    description: Optional[str] = Field(None, description="Evidence description")
    tags: dict = Field(default_factory=dict, description="Evidence tags")


class EvidenceResponse(BaseModel):
    """Response model for evidence data."""
    id: str
    evidence_type: EvidenceType
    metadata: EvidenceMetadata
    status: EvidenceStatus
    storage_id: str
    case_id: Optional[str]
    chain_of_custody: List[dict]
    worm_locked: bool
    processing_result: Optional[dict]


class EvidenceUpdateRequest(BaseModel):
    """Request model for updating evidence."""
    description: Optional[str] = Field(None, description="Evidence description")
    tags: Optional[dict] = Field(None, description="Evidence tags")
    case_id: Optional[str] = Field(None, description="Associated case ID")


@router.post("/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
@requires("evidence_manager")
async def upload_evidence(
    file: UploadFile = File(...),
    evidence_type: EvidenceType = Form(...),
    case_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: str = Form("{}"),  # JSON string
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    evidence_service: EvidenceService = Depends(get_evidence_service)
):
    """Upload evidence file."""
    # Check permissions
    if not mode_enforcer.can_upload_evidence(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to upload evidence"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Read file data
    try:
        file_data = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    # Parse tags
    import json
    try:
        tags_dict = json.loads(tags) if tags else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tags JSON format"
        )
    
    try:
        # Store evidence using service
        evidence = await evidence_service.store_evidence(
            file_data=file_data,
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            evidence_type=evidence_type,
            case_id=case_id or "",
            uploaded_by=current_user,
            description=description,
            tags=tags_dict
        )
        
        # Process evidence asynchronously
        # Note: In production, this would be queued for background processing
        await evidence_service.process_evidence(evidence.id)
        
        return EvidenceResponse(
            id=evidence.id,
            evidence_type=evidence.evidence_type,
            metadata=evidence.metadata,
            status=evidence.status,
            storage_id=evidence.storage_id,
            case_id=evidence.case_id,
            chain_of_custody=evidence.chain_of_custody,
            worm_locked=evidence.worm_locked,
            processing_result=evidence.processing_result.to_dict() if evidence.processing_result else None,
        )
        
    except Exception as e:
        logger.error(f"Failed to upload evidence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload evidence: {str(e)}"
        )


@router.get("/", response_model=List[EvidenceResponse])
async def list_evidence(
    skip: int = 0,
    limit: int = 100,
    evidence_type_filter: Optional[EvidenceType] = None,
    status_filter: Optional[EvidenceStatus] = None,
    case_id_filter: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    evidence_service: EvidenceService = Depends(get_evidence_service)
):
    """
    List evidence with optional filtering.
    
    Retrieves a paginated list of evidence items with optional filtering by type,
    status, and case ID. This endpoint proxies requests to the Evidence service
    and handles authentication, authorization, and error responses.
    
    **Authentication Required**: Yes
    **Authorization**: User must have evidence listing permissions
    
    **Query Parameters**:
    - `skip` (int): Number of items to skip for pagination (default: 0)
    - `limit` (int): Maximum number of items to return (default: 100, max: 1000)
    - `evidence_type_filter` (EvidenceType): Filter by evidence type (document, audio, video, image)
    - `status_filter` (EvidenceStatus): Filter by evidence status (uploaded, processing, processed, error)
    - `case_id_filter` (str): Filter by associated case ID
    
    **Response**:
    Returns a list of EvidenceResponse objects containing:
    - Evidence ID and metadata
    - File information (filename, size, checksum)
    - Processing status and results
    - Chain of custody information
    - WORM lock status
    
    **Error Responses**:
    - `403 Forbidden`: Insufficient permissions to list evidence
    - `502 Bad Gateway`: Upstream Evidence service error or circuit breaker open
    
    **Example**:
    ```bash
    GET /api/v1/evidence?skip=0&limit=10&evidence_type_filter=document&status_filter=processed
    ```
    """
    # Check permissions
    if not mode_enforcer.can_list_evidence(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to list evidence"
        )
    
    try:
        # Get evidence from service
        evidence_list = await evidence_service.list_evidence(
            case_id=case_id_filter,
            skip=skip,
            limit=limit,
            status_filter=status_filter
        )
        
        # Filter by evidence type if specified
        if evidence_type_filter:
            evidence_list = [e for e in evidence_list if e.evidence_type == evidence_type_filter]
        
        # Convert to response format
        return [
            EvidenceResponse(
                id=evidence.id,
                evidence_type=evidence.evidence_type,
                metadata=evidence.metadata,
                status=evidence.status,
                storage_id=evidence.storage_id,
                case_id=evidence.case_id,
                chain_of_custody=evidence.chain_of_custody,
                worm_locked=evidence.worm_locked,
                processing_result=evidence.processing_result.to_dict() if evidence.processing_result else None,
            )
            for evidence in evidence_list
        ]
        
    except Exception as e:
        # Log error and return 502 Bad Gateway
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve evidence list: {str(e)}"
        )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    evidence_service: EvidenceService = Depends(get_evidence_service)
):
    """
    Get a specific evidence item by ID.
    
    Retrieves detailed information about a specific evidence item by its ID.
    This endpoint proxies requests to the Evidence service and handles
    authentication, authorization, and error responses.
    
    **Authentication Required**: Yes
    **Authorization**: User must have evidence viewing permissions for the specific evidence
    
    **Path Parameters**:
    - `evidence_id` (str): Unique identifier of the evidence item (UUID format)
    
    **Response**:
    Returns an EvidenceResponse object containing:
    - Evidence ID and metadata
    - File information (filename, size, checksum, content type)
    - Processing status and results
    - Chain of custody information
    - WORM lock status
    - Associated case ID
    
    **Error Responses**:
    - `403 Forbidden`: Insufficient permissions to view evidence
    - `404 Not Found`: Evidence item not found
    - `502 Bad Gateway`: Upstream Evidence service error or circuit breaker open
    
    **Example**:
    ```bash
    GET /api/v1/evidence/123e4567-e89b-12d3-a456-426614174000
    ```
    """
    # Check permissions
    if not mode_enforcer.can_view_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view evidence"
        )
    
    try:
        # Get evidence from service
        evidence = await evidence_service.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        return EvidenceResponse(
            id=evidence.id,
            evidence_type=evidence.evidence_type,
            metadata=evidence.metadata,
            status=evidence.status,
            storage_id=evidence.storage_id,
            case_id=evidence.case_id,
            chain_of_custody=evidence.chain_of_custody,
            worm_locked=evidence.worm_locked,
            processing_result=evidence.processing_result.to_dict() if evidence.processing_result else None,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Log error and return 502 Bad Gateway
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve evidence: {str(e)}"
        )


@router.put("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    request: EvidenceUpdateRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Update evidence metadata."""
    # Check permissions
    if not mode_enforcer.can_edit_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit evidence"
        )
    
    # TODO: Get evidence from database
    # evidence = await evidence_service.get_evidence(evidence_id)
    # if not evidence:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Evidence not found"
    #     )
    
    # Check if evidence is WORM locked
    # if evidence.worm_locked:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Cannot modify WORM-locked evidence"
    #     )
    
    # TODO: Update evidence
    # updated_evidence = await evidence_service.update_evidence(
    #     evidence_id, 
    #     request.dict(exclude_unset=True)
    # )
    
    # Mock response for now
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Evidence not found"
    )


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Delete evidence."""
    # Check permissions
    if not mode_enforcer.can_delete_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete evidence"
        )
    
    # TODO: Get evidence from database
    # evidence = await evidence_service.get_evidence(evidence_id)
    # if not evidence:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Evidence not found"
    #     )
    
    # Check if evidence is WORM locked
    # if evidence.worm_locked:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Cannot delete WORM-locked evidence"
    #     )
    
    # TODO: Delete evidence
    # await evidence_service.delete_evidence(evidence_id)
    
    # Mock response for now
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Evidence not found"
    )


@router.post("/{evidence_id}/worm-lock", response_model=dict)
async def apply_worm_lock(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Apply WORM lock to evidence."""
    # Check permissions
    if not mode_enforcer.can_lock_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to lock evidence"
        )
    
    # TODO: Get evidence from database
    # evidence = await evidence_service.get_evidence(evidence_id)
    # if not evidence:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Evidence not found"
    #     )
    
    # Check if already locked
    # if evidence.worm_locked:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Evidence is already WORM locked"
    #     )
    
    try:
        # Get HTTP client and evidence service URL
        http_client = get_http_client()
        evidence_url = get_service_url("evidence")
        
        # Make HTTP call to evidence service
        response = await http_client.post(
            f"{evidence_url}/evidence/{evidence_id}/commit",
            headers={"X-User-ID": current_user}
        )
        
        return {
            "evidence_id": evidence_id,
            "status": "committed",
            "immutable_at": response.get("immutable_at"),
            "locked_by": response.get("locked_by"),
            "lock_reason": response.get("lock_reason")
        }
        
    except Exception as e:
        # Log error and return 502 Bad Gateway
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to commit evidence: {str(e)}"
        )


@router.post("/{evidence_id}/commit", response_model=dict)
@requires("evidence_manager")
async def commit_evidence(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Commit evidence and apply WORM lock."""
    # Check permissions
    if not mode_enforcer.can_lock_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to commit evidence"
        )
    
    try:
        # Get HTTP client and evidence service URL
        http_client = get_http_client()
        evidence_url = get_service_url("evidence")
        
        # Make HTTP call to evidence service
        response = await http_client.post(
            f"{evidence_url}/evidence/{evidence_id}/commit",
            headers={"X-User-ID": current_user}
        )
        
        return {
            "evidence_id": evidence_id,
            "status": "committed",
            "immutable_at": response.get("immutable_at"),
            "locked_by": response.get("locked_by"),
            "lock_reason": response.get("lock_reason")
        }
        
    except Exception as e:
        # Log error and return 502 Bad Gateway
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to commit evidence: {str(e)}"
        )


@router.get("/{evidence_id}/download")
async def download_evidence(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Download evidence file."""
    # Check permissions
    if not mode_enforcer.can_download_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download evidence"
        )
    
    # TODO: Get evidence from database
    # evidence = await evidence_service.get_evidence(evidence_id)
    # if not evidence:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Evidence not found"
    #     )
    
    # TODO: Get file data from storage
    # file_data = await evidence_service.get_evidence_file(evidence_id)
    
    # Mock response for now
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Evidence not found"
    )


@router.get("/{evidence_id}/chain-of-custody", response_model=List[dict])
async def get_chain_of_custody(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Get chain of custody for evidence."""
    # Check permissions
    if not mode_enforcer.can_view_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view chain of custody"
        )
    
    # TODO: Get evidence from database
    # evidence = await evidence_service.get_evidence(evidence_id)
    # if not evidence:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Evidence not found"
    #     )
    
    # return evidence.chain_of_custody
    
    # Mock response for now
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Evidence not found"
    )
