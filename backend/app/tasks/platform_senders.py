"""
Synchronous Platform Senders for Celery Workers
=================================================

WHY this file exists separate from app/routers/telegram.py and
app/routers/discord.py:
Those routers are async FastAPI route handlers, built for FastAPI's
Depends dependency injection and an async database session. Celery tasks
run in a synchronous worker process with no event loop (see celery_app.py
and sync_session.py for the full reasoning). An async function cannot be
called directly from sync code without wrapping it in asyncio.run(),
which recreates the exact event loop in a sync worker problem this
project has deliberately avoided since the Phase 5 sync engine was built.

The functions in this file are synchronous mirrors of the exact same
platform API calls the FastAPI routers make. Same endpoint, same request
shape, same headers, same status code handling. They are not a
reinterpretation of how Telegram or Discord posting works, they are that
same logic expressed with httpx.Client (sync) instead of
httpx.AsyncClient (async), so both the composer's post now path and the
Celery scheduler's post later path send messages in an identical way.

WHY a uniform return shape across different platforms:
Every function returns the same SendResult shape. This maps directly onto
app.database.models.PostResult's columns. The caller in scheduler_task.py
writes whatever this dict contains straight into a new PostResult row
without platform specific branching on the result, only the send call
itself is platform specific.

WHY no retry logic inside these functions:
Retry timing, backoff, and the retry count ceiling are owned entirely by
ScheduledPost.retry_count, max_retries, and next_retry_at, checked by
Celery Beat's poll task on its next cycle. A sender function that retried
internally would create a second, competing retry mechanism, exactly the
two sources of truth problem this project has avoided everywhere else.
Each function attempts exactly once and reports what happened.

Author: Dheeraj Mishra / SocialSpace
Phase: 5 - Celery + Redis Scheduling Engine
"""

import logging
from typing import Optional, TypedDict

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# SHARED RESULT SHAPE
# ============================================================================

class SendResult(TypedDict):
    """
    Uniform outcome shape returned by every platform sender.

    WHY TypedDict and not a Pydantic model: this dict is constructed and
    consumed entirely within this synchronous, framework agnostic module
    and scheduler_task.py. Pydantic validation adds no value here since
    both ends are Python code under our control, not an external boundary
    like an HTTP request body. TypedDict gives the same IDE autocomplete
    and type checking benefit with zero runtime overhead.
    """
    success: bool
    platform_post_id: Optional[str]
    platform_post_url: Optional[str]
    error_message: Optional[str]
    error_code: Optional[str]


def _ok(platform_post_id: str, platform_post_url: Optional[str] = None) -> SendResult:
    """WHY a helper: every success path returns the same shape with only
    the id and url varying. Centralising it means a future field addition
    to SendResult only needs updating in one place, not at every call site."""
    return {
        "success": True,
        "platform_post_id": platform_post_id,
        "platform_post_url": platform_post_url,
        "error_message": None,
        "error_code": None,
    }


def _fail(error_message: str, error_code: str) -> SendResult:
    """WHY a helper: mirrors _ok above for the failure path."""
    return {
        "success": False,
        "platform_post_id": None,
        "platform_post_url": None,
        "error_message": error_message,
        "error_code": error_code,
    }


# ============================================================================
# TELEGRAM
# ============================================================================

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


