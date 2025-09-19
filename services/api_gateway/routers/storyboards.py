"""Storyboard management API routes."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from ...shared.models.storyboard import Storyboard, StoryboardMetadata, StoryboardStatus, Scene, SceneType, EvidenceAnchor
from ...shared.database import get_db_session
from ...shared.services.database_service import DatabaseService
from ...shared.policy.middleware import requires
from ..middleware.auth import get_current_user
from ..middleware.mode_enforcer import ModeEnforcer


router = APIRouter()


class EvidenceAnchorRequest(BaseModel):
    """Request model for evidence anchor."""
    evidence_id: str = Field(..., description="Evidence ID")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    description: str = Field(..., description="Anchor description")
    confidence: float = Field(default=1.0, description="Confidence score")
    annotations: dict = Field(default_factory=dict, description="Additional annotations")


class SceneRequest(BaseModel):
    """Request model for scene."""
    scene_type: SceneType = Field(..., description="Type of scene")
    title: str = Field(..., description="Scene title")
    description: str = Field(..., description="Scene description")
    duration_seconds: float = Field(..., description="Scene duration")
    start_time: float = Field(default=0.0, description="Scene start time")
    evidence_anchors: List[EvidenceAnchorRequest] = Field(default_factory=list, description="Evidence anchors")
    camera_config: dict = Field(default_factory=dict, description="Camera configuration")
    lighting_config: dict = Field(default_factory=dict, description="Lighting configuration")
    materials: List[dict] = Field(default_factory=list, description="Material configurations")
    transitions: dict = Field(default_factory=dict, description="Transition configurations")


class StoryboardCreateRequest(BaseModel):
    """Request model for creating a storyboard."""
    title: str = Field(..., description="Storyboard title")
    description: str = Field(..., description="Storyboard description")
    case_id: str = Field(..., description="Associated case ID")
    scenes: List[SceneRequest] = Field(default_factory=list, description="Storyboard scenes")
    render_config: dict = Field(default_factory=dict, description="Render configuration")


class StoryboardUpdateRequest(BaseModel):
    """Request model for updating a storyboard."""
    title: Optional[str] = Field(None, description="Storyboard title")
    description: Optional[str] = Field(None, description="Storyboard description")
    scenes: Optional[List[SceneRequest]] = Field(None, description="Storyboard scenes")
    render_config: Optional[dict] = Field(None, description="Render configuration")


class StoryboardResponse(BaseModel):
    """Response model for storyboard data."""
    id: str
    metadata: StoryboardMetadata
    status: StoryboardStatus
    scenes: List[Scene]
    validation_result: Optional[dict]
    timeline_id: Optional[str]
    render_config: dict
    total_duration: float
    evidence_ids: List[str]


@router.post("/", response_model=StoryboardResponse, status_code=status.HTTP_201_CREATED)
async def create_storyboard(
    request: StoryboardCreateRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Create a new storyboard."""
    # Check permissions
    if not mode_enforcer.can_create_storyboard(current_user, request.case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create storyboard"
        )
    
    # Create storyboard metadata
    metadata = StoryboardMetadata(
        title=request.title,
        description=request.description,
        case_id=request.case_id,
        created_by=current_user,
    )
    
    # Create scenes
    scenes = []
    for scene_request in request.scenes:
        # Create evidence anchors
        evidence_anchors = [
            EvidenceAnchor(
                evidence_id=anchor.evidence_id,
                start_time=anchor.start_time,
                end_time=anchor.end_time,
                description=anchor.description,
                confidence=anchor.confidence,
                annotations=anchor.annotations,
            )
            for anchor in scene_request.evidence_anchors
        ]
        
        # Create scene
        scene = Scene(
            scene_type=scene_request.scene_type,
            title=scene_request.title,
            description=scene_request.description,
            duration_seconds=scene_request.duration_seconds,
            start_time=scene_request.start_time,
            evidence_anchors=evidence_anchors,
            camera_config=scene_request.camera_config,
            lighting_config=scene_request.lighting_config,
            materials=scene_request.materials,
            transitions=scene_request.transitions,
        )
        scenes.append(scene)
    
    # Create storyboard
    storyboard = Storyboard(
        metadata=metadata,
        scenes=scenes,
        render_config=request.render_config,
    )
    
    # Save to database
    db_service = DatabaseService(db_session)
    db_storyboard = await db_service.create_storyboard(
        case_id=request.case_id,
        title=request.title,
        description=request.description,
        content=storyboard.to_json(),  # Serialize storyboard to JSON
        created_by=current_user,
        metadata={
            "scenes": [scene.to_dict() for scene in scenes],
            "render_config": request.render_config,
            "total_duration": storyboard.get_total_duration(),
            "evidence_ids": list(set([anchor.evidence_id for scene in scenes for anchor in scene.evidence_anchors]))
        }
    )
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="create_storyboard",
        resource_type="storyboard",
        resource_id=str(db_storyboard.id),
        details={"title": request.title, "case_id": request.case_id}
    )
    
    return StoryboardResponse(
        id=str(db_storyboard.id),
        metadata=metadata,
        status=StoryboardStatus(db_storyboard.status),
        scenes=scenes,
        validation_result=None,  # Will be populated after validation
        timeline_id=None,  # Will be populated after compilation
        render_config=request.render_config,
        total_duration=storyboard.get_total_duration(),
        evidence_ids=list(set([anchor.evidence_id for scene in scenes for anchor in scene.evidence_anchors]))
    )


