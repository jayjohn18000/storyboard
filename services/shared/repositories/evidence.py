"""
Evidence repository for database operations.

This module provides evidence-specific database operations including
CRUD operations and business logic queries.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.database_models import Evidence, Case, User

logger = logging.getLogger(__name__)


class EvidenceRepository(BaseRepository):
    """Repository for Evidence entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Evidence, session)
    
    async def get_with_relationships(self, evidence_id: UUID) -> Optional[Evidence]:
        """
        Get evidence with all related entities.
        
        Args:
            evidence_id: Evidence ID
            
        Returns:
            Evidence with relationships if found, None otherwise
        """
        try:
            query = (
                select(Evidence)
                .options(
                    selectinload(Evidence.case),
                    selectinload(Evidence.uploader)
                )
                .where(Evidence.id == evidence_id)
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get evidence with relationships: {e}")
            return None
    
    async def get_by_case(self, case_id: UUID, skip: int = 0, limit: int = 100) -> List[Evidence]:
        """
        Get evidence by case ID.
        
        Args:
            case_id: Case ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of evidence
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            case_id=case_id
        )
    
    async def get_by_uploader(self, uploader_id: UUID, skip: int = 0, limit: int = 100) -> List[Evidence]:
        """
        Get evidence uploaded by a specific user.
        
        Args:
            uploader_id: Uploader user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of evidence
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            uploaded_by=uploader_id
        )
    
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Evidence]:
        """
        Get evidence by status.
        
        Args:
            status: Evidence status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of evidence
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            status=status
        )
    
    async def get_by_file_hash(self, file_hash: str) -> Optional[Evidence]:
        """
        Get evidence by file hash.
        
        Args:
            file_hash: File hash
            
        Returns:
            Evidence if found, None otherwise
        """
        return await self.get_by_field("file_hash", file_hash)
    
    async def get_by_mime_type(self, mime_type: str, skip: int = 0, limit: int = 100) -> List[Evidence]:
        """
        Get evidence by MIME type.
        
        Args:
            mime_type: MIME type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of evidence
        """
        return await self.get_multi(
            skip=skip,
            limit=limit,
            mime_type=mime_type
        )
    
    async def search_evidence(
        self,
        search_term: str,
        case_id: Optional[UUID] = None,
        status: Optional[str] = None,
        mime_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Evidence]:
        """
        Search evidence by filename and description.
        
        Args:
            search_term: Search term
            case_id: Optional case filter
            status: Optional status filter
            mime_type: Optional MIME type filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching evidence
        """
        try:
            query = select(Evidence)
            
            # Build search conditions
            search_conditions = [
                Evidence.filename.ilike(f"%{search_term}%")
            ]
            query = query.where(or_(*search_conditions))
            
            # Apply filters
            if case_id:
                query = query.where(Evidence.case_id == case_id)
            if status:
                query = query.where(Evidence.status == status)
            if mime_type:
                query = query.where(Evidence.mime_type == mime_type)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to search evidence: {e}")
            return []
    
    async def get_evidence_statistics(self, case_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get evidence statistics.
        
        Args:
            case_id: Optional case ID filter
            
        Returns:
            Dictionary with evidence statistics
        """
        try:
            query = select(Evidence)
            if case_id:
                query = query.where(Evidence.case_id == case_id)
            
            result = await self.session.execute(query)
            evidence_list = result.scalars().all()
            
            # Calculate statistics
            total_count = len(evidence_list)
            total_size = sum(e.file_size for e in evidence_list)
            
            status_counts = {}
            mime_type_counts = {}
            
            for evidence in evidence_list:
                # Count by status
                status_counts[evidence.status] = status_counts.get(evidence.status, 0) + 1
                
                # Count by MIME type
                mime_type_counts[evidence.mime_type] = mime_type_counts.get(evidence.mime_type, 0) + 1
            
            return {
                "total_count": total_count,
                "total_size_bytes": total_size,
                "status_counts": status_counts,
                "mime_type_counts": mime_type_counts,
                "average_size_bytes": total_size / total_count if total_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get evidence statistics: {e}")
            return {
                "total_count": 0,
                "total_size_bytes": 0,
                "status_counts": {},
                "mime_type_counts": {},
                "average_size_bytes": 0
            }
    
    async def get_recent_evidence(self, limit: int = 10) -> List[Evidence]:
        """
        Get recently uploaded evidence.
        
        Args:
            limit: Maximum number of evidence to return
            
        Returns:
            List of recent evidence
        """
        try:
            query = (
                select(Evidence)
                .order_by(Evidence.uploaded_at.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get recent evidence: {e}")
            return []
    
    async def get_evidence_by_date_range(
        self,
        start_date: str,
        end_date: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Evidence]:
        """
        Get evidence uploaded within a date range.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of evidence
        """
        try:
            query = (
                select(Evidence)
                .where(
                    and_(
                        Evidence.uploaded_at >= start_date,
                        Evidence.uploaded_at <= end_date
                    )
                )
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get evidence by date range: {e}")
            return []
    
    async def update_evidence_status(self, evidence_id: UUID, status: str) -> Optional[Evidence]:
        """
        Update evidence status.
        
        Args:
            evidence_id: Evidence ID
            status: New status
            
        Returns:
            Updated evidence if found, None otherwise
        """
        return await self.update(evidence_id, {"status": status})
    
    async def mark_as_processed(self, evidence_id: UUID, processing_results: Dict[str, Any]) -> Optional[Evidence]:
        """
        Mark evidence as processed with results.
        
        Args:
            evidence_id: Evidence ID
            processing_results: Processing results
            
        Returns:
            Updated evidence if found, None otherwise
        """
        return await self.update(
            evidence_id,
            {
                "status": "processed",
                "processing_results": processing_results,
                "processed_at": func.now()
            }
        )
    
    async def mark_as_failed(self, evidence_id: UUID, error_message: str) -> Optional[Evidence]:
        """
        Mark evidence as failed with error message.
        
        Args:
            evidence_id: Evidence ID
            error_message: Error message
            
        Returns:
            Updated evidence if found, None otherwise
        """
        return await self.update(
            evidence_id,
            {
                "status": "failed",
                "processing_results": {"error": error_message}
            }
        )
    
    async def get_duplicate_files(self, file_hash: str) -> List[Evidence]:
        """
        Get all evidence with the same file hash (duplicates).
        
        Args:
            file_hash: File hash
            
        Returns:
            List of evidence with same hash
        """
        return await self.get_multi_by_field("file_hash", file_hash)
    
    async def get_large_files(self, size_threshold: int, skip: int = 0, limit: int = 100) -> List[Evidence]:
        """
        Get evidence files larger than threshold.
        
        Args:
            size_threshold: Size threshold in bytes
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of large evidence files
        """
        try:
            query = (
                select(Evidence)
                .where(Evidence.file_size > size_threshold)
                .order_by(Evidence.file_size.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get large files: {e}")
            return []
