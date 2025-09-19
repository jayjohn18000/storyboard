"""Evidence management API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from datetime import datetime

from ...shared.models.evidence import Evidence, EvidenceMetadata, EvidenceType, EvidenceStatus
from ...shared.http_client import get_http_client
from ...shared.config import get_service_url
from ...shared.database import get_db_session
from ...shared.services.database_service import DatabaseService
from ...shared.policy.middleware import requires
from ..middleware.auth import get_current_user
from ..middleware.mode_enforcer import ModeEnforcer


router = APIRouter()


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
    mode_enforcer: ModeEnforcer = Depends()
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
    
    # Create evidence metadata
    metadata = EvidenceMetadata(
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(file_data),
        checksum="",  # Will be calculated by storage service
        uploaded_by=current_user,
        description=description or "",
        tags=tags_dict,
    )
    
    # Create evidence
    evidence = Evidence(
        evidence_type=evidence_type,
        metadata=metadata,
        case_id=case_id,
    )
    
    # Store evidence and process via evidence service
    try:
        # Get HTTP client and evidence service URL
        http_client = get_http_client()
        evidence_url = get_service_url("evidence")
        
        # Prepare form data for evidence service
        form_data = {
            "file": (file.filename, file_data, file.content_type or "application/octet-stream"),
            "case_id": case_id or "",
            "description": description or "",
            "tags": tags
        }
        
        # Make HTTP call to evidence service
        response = await http_client.post(
            f"{evidence_url}/evidence/upload",
            files=form_data,
            headers={"X-User-ID": current_user}
        )
        
        # Update evidence with storage_id from response
        evidence.storage_id = response.get("object_id", "")
        
        # Store evidence in database
        db_service = DatabaseService(db_session)
        evidence_record = await db_service.create_evidence(
            evidence_type=evidence_type.value,
            metadata=evidence.metadata.to_dict(),
            case_id=case_id,
            storage_id=evidence.storage_id,
            uploaded_by=current_user
        )
        
        # Create audit log
        await db_service.create_audit_log(
            user_id=current_user,
            action="upload_evidence",
            resource_type="evidence",
            resource_id=str(evidence_record.id),
            details={"filename": file.filename, "size": len(file_data)}
        )
        
        # Update evidence ID with database ID
        evidence.id = str(evidence_record.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to store evidence: {str(e)}"
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


@router.get("/", response_model=List[EvidenceResponse])
async def list_evidence(
    skip: int = 0,
    limit: int = 100,
    evidence_type_filter: Optional[EvidenceType] = None,
    status_filter: Optional[EvidenceStatus] = None,
    case_id_filter: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
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
        # Get HTTP client and evidence service URL
        http_client = get_http_client()
        evidence_url = get_service_url("evidence")
        
        # Build query parameters
        params = {
            "skip": skip,
            "limit": limit,
        }
        if evidence_type_filter:
            params["evidence_type_filter"] = evidence_type_filter.value
        if status_filter:
            params["status_filter"] = status_filter.value
        if case_id_filter:
            params["case_id_filter"] = case_id_filter
        
        # Make HTTP call to evidence service
        response = await http_client.get(
            f"{evidence_url}/evidence",
            params=params,
            headers={"X-User-ID": current_user}
        )
        
        # Convert response to EvidenceResponse objects
        evidence_list = []
        for evidence_data in response.get("evidence", []):
            # Map the response format to EvidenceResponse format
            evidence_response = EvidenceResponse(
                id=evidence_data["evidence_id"],
                evidence_type=EvidenceType.DOCUMENT,  # Default, should be determined from content_type
                metadata=EvidenceMetadata(
                    filename=evidence_data["filename"],
                    content_type=evidence_data["content_type"],
                    size_bytes=evidence_data["size_bytes"],
                    checksum=evidence_data["checksum"],
                    uploaded_by=evidence_data.get("uploaded_by", "unknown"),
                    description="",
                    tags={}
                ),
                status=EvidenceStatus.UPLOADED,  # Map from status string
                storage_id=evidence_data["evidence_id"],
                case_id=evidence_data.get("case_id"),
                chain_of_custody=[],
                worm_locked=evidence_data.get("worm_locked", False),
                processing_result=None
            )
            evidence_list.append(evidence_response)
        
        return evidence_list
        
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
    mode_enforcer: ModeEnforcer = Depends()
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
        # Get HTTP client and evidence service URL
        http_client = get_http_client()
        evidence_url = get_service_url("evidence")
        
        # Make HTTP call to evidence service
        response = await http_client.get(
            f"{evidence_url}/evidence/{evidence_id}",
            headers={"X-User-ID": current_user}
        )
        
        # Convert response to EvidenceResponse
        evidence_response = EvidenceResponse(
            id=response["evidence_id"],
            evidence_type=EvidenceType.DOCUMENT,  # Default, should be determined from content_type
            metadata=EvidenceMetadata(
                filename=response["filename"],
                content_type=response["content_type"],
                size_bytes=response["size_bytes"],
                checksum=response["checksum"],
                uploaded_by=response.get("uploaded_by", "unknown"),
                description="",
                tags={}
            ),
            status=EvidenceStatus.UPLOADED,  # Map from status string
            storage_id=response["evidence_id"],
            case_id=response.get("case_id"),
            chain_of_custody=[],
            worm_locked=response.get("worm_locked", False),
            processing_result=response.get("processing_results")
        )
        
        return evidence_response
        
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
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Update evidence metadata."""
    # Check permissions
    if not mode_enforcer.can_edit_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit evidence"
        )
    
    # Get evidence from database
    db_service = DatabaseService(db_session)
    evidence = await db_service.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    # Check if evidence is WORM locked
    if evidence.worm_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify WORM-locked evidence"
        )
    
    # Prepare update data
    update_data = {}
    if request.description is not None:
        update_data["description"] = request.description
    if request.case_id is not None:
        update_data["case_id"] = request.case_id
    
    # Update metadata if provided
    if request.tags is not None:
        metadata_dict = evidence.metadata or {}
        metadata_dict["tags"] = request.tags
        update_data["metadata"] = metadata_dict
    
    # Update evidence
    updated_evidence = await db_service.update_evidence(evidence_id, **update_data)
    if not updated_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="update_evidence",
        resource_type="evidence",
        resource_id=evidence_id,
        details=update_data
    )
    
    # Convert to response format
    metadata_dict = updated_evidence.metadata or {}
    
    return EvidenceResponse(
        id=str(updated_evidence.id),
        evidence_type=EvidenceType(updated_evidence.evidence_type),
        metadata=EvidenceMetadata(
            filename=metadata_dict.get("filename", ""),
            content_type=metadata_dict.get("content_type", ""),
            size_bytes=metadata_dict.get("size_bytes", 0),
            checksum=metadata_dict.get("checksum", ""),
            uploaded_by=metadata_dict.get("uploaded_by", ""),
            description=updated_evidence.description or "",
            tags=metadata_dict.get("tags", {})
        ),
        status=EvidenceStatus(updated_evidence.status),
        storage_id=updated_evidence.storage_id or "",
        case_id=updated_evidence.case_id,
        chain_of_custody=updated_evidence.chain_of_custody or [],
        worm_locked=updated_evidence.worm_locked,
        processing_result=updated_evidence.processing_result
    )


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Delete evidence."""
    # Check permissions
    if not mode_enforcer.can_delete_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete evidence"
        )
    
    # Get evidence from database
    db_service = DatabaseService(db_session)
    evidence = await db_service.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    # Check if evidence is WORM locked
    if evidence.worm_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete WORM-locked evidence"
        )
    
    # Delete evidence
    success = await db_service.delete_evidence(evidence_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete evidence"
        )
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="delete_evidence",
        resource_type="evidence",
        resource_id=evidence_id,
        details={"filename": evidence.metadata.get("filename", "") if evidence.metadata else ""}
    )


@router.post("/{evidence_id}/worm-lock", response_model=dict)
async def apply_worm_lock(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Apply WORM lock to evidence."""
    # Check permissions
    if not mode_enforcer.can_lock_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to lock evidence"
        )
    
    try:
        # Get evidence from database
        db_service = DatabaseService(db_session)
        evidence = await db_service.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        # Check if already locked
        if evidence.worm_locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evidence is already WORM locked"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evidence: {str(e)}"
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
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Download evidence file."""
    # Check permissions
    if not mode_enforcer.can_download_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download evidence"
        )
    
    # Get evidence from database
    db_service = DatabaseService(db_session)
    evidence = await db_service.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    try:
        # Get HTTP client and evidence service URL
        http_client = get_http_client()
        evidence_url = get_service_url("evidence")
        
        # Make HTTP call to evidence service to get file data
        response = await http_client.get(
            f"{evidence_url}/evidence/{evidence_id}/download",
            headers={"X-User-ID": current_user}
        )
        
        # Create audit log
        await db_service.create_audit_log(
            user_id=current_user,
            action="download_evidence",
            resource_type="evidence",
            resource_id=evidence_id,
            details={"filename": evidence.metadata.get("filename", "") if evidence.metadata else ""}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to download evidence: {str(e)}"
        )


@router.get("/{evidence_id}/chain-of-custody", response_model=List[dict])
async def get_chain_of_custody(
    evidence_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Get chain of custody for evidence."""
    # Check permissions
    if not mode_enforcer.can_view_evidence(current_user, evidence_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view chain of custody"
        )
    
    # Get evidence from database
    db_service = DatabaseService(db_session)
    evidence = await db_service.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    
    # Return chain of custody
    return evidence.chain_of_custody or []
