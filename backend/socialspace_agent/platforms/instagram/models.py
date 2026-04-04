"""
Instagram Platform - Data Models
=================================

Instagram-specific data models and media types.

Instagram Content Types:
------------------------
- Image posts
- Video posts
- Carousel posts (multiple images/videos)
- Stories
- Reels
- IGTV
- Comments
- Direct messages (limited API access)

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 5
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# INSTAGRAM USER
# ============================================

class InstagramUser(BaseModel):
    """
    Instagram user/account model.
    
    Represents an Instagram user or business account.
    """
    id: str = Field(..., description="Instagram user ID")
    username: str = Field(..., description="Instagram username")
    name: Optional[str] = Field(None, description="Display name")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    followers_count: Optional[int] = Field(None, description="Number of followers")
    follows_count: Optional[int] = Field(None, description="Number of accounts followed")
    media_count: Optional[int] = Field(None, description="Number of posts")
    biography: Optional[str] = Field(None, description="Bio text")
    website: Optional[str] = Field(None, description="Website URL")


# ============================================
# INSTAGRAM MEDIA
# ============================================

class InstagramMedia(BaseModel):
    """
    Instagram media (post) model.
    
    Represents a post on Instagram (image, video, carousel, reel, etc.).
    """
    id: str = Field(..., description="Media ID")
    
    # Media type
    media_type: Literal["IMAGE", "VIDEO", "CAROUSEL_ALBUM"] = Field(
        ..., description="Type of media"
    )
    
    # Content
    media_url: Optional[str] = Field(None, description="Media URL (image/video)")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL (for videos)")
    permalink: Optional[str] = Field(None, description="Link to post on Instagram")
    
    # Caption and metadata
    caption: Optional[str] = Field(None, description="Post caption")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    
    # Engagement
    like_count: Optional[int] = Field(None, description="Number of likes")
    comments_count: Optional[int] = Field(None, description="Number of comments")
    
    # Carousel children (for CAROUSEL_ALBUM)
    children: Optional[List[Dict[str, Any]]] = Field(
        None, description="Child media for carousel posts"
    )
    
    # Media product type
    media_product_type: Optional[str] = Field(
        None, description="FEED, STORY, REELS, IGTV"
    )
    
    # Owner
    owner: Optional[Dict[str, Any]] = Field(None, description="Media owner info")
    
    def is_story(self) -> bool:
        """Check if this is a story."""
        return self.media_product_type == "STORY"
    
    def is_reel(self) -> bool:
        """Check if this is a reel."""
        return self.media_product_type == "REELS"
    
    def is_feed_post(self) -> bool:
        """Check if this is a regular feed post."""
        return self.media_product_type == "FEED" or self.media_product_type is None


# ============================================
# INSTAGRAM COMMENT
# ============================================

class InstagramComment(BaseModel):
    """
    Instagram comment model.
    
    Represents a comment on a post.
    """
    id: str = Field(..., description="Comment ID")
    text: str = Field(..., description="Comment text")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    
    # User who made the comment
    from_user: Optional[Dict[str, Any]] = Field(
        alias="from",
        default=None,
        description="User who commented"
    )
    
    # Username (if from is not available)
    username: Optional[str] = Field(None, description="Username of commenter")
    
    # Parent comment (for replies)
    parent_id: Optional[str] = Field(None, description="Parent comment ID (if reply)")
    
    # Engagement
    like_count: Optional[int] = Field(0, description="Number of likes on comment")
    
    # Media reference
    media: Optional[Dict[str, Any]] = Field(None, description="Media this comment is on")
    
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment."""
        return self.parent_id is not None


# ============================================
# INSTAGRAM MENTION
# ============================================

class InstagramMention(BaseModel):
    """
    Instagram mention model.
    
    Represents when someone mentions the account in a story or post.
    """
    id: str = Field(..., description="Mention ID")
    media_id: str = Field(..., description="Media ID where mention occurred")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    
    # User who mentioned
    from_user: Optional[Dict[str, Any]] = Field(
        alias="from",
        default=None,
        description="User who mentioned the account"
    )


# ============================================
# INSTAGRAM STORY
# ============================================

class InstagramStory(BaseModel):
    """
    Instagram story model.
    
    Stories are temporary posts that disappear after 24 hours.
    """
    id: str = Field(..., description="Story ID")
    media_type: Literal["IMAGE", "VIDEO"] = Field(..., description="Story media type")
    media_url: str = Field(..., description="Story media URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail (for video)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")


# ============================================
# INSTAGRAM INSIGHTS
# ============================================

class InstagramInsights(BaseModel):
    """
    Instagram insights/analytics model.
    
    Engagement metrics for posts, stories, or account.
    """
    impressions: Optional[int] = Field(None, description="Number of times seen")
    reach: Optional[int] = Field(None, description="Number of unique accounts reached")
    engagement: Optional[int] = Field(None, description="Total engagement")
    saved: Optional[int] = Field(None, description="Number of saves")
    video_views: Optional[int] = Field(None, description="Video views")


# ============================================
# INSTAGRAM API RESPONSE
# ============================================

class InstagramPaginatedResponse(BaseModel):
    """
    Paginated response from Instagram Graph API.
    
    Most Instagram endpoints return paginated data.
    """
    data: List[Dict[str, Any]] = Field(..., description="Array of data objects")
    paging: Optional[Dict[str, str]] = Field(
        None, description="Pagination cursors (next, previous)"
    )
    
    def has_next_page(self) -> bool:
        """Check if there are more results."""
        return bool(self.paging and "next" in self.paging)
    
    def get_next_cursor(self) -> Optional[str]:
        """Get the next page cursor."""
        if self.paging and "cursors" in self.paging:
            return self.paging["cursors"].get("after")
        return None


class InstagramErrorResponse(BaseModel):
    """Error response from Instagram Graph API."""
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    code: int = Field(..., description="Error code")
    error_subcode: Optional[int] = Field(None, description="Error subcode")
    fbtrace_id: Optional[str] = Field(None, description="Facebook trace ID")


# ============================================
# INSTAGRAM WEBHOOK
# ============================================

class InstagramWebhookEntry(BaseModel):
    """Instagram webhook entry."""
    id: str = Field(..., description="Instagram Business Account ID")
    time: int = Field(..., description="Unix timestamp")
    changes: List[Dict[str, Any]] = Field(..., description="Array of changes")


class InstagramWebhook(BaseModel):
    """
    Instagram webhook payload.
    
    Received when subscribed events occur (comments, mentions, etc.).
    """
    object: str = Field(..., description="Object type (instagram)")
    entry: List[InstagramWebhookEntry] = Field(..., description="Webhook entries")
