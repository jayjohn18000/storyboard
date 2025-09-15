"""Database connection and session management.

This module provides backward compatibility for the existing database interface.
New code should use the db/session.py module instead.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import get_db as new_get_db, init_database as new_init_database, close_database as new_close_database

logger = logging.getLogger(__name__)

# Re-export functions for backward compatibility
async def init_database():
    """Initialize database connection."""
    await new_init_database()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with new_get_db() as session:
        yield session


async def close_database():
    """Close database connection."""
    await new_close_database()
