"""
Synchronous Database Session for Celery Workers
=================================================

WHY this file exists separate from app/database/session.py:
session.py's AsyncSessionLocal is built on asyncpg and requires an asyncio
event loop to drive every query. Celery's worker pool on Windows runs plain
synchronous Python with no event loop at all (see celery_app.py for why
--pool=solo is required on Windows). Forcing async code to run inside a
sync Celery task via asyncio.run() creates a new event loop and a new
connection on every single task execution, which under repeated task runs
causes connection pool exhaustion and can deadlock against the FastAPI
process's own pool on the same Postgres instance. The correct, standard
pattern for mixing an async web framework with a sync task queue is exactly
what this file provides: a second, independent, fully synchronous
SQLAlchemy engine using psycopg2, dedicated to the Celery process. Same
database, same tables, two separate connection pools, because they are two
separate processes that were never meant to share one.

WHY derive the sync URL from DATABASE_URL instead of a new env var:
Requiring a second DATABASE_URL_SYNC value in .env would mean the same
credentials exist twice. A future password rotation would need to update
two lines instead of one, an easy way to end up with one stale, silently
wrong connection string. Deriving it programmatically from the existing
DATABASE_URL guarantees both engines always point at the same credentials.
If DATABASE_URL does not use the asyncpg driver scheme, that assumption is
wrong for this codebase, and the code below raises immediately with a
clear message rather than silently connecting to the wrong place. It never
prints the URL itself, since that would print the database password to
logs or console.

WHY psycopg2 and not a newer psycopg driver:
psycopg2-binary is already a permanent, protected dependency in this
project. Alembic already proves psycopg2 works against this exact
database. Reusing it here means zero new dependencies for the sync engine.

Author: Dheeraj Mishra / SocialSpace
Phase: 5 - Celery + Redis Scheduling Engine
"""

import os
import logging
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# DERIVE SYNC DATABASE URL FROM THE EXISTING ASYNC URL
# ============================================================================

_ASYNC_DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

if not _ASYNC_DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. The Celery sync "
        "engine derives its connection string from this value and cannot "
        "start without it."
    )

if "+asyncpg" not in _ASYNC_DATABASE_URL:
    # WHY raise instead of silently falling back to a plain postgresql
    # scheme: a silent fallback could connect this worker with different
    # driver behaviour than expected, or mask a typo in .env. Failing
    # loudly here, with no credential printed, is safer than a working but
    # wrong connection discovered only when a scheduled post mysteriously
    # never fires days from now.
    raise ValueError(
        "DATABASE_URL does not contain '+asyncpg'. This file assumes the "
        "existing DATABASE_URL uses the asyncpg driver scheme "
        "(postgresql+asyncpg://...) and derives the sync engine's URL by "
        "replacing +asyncpg with +psycopg2. UNCERTAIN: verify the actual "
        "scheme in .env and update this replacement logic to match. The "
        "value itself is intentionally not shown here to avoid printing "
        "credentials."
    )

SYNC_DATABASE_URL: str = _ASYNC_DATABASE_URL.replace("+asyncpg", "+psycopg2")

# ============================================================================
# SYNC ENGINE
# ============================================================================

# WHY pool_size=5, smaller than the async engine's 10: the async engine
# serves concurrent HTTP requests from potentially many simultaneous users.
# This engine serves exactly one Celery worker process running --pool=solo
# on Windows, meaning one task at a time. A large pool here would hold open
# Postgres connections for no benefit.
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_sync_db() -> Iterator[Session]:
    """
    Context manager that yields a synchronous database session for use
    inside Celery tasks.

    WHY a context manager and not a generator based dependency like get_db:
    FastAPI's Depends system calls get_db as a generator automatically.
    Celery tasks have no equivalent dependency injection framework, they
    are plain function calls. A context manager, used as
    "with get_sync_db() as db:", is the natural sync Python idiom for
    acquire a resource, always release it, even on exception, outside a
    web framework.

    WHY explicit commit and rollback here, mirroring get_db's behaviour:
    Same contract as the async get_db. Commit on clean exit, rollback on
    any exception, always close. Celery tasks must never leave a session
    open or a transaction hanging after a task function returns, since the
    same worker process reuses this session factory for every subsequent
    task it picks up.

    Yields:
        An active synchronous SQLAlchemy Session.

    Usage:
        from app.database.sync_session import get_sync_db

        def some_celery_task():
            with get_sync_db() as db:
                ...
    """
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


logger.info("Sync engine configured for Celery workers.")