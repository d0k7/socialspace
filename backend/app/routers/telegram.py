"""
SocialSpace — Telegram Bot Router
===================================
Created: Phase 2, Session 2.2
April 19, 2026

WHY this file exists:
Implements Telegram posting via Bot API. Unlike Twitter and LinkedIn,
Telegram's Bot API is completely free with no paid tier requirement.
A bot token from @BotFather is all that is needed to send messages
to any chat, group, or channel where the bot is a member.

No OAuth flow needed:
Telegram bots authenticate with a single static token — not per-user
OAuth. This means one bot serves all SocialSpace users. The bot posts
on behalf of SocialSpace as a platform, not on behalf of the individual
user's personal Telegram account. This is the correct pattern for
Telegram bots and is how every Telegram integration works.

Architecture:
    - Bot token stored in .env (TELEGRAM_BOT_TOKEN)
    - User provides their chat_id (from /connect flow or manual entry)
    - SocialSpace stores chat_id in PlatformConnection.tokens JSON
    - Posting calls Telegram Bot API sendMessage endpoint
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

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])

# ============================================================================
# CONSTANTS
# ============================================================================

TELEGRAM_API_BASE = "https://api.telegram.org/bot"

# ============================================================================
# REQUEST / RESPONSE MODELS
# ============================================================================


class TelegramConnectRequest(BaseModel):
    """
    Request to connect a Telegram chat to SocialSpace.

    WHY chat_id not username:
    Telegram Bot API requires numeric chat_id for sendMessage.
    Usernames are optional and not all chats have them.
    The user gets their chat_id by messaging the bot and calling
    /api/telegram/get-chat-id which reads it from the bot's updates.
    """
    chat_id: str = Field(
        ...,
        description="Telegram chat ID — numeric ID of the user, group, or channel"
    )
    chat_name: Optional[str] = Field(
        None,
        description="Human-readable name for this chat (for display in UI)"
    )


class TelegramMessageRequest(BaseModel):
    """
    Request body for sending a Telegram message.

    WHY 4096 max: Telegram's message length limit is 4096 characters.
    Enforcing here prevents a wasted API call.
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Message text (1-4096 characters)"
    )
    parse_mode: Optional[str] = Field(
        default="HTML",
        description="Telegram parse mode: HTML or Markdown"
    )


