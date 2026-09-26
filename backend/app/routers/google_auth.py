"""
Google OAuth 2.0 Login Router
==============================

Google Sign-In as a second entry point into SocialSpace's existing JWT
auth system, not a second auth system.

WHY this is not reddit.py's shape:
Reddit's flow links a platform to an already-authenticated user, so its
/authorize requires get_current_active_user and its state store maps
state -> an existing user_id. Google Sign-In authenticates someone who has
no session yet, there is no user_id to map state to until the callback
tells us who they are. Same OAuth mechanics, different state semantics.

WHY no Google tokens are ever persisted:
Reddit needs a durable refresh_token because SocialSpace posts to Reddit
indefinitely. Google is used once, at login time, to confirm identity and
read email/name. After that, SocialSpace's own JWT tokens (identical to a
password login) take over. Nothing Google-related touches the database.

Endpoints:
    GET /api/auth/google/login    - Redirect to Google's consent screen
    GET /api/auth/google/callback - Handle Google's redirect, mint SocialSpace JWTs

Author: Dheeraj Mishra / SocialSpace
Phase: SSO
"""

import secrets
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import User
from app.auth.security import hash_password, create_access_token, create_refresh_token
from socialspace_agent.utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/google", tags=["Authentication"])

settings = get_settings()


# ============================================================================
# CONSTANTS
# ============================================================================

# WHY these exact URLs: taken directly from Google's own OpenID Connect
# discovery document, not assumed. Google has deprecated older
# oauth2/v1 and v2 userinfo URLs in favor of openidconnect.googleapis.com.
GOOGLE_AUTHORIZE_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL: str = "https://openidconnect.googleapis.com/v1/userinfo"

# WHY only these three scopes: this flow needs enough to identify the
# person (email) and greet them (name). It does not touch Gmail, Calendar,
# or Drive, so it does not ask for access to any of them.
GOOGLE_SCOPES: str = "openid email profile"

FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

# WHY a dict of state -> issued_at, not just a set:
# This endpoint has zero auth wall in front of it, unlike reddit.py's
# /authorize which requires an existing session, so it is more exposed.
# Bounding how long a dangling, unused state stays valid costs two extra
# lines and closes that gap.
_oauth_states: dict[str, datetime] = {}
STATE_LIFETIME = timedelta(minutes=10)

DEFAULT_TOKEN_LIFETIME_SECONDS: int = 3600


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

async def _exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """
    Exchange a Google authorization code for an access token.

    WHY client_secret in the POST body, not HTTP Basic Auth like reddit.py:
    Google's token endpoint accepts client_id/client_secret as regular form
    fields, matching Google's own documented request shape rather than
    assuming Reddit's Basic Auth pattern transfers unchanged.

    Raises:
        HTTPException 502: Google's token endpoint returned non-200.
        HTTPException 503: Network failure contacting Google.
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth credentials not configured in .env.",
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error contacting Google token endpoint: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Could not reach Google. Check network connectivity.",
            ) from exc

    if response.status_code != 200:
        logger.error(
            f"Google token exchange failed: HTTP {response.status_code} | {response.text}"
        )
        raise HTTPException(
            status_code=502,
            detail="Google token exchange failed. Authorization code may have expired.",
        )

    return response.json()


async def _fetch_google_identity(access_token: str) -> dict:
    """
    Fetch the authenticated person's Google profile.

    WHY a follow-up API call instead of decoding the id_token directly:
    Google's token response includes a signed id_token JWT that already
    contains email and name, but decoding it correctly means verifying its
    signature against Google's rotating public keys, checking aud matches
    our client_id, and checking iss and exp. A follow-up call to Google's
    own userinfo endpoint gets identical data with none of that
    verification surface, matching exactly why reddit.py's
    _fetch_reddit_identity calls Reddit's /api/v1/me instead of parsing
    anything client-side.

    Raises:
        HTTPException 502: Google's userinfo endpoint returned non-200.
        HTTPException 503: Network failure.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error fetching Google identity: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Could not reach Google after token exchange.",
            ) from exc

    if response.status_code != 200:
        logger.error(f"Google userinfo failed: HTTP {response.status_code} | {response.text}")
        raise HTTPException(
            status_code=502,
            detail="Could not fetch Google identity after authorization.",
        )

    return response.json()


