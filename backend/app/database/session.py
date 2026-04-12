"""
Database Session Management
============================
WHY: Single source of truth for database connections.
     Async engine for non-blocking I/O — critical for AI workloads
     where DB calls must not block the event loop.
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# WHY pool_size=10: Handles concurrent requests without hammering the DB.
# WHY max_overflow=20: Allows burst traffic up to 30 total connections.
# WHY pool_pre_ping=True: Detects stale connections before using them,
#     preventing "connection closed" errors after idle periods.
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # WHY: Prevents lazy-load errors after commit
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a database session.

    WHY: Using a dependency ensures the session is always closed
         after the request, even if an exception occurs.

    Usage:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()