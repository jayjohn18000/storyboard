"""Case management API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from ...shared.models.case import Case, CaseMetadata, CaseStatus, CaseType
from ...shared.database import get_db_session
from ...shared.services.database_service import DatabaseService
from ...shared.policy.middleware import requires, PolicyEnforcer
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
@requires("case_manager")
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
@requires("viewer")
async def list_cases(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[CaseStatus] = None,
    case_type_filter: Optional[CaseType] = None,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """List cases with optional filtering."""
    # Check permissions
    if not mode_enforcer.can_list_cases(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to list cases"
        )
    
    # Get cases from database
    db_service = DatabaseService(db_session)
    db_cases = await db_service.list_cases(
        skip=skip,
        limit=limit,
        status_filter=status_filter.value if status_filter else None,
        user_id=current_user
    )
    
    # Convert database cases to response format
    cases = []
    for db_case in db_cases:
        # Extract metadata
        metadata_dict = db_case.metadata or {}
        
        # Create CaseMetadata object
        metadata = CaseMetadata(
            case_number=metadata_dict.get("case_number", ""),
            title=db_case.title,
            case_type=CaseType(metadata_dict.get("case_type", "CIVIL")),
            jurisdiction=metadata_dict.get("jurisdiction", ""),
            court=metadata_dict.get("court", ""),
            judge=metadata_dict.get("judge"),
            attorneys=metadata_dict.get("attorneys", []),
            created_by=db_case.created_by,
        )
        
        # Get related IDs
        evidence_ids = [str(e.id) for e in db_case.evidence] if hasattr(db_case, 'evidence') else []
        storyboard_ids = [str(s.id) for s in db_case.storyboards] if hasattr(db_case, 'storyboards') else []
        render_ids = [str(r.id) for r in db_case.renders] if hasattr(db_case, 'renders') else []
        
        cases.append(CaseResponse(
            id=str(db_case.id),
            metadata=metadata,
            status=CaseStatus(db_case.status),
            evidence_ids=evidence_ids,
            storyboard_ids=storyboard_ids,
            render_ids=render_ids,
            tags=metadata_dict.get("tags", {}),
            notes=db_case.notes or "",
            created_at=db_case.created_at,
            updated_at=db_case.updated_at,
        ))
    
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Get a specific case by ID."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case"
        )
    
    # Get case from database
    db_service = DatabaseService(db_session)
    db_case = await db_service.get_case(case_id)
    if not db_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Extract metadata
    metadata_dict = db_case.metadata or {}
    
    # Create CaseMetadata object
    metadata = CaseMetadata(
        case_number=metadata_dict.get("case_number", ""),
        title=db_case.title,
        case_type=CaseType(metadata_dict.get("case_type", "CIVIL")),
        jurisdiction=metadata_dict.get("jurisdiction", ""),
        court=metadata_dict.get("court", ""),
        judge=metadata_dict.get("judge"),
        attorneys=metadata_dict.get("attorneys", []),
        created_by=db_case.created_by,
    )
    
    # Get related IDs
    evidence_ids = [str(e.id) for e in db_case.evidence] if hasattr(db_case, 'evidence') else []
    storyboard_ids = [str(s.id) for s in db_case.storyboards] if hasattr(db_case, 'storyboards') else []
    render_ids = [str(r.id) for r in db_case.renders] if hasattr(db_case, 'renders') else []
    
    return CaseResponse(
        id=str(db_case.id),
        metadata=metadata,
        status=CaseStatus(db_case.status),
        evidence_ids=evidence_ids,
        storyboard_ids=storyboard_ids,
        render_ids=render_ids,
        tags=metadata_dict.get("tags", {}),
        notes=db_case.notes or "",
        created_at=db_case.created_at,
        updated_at=db_case.updated_at,
    )


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    request: CaseUpdateRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Update a case."""
    # Check permissions
    if not mode_enforcer.can_edit_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit case"
        )
    
    # Get case from database
    db_service = DatabaseService(db_session)
    db_case = await db_service.get_case(case_id)
    if not db_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Prepare update data
    update_data = {}
    if request.title is not None:
        update_data["title"] = request.title
    if request.status is not None:
        update_data["status"] = request.status.value
    if request.description is not None:
        update_data["description"] = request.description
    if request.notes is not None:
        update_data["notes"] = request.notes
    
    # Update metadata if provided
    if any([request.judge, request.attorneys, request.tags]):
        metadata_dict = db_case.metadata or {}
        if request.judge is not None:
            metadata_dict["judge"] = request.judge
        if request.attorneys is not None:
            metadata_dict["attorneys"] = request.attorneys
        if request.tags is not None:
            metadata_dict["tags"] = request.tags
        update_data["metadata"] = metadata_dict
    
    # Update case
    updated_case = await db_service.update_case(case_id, **update_data)
    if not updated_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="update_case",
        resource_type="case",
        resource_id=case_id,
        details=update_data
    )
    
    # Extract metadata
    metadata_dict = updated_case.metadata or {}
    
    # Create CaseMetadata object
    metadata = CaseMetadata(
        case_number=metadata_dict.get("case_number", ""),
        title=updated_case.title,
        case_type=CaseType(metadata_dict.get("case_type", "CIVIL")),
        jurisdiction=metadata_dict.get("jurisdiction", ""),
        court=metadata_dict.get("court", ""),
        judge=metadata_dict.get("judge"),
        attorneys=metadata_dict.get("attorneys", []),
        created_by=updated_case.created_by,
    )
    
    # Get related IDs
    evidence_ids = [str(e.id) for e in updated_case.evidence] if hasattr(updated_case, 'evidence') else []
    storyboard_ids = [str(s.id) for s in updated_case.storyboards] if hasattr(updated_case, 'storyboards') else []
    render_ids = [str(r.id) for r in updated_case.renders] if hasattr(updated_case, 'renders') else []
    
    return CaseResponse(
        id=str(updated_case.id),
        metadata=metadata,
        status=CaseStatus(updated_case.status),
        evidence_ids=evidence_ids,
        storyboard_ids=storyboard_ids,
        render_ids=render_ids,
        tags=metadata_dict.get("tags", {}),
        notes=updated_case.notes or "",
        created_at=updated_case.created_at,
        updated_at=updated_case.updated_at,
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Delete a case."""
    # Check permissions
    if not mode_enforcer.can_delete_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete case"
        )
    
    # Check if case exists
    db_service = DatabaseService(db_session)
    db_case = await db_service.get_case(case_id)
    if not db_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Delete case
    success = await db_service.delete_case(case_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete case"
        )
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="delete_case",
        resource_type="case",
        resource_id=case_id,
        details={"title": db_case.title}
    )


@router.get("/{case_id}/evidence", response_model=List[str])
async def get_case_evidence(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Get evidence IDs for a case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case evidence"
        )
    
    # Get case evidence from database
    db_service = DatabaseService(db_session)
    evidence_list = await db_service.list_evidence(case_id=case_id)
    
    return [str(evidence.id) for evidence in evidence_list]


@router.get("/{case_id}/storyboards", response_model=List[str])
async def get_case_storyboards(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Get storyboard IDs for a case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case storyboards"
        )
    
    # Get case storyboards from database
    db_service = DatabaseService(db_session)
    storyboards_list = await db_service.list_storyboards(case_id=case_id)
    
    return [str(storyboard.id) for storyboard in storyboards_list]


@router.get("/{case_id}/renders", response_model=List[str])
async def get_case_renders(
    case_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Get render IDs for a case."""
    # Check permissions
    if not mode_enforcer.can_view_case(current_user, case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view case renders"
        )
    
    # Get case renders from database
    db_service = DatabaseService(db_session)
    renders_list = await db_service.list_renders(case_id=case_id)
    
    return [str(render.id) for render in renders_list]
