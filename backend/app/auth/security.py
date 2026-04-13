"""
Security Utilities — Password Hashing and JWT Tokens
======================================================
WHY: Centralised security logic so hashing/token logic
     is never duplicated across routers or services.

DECISIONS:
- bcrypt for hashing: industry standard, adaptive cost factor,
  resistant to GPU attacks. Alternatives: argon2 (newer but less
  widely battle-tested in Python ecosystem), scrypt (memory-hard
  but slower on low-memory servers).
- JWT for tokens: stateless, no DB lookup per request, scales
  horizontally. Trade-off: cannot invalidate individual tokens
  without a blocklist. Acceptable for MVP — add Redis blocklist
  in Phase 4 when we need forced logout.
- HS256 algorithm: symmetric, fast, sufficient for single-server.
  Upgrade to RS256 (asymmetric) when we add microservices.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ============================================================================
# PASSWORD HASHING
# ============================================================================

# WHY bcrypt schemes list: passlib handles algorithm migration gracefully.
# If we switch algorithms in future, old hashes still verify correctly
# until users log in and their hash is transparently upgraded.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    WHY: Never store plain-text passwords. bcrypt adds a random salt
         automatically, so identical passwords produce different hashes.

    Args:
        password: Plain-text password from registration form.

    Returns:
        Bcrypt hash string safe to store in the database.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    WHY: Uses constant-time comparison internally to prevent
         timing attacks where an attacker infers correctness
         from response time differences.

    Args:
        plain_password: Password submitted at login.
        hashed_password: Stored hash from the database.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT TOKENS
# ============================================================================

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a short-lived JWT access token.

    WHY short-lived (30 min default): Limits the damage window if a token
    is stolen. The refresh token handles re-authentication transparently.

    Args:
        subject: User ID (UUID string) — the token's identity claim.
        expires_delta: Override default expiry for testing.

    Returns:
        Signed JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,          # Subject — who this token represents
        "exp": expire,           # Expiry — when token becomes invalid
        "type": "access",        # Type — distinguishes from refresh token
        "iat": datetime.now(timezone.utc),  # Issued at
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a long-lived JWT refresh token.

    WHY separate refresh token: Access tokens are sent with every request
    (higher exposure). Refresh tokens are sent only to /auth/refresh
    (lower exposure). Separating them limits blast radius of token theft.

    Args:
        subject: User ID (UUID string).
        expires_delta: Override default expiry for testing.

    Returns:
        Signed JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    WHY raises JWTError on failure: Callers handle the exception and
    return 401. Never silently swallow token errors.

    Args:
        token: Raw JWT string from Authorization header.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If token is expired, malformed, or signature invalid.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])