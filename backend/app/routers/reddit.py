"""
Reddit OAuth 2.0 Router
=======================

Implements the complete Reddit OAuth 2.0 Authorization Code flow for SocialSpace.

WHY Authorization Code (not Implicit/Client Credentials):
- Implicit flow is deprecated by OAuth 2.0 Security BCP (RFC 9700)
- Client Credentials cannot act on behalf of a user
- Authorization Code with 'permanent' duration grants a refresh_token,
  enabling SocialSpace to post autonomously without re-authorization

WHY NOT PKCE for Reddit (unlike Twitter):
- Reddit's token exchange uses HTTP Basic Auth (client_id:client_secret),
  not a code_verifier. Reddit's API does not require PKCE as of v1.

Endpoints:
    GET /api/reddit/authorize    - Initiate OAuth flow (browser redirect)
    GET /api/reddit/callback     - Handle Reddit callback (browser redirect)
    GET /api/reddit/status       - Connection status from DB
    POST /api/reddit/submit      - Post to subreddit (with auto token refresh)
    DELETE /api/reddit/disconnect - Soft delete connection

Author: Dheeraj Mishra / SocialSpace
Phase: 4.3 - Reddit Integration
"""

import secrets
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import PlatformConnection, User
from app.auth.dependencies import get_current_active_user
from socialspace_agent.utils.config import get_settings

logger = logging.getLogger(__name__)


# ============================================================================
# ROUTER CONFIGURATION
# ============================================================================

router = APIRouter(
    prefix="/api/reddit",
    tags=["reddit"],
)

settings = get_settings()


# ============================================================================
# CONSTANTS
# ============================================================================

REDDIT_AUTHORIZE_URL: str = "https://www.reddit.com/api/v1/authorize"
REDDIT_TOKEN_URL: str = "https://www.reddit.com/api/v1/access_token"
REDDIT_IDENTITY_URL: str = "https://oauth.reddit.com/api/v1/me"
REDDIT_SUBMIT_URL: str = "https://oauth.reddit.com/api/submit"

# WHY specific User-Agent string: Reddit's API enforces a descriptive User-Agent
# policy. Generic agents like 'python-httpx/0.x' trigger rate limits immediately.
# Format: <platform>:<app ID>:<version> (by /u/<reddit_username>)
USER_AGENT: str = "web:com.socialspace.agent:1.0.0 (by /u/socialspace_agent)"

# WHY permanent duration: SocialSpace is an autonomous agent that posts without
# the user being present. 'permanent' grants a refresh_token for indefinite
# access. 'temporary' tokens expire after 1 hour with no refresh path.
REDDIT_DURATION: str = "permanent"

# WHY these scopes:
# identity - read username so UI shows "Connected as u/..." - required for UX
# submit   - create posts on behalf of the user - the core feature
# Future: read, flair, privatemessages when those features are built
REDDIT_SCOPES: str = "identity submit"

# WHY in-memory state store vs Redis:
# OAuth state tokens are valid for < 10 minutes (one browser redirect round-trip).
# Storing in Redis adds infrastructure complexity for data with zero durability
# requirement. If server restarts mid-OAuth, the user clicks Connect again.
# Risk accepted: not suitable for multi-process deployments. Fine for Phase 4.
# TODO Phase 5: move to Redis when Celery + Redis infrastructure is live.
_oauth_states: dict[str, str] = {}  # {state_token: user_id_str}

# WHY hardcoded: config.py does not yet have FRONTEND_URL.
# Will be moved to settings in Phase 5 when Celery config is added.
FRONTEND_URL: str = "http://localhost:5173"

