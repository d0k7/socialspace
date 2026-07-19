"""
SocialSpace - Posts and Scheduling Router
===========================================
Created: Phase 5, Session 5.x
July 2026

WHY this file exists:
This is the API surface that lets a user create content and schedule it
for future publishing. Scheduling and content creation happen together as
one action here, not as separate draft-then-schedule steps, because there
is currently no separate draft saving flow in this project's composer to
build on top of. ScheduledPost.post_id is a strict one to one foreign key
(unique=True), which is why schedule_post creates both rows together in
one atomic unit of work rather than treating scheduling as an action on a
pre existing post.

WHY reject unconnected platforms at schedule time, not at publish time:
publish_post (Celery) already handles a platform with no active
PlatformConnection gracefully, recording an honest "not_connected"
PostResult rather than crashing. But discovering that failure hours later,
when the post silently never went out and nobody is watching, is a much
worse experience than being told immediately, at the moment of scheduling,
exactly which platform needs to be connected first.

WHY scheduled_at_local and timezone are two separate request fields, not
one pre converted UTC value: ScheduledPost.timezone exists specifically to
remember the named IANA timezone the user picked, not just a numeric
offset, so the stored local time stays correct across daylight saving
transitions in timezones that observe it, and so this same value can be
used to show "9:00 AM IST" back to the user without forcing UTC math on
the frontend. Accepting a pre converted UTC timestamp instead would make
that column meaningless.
"""

import logging
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.models import Post, ScheduledPost, PlatformConnection, User
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/posts", tags=["Posts"])


# ============================================================================
# REQUEST / RESPONSE MODELS
# ============================================================================

class SchedulePostRequest(BaseModel):
    """
    Request to create and schedule a new post.

    WHY min_length=1 on content is not enough on its own: Pydantic's
    min_length only rejects a literal empty string, not whitespace only
    content like "   ". The field_validator below closes that gap.
    """
    content: str = Field(..., min_length=1, max_length=10000)
    platforms: list[str] = Field(..., min_length=1)
    scheduled_at_local: str = Field(
        ...,
        description="Naive local datetime with no offset, e.g. 2026-07-25T09:00:00",
    )
    timezone: str = Field(
        ...,
        description="IANA timezone name, e.g. Asia/Kolkata",
    )
    media_urls: Optional[list[str]] = None
    is_ai_generated: bool = False
    ai_prompt: Optional[str] = None
    ai_model_used: Optional[str] = None

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        """Reject content that is only whitespace, min_length=1 alone lets this through."""
        if not v.strip():
            raise ValueError("content cannot be blank or whitespace only")
        return v

    @field_validator("platforms")
    @classmethod
    def dedupe_platforms(cls, v: list[str]) -> list[str]:
        """
        Remove duplicate platform names while preserving the order the
        user specified them in. A duplicate does not break anything
        downstream, publish_post's idempotency check would simply skip
        the second occurrence, but de-duplicating here keeps the stored
        Post.platforms list clean and the schedule confirmation honest
        about what will actually be attempted.
        """
        return list(dict.fromkeys(v))


class ScheduledPostSummary(BaseModel):
    """One row in the scheduled posts list."""
    post_id: str
    content_preview: str
    platforms: list[str]
    status: str
    scheduled_at_utc: str
    timezone: str
    retry_count: int
    max_retries: int
    created_at: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/schedule", status_code=status.HTTP_201_CREATED)