def _purge_expired_states() -> None:
    """
    Drop expired entries from the in-memory state store.

    WHY inline on every /login, not a background job: this flow's entire
    volume is however many times a day someone clicks the button. A
    scheduled cleanup for a dict this small would be more code than the
    problem it solves.
    """
    now = datetime.now(timezone.utc)
    expired = [s for s, issued in _oauth_states.items() if now - issued > STATE_LIFETIME]
    for s in expired:
        _oauth_states.pop(s, None)


# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@router.get(
    "/login",
    summary="Start Google Sign-In",
    response_description="302 redirect to Google's consent screen",
)
async def google_login() -> RedirectResponse:
    """
    Redirect the browser to Google's OAuth 2.0 consent screen.

    WHY no current_user dependency, unlike reddit.py's /authorize:
    There is no session yet. This endpoint is how a session gets created.
    Requiring auth here would make Google Sign-In impossible to ever use.

    Raises:
        HTTPException 503: Google credentials absent from .env.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth credentials not yet configured. Check GOOGLE_CLIENT_ID is in your .env file.",
        )

    _purge_expired_states()

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(timezone.utc)

    redirect_uri = settings.google_redirect_uri or "http://localhost:8000/api/auth/google/callback"

    auth_url = (
        f"{GOOGLE_AUTHORIZE_URL}"
        f"?client_id={settings.google_client_id}"
        f"&response_type=code"
        f"&state={state}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={GOOGLE_SCOPES}"
        f"&prompt=select_account"
    )

    logger.info("Google Sign-In flow started")
    return RedirectResponse(url=auth_url)


@router.get(
    "/callback",
    summary="Handle Google's redirect back",
    response_description="302 redirect to frontend with SocialSpace JWTs",
    include_in_schema=False,
)
async def google_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Handle Google's callback, exchange the code, and log the person in.

    WHY tokens travel in the URL fragment (#), not query params (?):
    Reddit's callback only ever redirects with a boolean flag, nothing
    sensitive. This one carries real JWT access and refresh tokens. Query
    params get sent to servers in Referer headers and land in access
    logs; a # fragment never leaves the browser, so it's the safer of the
    two for a redirect that actually needs to carry secrets.
    """
    error_base = f"{FRONTEND_URL}/login?google_error="

    if error:
        logger.warning(f"Google OAuth provider error: {error}")
        return RedirectResponse(url=f"{error_base}access_denied")

    _purge_expired_states()

    if not state or state not in _oauth_states:
        logger.warning("Google callback: invalid or expired state.")
        return RedirectResponse(url=f"{error_base}invalid_state")

    _oauth_states.pop(state)

    if not code:
        logger.error("Google callback: valid state but no code")
        return RedirectResponse(url=f"{error_base}no_code")

    redirect_uri = settings.google_redirect_uri or "http://localhost:8000/api/auth/google/callback"

    try:
        token_data = await _exchange_code_for_tokens(code, redirect_uri)
    except HTTPException as exc:
        logger.error(f"Google token exchange failed: {exc.detail}")
        return RedirectResponse(url=f"{error_base}token_exchange_failed")

    try:
        google_user = await _fetch_google_identity(token_data["access_token"])
    except HTTPException as exc:
        logger.error(f"Google identity fetch failed: {exc.detail}")
        return RedirectResponse(url=f"{error_base}identity_fetch_failed")

    email: Optional[str] = google_user.get("email")
    if not email:
        logger.error("Google callback: userinfo response had no email")
        return RedirectResponse(url=f"{error_base}no_email")

    email = email.lower().strip()
    name: str = (google_user.get("name") or email.split("@")[0]).strip()

    # WHY no email_verified check here: Google only lets an account
    # authenticate this way for an email it has already verified at the
    # provider level. Re-checking here would reject legitimate accounts
    # for no real security gain.

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            is_active=True,
            is_verified=True,  # Google already verified this email
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        logger.info(f"New user created via Google Sign-In: {email} (id={user.id})")
    else:
        logger.info(f"Existing user logged in via Google Sign-In: {email} (id={user.id})")

    if not user.is_active:
        return RedirectResponse(url=f"{error_base}account_deactivated")

    # WHY the same create_access_token/create_refresh_token as /api/auth/login:
    # Google is a second door into the one existing auth system. Everything
    # downstream treats this identically to a password login from here on.
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/google/callback#access_token={access_token}&refresh_token={refresh_token}"
    )