# Default token lifetime if Reddit omits expires_in (should never happen but defensive)
DEFAULT_TOKEN_LIFETIME_SECONDS: int = 3600


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class RedditSubmitRequest(BaseModel):
    """
    Payload for submitting a Reddit text (self) post.

    WHY separate fields vs a generic content blob:
    Reddit's /api/submit requires subreddit, title, and text as distinct
    parameters. Flattening them into a generic field would require parsing
    on the backend with no benefit.
    """

    subreddit: str = Field(
        ...,
        min_length=1,
        max_length=21,
        description="Target subreddit name (with or without r/ prefix)",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Post title. Reddit hard-limits to 300 characters.",
    )
    text: str = Field(
        default="",
        max_length=40000,
        description="Post body in markdown. Max 40,000 characters.",
    )


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

async def _exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """
    Exchange an authorization code for Reddit access + refresh tokens.

    WHY Basic Auth for token exchange:
    Reddit's token endpoint authenticates the client via HTTP Basic Auth where
    username=client_id and password=client_secret. This is RFC 6749 Section 2.3.1
    for confidential clients. Reddit does not accept client_secret in the body.

    Args:
        code:         Authorization code from Reddit callback URL.
        redirect_uri: Must exactly match the redirect_uri in /authorize.

    Returns:
        Token dict from Reddit: access_token, refresh_token, expires_in, scope.

    Raises:
        HTTPException 502: Reddit token endpoint returned non-200.
        HTTPException 503: Network failure contacting Reddit.
    """
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "Reddit API credentials not configured. "
                "Awaiting Reddit API application approval."
            ),
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                REDDIT_TOKEN_URL,
                auth=(settings.reddit_client_id, settings.reddit_client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"User-Agent": USER_AGENT},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error contacting Reddit token endpoint: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Could not reach Reddit API. Check network connectivity.",
            ) from exc

    if response.status_code != 200:
        logger.error(
            f"Reddit token exchange failed: HTTP {response.status_code} | {response.text}"
        )
        raise HTTPException(
            status_code=502,
            detail="Reddit token exchange failed. Authorization code may have expired.",
        )

    return response.json()


