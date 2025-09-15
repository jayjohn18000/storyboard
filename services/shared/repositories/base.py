"""
Base repository class for database operations.

This module provides a base repository class with common CRUD operations
and query patterns for all database entities.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, NoResultFound
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')
ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class RepositoryError(Exception):
    """Base repository error."""
    pass


class NotFoundError(RepositoryError):
    """Entity not found error."""
    pass


class IntegrityError(RepositoryError):
    """Database integrity error."""
    pass


class BaseRepository:
    """Base repository class with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session
    
    async def create(self, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        Create new entity.
        
        Args:
            obj_in: Pydantic model with data to create
            **kwargs: Additional fields to set
            
        Returns:
            Created entity
            
        Raises:
            IntegrityError: If database constraint violation
        """
        try:
            # Convert Pydantic model to dict
            obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            
            # Add additional fields
            obj_data.update(kwargs)
            
            # Create model instance
            db_obj = self.model(**obj_data)
            
            # Add to session and commit
            self.session.add(db_obj)
            await self.session.flush()
            await self.session.refresh(db_obj)
            
            logger.debug(f"Created {self.model.__name__} with ID: {db_obj.id}")
            return db_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise IntegrityError(f"Failed to create {self.model.__name__}: {e}")
    
    async def get(self, id: Union[str, UUID], **kwargs) -> Optional[ModelType]:
        """
        Get entity by ID.
        
        Args:
            id: Entity ID
            **kwargs: Additional query filters
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            query = select(self.model).where(self.model.id == id)
            
            # Add additional filters
            for key, value in kwargs.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} with ID {id}: {e}")
            return None
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple entities with pagination and filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Query filters
            
        Returns:
            List of entities
        """
        try:
            query = select(self.model)
            
            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    if isinstance(value, list):
                        query = query.where(getattr(self.model, key).in_(value))
                    else:
                        query = query.where(getattr(self.model, key) == value)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get multiple {self.model.__name__}: {e}")
            return []
    
    async def update(
        self,
        id: Union[str, UUID],
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        **kwargs
    ) -> Optional[ModelType]:
        """
        Update entity.
        
        Args:
            id: Entity ID
            obj_in: Update data (Pydantic model or dict)
            **kwargs: Additional fields to update
            
        Returns:
            Updated entity if found, None otherwise
        """
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in
            
            # Add additional fields
            update_data.update(kwargs)
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                # No updates to make
                return await self.get(id)
            
            # Build update query
            query = (
                update(self.model)
                .where(self.model.id == id)
                .values(**update_data)
                .returning(self.model)
            )
            
            result = await self.session.execute(query)
            updated_obj = result.scalar_one_or_none()
            
            if updated_obj:
                await self.session.flush()
                await self.session.refresh(updated_obj)
                logger.debug(f"Updated {self.model.__name__} with ID: {id}")
            
            return updated_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update {self.model.__name__} with ID {id}: {e}")
            return None
    
    async def delete(self, id: Union[str, UUID]) -> bool:
        """
        Delete entity.
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            
            if result.rowcount > 0:
                logger.debug(f"Deleted {self.model.__name__} with ID: {id}")
                return True
            else:
                logger.warning(f"{self.model.__name__} with ID {id} not found for deletion")
                return False
                
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete {self.model.__name__} with ID {id}: {e}")
            return False
    
    async def count(self, **filters) -> int:
        """
        Count entities with filters.
        
        Args:
            **filters: Query filters
            
        Returns:
            Number of entities matching filters
        """
        try:
            query = select(func.count(self.model.id))
            
            # Apply filters
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    if isinstance(value, list):
                        query = query.where(getattr(self.model, key).in_(value))
                    else:
                        query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"Failed to count {self.model.__name__}: {e}")
            return 0
    
    async def exists(self, id: Union[str, UUID]) -> bool:
        """
        Check if entity exists.
        
        Args:
            id: Entity ID
            
        Returns:
            True if exists, False otherwise
        """
        try:
            query = select(self.model.id).where(self.model.id == id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Failed to check existence of {self.model.__name__} with ID {id}: {e}")
            return False
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Get entity by field value.
        
        Args:
            field: Field name
            value: Field value
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on {self.model.__name__}")
            
            query = select(self.model).where(getattr(self.model, field) == value)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} by {field}={value}: {e}")
            return None
    
    async def get_multi_by_field(self, field: str, value: Any) -> List[ModelType]:
        """
        Get multiple entities by field value.
        
        Args:
            field: Field name
            value: Field value
            
        Returns:
            List of entities
        """
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on {self.model.__name__}")
            
            query = select(self.model).where(getattr(self.model, field) == value)
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get multiple {self.model.__name__} by {field}={value}: {e}")
            return []
    
    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        Search entities by text in specified fields.
        
        Args:
            search_term: Search term
            search_fields: Fields to search in
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional query filters
            
        Returns:
            List of matching entities
        """
        try:
            query = select(self.model)
            
            # Build search conditions
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(
                        getattr(self.model, field).ilike(f"%{search_term}%")
                    )
            
            if search_conditions:
                query = query.where(or_(*search_conditions))
            
            # Apply additional filters
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    if isinstance(value, list):
                        query = query.where(getattr(self.model, key).in_(value))
                    else:
                        query = query.where(getattr(self.model, key) == value)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to search {self.model.__name__}: {e}")
            return []
