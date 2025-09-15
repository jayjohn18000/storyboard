"""Case management API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from ...shared.models.case import Case, CaseMetadata, CaseStatus, CaseType
from ...shared.database import get_db_session
from ...shared.services.database_service import DatabaseService
from ..middleware.auth import get_current_user
from ..middleware.mode_enforcer import ModeEnforcer


router = APIRouter()


class CaseCreateRequest(BaseModel):
    """Request model for creating a case."""
    case_number: str = Field(..., description="Case number")
    title: str = Field(..., description="Case title")
    case_type: CaseType = Field(..., description="Type of case")
    jurisdiction: str = Field(..., description="Jurisdiction")
    court: str = Field(..., description="Court name")
    judge: Optional[str] = Field(None, description="Judge name")
    attorneys: List[str] = Field(default_factory=list, description="List of attorneys")
    description: Optional[str] = Field(None, description="Case description")
    tags: dict = Field(default_factory=dict, description="Case tags")


class CaseUpdateRequest(BaseModel):
    """Request model for updating a case."""
    title: Optional[str] = Field(None, description="Case title")
    status: Optional[CaseStatus] = Field(None, description="Case status")
    judge: Optional[str] = Field(None, description="Judge name")
    attorneys: Optional[List[str]] = Field(None, description="List of attorneys")
    description: Optional[str] = Field(None, description="Case description")
    tags: Optional[dict] = Field(None, description="Case tags")
    notes: Optional[str] = Field(None, description="Case notes")


class CaseResponse(BaseModel):
    """Response model for case data."""
    id: str
    metadata: CaseMetadata
    status: CaseStatus
    evidence_ids: List[str]
    storyboard_ids: List[str]
    render_ids: List[str]
    tags: dict
    notes: str
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    request: CaseCreateRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Create a new case."""
    # Check permissions
    if not mode_enforcer.can_create_case(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create case"
        )
    
    # Create case metadata
    metadata = CaseMetadata(
        case_number=request.case_number,
        title=request.title,
        case_type=request.case_type,
        jurisdiction=request.jurisdiction,
        court=request.court,
        judge=request.judge,
        attorneys=request.attorneys,
        created_by=current_user,
    )
    
    # Create case using database service
    db_service = DatabaseService(db_session)
    db_case = await db_service.create_case(
        title=request.title,
        description=request.description or "",
        case_number=request.case_number,
        created_by=current_user,
        metadata={
            "case_type": request.case_type.value,
            "jurisdiction": request.jurisdiction,
            "court": request.court,
            "judge": request.judge,
            "attorneys": request.attorneys,
            "tags": request.tags,
        }
    )
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="create_case",
        resource_type="case",
        resource_id=str(db_case.id),
        details={"case_number": request.case_number, "title": request.title}
    )
    
    return CaseResponse(
        id=str(db_case.id),
        metadata=metadata,
        status=CaseStatus(db_case.status),
        evidence_ids=[],
        storyboard_ids=[],
        render_ids=[],
        tags=request.tags,
        notes="",
        created_at=db_case.created_at,
        updated_at=db_case.updated_at,
    )


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[CaseStatus] = None,
    case_type_filter: Optional[CaseType] = None,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """List cases with optional filtering."""
    # Check permissions
    if not mode_enforcer.can_list_cases(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to list cases"
        )
    
    # TODO: Implement database query with filters
    # cases = await case_service.list_cases(
    #     skip=skip,
    #     limit=limit,
    #     status_filter=status_filter,
    #     case_type_filter=case_type_filter,
    #     user_id=current_user
    # )
    
    # Mock response for now
    cases = []
    
    return [
        CaseResponse(
            id=case.id,
            metadata=case.metadata,
            status=case.status,
            evidence_ids=case.evidence_ids,
            storyboard_ids=case.storyboard_ids,
            render_ids=case.render_ids,
            tags=case.tags,
            notes=case.notes,
            created_at=case.metadata.created_at,
            updated_at=case.metadata.updated_at,
        )
        for case in cases
    ]


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Get a specific case by ID."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case"
        )
    
    # TODO: Get case from database
    # case = await case_service.get_case(case_id)
    # if not case:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Case not found"
    #     )
    
    # Mock response for now
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Case not found"
    )


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    request: CaseUpdateRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Update a case."""
    # Check permissions
    if not mode_enforcer.can_edit_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit case"
        )
    
    # TODO: Get case from database
    # case = await case_service.get_case(case_id)
    # if not case:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Case not found"
    #     )
    
    # TODO: Update case
    # updated_case = await case_service.update_case(case_id, request.dict(exclude_unset=True))
    
    # Mock response for now
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Case not found"
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Delete a case."""
    # Check permissions
    if not mode_enforcer.can_delete_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete case"
        )
    
    # TODO: Check if case exists
    # case = await case_service.get_case(case_id)
    # if not case:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Case not found"
    #     )
    
    # TODO: Delete case
    # await case_service.delete_case(case_id)
    
    # Mock response for now
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Case not found"
    )


@router.get("/{case_id}/evidence", response_model=List[str])
async def get_case_evidence(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Get evidence IDs for a case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case evidence"
        )
    
    # TODO: Get case evidence from database
    # evidence_ids = await case_service.get_case_evidence(case_id)
    
    # Mock response for now
    return []


@router.get("/{case_id}/storyboards", response_model=List[str])
async def get_case_storyboards(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Get storyboard IDs for a case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case storyboards"
        )
    
    # TODO: Get case storyboards from database
    # storyboard_ids = await case_service.get_case_storyboards(case_id)
    
    # Mock response for now
    return []


@router.get("/{case_id}/renders", response_model=List[str])
async def get_case_renders(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Get render IDs for a case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case renders"
        )
    
    # TODO: Get case renders from database
    # render_ids = await case_service.get_case_renders(case_id)
    
    # Mock response for now
    return []
