"""Database service for CRUD operations."""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from ..models.database_models import User, Case, Evidence, Storyboard, Render, ExportJob, AuditLog

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # User operations
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, email: str, name: str, role: str = "viewer") -> User:
        """Create new user."""
        user = User(email=email, name=name, role=role)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    # Case operations
    async def get_case(self, case_id: str) -> Optional[Case]:
        """Get case by ID."""
        result = await self.session.execute(
            select(Case)
            .options(selectinload(Case.creator))
            .where(Case.id == case_id)
        )
        return result.scalar_one_or_none()
    
    async def list_cases(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Case]:
        """List cases with optional filtering."""
        query = select(Case).options(selectinload(Case.creator))
        
        if status_filter:
            query = query.where(Case.status == status_filter)
        
        if user_id:
            query = query.where(Case.created_by == user_id)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_case(
        self, 
        title: str, 
        description: str, 
        case_number: str, 
        created_by: str,
        metadata: Dict[str, Any] = None
    ) -> Case:
        """Create new case."""
        case = Case(
            title=title,
            description=description,
            case_number=case_number,
            created_by=created_by,
            metadata=metadata or {}
        )
        self.session.add(case)
        await self.session.commit()
        await self.session.refresh(case)
        return case
    
    async def update_case(self, case_id: str, **kwargs) -> Optional[Case]:
        """Update case."""
        await self.session.execute(
            update(Case)
            .where(Case.id == case_id)
            .values(**kwargs)
        )
        await self.session.commit()
        return await self.get_case(case_id)
    
    async def delete_case(self, case_id: str) -> bool:
        """Delete case."""
        result = await self.session.execute(
            delete(Case).where(Case.id == case_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    # Evidence operations
    async def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        result = await self.session.execute(
            select(Evidence)
            .options(selectinload(Evidence.case), selectinload(Evidence.uploader))
            .where(Evidence.id == evidence_id)
        )
        return result.scalar_one_or_none()
    
    async def list_evidence(
        self, 
        case_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None
    ) -> List[Evidence]:
        """List evidence with optional filtering."""
        query = select(Evidence).options(
            selectinload(Evidence.case), 
            selectinload(Evidence.uploader)
        )
        
        if case_id:
            query = query.where(Evidence.case_id == case_id)
        
        if status_filter:
            query = query.where(Evidence.status == status_filter)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_evidence(
        self,
        case_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        file_hash: str,
        uploaded_by: str,
        metadata: Dict[str, Any] = None
    ) -> Evidence:
        """Create new evidence."""
        evidence = Evidence(
            case_id=case_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            uploaded_by=uploaded_by,
            metadata=metadata or {}
        )
        self.session.add(evidence)
        await self.session.commit()
        await self.session.refresh(evidence)
        return evidence
    
    async def update_evidence(self, evidence_id: str, **kwargs) -> Optional[Evidence]:
        """Update evidence."""
        await self.session.execute(
            update(Evidence)
            .where(Evidence.id == evidence_id)
            .values(**kwargs)
        )
        await self.session.commit()
        return await self.get_evidence(evidence_id)
    
    async def delete_evidence(self, evidence_id: str) -> bool:
        """Delete evidence."""
        result = await self.session.execute(
            delete(Evidence).where(Evidence.id == evidence_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    # Storyboard operations
    async def get_storyboard(self, storyboard_id: str) -> Optional[Storyboard]:
        """Get storyboard by ID."""
        result = await self.session.execute(
            select(Storyboard)
            .options(selectinload(Storyboard.case), selectinload(Storyboard.creator))
            .where(Storyboard.id == storyboard_id)
        )
        return result.scalar_one_or_none()
    
    async def list_storyboards(
        self, 
        case_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None
    ) -> List[Storyboard]:
        """List storyboards with optional filtering."""
        query = select(Storyboard).options(
            selectinload(Storyboard.case), 
            selectinload(Storyboard.creator)
        )
        
        if case_id:
            query = query.where(Storyboard.case_id == case_id)
        
        if status_filter:
            query = query.where(Storyboard.status == status_filter)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_storyboard(
        self,
        case_id: str,
        title: str,
        description: str,
        created_by: str,
        metadata: Dict[str, Any] = None,
        scenes: List[Dict[str, Any]] = None
    ) -> Storyboard:
        """Create new storyboard."""
        storyboard = Storyboard(
            case_id=case_id,
            title=title,
            description=description,
            created_by=created_by,
            metadata=metadata or {},
            scenes=scenes or []
        )
        self.session.add(storyboard)
        await self.session.commit()
        await self.session.refresh(storyboard)
        return storyboard
    
    async def update_storyboard(self, storyboard_id: str, **kwargs) -> Optional[Storyboard]:
        """Update storyboard."""
        await self.session.execute(
            update(Storyboard)
            .where(Storyboard.id == storyboard_id)
            .values(**kwargs)
        )
        await self.session.commit()
        return await self.get_storyboard(storyboard_id)
    
    async def delete_storyboard(self, storyboard_id: str) -> bool:
        """Delete storyboard."""
        result = await self.session.execute(
            delete(Storyboard).where(Storyboard.id == storyboard_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    # Render operations
    async def get_render(self, render_id: str) -> Optional[Render]:
        """Get render by ID."""
        result = await self.session.execute(
            select(Render)
            .options(
                selectinload(Render.case), 
                selectinload(Render.storyboard),
                selectinload(Render.creator)
            )
            .where(Render.id == render_id)
        )
        return result.scalar_one_or_none()
    
    async def list_renders(
        self, 
        case_id: Optional[str] = None,
        storyboard_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None
    ) -> List[Render]:
        """List renders with optional filtering."""
        query = select(Render).options(
            selectinload(Render.case), 
            selectinload(Render.storyboard),
            selectinload(Render.creator)
        )
        
        if case_id:
            query = query.where(Render.case_id == case_id)
        
        if storyboard_id:
            query = query.where(Render.storyboard_id == storyboard_id)
        
        if status_filter:
            query = query.where(Render.status == status_filter)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_render(
        self,
        case_id: str,
        storyboard_id: str,
        title: str,
        description: str,
        created_by: str,
        render_config: Dict[str, Any] = None
    ) -> Render:
        """Create new render."""
        render = Render(
            case_id=case_id,
            storyboard_id=storyboard_id,
            title=title,
            description=description,
            created_by=created_by,
            render_config=render_config or {}
        )
        self.session.add(render)
        await self.session.commit()
        await self.session.refresh(render)
        return render
    
    async def update_render(self, render_id: str, **kwargs) -> Optional[Render]:
        """Update render."""
        await self.session.execute(
            update(Render)
            .where(Render.id == render_id)
            .values(**kwargs)
        )
        await self.session.commit()
        return await self.get_render(render_id)
    
    async def delete_render(self, render_id: str) -> bool:
        """Delete render."""
        result = await self.session.execute(
            delete(Render).where(Render.id == render_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    # Audit log operations
    async def create_audit_log(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Dict[str, Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log
