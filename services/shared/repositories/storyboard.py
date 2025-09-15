"""
Storyboard repository for database operations.

This module provides storyboard-specific database operations including
CRUD operations and business logic queries.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.database_models import Storyboard, Case, User, Render

logger = logging.getLogger(__name__)


class StoryboardRepository(BaseRepository):
    """Repository for Storyboard entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Storyboard, session)
    
    async def get_with_relationships(self, storyboard_id: UUID) -> Optional[Storyboard]:
        """
        Get storyboard with all related entities.
        
        Args:
            storyboard_id: Storyboard ID
            
        Returns:
            Storyboard with relationships if found, None otherwise
        """
        try:
            query = (
                select(Storyboard)
                .options(
                    selectinload(Storyboard.case),
                    selectinload(Storyboard.creator),
                    selectinload(Storyboard.renders)
                )
                .where(Storyboard.id == storyboard_id)
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get storyboard with relationships: {e}")
            return None
    
    async def get_by_case(self, case_id: UUID, skip: int = 0, limit: int = 100) -> List[Storyboard]:
        """
        Get storyboards by case ID.
        
        Args:
            case_id: Case ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of storyboards
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            case_id=case_id
        )
    
    async def get_by_creator(self, creator_id: UUID, skip: int = 0, limit: int = 100) -> List[Storyboard]:
        """
        Get storyboards created by a specific user.
        
        Args:
            creator_id: Creator user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of storyboards
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            created_by=creator_id
        )
    
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Storyboard]:
        """
        Get storyboards by status.
        
        Args:
            status: Storyboard status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of storyboards
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            status=status
        )
    
    async def search_storyboards(
        self,
        search_term: str,
        case_id: Optional[UUID] = None,
        status: Optional[str] = None,
        creator_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Storyboard]:
        """
        Search storyboards by title and description.
        
        Args:
            search_term: Search term
            case_id: Optional case filter
            status: Optional status filter
            creator_id: Optional creator filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching storyboards
        """
        try:
            query = select(Storyboard)
            
            # Build search conditions
            search_conditions = [
                Storyboard.title.ilike(f"%{search_term}%"),
                Storyboard.description.ilike(f"%{search_term}%")
            ]
            query = query.where(or_(*search_conditions))
            
            # Apply filters
            if case_id:
                query = query.where(Storyboard.case_id == case_id)
            if status:
                query = query.where(Storyboard.status == status)
            if creator_id:
                query = query.where(Storyboard.created_by == creator_id)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to search storyboards: {e}")
            return []
    
    async def get_storyboard_statistics(self, case_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get storyboard statistics.
        
        Args:
            case_id: Optional case ID filter
            
        Returns:
            Dictionary with storyboard statistics
        """
        try:
            query = select(Storyboard)
            if case_id:
                query = query.where(Storyboard.case_id == case_id)
            
            result = await self.session.execute(query)
            storyboard_list = result.scalars().all()
            
            # Calculate statistics
            total_count = len(storyboard_list)
            
            status_counts = {}
            scene_counts = []
            
            for storyboard in storyboard_list:
                # Count by status
                status_counts[storyboard.status] = status_counts.get(storyboard.status, 0) + 1
                
                # Count scenes
                if storyboard.scenes:
                    scene_counts.append(len(storyboard.scenes))
            
            return {
                "total_count": total_count,
                "status_counts": status_counts,
                "average_scenes": sum(scene_counts) / len(scene_counts) if scene_counts else 0,
                "total_scenes": sum(scene_counts)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storyboard statistics: {e}")
            return {
                "total_count": 0,
                "status_counts": {},
                "average_scenes": 0,
                "total_scenes": 0
            }
    
    async def get_recent_storyboards(self, limit: int = 10) -> List[Storyboard]:
        """
        Get recently created storyboards.
        
        Args:
            limit: Maximum number of storyboards to return
            
        Returns:
            List of recent storyboards
        """
        try:
            query = (
                select(Storyboard)
                .order_by(Storyboard.created_at.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get recent storyboards: {e}")
            return []
    
    async def get_storyboards_by_date_range(
        self,
        start_date: str,
        end_date: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Storyboard]:
        """
        Get storyboards created within a date range.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of storyboards
        """
        try:
            query = (
                select(Storyboard)
                .where(
                    and_(
                        Storyboard.created_at >= start_date,
                        Storyboard.created_at <= end_date
                    )
                )
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get storyboards by date range: {e}")
            return []
    
    async def update_storyboard_status(self, storyboard_id: UUID, status: str) -> Optional[Storyboard]:
        """
        Update storyboard status.
        
        Args:
            storyboard_id: Storyboard ID
            status: New status
            
        Returns:
            Updated storyboard if found, None otherwise
        """
        update_data = {"status": status}
        
        # Add timestamp based on status
        if status == "validated":
            update_data["validated_at"] = func.now()
        elif status == "compiled":
            update_data["compiled_at"] = func.now()
        
        return await self.update(storyboard_id, update_data)
    
    async def mark_as_validated(self, storyboard_id: UUID, validation_result: Dict[str, Any]) -> Optional[Storyboard]:
        """
        Mark storyboard as validated with results.
        
        Args:
            storyboard_id: Storyboard ID
            validation_result: Validation results
            
        Returns:
            Updated storyboard if found, None otherwise
        """
        return await self.update(
            storyboard_id,
            {
                "status": "validated",
                "validation_result": validation_result,
                "validated_at": func.now()
            }
        )
    
    async def mark_as_compiled(self, storyboard_id: UUID, timeline_id: UUID) -> Optional[Storyboard]:
        """
        Mark storyboard as compiled with timeline ID.
        
        Args:
            storyboard_id: Storyboard ID
            timeline_id: Timeline ID
            
        Returns:
            Updated storyboard if found, None otherwise
        """
        return await self.update(
            storyboard_id,
            {
                "status": "compiled",
                "timeline_id": timeline_id,
                "compiled_at": func.now()
            }
        )
    
    async def mark_as_failed(self, storyboard_id: UUID, error_message: str) -> Optional[Storyboard]:
        """
        Mark storyboard as failed with error message.
        
        Args:
            storyboard_id: Storyboard ID
            error_message: Error message
            
        Returns:
            Updated storyboard if found, None otherwise
        """
        return await self.update(
            storyboard_id,
            {
                "status": "failed",
                "validation_result": {"error": error_message}
            }
        )
    
    async def get_draft_storyboards(self, skip: int = 0, limit: int = 100) -> List[Storyboard]:
        """
        Get draft storyboards.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of draft storyboards
        """
        return await self.get_by_status("draft", skip, limit)
    
    async def get_validated_storyboards(self, skip: int = 0, limit: int = 100) -> List[Storyboard]:
        """
        Get validated storyboards ready for compilation.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of validated storyboards
        """
        return await self.get_by_status("validated", skip, limit)
    
    async def get_compiled_storyboards(self, skip: int = 0, limit: int = 100) -> List[Storyboard]:
        """
        Get compiled storyboards ready for rendering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of compiled storyboards
        """
        return await self.get_by_status("compiled", skip, limit)
    
    async def get_storyboards_with_renders(self, skip: int = 0, limit: int = 100) -> List[Storyboard]:
        """
        Get storyboards that have associated renders.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of storyboards with renders
        """
        try:
            query = (
                select(Storyboard)
                .join(Render)
                .distinct()
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get storyboards with renders: {e}")
            return []
