"""
TikTok Platform - Data Models
==============================

TikTok-specific data models.

TikTok Concepts:
----------------
- User: TikTok user/creator
- Video: Short-form video content
- Comment: Discussion on videos
- Sound: Audio/music track
- Hashtag: Challenge/trend tag

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 12
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# TIKTOK USER
# ============================================

class TikTokUser(BaseModel):
    """
    TikTok user model.
    
    Represents a TikTok user/creator.
    """
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username (without @)")
    display_name: str = Field(..., description="Display name")
    
    # Profile info
    bio_description: Optional[str] = Field(None, description="Bio/description")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    
    # Statistics
    follower_count: Optional[int] = Field(0, description="Number of followers")
    following_count: Optional[int] = Field(0, description="Number of following")
    likes_count: Optional[int] = Field(0, description="Total likes received")
    video_count: Optional[int] = Field(0, description="Number of videos")
    
    # Verification
    is_verified: Optional[bool] = Field(False, description="Verified account")
    
    def get_handle(self) -> str:
        """Get username with @ prefix."""
        return f"@{self.username}"
    
    def get_profile_url(self) -> str:
        """Get profile URL."""
        return f"https://tiktok.com/@{self.username}"


# ============================================
# TIKTOK VIDEO
# ============================================

class TikTokVideoStats(BaseModel):
    """Video statistics."""
    view_count: Optional[int] = Field(0, description="View count")
    like_count: Optional[int] = Field(0, description="Like count")
    comment_count: Optional[int] = Field(0, description="Comment count")
    share_count: Optional[int] = Field(0, description="Share count")


class TikTokVideo(BaseModel):
    """
    TikTok video model.
    
    Represents a TikTok video.
    """
    id: str = Field(..., description="Video ID")
    
    # Creator
    author: Optional[Dict[str, str]] = Field(None, description="Video author")
    
    # Content
    description: Optional[str] = Field(None, description="Video description/caption")
    
    # Media
    video_url: Optional[str] = Field(None, description="Video URL")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")
    
    # Duration
    duration: Optional[int] = Field(None, description="Video duration in seconds")
    
    # Timestamps
    create_time: Optional[int] = Field(None, description="Creation timestamp (Unix)")
    
    # Statistics
    stats: Optional[TikTokVideoStats] = Field(None, description="Video statistics")
    
    # Hashtags
    hashtags: Optional[List[str]] = Field(None, description="Hashtags used")
    
    # Visibility
    is_private: Optional[bool] = Field(False, description="Private video")
    
    def get_view_count(self) -> int:
        """Get view count."""
        return self.stats.view_count if self.stats else 0
    
    def get_like_count(self) -> int:
        """Get like count."""
        return self.stats.like_count if self.stats else 0
    
    def get_comment_count(self) -> int:
        """Get comment count."""
        return self.stats.comment_count if self.stats else 0
    
    def get_share_count(self) -> int:
        """Get share count."""
        return self.stats.share_count if self.stats else 0
    
    def get_url(self) -> str:
        """Get video URL."""
        if self.author and "username" in self.author:
            return f"https://tiktok.com/@{self.author['username']}/video/{self.id}"
        return f"https://tiktok.com/video/{self.id}"


# ============================================
# TIKTOK COMMENT
# ============================================

class TikTokComment(BaseModel):
    """
    TikTok comment model.
    
    Represents a comment on a video.
    """
    id: str = Field(..., description="Comment ID")
    
    # Video reference
    video_id: str = Field(..., description="Video ID")
    
    # Author
    user: Optional[Dict[str, Any]] = Field(None, description="Comment author")
    
    # Content
    text: str = Field(..., description="Comment text")
    
    # Timestamps
    create_time: Optional[int] = Field(None, description="Creation timestamp (Unix)")
    
    # Engagement
    like_count: Optional[int] = Field(0, description="Like count")
    reply_count: Optional[int] = Field(0, description="Reply count")
    
    # Parent (for replies)
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID")
    
    def get_author_name(self) -> str:
        """Get author name."""
        if self.user:
            return self.user.get("display_name") or self.user.get("username", "Unknown")
        return "Unknown"
    
    def is_reply(self) -> bool:
        """Check if this is a reply."""
        return self.parent_comment_id is not None


# ============================================
# TIKTOK SOUND
# ============================================

class TikTokSound(BaseModel):
    """
    TikTok sound/music model.
    """
    id: str = Field(..., description="Sound ID")
    title: str = Field(..., description="Sound title")
    author: Optional[str] = Field(None, description="Sound author/artist")
    
    # Media
    duration: Optional[int] = Field(None, description="Duration in seconds")
    cover_url: Optional[str] = Field(None, description="Cover image URL")
    
    # Usage
    video_count: Optional[int] = Field(0, description="Number of videos using this sound")


# ============================================
# TIKTOK HASHTAG
# ============================================

class TikTokHashtag(BaseModel):
    """
    TikTok hashtag/challenge model.
    """
    id: str = Field(..., description="Hashtag ID")
    name: str = Field(..., description="Hashtag name (without #)")
    
    # Statistics
    view_count: Optional[int] = Field(0, description="Total views")
    video_count: Optional[int] = Field(0, description="Number of videos")
    
    def get_formatted_name(self) -> str:
        """Get hashtag with # prefix."""
        return f"#{self.name}"


# ============================================
# TIKTOK API RESPONSE
# ============================================

class TikTokCursor(BaseModel):
    """Pagination cursor."""
    cursor: Optional[str] = Field(None, description="Pagination cursor")
    has_more: Optional[bool] = Field(False, description="Has more results")


class TikTokResponse(BaseModel):
    """
    Generic TikTok API response.
    """
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error info")
    cursor: Optional[TikTokCursor] = Field(None, description="Pagination cursor")
    
    def has_data(self) -> bool:
        """Check if response has data."""
        return self.data is not None
    
    def has_error(self) -> bool:
        """Check if response has error."""
        return self.error is not None
    
    def has_more(self) -> bool:
        """Check if there are more results."""
        if self.cursor:
            return self.cursor.has_more or False
        return False


# ============================================
# TIKTOK ERROR
# ============================================

class TikTokError(BaseModel):
    """TikTok API error."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    log_id: Optional[str] = Field(None, description="Log ID for debugging")
