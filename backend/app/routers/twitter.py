"""
SocialSpace — Twitter OAuth 2.0 PKCE Router
=============================================
Created: Phase 2, Session 2.1
April 18, 2026

WHY this file exists:
Implements the complete Twitter OAuth 2.0 PKCE (Proof Key for Code Exchange)
flow for SocialSpace. PKCE is required by Twitter for confidential clients
(Web App type) and prevents authorization code interception attacks.

Flow:
    1. Frontend calls /api/auth/twitter/authorize
       -> Backend generates code_verifier + code_challenge (PKCE)
       -> Backend generates state (CSRF protection)
       -> Both are stored in memory with expiry
       -> Backend returns the Twitter authorization URL
    2. User is redirected to Twitter, approves permissions
    3. Twitter redirects to /api/auth/twitter/callback?code=...&state=...
       -> Backend validates state (CSRF check)
       -> Backend exchanges code + code_verifier for access + refresh tokens
       -> Backend calls Twitter API to get user profile
       -> Backend upserts PlatformConnection in PostgreSQL
       -> Backend redirects user to frontend /platforms page
    4. Frontend calls /api/auth/twitter/status to confirm connection

Security guarantees:
    - State parameter prevents CSRF attacks on the OAuth flow
    - PKCE prevents authorization code interception
    - State + verifier stored server-side only, never sent to frontend
    - Tokens stored in DB, never in frontend localStorage

Limitations (acceptable for Phase 2):
    - State store is in-memory — lost on server restart (Phase 4: move to Redis)
    - No token rotation on refresh yet (Phase 3)
"""

import base64
import hashlib
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.models import PlatformConnection, User
from app.database.session import get_db
from socialspace_agent.utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/twitter", tags=["Twitter OAuth"])

# ============================================================================
# CONSTANTS
# ============================================================================

# WHY: Twitter OAuth 2.0 endpoints — pinned as constants so a URL change
# is a one-line fix, not a grep-and-replace across the file.
TWITTER_AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
TWITTER_USER_URL = "https://api.twitter.com/2/users/me"

# WHY these scopes:
# tweet.read   — read timeline, check post success
# tweet.write  — post tweets (core SocialSpace feature)
# users.read   — get profile info (username, display name, avatar)
# offline.access — get refresh token so user stays connected without re-auth
TWITTER_SCOPES = "tweet.read tweet.write users.read offline.access"

# WHY 10 minutes: Long enough for a user to complete authorization,
# short enough to limit CSRF window if state is somehow leaked.
STATE_EXPIRY_SECONDS = 600

# ============================================================================
# IN-MEMORY STATE STORE
# WHY in-memory for Phase 2:
# The state (CSRF token) and code_verifier (PKCE) must be stored between
# the /authorize call and the /callback call. Redis is the production solution
# but adds infrastructure complexity. In-memory is correct for single-server
# development. Phase 4 will migrate to Redis with TTL.
#
# Structure: { state: { "code_verifier": str, "user_id": str, "expires_at": float } }
# ============================================================================

_state_store: dict[str, dict] = {}


def _store_state(state: str, code_verifier: str, user_id: str) -> None:
    """
    Store PKCE state for callback validation.

    WHY purge expired states on every write: Prevents unbounded memory growth
    without needing a background cleanup task. On a low-traffic dev server
    this is sufficient. On high traffic, a scheduled cleanup or Redis TTL
    would replace this.

    Args:
        state: Random CSRF token generated for this auth attempt
        code_verifier: PKCE verifier to be sent during token exchange
        user_id: SocialSpace user UUID initiating the OAuth flow
    """
    # Purge expired entries to prevent memory growth
    now = time.time()
    expired_keys = [k for k, v in _state_store.items() if v["expires_at"] < now]
    for k in expired_keys:
        del _state_store[k]
        logger.debug("Purged expired OAuth state: %s", k[:8])

    _state_store[state] = {
        "code_verifier": code_verifier,
        "user_id": user_id,
        "expires_at": now + STATE_EXPIRY_SECONDS,
    }
    logger.debug("Stored OAuth state for user %s (expires in %ds)", user_id, STATE_EXPIRY_SECONDS)