def send_telegram_sync(
    bot_token: str,
    chat_id: str,
    content: str,
    parse_mode: str = "HTML",
) -> SendResult:
    """
    Send a message to a Telegram chat. Synchronous mirror of
    app.routers.telegram.send_telegram_message, same endpoint, same
    request shape, same status code handling.

    WHY platform_post_url is always None: Telegram only produces a public
    deep link (https://t.me/username/message_id) for chats with a public
    username, such as a public channel. This project stores only chat_id,
    not whether that chat has a public username, so a URL cannot be
    constructed without risking a wrong or broken link. Returning None is
    the honest answer given what we actually know.

    Args:
        bot_token: TELEGRAM_BOT_TOKEN from settings.
        chat_id: Destination chat, numeric Telegram chat ID.
        content: Message text, 1 to 4096 characters.
        parse_mode: Telegram parse mode, HTML or Markdown.

    Returns:
        SendResult, see module docstring for the shape.
    """
    if not bot_token:
        return _fail("Telegram bot token not configured.", "not_configured")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{TELEGRAM_API_BASE}{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": content,
                    "parse_mode": parse_mode,
                },
            )
    except httpx.TimeoutException:
        logger.error("Telegram API timed out for chat_id %s", chat_id)
        return _fail("Telegram API timed out.", "timeout")
    except httpx.RequestError as exc:
        logger.error("Telegram network error for chat_id %s: %s", chat_id, exc)
        return _fail(f"Network error reaching Telegram: {exc}", "network_error")

    if response.status_code == 400:
        error_data = response.json()
        description = error_data.get("description", "Bad request")
        logger.error(
            "Telegram rejected message to chat_id %s: %s", chat_id, description
        )
        return _fail(
            f"Telegram rejected this message: {description}", "rejected_by_platform"
        )

    if response.status_code == 403:
        logger.error("Telegram bot blocked in chat_id %s", chat_id)
        return _fail(
            "Telegram bot was blocked in this chat. Reconnect required.",
            "forbidden",
        )

    if response.status_code != 200:
        logger.error(
            "Telegram API unexpected status %d for chat_id %s: %s",
            response.status_code,
            chat_id,
            response.text,
        )
        return _fail(
            f"Telegram API returned unexpected status {response.status_code}",
            "unexpected_status",
        )

    message_data = response.json()["result"]
    message_id = str(message_data["message_id"])
    logger.info(
        "Telegram message sent to chat_id %s, message_id %s", chat_id, message_id
    )
    return _ok(platform_post_id=message_id, platform_post_url=None)


# ============================================================================
# DISCORD
# ============================================================================

DISCORD_API_BASE = "https://discord.com/api/v10"


def send_discord_sync(bot_token: str, channel_id: str, content: str) -> SendResult:
    """
    Send a message to a Discord channel. Synchronous mirror of
    app.routers.discord.send_discord_message, same endpoint, same request
    shape, same status code handling.

    WHY platform_post_url is always None: a Discord message permalink
    (https://discord.com/channels/guild_id/channel_id/message_id) requires
    guild_id. This project's PlatformConnection stores only channel_id,
    not guild_id, so a correct permalink cannot be built from data we
    actually have. UNCERTAIN whether Discord's create message response
    reliably includes guild_id. Rather than guess, this returns None. If
    guild_id turns out to be available and worth storing, that is a
    schema addition for a later session, not something to fake here.

    Args:
        bot_token: DISCORD_BOT_TOKEN from settings.
        channel_id: Destination channel, numeric Discord channel ID.
        content: Message content, 1 to 2000 characters.

    Returns:
        SendResult, see module docstring for the shape.
    """
    if not bot_token:
        return _fail("Discord bot token not configured.", "not_configured")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {bot_token}",
                    "Content-Type": "application/json",
                },
                json={"content": content},
            )
    except httpx.TimeoutException:
        logger.error("Discord API timed out for channel_id %s", channel_id)
        return _fail("Discord API timed out.", "timeout")
    except httpx.RequestError as exc:
        logger.error("Discord network error for channel_id %s: %s", channel_id, exc)
        return _fail(f"Network error reaching Discord: {exc}", "network_error")

    if response.status_code == 401:
        logger.error("Discord API 401, bot token invalid")
        return _fail("Discord bot token is invalid.", "not_configured")

    if response.status_code == 403:
        logger.error(
            "Discord API 403 for channel_id %s, missing permissions", channel_id
        )
        return _fail(
            "Discord bot lacks Send Messages permission in this channel.",
            "forbidden",
        )

    if response.status_code == 404:
        logger.error("Discord channel %s not found", channel_id)
        return _fail(
            "Discord channel not found, it may have been deleted.",
            "not_found",
        )

    if response.status_code == 429:
        logger.warning("Discord rate limit hit for channel_id %s", channel_id)
        return _fail("Discord rate limit reached.", "rate_limited")

    if response.status_code not in (200, 201):
        logger.error(
            "Discord API unexpected status %d for channel_id %s: %s",
            response.status_code,
            channel_id,
            response.text,
        )
        return _fail(
            f"Discord API returned unexpected status {response.status_code}",
            "unexpected_status",
        )

    message_data = response.json()
    message_id = str(message_data["id"])
    logger.info(
        "Discord message sent to channel_id %s, message_id %s", channel_id, message_id
    )
    return _ok(platform_post_id=message_id, platform_post_url=None)