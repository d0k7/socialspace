"""
Auth Router — Registration, Login, Refresh, Me, Logout
========================================================
WHY: All auth endpoints in one router, mounted at /api/auth.
     Business logic is minimal here — security.py handles
     crypto, dependencies.py handles token validation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.database.session import get_db
from app.database.models import User
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.dependencies import get_current_active_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ============================================================================
# REGISTER
# ============================================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user account.

    WHY return tokens immediately: Avoids forcing a separate login step
    after registration — better UX, one fewer round trip.

    Raises:
        409: Email already registered.
    """
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == request.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(
        name=request.name.strip(),
        email=request.email.lower().strip(),
        hashed_password=hash_password(request.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()   # Get the generated UUID before commit
    await db.refresh(user)

    # Generate tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"New user registered: {user.email} (id={user.id})")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ============================================================================
# LOGIN
# ============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate and return JWT tokens.

    WHY same error for wrong email vs wrong password: Prevents user
    enumeration attacks where an attacker probes which emails exist.

    Raises:
        401: Invalid credentials.
    """
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email.lower().strip())
    )
    user = result.scalar_one_or_none()

    # WHY check both conditions before raising: Prevents timing attacks
    # from early-exit when user not found vs wrong password.
    if not user or not verify_password(request.password, user.hashed_password):
        raise invalid_credentials

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"User logged in: {user.email} (id={user.id})")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ============================================================================
# REFRESH
# ============================================================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Exchange a refresh token for a new access token.

    WHY: Access tokens expire in 30 minutes. The frontend calls this
    automatically to get a new access token without forcing re-login.
    """
    from jose import JWTError
    import uuid

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
    )

    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    access_token = create_access_token(subject=str(user.id))
    refresh_token_new = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_new,
        user=UserResponse.model_validate(user),
    )


# ============================================================================
# ME
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Return the currently authenticated user's profile.

    WHY: Frontend calls this on app load to restore session state
    without storing sensitive user data in localStorage.
    """
    return UserResponse.model_validate(current_user)


# ============================================================================
# LOGOUT
# ============================================================================

@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """
    Logout endpoint.

    WHY: Currently stateless — the frontend deletes its tokens.
    In Phase 4 we add a Redis token blocklist here so stolen tokens
    can be forcibly invalidated server-side.
    """
    logger.info(f"User logged out: {current_user.email}")
    return MessageResponse(message="Successfully logged out.")