async def _fetch_reddit_identity(access_token: str) -> dict:
    """
    Fetch the authenticated user's Reddit profile via /api/v1/me.

    WHY at connect time (not on every status check):
    Fetching identity once at connect time lets us cache the username in DB.
    Calling the Reddit API on every status check would waste quota, add latency,
    and break the page if Reddit is down.

    Args:
        access_token: Fresh token from _exchange_code_for_tokens.

    Returns:
        Reddit user dict. Contains 'name' (username) and 'id'.

    Raises:
        HTTPException 502: Reddit /me returned non-200.
        HTTPException 503: Network failure.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                REDDIT_IDENTITY_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": USER_AGENT,
                },
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error fetching Reddit identity: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Could not reach Reddit API after token exchange.",
            ) from exc

    if response.status_code != 200:
        logger.error(
            f"Reddit /me failed: HTTP {response.status_code} | {response.text}"
        )
        raise HTTPException(
            status_code=502,
            detail="Could not fetch Reddit user identity after authorization.",
        )

    return response.json()


async def _refresh_access_token(
    connection: PlatformConnection,
    db: AsyncSession,
) -> str:
    """
    Refresh a Reddit access token using the stored refresh_token.

    WHY refresh instead of re-authorize:
    Reddit access tokens expire after 1 hour. Re-authorization requires user
    interaction (browser redirect). The refresh token is permanent (requested
    via duration=permanent at authorize time) and allows silent renewal.
    This is the standard OAuth 2.0 token refresh flow (RFC 6749 Section 6).

    Mutates connection.access_token, connection.token_expires_at, connection.tokens.
    get_db commits on context exit - do NOT call db.commit() here.

    Args:
        connection: Active PlatformConnection row for user+reddit.
        db:         Active async DB session.

    Returns:
        New access token string.

    Raises:
        HTTPException 401: Refresh token missing or refresh call failed.
        HTTPException 503: Network failure contacting Reddit.
    """
    if not connection.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Reddit refresh token missing. Please reconnect via OAuth.",
        )

    if not settings.reddit_client_id or not settings.reddit_client_secret:
        raise HTTPException(status_code=503, detail="Reddit credentials not configured.")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                REDDIT_TOKEN_URL,
                auth=(settings.reddit_client_id, settings.reddit_client_secret),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": connection.refresh_token,
                },
                headers={"User-Agent": USER_AGENT},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error refreshing Reddit token: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Could not reach Reddit to refresh token.",
            ) from exc

    if response.status_code != 200:
        logger.error(
            f"Reddit token refresh failed: HTTP {response.status_code} | {response.text}"
        )
        # WHY 401 not 502: caller interprets 401 as "user must reconnect" and
        # returns a meaningful re-auth prompt to the frontend.
        raise HTTPException(
            status_code=401,
            detail="Reddit token refresh failed. Please reconnect your Reddit account.",
        )

    token_data = response.json()
    new_token: str = token_data["access_token"]
    expires_in: int = token_data.get("expires_in", DEFAULT_TOKEN_LIFETIME_SECONDS)

    # Mutate connection in place - get_db commits on exit
    connection.access_token = new_token
    connection.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    # WHY merge not replace: Reddit may omit refresh_token on refresh response
    # if it is unchanged. Merging preserves the existing refresh_token in that case.
    connection.tokens = {**(connection.tokens or {}), **token_data}

    logger.info(f"Reddit token refreshed for user_id={connection.user_id}")
    return new_token


async def _get_active_connection(user_id: int, db: AsyncSession) -> PlatformConnection:
    """
    Fetch the active Reddit PlatformConnection for a user or raise HTTP 400.

    Extracted as a helper because both /submit and /disconnect need the same
    query + error handling. Avoids duplicating the SQLAlchemy select block.

    Args:
        user_id: Authenticated user's integer ID.
        db:      Active async DB session.

    Returns:
        Active PlatformConnection row.

    Raises:
        HTTPException 400: No active Reddit connection found for this user.
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == user_id,
            PlatformConnection.platform == "reddit",
            PlatformConnection.is_active == True,  # noqa: E712
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Reddit is not connected. Please authorize via the Platforms page.",
        )

    return connection


# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@router.get(
    "/authorize",
    summary="Start Reddit OAuth 2.0 flow",
    response_description="302 redirect to Reddit authorization page",
)
async def reddit_authorize(
    current_user: User = Depends(get_current_active_user),
) -> RedirectResponse:
    """
    Initiate Reddit OAuth 2.0 Authorization Code flow.

    WHY state generation is server-side (not frontend):
    The CSRF state token must be stored server-side so the callback can
    validate it. If the frontend generated the state, we would need a
    separate storage endpoint anyway. Generating and storing in one place
    is simpler and eliminates one round-trip.

    Returns:
        302 RedirectResponse to Reddit's OAuth consent page.

    Raises:
        HTTPException 503: Reddit credentials absent from .env.
    """
    if not settings.reddit_client_id:
        raise HTTPException(
            status_code=503,
            detail=(
                "Reddit API credentials not yet configured. "
                "The API application is pending Reddit's approval. "
                "Check back once REDDIT_CLIENT_ID is in your .env file."
            ),
        )

    # WHY 32 bytes: OWASP recommends >= 128 bits of entropy for CSRF state tokens.
    # secrets.token_urlsafe(32) produces 43 URL-safe base64 characters.
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = str(current_user.id)

    redirect_uri = (
        settings.reddit_redirect_uri
        or "http://localhost:8000/api/reddit/callback"
    )

    # WHY space-separated scopes: Reddit's /authorize uses space-separated
    # scope strings. Comma-separated is wrong here (unlike some other platforms).
    auth_url = (
        f"{REDDIT_AUTHORIZE_URL}"
        f"?client_id={settings.reddit_client_id}"
        f"&response_type=code"
        f"&state={state}"
        f"&redirect_uri={redirect_uri}"
        f"&duration={REDDIT_DURATION}"
        f"&scope={REDDIT_SCOPES}"
    )

    logger.info(f"Reddit OAuth flow started for user_id={current_user.id}")
    return RedirectResponse(url=auth_url)