async def schedule_post(
    request: SchedulePostRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new post and schedule it for future publishing.

    Args:
        request: content, target platforms, local scheduled time, and the
            IANA timezone name that local time is in.
        current_user: authenticated SocialSpace user.
        db: async database session.

    Returns:
        post_id, scheduled_at_utc (ISO), scheduled_at_local, timezone,
        platforms (deduplicated), status.

    Raises:
        HTTPException 400: unknown timezone name, scheduled_at_local is
            not parseable, scheduled_at_local includes an offset or Z
            (it must be a naive local time), the resulting UTC time is
            not in the future, or one or more target platforms have no
            active connection for this user.
    """
    try:
        tz = ZoneInfo(request.timezone)
    except ZoneInfoNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown timezone '{request.timezone}'. Use an IANA name such as Asia/Kolkata.",
        )

    try:
        naive_dt = datetime.fromisoformat(request.scheduled_at_local)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid scheduled_at_local '{request.scheduled_at_local}'. "
                "Expected ISO format with no offset, e.g. 2026-07-25T09:00:00."
            ),
        )

    if naive_dt.tzinfo is not None:
        # WHY reject an offset or Z here: Python 3.11's fromisoformat
        # accepts a trailing Z or +HH:MM and returns an aware datetime.
        # Accepting that silently would mean this endpoint sometimes
        # receives a pre converted UTC time and sometimes a true local
        # time with no way to tell them apart, defeating the entire point
        # of the separate timezone field.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "scheduled_at_local must not include a UTC offset or 'Z'. "
                "Send the local wall clock time and set timezone separately."
            ),
        )

    localized_dt = naive_dt.replace(tzinfo=tz)
    scheduled_at_utc = localized_dt.astimezone(timezone.utc)

    now_utc = datetime.now(timezone.utc)
    if scheduled_at_utc <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_at_local must be in the future.",
        )

    # Validate every target platform is actually connected for this user
    connected_result = await db.execute(
        select(PlatformConnection.platform).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform.in_(request.platforms),
            PlatformConnection.is_active == True,  # noqa: E712
        )
    )
    connected_platforms = {row[0] for row in connected_result.all()}
    missing = [p for p in request.platforms if p not in connected_platforms]

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"These platforms are not connected: {', '.join(missing)}. "
                "Connect them first on the Platforms page."
            ),
        )

    post = Post(
        user_id=current_user.id,
        content=request.content,
        media_urls=request.media_urls,
        platforms=request.platforms,
        status="scheduled",
        is_ai_generated=request.is_ai_generated,
        ai_prompt=request.ai_prompt,
        ai_model_used=request.ai_model_used,
    )
    db.add(post)

    # WHY flush here, not just commit at the end: Post.id uses a Python
    # side default (default=uuid.uuid4), which SQLAlchemy populates during
    # flush, not at object construction. ScheduledPost below needs a real
    # post.id value for its foreign key, so it must be created after an
    # explicit flush, not after the eventual commit. get_db still commits
    # both rows together as one transaction when the request completes.
    await db.flush()

    scheduled_post = ScheduledPost(
        post_id=post.id,
        scheduled_at=scheduled_at_utc,
        timezone=request.timezone,
    )
    db.add(scheduled_post)

    logger.info(
        "Post %s scheduled for user %s at %s (%s), platforms: %s",
        post.id,
        current_user.id,
        scheduled_at_utc.isoformat(),
        request.timezone,
        request.platforms,
    )

    return {
        "post_id": str(post.id),
        "scheduled_at_utc": scheduled_at_utc.isoformat(),
        "scheduled_at_local": request.scheduled_at_local,
        "timezone": request.timezone,
        "platforms": request.platforms,
        "status": post.status,
    }


@router.get("/scheduled", response_model=list[ScheduledPostSummary])
async def list_scheduled_posts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduledPostSummary]:
    """
    List this user's posts that are currently scheduled or in the middle
    of publishing, soonest first.

    WHY this excludes published, partial, failed, and cancelled posts:
    this endpoint answers "what do I have coming up", not "show me
    everything that ever happened". A separate history endpoint covering
    completed posts is a natural future addition, deliberately not built
    here to keep this endpoint's scope honest and narrow.

    Returns:
        List of ScheduledPostSummary, ordered by scheduled_at ascending.
    """
    result = await db.execute(
        select(Post, ScheduledPost)
        .join(ScheduledPost, ScheduledPost.post_id == Post.id)
        .where(
            Post.user_id == current_user.id,
            Post.status.in_(["scheduled", "publishing"]),
        )
        .order_by(ScheduledPost.scheduled_at.asc())
    )
    rows = result.all()

    summaries: list[ScheduledPostSummary] = []
    for post, scheduled in rows:
        preview = (
            post.content if len(post.content) <= 140 else post.content[:137] + "..."
        )
        summaries.append(
            ScheduledPostSummary(
                post_id=str(post.id),
                content_preview=preview,
                platforms=post.platforms,
                status=post.status,
                scheduled_at_utc=scheduled.scheduled_at.isoformat(),
                timezone=scheduled.timezone,
                retry_count=scheduled.retry_count,
                max_retries=scheduled.max_retries,
                created_at=post.created_at.isoformat(),
            )
        )

    return summaries


@router.delete("/scheduled/{post_id}")
async def cancel_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cancel a scheduled post before it publishes.

    WHY this sets Post.status to 'cancelled' instead of deleting the row:
    matches the same audit preserving pattern already used for platform
    disconnects elsewhere in this project. The ScheduledPost row and any
    PostResult history from an earlier failed attempt stay intact.

    WHY only status == 'scheduled' can be cancelled: 'publishing' means a
    Celery task is actively sending this post right now, cancelling mid
    send would race against that task's own commit. Anything already
    published, partial, failed, or cancelled is a terminal state where
    cancellation no longer means anything.

    Args:
        post_id: UUID string of the post to cancel.

    Returns:
        { "cancelled": true, "post_id": str }

    Raises:
        HTTPException 400: post_id is not a valid UUID, or the post is
            not currently in a cancellable state.
        HTTPException 404: no post with this id belongs to this user.
    """
    try:
        post_uuid = uuid.UUID(post_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="post_id must be a valid UUID.",
        )

    result = await db.execute(
        select(Post).where(
            Post.id == post_uuid,
            Post.user_id == current_user.id,
        )
    )
    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scheduled post found with this id for your account.",
        )

    if post.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot cancel a post with status '{post.status}'. "
                "Only posts still waiting to publish can be cancelled."
            ),
        )

    post.status = "cancelled"

    logger.info("Post %s cancelled by user %s", post_id, current_user.id)

    return {"cancelled": True, "post_id": post_id}