class TelegramMessageResponse(BaseModel):
    """Response after successfully sending a Telegram message."""
    message_id: int
    chat_id: str
    content: str
    sent_at: str  # ISO 8601 UTC


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/connect")
async def telegram_connect(
    request: TelegramConnectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Connect a Telegram chat to the current user's SocialSpace account.

    WHY store chat_id in PlatformConnection:
    Follows the same pattern as Twitter/LinkedIn connections. The
    PlatformConnection table is the canonical store for all platform
    credentials. Telegram's "credential" is just the chat_id — where
    SocialSpace is allowed to post on behalf of this user.

    Args:
        request: TelegramConnectRequest with chat_id and optional chat_name
        current_user: Authenticated SocialSpace user
        db: Async database session

    Returns:
        { "connected": true, "chat_id": str, "chat_name": str }

    Raises:
        HTTPException 400: chat_id is invalid or bot cannot reach it
        HTTPException 500: Telegram bot token not configured
    """
    settings = get_settings()

    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot is not configured. Add TELEGRAM_BOT_TOKEN to .env",
        )

    # -------------------------------------------------------------------------
    # Validate chat_id by sending a silent test message
    # WHY validate: Store only reachable chat_ids. A wrong chat_id would cause
    # every subsequent post to fail with no clear error.
    # -------------------------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            test_response = await client.post(
                f"{TELEGRAM_API_BASE}{settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": request.chat_id,
                    "text": "✅ SocialSpace connected! You will receive posts here.",
                },
            )

            if test_response.status_code != 200:
                error_data = test_response.json()
                logger.error(
                    "Telegram validation failed for chat_id %s: %s",
                    request.chat_id,
                    error_data,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not reach Telegram chat {request.chat_id}. Make sure you have messaged @socialspace_agent_bot first.",
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Telegram API timed out. Please try again.",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error reaching Telegram API: {exc}",
        )

    # -------------------------------------------------------------------------
    # Upsert PlatformConnection
    # WHY upsert: User may reconnect with a different chat_id (e.g. switched
    # from personal to group). Update existing row instead of duplicating.
    # -------------------------------------------------------------------------
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "telegram",
        )
    )
    existing = result.scalar_one_or_none()

    chat_name = request.chat_name or f"Telegram Chat {request.chat_id}"

    if existing:
        existing.tokens = {"chat_id": request.chat_id}
        existing.platform_user_id = request.chat_id
        existing.platform_username = chat_name
        existing.platform_display_name = chat_name
        existing.is_active = True
        existing.last_used_at = datetime.now(timezone.utc)
        logger.info(
            "Updated Telegram connection for user %s — chat_id: %s",
            current_user.id,
            request.chat_id,
        )
    else:
        connection = PlatformConnection(
            user_id=current_user.id,
            platform="telegram",
            is_active=True,
            tokens={"chat_id": request.chat_id},
            platform_user_id=request.chat_id,
            platform_username=chat_name,
            platform_display_name=chat_name,
        )
        db.add(connection)
        logger.info(
            "Created Telegram connection for user %s — chat_id: %s",
            current_user.id,
            request.chat_id,
        )

    return {
        "connected": True,
        "chat_id": request.chat_id,
        "chat_name": chat_name,
    }


@router.post("/message", response_model=TelegramMessageResponse)
async def send_telegram_message(
    request: TelegramMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramMessageResponse:
    """
    Send a message to the user's connected Telegram chat.

    WHY this is the core posting endpoint:
    This is SocialSpace's first working real post to a real platform.
    Telegram Bot API is free, reliable, and requires no paid tier.

    Args:
        request: TelegramMessageRequest with content and parse_mode
        current_user: Authenticated SocialSpace user
        db: Async database session

    Returns:
        TelegramMessageResponse with message_id, chat_id, content, sent_at

    Raises:
        HTTPException 404: No active Telegram connection for this user
        HTTPException 400: Telegram rejected the message
        HTTPException 500: Bot token not configured or unexpected error
    """
    settings = get_settings()

    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot is not configured.",
        )

    # Load Telegram connection
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "telegram",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Telegram connection found. Connect Telegram first via /api/telegram/connect.",
        )

    chat_id = connection.tokens.get("chat_id")
    if not chat_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram connection is corrupted. Please reconnect.",
        )

    # -------------------------------------------------------------------------
    # Send message via Telegram Bot API
    # WHY sendMessage not other methods: sendMessage handles text content
    # for all chat types (private, group, channel). Media requires
    # sendPhoto/sendVideo — Phase 3 addition.
    # -------------------------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TELEGRAM_API_BASE}{settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": request.content,
                    "parse_mode": request.parse_mode,
                },
            )

            if response.status_code == 400:
                error_data = response.json()
                logger.error(
                    "Telegram rejected message for user %s: %s",
                    current_user.id,
                    error_data,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Telegram rejected this message: {error_data.get('description', 'Bad request')}",
                )

            if response.status_code == 403:
                logger.error(
                    "Telegram bot blocked by user %s in chat %s",
                    current_user.id,
                    chat_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Telegram bot was blocked. Please unblock @socialspace_agent_bot and reconnect.",
                )

            if response.status_code != 200:
                logger.error(
                    "Telegram API unexpected status %d for user %s: %s",
                    response.status_code,
                    current_user.id,
                    response.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Telegram API returned unexpected status {response.status_code}",
                )

            message_data = response.json()["result"]
            message_id = message_data["message_id"]
            sent_at = datetime.now(timezone.utc).isoformat()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Telegram API timed out. Please try again.",
        )
    except httpx.RequestError as exc:
        logger.error(
            "Telegram API network error for user %s: %s",
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Network error reaching Telegram API. Please try again.",
        )

    # Update last_used_at
    connection.last_used_at = datetime.now(timezone.utc)

    logger.info(
        "Telegram message sent for user %s — chat_id: %s message_id: %s",
        current_user.id,
        chat_id,
        message_id,
    )

    return TelegramMessageResponse(
        message_id=message_id,
        chat_id=chat_id,
        content=request.content,
        sent_at=sent_at,
    )


@router.get("/status")
async def telegram_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Check if the current user has Telegram connected.

    Returns:
        { "connected": bool, "chat_id": str|None, "chat_name": str|None }
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "telegram",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        return {"connected": False, "chat_id": None, "chat_name": None}

    return {
        "connected": True,
        "chat_id": connection.platform_user_id,
        "chat_name": connection.platform_display_name,
    }


@router.delete("/disconnect")
async def telegram_disconnect(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Disconnect Telegram from the current user's account.

    WHY soft delete: Preserves connection record for audit purposes.
    """
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "telegram",
            PlatformConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Telegram connection found.",
        )

    connection.is_active = False
    connection.tokens = {}

    logger.info("Telegram disconnected for user %s", current_user.id)

    return {"disconnected": True}