@router.get(
    "/callback",
    summary="Handle Reddit OAuth callback",
    response_description="302 redirect to frontend with success or error param",
    include_in_schema=False,
)
async def reddit_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Handle the OAuth 2.0 callback from Reddit after user authorization.

    WHY no current_user dependency here:
    At callback time there is no Authorization header. The request is the
    user's browser following Reddit's redirect. The user is identified via
    the 'state' parameter stored in _oauth_states during /authorize. This
    is the standard OAuth 2.0 callback pattern - state is the auth mechanism.

    Reddit sends to this endpoint via browser redirect. Query params:
        code  - authorization code (present on success)
        state - CSRF token we generated in /authorize
        error - set by Reddit if user denied access

    Redirect targets:
        Success: {FRONTEND_URL}/platforms?reddit_connected=true
        Failure: {FRONTEND_URL}/platforms?reddit_error={reason}
    """
    error_base = f"{FRONTEND_URL}/platforms?reddit_error="

    # Case 1: Reddit reported an error (user clicked Decline, app suspended, etc.)
    if error:
        logger.warning(f"Reddit OAuth provider error: {error}")
        return RedirectResponse(url=f"{error_base}access_denied")

    # Case 2: CSRF check - state must be in our store and non-expired
    if not state or state not in _oauth_states:
        logger.warning(
            f"Reddit callback: invalid or expired state. "
            f"Active state count: {len(_oauth_states)}"
        )
        return RedirectResponse(url=f"{error_base}invalid_state")

    # Consume state immediately - one-time use prevents replay attacks
    user_id_str = _oauth_states.pop(state)

    # Case 3: State valid but code absent (should not happen, defensive)
    if not code:
        logger.error(f"Reddit callback: valid state for user {user_id_str} but no code")
        return RedirectResponse(url=f"{error_base}no_code")

    redirect_uri = (
        settings.reddit_redirect_uri
        or "http://localhost:8000/api/reddit/callback"
    )

    # Exchange authorization code for tokens
    try:
        token_data = await _exchange_code_for_tokens(code, redirect_uri)
    except HTTPException as exc:
        logger.error(f"Token exchange failed for user {user_id_str}: {exc.detail}")
        return RedirectResponse(url=f"{error_base}token_exchange_failed")

    # Fetch Reddit username to display in UI and store in DB
    try:
        reddit_user = await _fetch_reddit_identity(token_data["access_token"])
    except HTTPException as exc:
        logger.error(f"Identity fetch failed for user {user_id_str}: {exc.detail}")
        return RedirectResponse(url=f"{error_base}identity_fetch_failed")

    username: str = reddit_user.get("name", "unknown")
    reddit_user_id: str = str(reddit_user.get("id", ""))
    expires_in: int = token_data.get("expires_in", DEFAULT_TOKEN_LIFETIME_SECONDS)
    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Upsert PlatformConnection - update existing row or create new one
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == int(user_id_str),
            PlatformConnection.platform == "reddit",
        )
    )
    connection = result.scalar_one_or_none()

    if connection:
        # WHY update all credential fields: user may have re-authorized with
        # a different Reddit account, or the previous refresh_token was revoked.
        connection.is_active = True
        connection.access_token = token_data.get("access_token")
        connection.refresh_token = token_data.get("refresh_token")
        connection.platform_user_id = reddit_user_id
        connection.platform_username = username
        connection.platform_display_name = f"u/{username}"
        connection.token_expires_at = token_expires_at
        connection.tokens = token_data
    else:
        connection = PlatformConnection(
            user_id=int(user_id_str),
            platform="reddit",
            is_active=True,
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            platform_user_id=reddit_user_id,
            platform_username=username,
            platform_display_name=f"u/{username}",
            token_expires_at=token_expires_at,
            tokens=token_data,
        )
        db.add(connection)

    # WHY no db.commit(): get_db session auto-commits on context exit.
    # Calling commit() here would double-commit and cause session state issues.

    logger.info(
        f"Reddit OAuth complete: user_id={user_id_str} connected as u/{username}"
    )
    return RedirectResponse(url=f"{FRONTEND_URL}/platforms?reddit_connected=true")


@router.get("/status", summary="Get Reddit connection status")
async def reddit_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return Reddit connection status for the authenticated user.

    WHY read from DB not from Reddit API:
    Status checks happen on every PlatformsPage load. Calling the Reddit API
    on every load wastes quota, adds 200-500ms latency, and breaks the page
    if Reddit has an outage. Reading our DB is < 5ms and never fails due to
    Reddit being down.

    Returns:
        connected (bool):     Whether an active connection exists.
        username (str|None):  Reddit username if connected.
        display_name (str|None): Formatted as "u/username" if connected.
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "reddit",
            PlatformConnection.is_active == True,  # noqa: E712
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        return {"connected": False, "username": None, "display_name": None}

    return {
        "connected": True,
        "username": connection.platform_username,
        "display_name": connection.platform_display_name,
    }


@router.post("/submit", summary="Submit a text post to Reddit")
async def reddit_submit(
    payload: RedditSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Submit a self (text) post to a subreddit on behalf of the user.

    Token refresh strategy: automatic, transparent, single-retry.
    If the access token has expired (Reddit tokens expire after 1 hour),
    the endpoint refreshes it using the stored refresh_token and retries
    the post once. The user sees a successful post with no re-auth prompt.

    WHY kind="self" only:
    SocialSpace generates text content. Link posts require a URL, which is
    a different content type. Link post support is a future Phase 6 feature.

    WHY resubmit=True:
    Without this, Reddit rejects a post if the same title was recently
    submitted to the same subreddit. SocialSpace may retry failed posts,
    and this flag prevents false duplicate errors.

    Returns:
        posted (bool):        Always True on success.
        subreddit (str):      Normalized name (no r/ prefix).
        title (str):          Post title as submitted.
        post_url (str|None):  Direct URL to post if extractable from response.

    Raises:
        HTTPException 400: Not connected, or Reddit rejected the post logically.
        HTTPException 401: Token refresh failed - user must reconnect.
        HTTPException 502: Reddit API returned unexpected non-2xx.
        HTTPException 503: Network error.
    """
    connection = await _get_active_connection(current_user.id, db)

    # WHY strip r/ and leading slash: users copy "r/subreddit" from Reddit URLs.
    # Reddit's /api/submit rejects the "r/" prefix - it expects just "subreddit".
    subreddit = payload.subreddit.lstrip("r/").lstrip("/").strip()

    if not subreddit:
        raise HTTPException(
            status_code=400,
            detail="Subreddit name is empty after stripping r/ prefix.",
        )

    submit_payload = {
        "kind": "self",
        "sr": subreddit,
        "title": payload.title,
        "text": payload.text,
        "resubmit": True,
        "nsfw": False,
        "spoiler": False,
    }

    access_token = connection.access_token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": USER_AGENT,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                REDDIT_SUBMIT_URL,
                json=submit_payload,
                headers=headers,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error submitting to Reddit: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Network error reaching Reddit. Post was not submitted.",
            ) from exc

        # WHY retry exactly once on 401:
        # Retry-once prevents infinite loops if the refresh token is also invalid.
        # Two 401s in a row means the user genuinely needs to reconnect.
        if response.status_code == 401:
            logger.info(
                f"Reddit 401 for user_id={current_user.id} - refreshing token and retrying"
            )
            access_token = await _refresh_access_token(connection, db)
            headers["Authorization"] = f"Bearer {access_token}"

            try:
                response = await client.post(
                    REDDIT_SUBMIT_URL,
                    json=submit_payload,
                    headers=headers,
                    timeout=30.0,
                )
            except httpx.RequestError as exc:
                logger.error(f"Network error on Reddit submit retry: {exc}")
                raise HTTPException(
                    status_code=503,
                    detail="Network error on retry. Post was not submitted.",
                ) from exc

    if response.status_code not in (200, 201):
        logger.error(
            f"Reddit submit HTTP error: {response.status_code} | {response.text[:500]}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"Reddit rejected the post (HTTP {response.status_code}). Check subreddit rules.",
        )

    response_data = response.json()

    # WHY check success flag: Reddit returns HTTP 200 even for logical errors
    # (rate limits, banned from subreddit, NSFW required, etc.). The 'success'
    # field inside the response body is the authoritative success indicator.
    if response_data.get("success") is False:
        error_message = "Post rejected by Reddit"
        try:
            # Reddit embeds error text in the jquery array of its legacy response format
            for item in response_data.get("jquery", []):
                if isinstance(item, list) and len(item) >= 4:
                    args = item[3]
                    if isinstance(args, list) and args and isinstance(args[0], str):
                        candidate = args[0]
                        if any(kw in candidate.lower() for kw in ["error", "ban", "rate", "spam", "wrong"]):
                            error_message = candidate
                            break
        except Exception:
            pass

        logger.warning(
            f"Reddit logical rejection for user_id={current_user.id} "
            f"to r/{subreddit}: {error_message}"
        )
        raise HTTPException(status_code=400, detail=error_message)

    # Extract post URL from Reddit's jquery response format (best-effort)
    # WHY best-effort: post was already made successfully; URL is a UX bonus.
    post_url: Optional[str] = None
    try:
        for item in response_data.get("jquery", []):
            if isinstance(item, list) and len(item) >= 4:
                call_args = item[3]
                if isinstance(call_args, list):
                    for val in call_args:
                        if isinstance(val, str) and "reddit.com/r/" in val:
                            post_url = val
                            break
            if post_url:
                break
    except Exception as exc:
        logger.debug(f"Could not extract post URL from Reddit response: {exc}")

    logger.info(
        f"Reddit post submitted: user_id={current_user.id} "
        f"to r/{subreddit} | url={post_url}"
    )

    return {
        "posted": True,
        "subreddit": subreddit,
        "title": payload.title,
        "post_url": post_url,
    }


