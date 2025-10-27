"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base

# Import all models so they're registered with Base.metadata
from app.models import budget, project, resource, schedule, task  # noqa: F401


async def init_database():
    """Initialize database tables."""
    print("Creating database tables...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables (use with caution!)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_database())
