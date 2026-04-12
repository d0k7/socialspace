"""
SocialSpace Database Models
============================
WHY: Single file for all ORM models during foundation phase.
     Split into separate files per domain once models exceed ~500 lines.

Tables:
    users           — registered accounts
    platform_connections — OAuth tokens per user per platform
    posts           — content created in the composer
    scheduled_posts — posts queued for future publishing
    post_results    — actual publish outcomes (success/fail/metrics)
    analytics_snapshots — periodic platform metric snapshots
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, JSON, Float, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utcnow() -> datetime:
    """WHY: Always store UTC. Convert to user timezone in the frontend."""
    return datetime.now(timezone.utc)


# ============================================================================
# USERS
# ============================================================================

class User(Base):
    """
    Registered SocialSpace user.

    WHY separate from platform connections: A user can connect many platforms.
    One-to-many relationship keeps credentials isolated per platform.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # AI brand voice — stored as JSON for flexibility
    # WHY JSON: Brand voice parameters will evolve as AI improves.
    # JSON avoids migrations for every new voice parameter.
    brand_voice: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    platform_connections: Mapped[list["PlatformConnection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


# ============================================================================
# PLATFORM CONNECTIONS
# ============================================================================

class PlatformConnection(Base):
    """
    OAuth credentials for one platform for one user.

    WHY store encrypted tokens here: The platform adapter library needs
    real credentials to make API calls. These are the bridge between
    the user's account and the real platform API.

    WHY UniqueConstraint on (user_id, platform): One connection per
    platform per user. Prevents duplicate OAuth flows overwriting each other.
    """
    __tablename__ = "platform_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="uq_platform_connections_user_platform"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # WHY JSON for tokens: OAuth token shapes differ per platform.
    # Twitter needs bearer_token + access_token + secret.
    # Instagram needs access_token + user_id.
    # JSON handles all shapes without schema changes per platform.
    tokens: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Platform account info (cached from API)
    platform_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    user: Mapped["User"] = relationship(back_populates="platform_connections")

    def __repr__(self) -> str:
        return f"<PlatformConnection user={self.user_id} platform={self.platform}>"


# ============================================================================
# POSTS
# ============================================================================

class Post(Base):
    """
    A piece of content created in the composer.

    WHY separate from scheduled_posts: A post can exist as a draft
    before it is ever scheduled. Scheduling is an action on a post,
    not the post itself.
    """
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Target platforms
    platforms: Mapped[list] = mapped_column(JSON, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
        index=True
        # Values: draft | scheduled | publishing | published | failed | cancelled
    )

    # AI metadata — was this AI-generated? What prompt?
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="posts")
    scheduled_post: Mapped[Optional["ScheduledPost"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    results: Mapped[list["PostResult"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} status={self.status}>"


# ============================================================================
# SCHEDULED POSTS
# ============================================================================

class ScheduledPost(Base):
    """
    Scheduling metadata for a post.

    WHY separate table: Scheduling concerns (when, retry count, next attempt)
    are operationally separate from content concerns (what to post).
    The scheduler reads this table without loading full post content.
    """
    __tablename__ = "scheduled_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    timezone: Mapped[str] = mapped_column(
        String(50), default="UTC", nullable=False
    )

    # Retry logic
    # WHY: Platform APIs fail. Transient failures should retry automatically.
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationship
    post: Mapped["Post"] = relationship(back_populates="scheduled_post")

    def __repr__(self) -> str:
        return f"<ScheduledPost post={self.post_id} at={self.scheduled_at}>"


# ============================================================================
# POST RESULTS
# ============================================================================

class PostResult(Base):
    """
    Actual outcome of publishing a post to one platform.

    WHY per-platform result: A post targets multiple platforms.
    Each platform publish is an independent operation that can
    succeed or fail independently.
    """
    __tablename__ = "post_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)

    # Outcome
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_post_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    post: Mapped["Post"] = relationship(back_populates="results")

    def __repr__(self) -> str:
        return f"<PostResult post={self.post_id} platform={self.platform} ok={self.success}>"


# ============================================================================
# ANALYTICS SNAPSHOTS
# ============================================================================

class AnalyticsSnapshot(Base):
    """
    Periodic snapshot of platform metrics for one user.

    WHY snapshots not live queries: Platform APIs have rate limits.
    We snapshot metrics on a schedule (hourly/daily) and serve
    the frontend from our database. This is also what enables
    trend analysis — you need historical data points.
    """
    __tablename__ = "analytics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Core metrics — platform-agnostic
    followers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    following: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_posts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # WHY JSON for extended metrics: Each platform has unique metrics.
    # TikTok has video views, Pinterest has saves, Reddit has karma.
    # JSON stores platform-specific extras without schema explosion.
    extended_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    snapshotted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot user={self.user_id} platform={self.platform}>"