@router.delete("/disconnect", summary="Disconnect Reddit from user account")
async def reddit_disconnect(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Soft-delete the Reddit PlatformConnection for the current user.

    WHY soft delete (is_active=False) not hard delete:
    Preserves the audit trail. If the user reconnects later, we retain
    the original connect date and history. Hard delete loses all context.

    WHY clear tokens on disconnect:
    Storing active tokens on an is_active=False row is a security risk.
    Tokens are cleared immediately. The row stays for audit only.

    WHY NOT revoke token on Reddit's side:
    Reddit provides a revocation endpoint (POST /api/v1/revoke_token).
    Not implemented in Phase 4 because Reddit credentials are pending
    approval and are not yet live. Add revocation in Phase 5.

    Returns:
        disconnected (bool): True if connection was found and deactivated.
        detail (str|None):   Message if connection was already absent.
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "reddit",
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        # WHY 200 not 404: disconnect is idempotent. Calling disconnect when
        # already disconnected is not an error from the frontend's perspective.
        return {
            "disconnected": False,
            "detail": "Reddit was not connected for this account.",
        }

    connection.is_active = False
    connection.access_token = None
    connection.refresh_token = None
    connection.tokens = None
    # WHY no db.commit(): get_db auto-commits on context exit.

    logger.info(f"Reddit disconnected for user_id={current_user.id}")
    return {"disconnected": True}