@router.get("/", response_model=List[StoryboardResponse])
async def list_storyboards(
    skip: int = 0,
    limit: int = 100,
    case_id_filter: Optional[str] = None,
    status_filter: Optional[StoryboardStatus] = None,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """List storyboards with optional filtering."""
    # Check permissions
    if not mode_enforcer.can_list_storyboards(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to list storyboards"
        )
    
    # Get storyboards from database
    db_service = DatabaseService(db_session)
    db_storyboards = await db_service.list_storyboards(
        skip=skip,
        limit=limit,
        case_id=case_id_filter,
        status_filter=status_filter.value if status_filter else None,
        user_id=current_user
    )
    
    # Convert to response format
    storyboards = []
    for db_storyboard in db_storyboards:
        metadata_dict = db_storyboard.metadata or {}
        
        # Create StoryboardMetadata object
        metadata = StoryboardMetadata(
            title=db_storyboard.title,
            description=db_storyboard.description,
            case_id=db_storyboard.case_id,
            created_by=db_storyboard.created_by,
        )
        
        # Parse scenes from content or metadata
        scenes = []
        try:
            if db_storyboard.content:
                import json
                content_data = json.loads(db_storyboard.content)
                scenes = content_data.get("scenes", [])
        except:
            scenes = metadata_dict.get("scenes", [])
        
        storyboards.append(StoryboardResponse(
            id=str(db_storyboard.id),
            metadata=metadata,
            status=StoryboardStatus(db_storyboard.status),
            scenes=scenes,
            validation_result=None,  # Will be populated after validation
            timeline_id=None,  # Will be populated after compilation
            render_config=metadata_dict.get("render_config", {}),
            total_duration=metadata_dict.get("total_duration", 0.0),
            evidence_ids=metadata_dict.get("evidence_ids", [])
        ))
    
    return storyboards


@router.get("/{storyboard_id}", response_model=StoryboardResponse)
async def get_storyboard(
    storyboard_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends(),
    db_session = Depends(get_db_session)
):
    """Get a specific storyboard by ID."""
    # Check permissions
    if not mode_enforcer.can_view_storyboard(current_user, storyboard_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view storyboard"
        )
    
    # Get storyboard from database
    db_service = DatabaseService(db_session)
    db_storyboard = await db_service.get_storyboard(storyboard_id)
    if not db_storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    # Extract metadata
    metadata_dict = db_storyboard.metadata or {}
    
    # Create StoryboardMetadata object
    metadata = StoryboardMetadata(
        title=db_storyboard.title,
        description=db_storyboard.description,
        case_id=db_storyboard.case_id,
        created_by=db_storyboard.created_by,
    )
    
    # Parse scenes from content or metadata
    scenes = []
    try:
        if db_storyboard.content:
            import json
            content_data = json.loads(db_storyboard.content)
            scenes = content_data.get("scenes", [])
    except:
        scenes = metadata_dict.get("scenes", [])
    
    return StoryboardResponse(
        id=str(db_storyboard.id),
        metadata=metadata,
        status=StoryboardStatus(db_storyboard.status),
        scenes=scenes,
        validation_result=None,  # Will be populated after validation
        timeline_id=None,  # Will be populated after compilation
        render_config=metadata_dict.get("render_config", {}),
        total_duration=metadata_dict.get("total_duration", 0.0),
        evidence_ids=metadata_dict.get("evidence_ids", [])
    )


@router.put("/{storyboard_id}", response_model=StoryboardResponse)
async def update_storyboard(
    storyboard_id: str,
    request: StoryboardUpdateRequest,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Update a storyboard."""
    # Check permissions
    if not mode_enforcer.can_edit_storyboard(current_user, storyboard_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit storyboard"
        )
    
    # Get storyboard from database
    db_service = DatabaseService(db_session)
    db_storyboard = await db_service.get_storyboard(storyboard_id)
    if not db_storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    # Update storyboard
    update_data = request.dict(exclude_unset=True)
    updated_storyboard = await db_service.update_storyboard(
        storyboard_id, 
        **update_data
    )
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="update_storyboard",
        resource_type="storyboard",
        resource_id=storyboard_id,
        details={"updates": update_data}
    )
    
    # Parse content to extract scenes if content was updated
    scenes = []
    if 'content' in update_data:
        try:
            content_data = json.loads(update_data['content'])
            scenes = content_data.get('scenes', [])
        except json.JSONDecodeError:
            scenes = []
    
    return StoryboardResponse(
        id=str(updated_storyboard.id),
        case_id=str(updated_storyboard.case_id),
        title=updated_storyboard.title,
        description=updated_storyboard.description or "",
        content=updated_storyboard.content or "",
        scenes=scenes,
        render_config=updated_storyboard.metadata.get("render_config", {}) if updated_storyboard.metadata else {},
        created_at=updated_storyboard.created_at,
        updated_at=updated_storyboard.updated_at,
        created_by=updated_storyboard.created_by,
        validation_result={
            "is_valid": updated_storyboard.metadata.get("is_valid", True) if updated_storyboard.metadata else True,
            "errors": updated_storyboard.metadata.get("validation_errors", []) if updated_storyboard.metadata else []
        }
    )


@router.delete("/{storyboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storyboard(
    storyboard_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Delete a storyboard."""
    # Check permissions
    if not mode_enforcer.can_delete_storyboard(current_user, storyboard_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete storyboard"
        )
    
    # Get storyboard from database
    db_service = DatabaseService(db_session)
    db_storyboard = await db_service.get_storyboard(storyboard_id)
    if not db_storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    # Delete storyboard
    await db_service.delete_storyboard(storyboard_id)
    
    # Create audit log
    await db_service.create_audit_log(
        user_id=current_user,
        action="delete_storyboard",
        resource_type="storyboard",
        resource_id=storyboard_id,
        details={"title": db_storyboard.title, "case_id": str(db_storyboard.case_id)}
    )


@router.post("/{storyboard_id}/validate", response_model=dict)
async def validate_storyboard(
    storyboard_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Validate a storyboard."""
    # Check permissions
    if not mode_enforcer.can_validate_storyboard(current_user, storyboard_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to validate storyboard"
        )
    
    # Get storyboard from database
    db_service = DatabaseService(db_session)
    db_storyboard = await db_service.get_storyboard(storyboard_id)
    if not db_storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    # Validate storyboard content
    validation_errors = []
    validation_warnings = []
    
    try:
        # Parse JSON content
        content_data = json.loads(db_storyboard.content or "{}")
        scenes = content_data.get('scenes', [])
        
        # Basic validation
        if not scenes:
            validation_errors.append("No scenes found in storyboard")
        
        for i, scene in enumerate(scenes):
            if not scene.get('description'):
                validation_warnings.append(f"Scene {i+1} has no description")
            
            if not scene.get('duration_seconds', 0) > 0:
                validation_warnings.append(f"Scene {i+1} has no duration")
            
            # Check evidence anchors
            evidence_anchors = scene.get('evidence_anchors', [])
            for j, anchor in enumerate(evidence_anchors):
                if not anchor.get('evidence_id'):
                    validation_errors.append(f"Scene {i+1}, Evidence anchor {j+1} has no evidence_id")
        
        # Update validation status in database
        is_valid = len(validation_errors) == 0
        await db_service.update_storyboard(
            storyboard_id,
            metadata={
                **(db_storyboard.metadata or {}),
                "is_valid": is_valid,
                "validation_errors": validation_errors,
                "validation_warnings": validation_warnings,
                "last_validated": datetime.utcnow().isoformat()
            }
        )
        
        # Create audit log
        await db_service.create_audit_log(
            user_id=current_user,
            action="validate_storyboard",
            resource_type="storyboard",
            resource_id=storyboard_id,
            details={
                "is_valid": is_valid,
                "error_count": len(validation_errors),
                "warning_count": len(validation_warnings)
            }
        )
        
        return {
            "is_valid": is_valid,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "scene_count": len(scenes),
            "total_duration": sum(scene.get('duration_seconds', 0) for scene in scenes)
        }
        
    except json.JSONDecodeError:
        validation_errors.append("Invalid JSON content")
        return {
            "is_valid": False,
            "errors": validation_errors,
            "warnings": [],
            "scene_count": 0,
            "total_duration": 0
        }


@router.post("/{storyboard_id}/compile", response_model=dict)
@requires("storyboard_manager")
async def compile_storyboard(
    storyboard_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Compile storyboard to timeline."""
    # Check permissions
    if not mode_enforcer.can_compile_storyboard(current_user, storyboard_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to compile storyboard"
        )
    
    # TODO: Get storyboard from database
    # storyboard = await storyboard_service.get_storyboard(storyboard_id)
    # if not storyboard:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Storyboard not found"
    #     )
    
    # For now, use mock storyboard data
    storyboard_data = {
        "scenes": [
            {
                "id": "scene_1",
                "title": "Opening Scene",
                "duration": 5.0,
                "evidence_anchors": []
            }
        ],
        "metadata": {
            "title": "Mock Storyboard",
            "duration": 5.0
        }
    }
    
    # Call Storyboard service to compile
    try:
        from ...shared.http_client import get_http_client
        from ...shared.config import get_service_url
        
        http_client = await get_http_client()
        storyboard_url = get_service_url("storyboard")
        
        compile_request = {
            "storyboard_data": storyboard_data,
            "metadata": {"compiled_by": current_user}
        }
        
        response = await http_client.request_json(
            "POST",
            f"{storyboard_url}/storyboards/{storyboard_id}/compile",
            json=compile_request,
            timeout=30
        )
        
        return {
            "status": "compiled",
            "storyboard_id": storyboard_id,
            "timeline_id": response.get("timeline_id"),
            "compilation_result": response.get("compilation_result")
        }
        
    except Exception as e:
        logger.error(f"Failed to compile storyboard {storyboard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to compile storyboard: {str(e)}"
        )


@router.get("/{storyboard_id}/evidence-coverage", response_model=dict)
async def get_evidence_coverage(
    storyboard_id: str,
    current_user: str = Depends(get_current_user),
    mode_enforcer: ModeEnforcer = Depends()
):
    """Get evidence coverage for storyboard."""
    # Check permissions
    if not mode_enforcer.can_view_storyboard(current_user, storyboard_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view evidence coverage"
        )
    
    # Get storyboard from database
    db_service = DatabaseService(db_session)
    db_storyboard = await db_service.get_storyboard(storyboard_id)
    if not db_storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    # Get evidence coverage
    try:
        content_data = json.loads(db_storyboard.content or "{}")
        scenes = content_data.get('scenes', [])
        
        # Extract all evidence IDs referenced in the storyboard
        referenced_evidence_ids = set()
        for scene in scenes:
            evidence_anchors = scene.get('evidence_anchors', [])
            for anchor in evidence_anchors:
                if anchor.get('evidence_id'):
                    referenced_evidence_ids.add(anchor['evidence_id'])
        
        # Get all evidence for the case
        case_evidence = await db_service.list_evidence(case_id=str(db_storyboard.case_id))
        total_evidence_count = len(case_evidence)
        referenced_evidence_count = len(referenced_evidence_ids)
        
        # Calculate coverage percentage
        coverage_percentage = (referenced_evidence_count / total_evidence_count * 100) if total_evidence_count > 0 else 0
        
        # Get details about referenced evidence
        referenced_evidence_details = []
        for evidence in case_evidence:
            if evidence.id in referenced_evidence_ids:
                referenced_evidence_details.append({
                    "id": evidence.id,
                    "name": evidence.metadata.get("filename", "Unknown") if evidence.metadata else "Unknown",
                    "type": evidence.evidence_type,
                    "referenced_scenes": [
                        i+1 for i, scene in enumerate(scenes) 
                        if any(anchor.get('evidence_id') == evidence.id for anchor in scene.get('evidence_anchors', []))
                    ]
                })
        
        # Get unreferenced evidence
        unreferenced_evidence = [
            {
                "id": evidence.id,
                "name": evidence.metadata.get("filename", "Unknown") if evidence.metadata else "Unknown",
                "type": evidence.evidence_type
            }
            for evidence in case_evidence
            if evidence.id not in referenced_evidence_ids
        ]
        
        return {
            "storyboard_id": storyboard_id,
            "case_id": str(db_storyboard.case_id),
            "total_evidence_count": total_evidence_count,
            "referenced_evidence_count": referenced_evidence_count,
            "coverage_percentage": round(coverage_percentage, 2),
            "referenced_evidence": referenced_evidence_details,
            "unreferenced_evidence": unreferenced_evidence,
            "scene_count": len(scenes)
        }
        
    except json.JSONDecodeError:
        return {
            "storyboard_id": storyboard_id,
            "case_id": str(db_storyboard.case_id),
            "total_evidence_count": 0,
            "referenced_evidence_count": 0,
            "coverage_percentage": 0,
            "referenced_evidence": [],
            "unreferenced_evidence": [],
            "scene_count": 0,
            "error": "Invalid storyboard content"
        }
