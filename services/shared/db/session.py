"""
Database session management for Legal Simulation Platform.

This module provides database session management, connection pooling,
and transaction handling for all services.
"""

import os
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine

from ..config import config

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Global engine and session factory
engine = None
SessionLocal = None


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection."""
        if self._initialized:
            return
        
        try:
            # Get database URL from config
            database_url = config.database.database_url
            
            # Create async engine
            self.engine = create_async_engine(
                database_url,
                echo=config.app.debug,
                pool_size=config.database.database_pool_size,
                max_overflow=config.database.database_max_overflow,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            # Add connection event listeners
            self._add_event_listeners()
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _add_event_listeners(self):
        """Add database event listeners."""
        
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set database pragmas for better performance."""
            if "postgresql" in str(dbapi_connection):
                # PostgreSQL specific settings
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET timezone TO 'UTC'")
                    cursor.execute("SET statement_timeout TO '30s'")
        
        @event.listens_for(Engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(Engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin."""
            logger.debug("Connection checked in to pool")
    
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if not self._initialized:
            await self.initialize()
        
        return self.session_factory()
    
    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with context manager."""
        session = await self.get_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            async with self.get_db() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def init_database():
    """Initialize database connection."""
    await db_manager.initialize()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency for FastAPI.
    
    This function can be used as a FastAPI dependency to get database sessions.
    
    Yields:
        AsyncSession: Database session
    """
    async with db_manager.get_db() as session:
        yield session


async def get_session() -> AsyncSession:
    """
    Get database session directly.
    
    Returns:
        AsyncSession: Database session
    """
    return await db_manager.get_session()


async def close_database():
    """Close database connection."""
    await db_manager.close()


async def health_check() -> bool:
    """
    Check database health.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    return await db_manager.health_check()


# Legacy compatibility
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Legacy function for backward compatibility."""
    async with db_manager.get_db() as session:
        yield session
