"""
SocialSpace — Discord Bot Router
==================================
Created: Phase 2, Session 2.3
April 20, 2026

WHY this file exists:
Implements Discord posting via Bot API. Like Telegram, Discord's Bot API
is completely free with no paid tier requirement. A bot token from the
Discord Developer Portal is all that is needed to send messages to any
channel where the bot has Send Messages permission.

No OAuth flow needed:
Discord bots authenticate with a single static bot token. The bot posts
to a specific channel_id stored in PlatformConnection.tokens JSON.
This is the correct pattern for Discord bots.

Architecture:
    - Bot token stored in .env (DISCORD_BOT_TOKEN)
    - User provides channel_id during /connect flow
    - SocialSpace stores channel_id in PlatformConnection.tokens JSON
    - Posting calls Discord API v10 POST /channels/{channel_id}/messages
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.models import PlatformConnection, User
from app.database.session import get_db
from socialspace_agent.utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discord", tags=["Discord"])

# ============================================================================
# CONSTANTS
# ============================================================================

DISCORD_API_BASE = "https://discord.com/api/v10"

# ============================================================================
# REQUEST / RESPONSE MODELS
# ============================================================================


class DiscordConnectRequest(BaseModel):
    """
    Request to connect a Discord channel to SocialSpace.

    WHY channel_id not server_id:
    SocialSpace posts to a specific channel, not a whole server.
    A server can have many channels — the user picks which one
    receives SocialSpace posts.
    """
    channel_id: str = Field(
        ...,
        description="Discord channel ID — numeric ID of the target channel"
    )
    channel_name: Optional[str] = Field(
        None,
        description="Human-readable name for display in UI"
    )


class DiscordMessageRequest(BaseModel):
    """
    Request body for sending a Discord message.

    WHY 2000 max: Discord's message content limit is 2000 characters.
    Enforcing here prevents a wasted API call.
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message content (1-2000 characters)"
    )