def _consume_state(state: str) -> Optional[dict]:
    """
    Retrieve and immediately delete PKCE state.

    WHY consume (delete on read): State is single-use. If an attacker
    somehow replays the callback URL, the second attempt finds no state
    and is rejected. This is the standard CSRF token pattern.

    Args:
        state: State value received in callback query parameter

    Returns:
        State data dict if found and not expired, None otherwise
    """
    entry = _state_store.pop(state, None)
    if entry is None:
        logger.warning("OAuth state not found — possible CSRF attempt or expired state")
        return None
    if entry["expires_at"] < time.time():
        logger.warning("OAuth state expired — user took too long to authorize")
        return None
    return entry


# ============================================================================
# PKCE UTILITIES
# ============================================================================

def _generate_code_verifier() -> str:
    """
    Generate a cryptographically random PKCE code verifier.

    WHY 64 bytes -> 86 char base64url:
    RFC 7636 requires verifier length 43-128 chars. 64 bytes of entropy
    gives 86 base64url characters — well within range and cryptographically
    strong. secrets.token_bytes uses OS-level CSPRNG (urandom on Linux/Mac,
    CryptGenRandom on Windows).

    Returns:
        Base64url-encoded random string (86 characters, no padding)
    """
    return base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()


def _generate_code_challenge(verifier: str) -> str:
    """
    Derive PKCE code challenge from verifier using S256 method.

    WHY S256 not plain:
    S256 sends the SHA-256 hash of the verifier — even if the challenge is
    intercepted during authorization, the attacker cannot derive the verifier
    needed for token exchange. Twitter requires S256 for confidential clients.

    Formula: base64url(sha256(ascii(verifier)))

    Args:
        verifier: The code_verifier generated for this flow

    Returns:
        Base64url-encoded SHA-256 hash of the verifier (no padding)
    """
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/authorize")
async def twitter_authorize(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Step 1 of Twitter OAuth 2.0 PKCE flow.

    WHY returns URL instead of redirecting:
    The frontend handles the redirect so it can show a loading state,
    close any open modals, and track that a Twitter connection is in progress.
    A server-side redirect would bypass all frontend state management.

    Returns:
        { "authorization_url": "https://twitter.com/i/oauth2/authorize?..." }

    Raises:
        HTTPException 500: If Twitter client credentials are not configured
    """
    settings = get_settings()

    # Validate credentials are configured
    # WHY check here not at startup: Credentials may be added after server start.
    # Checking per-request gives a clear error message instead of a cryptic 401
    # from Twitter's servers.
    if not settings.twitter_client_id or not settings.twitter_client_secret:
        logger.error("Twitter OAuth attempted but TWITTER_CLIENT_ID/SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Twitter integration is not configured. Add TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET to .env",
        )

    # Generate PKCE pair
    code_verifier = _generate_code_verifier()
    code_challenge = _generate_code_challenge(code_verifier)

    # Generate state (CSRF token)
    # WHY 32 bytes: 256 bits of entropy — computationally infeasible to guess.
    state = secrets.token_urlsafe(32)

    # Store for callback validation
    _store_state(state, code_verifier, str(current_user.id))

    # Build Twitter authorization URL
    params = {
        "response_type": "code",
        "client_id": settings.twitter_client_id,
        "redirect_uri": settings.twitter_redirect_uri,
        "scope": TWITTER_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    authorization_url = f"{TWITTER_AUTHORIZE_URL}?{urlencode(params)}"

    logger.info(
        "Twitter OAuth flow initiated for user %s",
        current_user.id,
    )

    return {"authorization_url": authorization_url}


@router.get("/callback")
async def twitter_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Step 2 of Twitter OAuth 2.0 PKCE flow — Twitter redirects here.

    WHY no auth dependency here:
    The user is not authenticated at this point — they arrived from Twitter's
    redirect, not from the SocialSpace frontend. We identify them via the
    state parameter which maps to their user_id in the server-side state store.

    WHY redirect instead of JSON response:
    This endpoint is called by Twitter's servers redirecting the user's browser.
    The browser expects a page, not JSON. We redirect to the frontend which
    shows the result to the user.

    Args:
        code: Authorization code from Twitter (exchange for tokens)
        state: CSRF state token — must match what we generated in /authorize
        error: Error code if user denied or Twitter had an issue
        error_description: Human-readable error from Twitter

    Returns:
        RedirectResponse to frontend /platforms page with success or error param
    """
    settings = get_settings()
    frontend_url = settings.environment == "development" and "http://localhost:5173" or "http://localhost:5173"

    # -------------------------------------------------------------------------
    # Handle user denial or Twitter error
    # -------------------------------------------------------------------------
    if error:
        logger.warning("Twitter OAuth error: %s — %s", error, error_description)
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error={error}",
            status_code=status.HTTP_302_FOUND,
        )

    # -------------------------------------------------------------------------
    # Validate required parameters
    # -------------------------------------------------------------------------
    if not code or not state:
        logger.error("Twitter callback missing code or state parameter")
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error=missing_params",
            status_code=status.HTTP_302_FOUND,
        )

    # -------------------------------------------------------------------------
    # Validate and consume state (CSRF check)
    # -------------------------------------------------------------------------
    state_data = _consume_state(state)
    if state_data is None:
        logger.error("Twitter callback state validation failed — possible CSRF or timeout")
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error=invalid_state",
            status_code=status.HTTP_302_FOUND,
        )

    user_id = state_data["user_id"]
    code_verifier = state_data["code_verifier"]

    # -------------------------------------------------------------------------
    # Exchange authorization code for tokens
    # WHY Basic auth: Twitter requires client_id:client_secret as HTTP Basic
    # auth for confidential clients during token exchange. This is different
    # from the Bearer token used for API calls.
    # -------------------------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                TWITTER_TOKEN_URL,
                auth=(settings.twitter_client_id, settings.twitter_client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.twitter_redirect_uri,
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if token_response.status_code != 200:
                logger.error(
                    "Twitter token exchange failed: %d — %s",
                    token_response.status_code,
                    token_response.text,
                )
                return RedirectResponse(
                    url=f"{frontend_url}/platforms?twitter_error=token_exchange_failed",
                    status_code=status.HTTP_302_FOUND,
                )

            token_data = token_response.json()
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")  # seconds

    except httpx.TimeoutException:
        logger.error("Twitter token exchange timed out for user %s", user_id)
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error=timeout",
            status_code=status.HTTP_302_FOUND,
        )
    except httpx.RequestError as exc:
        logger.error("Twitter token exchange network error for user %s: %s", user_id, exc)
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error=network_error",
            status_code=status.HTTP_302_FOUND,
        )

    # -------------------------------------------------------------------------
    # Fetch Twitter user profile
    # WHY fetch profile: We cache username and display name so the frontend
    # can show "Connected as @dheeraj" without a live Twitter API call
    # every time the platforms page loads.
    # -------------------------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            user_response = await client.get(
                TWITTER_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"user.fields": "id,name,username,profile_image_url"},
            )

            if user_response.status_code != 200:
                logger.error(
                    "Twitter user fetch failed: %d — %s",
                    user_response.status_code,
                    user_response.text,
                )
                return RedirectResponse(
                    url=f"{frontend_url}/platforms?twitter_error=user_fetch_failed",
                    status_code=status.HTTP_302_FOUND,
                )

            twitter_user = user_response.json()["data"]
            twitter_user_id = twitter_user["id"]
            twitter_username = twitter_user["username"]
            twitter_display_name = twitter_user["name"]

    except httpx.TimeoutException:
        logger.error("Twitter user fetch timed out for user %s", user_id)
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error=timeout",
            status_code=status.HTTP_302_FOUND,
        )
    except httpx.RequestError as exc:
        logger.error("Twitter user fetch network error for user %s: %s", user_id, exc)
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error=network_error",
            status_code=status.HTTP_302_FOUND,
        )

    # -------------------------------------------------------------------------
    # Upsert PlatformConnection in database
    # WHY upsert not insert: User may reconnect Twitter after revoking access.
    # Upsert updates the existing row instead of failing with a unique constraint
    # violation on (user_id, platform).
    # -------------------------------------------------------------------------
    try:
        # Calculate token expiry timestamp
        token_expires_at: Optional[datetime] = None
        if expires_in:
            token_expires_at = datetime.fromtimestamp(
                time.time() + expires_in, tz=timezone.utc
            )

        # Check for existing connection
        result = await db.execute(
            select(PlatformConnection).where(
                PlatformConnection.user_id == user_id,
                PlatformConnection.platform == "twitter",
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing connection
            existing.tokens = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": token_data.get("token_type", "bearer"),
                "scope": token_data.get("scope", TWITTER_SCOPES),
            }
            existing.platform_user_id = twitter_user_id
            existing.platform_username = twitter_username
            existing.platform_display_name = twitter_display_name
            existing.token_expires_at = token_expires_at
            existing.is_active = True
            existing.last_used_at = datetime.now(timezone.utc)
            logger.info(
                "Updated Twitter connection for user %s (@%s)",
                user_id,
                twitter_username,
            )
        else:
            # Create new connection
            connection = PlatformConnection(
                user_id=user_id,
                platform="twitter",
                is_active=True,
                tokens={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": token_data.get("token_type", "bearer"),
                    "scope": token_data.get("scope", TWITTER_SCOPES),
                },
                platform_user_id=twitter_user_id,
                platform_username=twitter_username,
                platform_display_name=twitter_display_name,
                token_expires_at=token_expires_at,
            )
            db.add(connection)
            logger.info(
                "Created Twitter connection for user %s (@%s)",
                user_id,
                twitter_username,
            )

        # get_db dependency auto-commits on success
        await db.flush()

    except Exception as exc:
        logger.error(
            "Database error saving Twitter connection for user %s: %s",
            user_id,
            exc,
            exc_info=True,
        )
        return RedirectResponse(
            url=f"{frontend_url}/platforms?twitter_error=db_error",
            status_code=status.HTTP_302_FOUND,
        )

    logger.info(
        "Twitter OAuth complete — user %s connected as @%s",
        user_id,
        twitter_username,
    )

    return RedirectResponse(
        url=f"{frontend_url}/platforms?twitter_connected=true&username={twitter_username}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/status")
async def twitter_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Check if the current user has Twitter connected.

    WHY this endpoint:
    The frontend platforms page needs to know connection state on load.
    Querying our own DB is fast and avoids a live Twitter API call
    just to render a connected/disconnected badge.

    Returns:
        {
            "connected": bool,
            "username": str | None,
            "display_name": str | None,
            "expires_at": str | None  -- ISO 8601 UTC
        }
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "twitter",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        return {"connected": False, "username": None, "display_name": None, "expires_at": None}

    return {
        "connected": True,
        "username": connection.platform_username,
        "display_name": connection.platform_display_name,
        "expires_at": connection.token_expires_at.isoformat() if connection.token_expires_at else None,
    }


@router.delete("/disconnect")
async def twitter_disconnect(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Disconnect Twitter from the current user's account.

    WHY soft delete (is_active=False) not hard delete:
    Preserves the connection record for audit purposes and makes
    reconnection faster (upsert path in callback). Hard delete
    would lose historical connection data.

    Returns:
        { "disconnected": true }

    Raises:
        HTTPException 404: If no active Twitter connection found
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "twitter",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Twitter connection found for this user",
        )

    # Soft delete — preserve record, mark inactive, clear tokens
    # WHY clear tokens on disconnect: User revoked access — holding their
    # tokens after revocation is a security risk even if they are invalidated.
    connection.is_active = False
    connection.tokens = {}

    logger.info(
        "Twitter disconnected for user %s (@%s)",
        current_user.id,
        connection.platform_username,
    )

    return {"disconnected": True}


# ============================================================================
# TWEET POSTING
# ============================================================================

class TweetRequest(BaseModel):
    """
    Request body for posting a tweet.

    WHY content length validation here not just in Twitter API:
    Twitter's 280 char limit should be enforced server-side before making
    an outbound API call. Catching it here gives a clean 422 response
    instead of a confusing Twitter API error.
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=280,
        description="Tweet text content (1-280 characters)"
    )


class TweetResponse(BaseModel):
    """
    Response after successfully posting a tweet.

    WHY return tweet_id and tweet_url:
    Frontend needs tweet_id to link to the live tweet.
    tweet_url is pre-constructed so frontend does not need to know
    Twitter's URL format.
    """
    tweet_id: str
    tweet_url: str
    content: str
    posted_at: str  # ISO 8601 UTC


@router.post("/tweet", response_model=TweetResponse)
async def post_tweet(
    request: TweetRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TweetResponse:
    """
    Post a tweet to the authenticated user's connected Twitter account.

    WHY this endpoint exists:
    This is the core SocialSpace action - taking content and publishing it
    to a real platform. Everything before this was infrastructure. This is
    the product.

    Flow:
        1. Load the user's Twitter PlatformConnection from DB
        2. Extract access_token from the stored tokens JSON
        3. Call Twitter API v2 POST /2/tweets with Bearer token
        4. Return tweet_id and URL for frontend confirmation

    Args:
        request: TweetRequest with content (1-280 chars)
        current_user: Authenticated SocialSpace user
        db: Async database session

    Returns:
        TweetResponse with tweet_id, tweet_url, content, posted_at

    Raises:
        HTTPException 404: No active Twitter connection for this user
        HTTPException 400: Twitter API rejected the tweet (duplicate, policy, etc.)
        HTTPException 500: Network error or unexpected Twitter API failure
    """
    # -------------------------------------------------------------------------
    # Load Twitter connection from DB
    # WHY check is_active: User may have disconnected Twitter since last post.
    # Active check prevents using revoked tokens.
    # -------------------------------------------------------------------------
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "twitter",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Twitter connection found. Connect your Twitter account first.",
        )

    # -------------------------------------------------------------------------
    # Extract access token
    # WHY validate token exists: The tokens JSON could theoretically be empty
    # if a previous disconnect partially cleared it. Explicit check gives a
    # clear error instead of a 401 from Twitter with no explanation.
    # -------------------------------------------------------------------------
    access_token = connection.tokens.get("access_token")
    if not access_token:
        logger.error(
            "Twitter connection for user %s has no access_token in tokens JSON",
            current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Twitter connection is corrupted. Please disconnect and reconnect your Twitter account.",
        )

    # -------------------------------------------------------------------------
    # Post tweet via Twitter API v2
    # WHY POST /2/tweets not v1.1: Twitter API v2 is the current supported
    # version. v1.1 is deprecated and requires OAuth 1.0a which we do not use.
    # WHY text field not status: API v2 uses "text" not "status" (v1.1 name).
    # -------------------------------------------------------------------------
    twitter_api_url = "https://api.twitter.com/2/tweets"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                twitter_api_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"text": request.content},
            )

            # ----------------------------------------------------------------
            # Handle Twitter API error responses
            # WHY check status explicitly: httpx does not raise on 4xx/5xx
            # by default. We need to parse Twitter's error body for context.
            # ----------------------------------------------------------------
            if response.status_code == 401:
                logger.error(
                    "Twitter API returned 401 for user %s - token may be expired or revoked",
                    current_user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Twitter access token is expired or revoked. Please reconnect your Twitter account.",
                )

            if response.status_code == 403:
                error_body = response.json()
                logger.error(
                    "Twitter API returned 403 for user %s: %s",
                    current_user.id,
                    error_body,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Twitter rejected this tweet: {error_body.get('detail', 'Policy violation or duplicate content')}",
                )

            if response.status_code == 429:
                logger.error(
                    "Twitter API rate limit hit for user %s",
                    current_user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Twitter rate limit reached. Please wait before posting again.",
                )

            if response.status_code not in (200, 201):
                error_body = response.text
                logger.error(
                    "Twitter API unexpected status %d for user %s: %s",
                    response.status_code,
                    current_user.id,
                    error_body,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Twitter API returned unexpected status {response.status_code}",
                )

            tweet_data = response.json()
            tweet_id = tweet_data["data"]["id"]
            username = connection.platform_username
            posted_at = datetime.now(timezone.utc).isoformat()
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

    except httpx.TimeoutException:
        logger.error("Twitter API timed out for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Twitter API request timed out. Please try again.",
        )
    except httpx.RequestError as exc:
        logger.error(
            "Twitter API network error for user %s: %s",
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Network error reaching Twitter API. Please try again.",
        )

    # -------------------------------------------------------------------------
    # Update last_used_at on the connection
    # WHY: Tracks when this connection was last actively used. Useful for
    # identifying stale connections that have not posted in months.
    # -------------------------------------------------------------------------
    connection.last_used_at = datetime.now(timezone.utc)

    logger.info(
        "Tweet posted successfully for user %s (@%s) - tweet_id: %s",
        current_user.id,
        username,
        tweet_id,
    )

    return TweetResponse(
        tweet_id=tweet_id,
        tweet_url=tweet_url,
        content=request.content,
        posted_at=posted_at,
    )
