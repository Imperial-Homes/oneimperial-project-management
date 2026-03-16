"""Database configuration."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


# asyncpg connect-time settings:
#   timeout         — TCP handshake / connection timeout (s)
#   command_timeout — per-command asyncpg timeout (s, client-side)
#   server_settings — PostgreSQL session GUCs forwarded on connect
_CONNECT_ARGS = {
    "timeout": 10,
    "command_timeout": 30,
    "server_settings": {
        "statement_timeout": "30000",  # 30 s — kills runaway queries
        "lock_timeout": "10000",       # 10 s — avoids lock convoys
    },
}

# pool_size=5 steady-state + max_overflow=10 burst = 15 max per worker.
# Across 8 services on one Droplet this stays well within PostgreSQL's
# default max_connections=100 while still handling traffic spikes.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,   # discard stale connections before use
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,      # raise after 30 s waiting for a free connection
    pool_recycle=3600,    # recycle connections after 1 hour
    connect_args=_CONNECT_ARGS,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency: yields a transactional async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