class DiscordMessageResponse(BaseModel):
    """Response after successfully sending a Discord message."""
    message_id: str
    channel_id: str
    content: str
    sent_at: str  # ISO 8601 UTC


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/connect")
async def discord_connect(
    request: DiscordConnectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Connect a Discord channel to the current user's SocialSpace account.

    WHY validate by fetching channel info:
    Verifies the bot token is valid and the bot has access to the channel
    before storing. Prevents storing unreachable channels that would cause
    every subsequent post to fail silently.

    Args:
        request: DiscordConnectRequest with channel_id and optional name
        current_user: Authenticated SocialSpace user
        db: Async database session

    Returns:
        { "connected": true, "channel_id": str, "channel_name": str }

    Raises:
        HTTPException 400: Bot cannot access the channel
        HTTPException 500: Discord bot token not configured
    """
    settings = get_settings()

    if not settings.discord_bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Discord bot is not configured. Add DISCORD_BOT_TOKEN to .env",
        )

    # -------------------------------------------------------------------------
    # Validate channel access by fetching channel info
    # WHY fetch channel not send test message: Fetching channel info is a
    # read-only operation — no visible side effect for the user.
    # -------------------------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            channel_response = await client.get(
                f"{DISCORD_API_BASE}/channels/{request.channel_id}",
                headers={"Authorization": f"Bot {settings.discord_bot_token}"},
            )

            if channel_response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Discord bot token is invalid. Check DISCORD_BOT_TOKEN in .env",
                )

            if channel_response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Discord bot does not have access to channel {request.channel_id}. Make sure the bot is in the server and has Send Messages permission.",
                )

            if channel_response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Discord channel {request.channel_id} not found. Check the channel ID.",
                )

            if channel_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not access Discord channel: {channel_response.status_code}",
                )

            channel_data = channel_response.json()
            # WHY prefer API name over user-provided: API name is authoritative.
            # User may have typed the wrong name. Fall back to user-provided if
            # API does not return a name (e.g. DM channels have no name).
            resolved_name = (
                channel_data.get("name")
                or request.channel_name
                or f"Discord Channel {request.channel_id}"
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Discord API timed out. Please try again.",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error reaching Discord API: {exc}",
        )

    # -------------------------------------------------------------------------
    # Upsert PlatformConnection
    # -------------------------------------------------------------------------
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "discord",
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.tokens = {"channel_id": request.channel_id}
        existing.platform_user_id = request.channel_id
        existing.platform_username = resolved_name
        existing.platform_display_name = resolved_name
        existing.is_active = True
        existing.last_used_at = datetime.now(timezone.utc)
        logger.info(
            "Updated Discord connection for user %s — channel: %s (#%s)",
            current_user.id,
            request.channel_id,
            resolved_name,
        )
    else:
        connection = PlatformConnection(
            user_id=current_user.id,
            platform="discord",
            is_active=True,
            tokens={"channel_id": request.channel_id},
            platform_user_id=request.channel_id,
            platform_username=resolved_name,
            platform_display_name=resolved_name,
        )
        db.add(connection)
        logger.info(
            "Created Discord connection for user %s — channel: %s (#%s)",
            current_user.id,
            request.channel_id,
            resolved_name,
        )

    return {
        "connected": True,
        "channel_id": request.channel_id,
        "channel_name": resolved_name,
    }


@router.post("/message", response_model=DiscordMessageResponse)
async def send_discord_message(
    request: DiscordMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DiscordMessageResponse:
    """
    Send a message to the user's connected Discord channel.

    Args:
        request: DiscordMessageRequest with content (1-2000 chars)
        current_user: Authenticated SocialSpace user
        db: Async database session

    Returns:
        DiscordMessageResponse with message_id, channel_id, content, sent_at

    Raises:
        HTTPException 404: No active Discord connection for this user
        HTTPException 400: Discord rejected the message
        HTTPException 500: Bot token not configured or unexpected error
    """
    settings = get_settings()

    if not settings.discord_bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Discord bot is not configured.",
        )

    # Load Discord connection
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "discord",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Discord connection found. Connect Discord first via /api/discord/connect.",
        )

    channel_id = connection.tokens.get("channel_id")
    if not channel_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Discord connection is corrupted. Please reconnect.",
        )

    # -------------------------------------------------------------------------
    # Send message via Discord API v10
    # WHY embeds not plain text: Embeds allow richer formatting with title,
    # description, color, and footer. Plain content is simpler for Phase 2.
    # Embeds will be added in Phase 3 for AI-generated content presentation.
    # -------------------------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {settings.discord_bot_token}",
                    "Content-Type": "application/json",
                },
                json={"content": request.content},
            )

            if response.status_code == 401:
                logger.error(
                    "Discord API 401 for user %s — bot token invalid or expired",
                    current_user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Discord bot token is invalid. Please reconfigure.",
                )

            if response.status_code == 403:
                logger.error(
                    "Discord API 403 for user %s in channel %s — missing permissions",
                    current_user.id,
                    channel_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Discord bot lacks Send Messages permission in this channel.",
                )

            if response.status_code == 404:
                logger.error(
                    "Discord channel %s not found for user %s",
                    channel_id,
                    current_user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Discord channel not found. It may have been deleted. Please reconnect.",
                )

            if response.status_code == 429:
                logger.warning(
                    "Discord rate limit hit for user %s",
                    current_user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Discord rate limit reached. Please wait before posting again.",
                )

            if response.status_code not in (200, 201):
                logger.error(
                    "Discord API unexpected status %d for user %s: %s",
                    response.status_code,
                    current_user.id,
                    response.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Discord API returned unexpected status {response.status_code}",
                )

            message_data = response.json()
            message_id = message_data["id"]
            sent_at = datetime.now(timezone.utc).isoformat()

    except httpx.TimeoutException:
        logger.error("Discord API timed out for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Discord API timed out. Please try again.",
        )
    except httpx.RequestError as exc:
        logger.error(
            "Discord API network error for user %s: %s",
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Network error reaching Discord API. Please try again.",
        )

    # Update last_used_at
    connection.last_used_at = datetime.now(timezone.utc)

    logger.info(
        "Discord message sent for user %s — channel: %s message_id: %s",
        current_user.id,
        channel_id,
        message_id,
    )

    return DiscordMessageResponse(
        message_id=message_id,
        channel_id=channel_id,
        content=request.content,
        sent_at=sent_at,
    )


@router.get("/status")
async def discord_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Check if the current user has Discord connected.

    Returns:
        { "connected": bool, "channel_id": str|None, "channel_name": str|None }
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "discord",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        return {"connected": False, "channel_id": None, "channel_name": None}

    return {
        "connected": True,
        "channel_id": connection.platform_user_id,
        "channel_name": connection.platform_display_name,
    }


@router.delete("/disconnect")
async def discord_disconnect(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Disconnect Discord from the current user's account.

    WHY soft delete: Preserves connection record for audit purposes.
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "discord",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Discord connection found.",
        )

    connection.is_active = False
    connection.tokens = {}

    logger.info("Discord disconnected for user %s", current_user.id)

    return {"disconnected": True}