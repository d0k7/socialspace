"""
FastAPI Auth Dependencies
==========================
WHY: Dependencies are injected per-route via Depends().
     This keeps auth logic out of route handlers entirely.
     A route either gets a valid User object or the request
     is rejected at the dependency layer — never inside business logic.
"""

import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import User
from app.auth.security import decode_token

# WHY HTTPBearer: Extracts the Bearer token from the Authorization header
# automatically. Returns 403 if header is missing entirely.
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: resolve a valid JWT to a real User row.

    WHY this pattern: Every protected route gets a fully-loaded User
    object — not just a user_id string. This means routes never need
    to do their own user lookups, and auth logic stays in one place.

    Args:
        credentials: Bearer token extracted from Authorization header.
        db: Async database session.

    Returns:
        Authenticated User ORM object.

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)

        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if not user_id or token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Look up user in database
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Alias dependency for routes that need an active user.
    WHY: Explicit naming makes route intent clear in the signature.
    """
    return current_user