"""
Case repository for database operations.

This module provides case-specific database operations including
CRUD operations and business logic queries.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.database_models import Case, User, Evidence, Storyboard, Render

logger = logging.getLogger(__name__)


class CaseRepository(BaseRepository):
    """Repository for Case entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Case, session)
    
    async def get_with_relationships(self, case_id: UUID) -> Optional[Case]:
        """
        Get case with all related entities.
        
        Args:
            case_id: Case ID
            
        Returns:
            Case with relationships if found, None otherwise
        """
        try:
            query = (
                select(Case)
                .options(
                    selectinload(Case.creator),
                    selectinload(Case.evidence),
                    selectinload(Case.storyboards),
                    selectinload(Case.renders)
                )
                .where(Case.id == case_id)
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get case with relationships: {e}")
            return None
    
    async def get_by_case_number(self, case_number: str) -> Optional[Case]:
        """
        Get case by case number.
        
        Args:
            case_number: Case number
            
        Returns:
            Case if found, None otherwise
        """
        return await self.get_by_field("case_number", case_number)
    
    async def get_by_creator(self, creator_id: UUID, skip: int = 0, limit: int = 100) -> List[Case]:
        """
        Get cases created by a specific user.
        
        Args:
            creator_id: Creator user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of cases
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            created_by=creator_id
        )
    
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Case]:
        """
        Get cases by status.
        
        Args:
            status: Case status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of cases
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            status=status
        )
    
    async def search_cases(
        self,
        search_term: str,
        creator_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Case]:
        """
        Search cases by title and description.
        
        Args:
            search_term: Search term
            creator_id: Optional creator filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching cases
        """
        try:
            query = select(Case)
            
            # Build search conditions
            search_conditions = [
                Case.title.ilike(f"%{search_term}%"),
                Case.description.ilike(f"%{search_term}%"),
                Case.case_number.ilike(f"%{search_term}%")
            ]
            query = query.where(or_(*search_conditions))
            
            # Apply filters
            if creator_id:
                query = query.where(Case.created_by == creator_id)
            if status:
                query = query.where(Case.status == status)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to search cases: {e}")
            return []
    
    async def get_case_statistics(self, case_id: UUID) -> Dict[str, Any]:
        """
        Get case statistics including evidence, storyboard, and render counts.
        
        Args:
            case_id: Case ID
            
        Returns:
            Dictionary with case statistics
        """
        try:
            # Get evidence count
            evidence_query = select(Evidence).where(Evidence.case_id == case_id)
            evidence_result = await self.session.execute(evidence_query)
            evidence_count = len(evidence_result.scalars().all())
            
            # Get storyboard count
            storyboard_query = select(Storyboard).where(Storyboard.case_id == case_id)
            storyboard_result = await self.session.execute(storyboard_query)
            storyboard_count = len(storyboard_result.scalars().all())
            
            # Get render count
            render_query = select(Render).where(Render.case_id == case_id)
            render_result = await self.session.execute(render_query)
            render_count = len(render_result.scalars().all())
            
            return {
                "evidence_count": evidence_count,
                "storyboard_count": storyboard_count,
                "render_count": render_count,
                "total_items": evidence_count + storyboard_count + render_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get case statistics: {e}")
            return {
                "evidence_count": 0,
                "storyboard_count": 0,
                "render_count": 0,
                "total_items": 0
            }
    
    async def get_recent_cases(self, limit: int = 10) -> List[Case]:
        """
        Get recently created cases.
        
        Args:
            limit: Maximum number of cases to return
            
        Returns:
            List of recent cases
        """
        try:
            query = (
                select(Case)
                .order_by(Case.created_at.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get recent cases: {e}")
            return []
    
    async def get_cases_by_date_range(
        self,
        start_date: str,
        end_date: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Case]:
        """
        Get cases created within a date range.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of cases
        """
        try:
            query = (
                select(Case)
                .where(
                    and_(
                        Case.created_at >= start_date,
                        Case.created_at <= end_date
                    )
                )
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get cases by date range: {e}")
            return []
    
    async def update_case_status(self, case_id: UUID, status: str) -> Optional[Case]:
        """
        Update case status.
        
        Args:
            case_id: Case ID
            status: New status
            
        Returns:
            Updated case if found, None otherwise
        """
        return await self.update(case_id, {"status": status})
    
    async def archive_case(self, case_id: UUID) -> Optional[Case]:
        """
        Archive a case.
        
        Args:
            case_id: Case ID
            
        Returns:
            Updated case if found, None otherwise
        """
        return await self.update_case_status(case_id, "archived")
    
    async def restore_case(self, case_id: UUID) -> Optional[Case]:
        """
        Restore an archived case.
        
        Args:
            case_id: Case ID
            
        Returns:
            Updated case if found, None otherwise
        """
        return await self.update_case_status(case_id, "active")
