"""
YouTube Platform - Data Models
===============================

YouTube-specific data models.

YouTube Concepts:
-----------------
- Video: Main content unit
- Channel: Creator's page
- Comment: Discussion on video
- CommentThread: Comment with replies
- Playlist: Collection of videos

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 9
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


def _to_camel(string: str) -> str:
    """Convert snake_case field names to lowerCamelCase for API compatibility."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class YouTubeBaseModel(BaseModel):
    """Base model with YouTube API field alias behavior."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
        extra="ignore",
    )


# ============================================
# YOUTUBE CHANNEL
# ============================================

class YouTubeChannel(YouTubeBaseModel):
    """
    YouTube channel model.
    
    Represents a YouTube channel (creator's page).
    """
    id: str = Field(..., description="Channel ID")
    title: str = Field(..., description="Channel title")
    description: Optional[str] = Field(None, description="Channel description")
    custom_url: Optional[str] = Field(None, description="Custom URL (e.g., @username)")
    
    # Thumbnails
    thumbnails: Optional[Dict[str, Any]] = Field(None, description="Thumbnail images")
    
    # Statistics
    view_count: Optional[str] = Field(None, description="Total view count")
    subscriber_count: Optional[str] = Field(None, description="Subscriber count")
    video_count: Optional[str] = Field(None, description="Number of videos")
    
    # Timestamps
    published_at: Optional[str] = Field(None, description="Channel creation date")
    
    def get_url(self) -> str:
        """Get channel URL."""
        if self.custom_url:
            return f"https://youtube.com/{self.custom_url}"
        return f"https://youtube.com/channel/{self.id}"
    
    def get_subscribers(self) -> int:
        """Get subscriber count as integer."""
        try:
            return int(self.subscriber_count) if self.subscriber_count else 0
        except:
            return 0


# ============================================
# YOUTUBE VIDEO
# ============================================

class YouTubeVideoSnippet(YouTubeBaseModel):
    """Video snippet (basic info)."""
    published_at: str = Field(..., description="Publication timestamp")
    channel_id: str = Field(..., description="Channel ID")
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    thumbnails: Dict[str, Any] = Field(..., description="Thumbnail images")
    channel_title: str = Field(..., description="Channel title")
    tags: Optional[List[str]] = Field(None, description="Video tags")
    category_id: Optional[str] = Field(None, description="Category ID")


class YouTubeVideoStatistics(YouTubeBaseModel):
    """Video statistics."""
    view_count: Optional[str] = Field(None, description="View count")
    like_count: Optional[str] = Field(None, description="Like count")
    comment_count: Optional[str] = Field(None, description="Comment count")
    
    def get_views(self) -> int:
        """Get view count as integer."""
        try:
            return int(self.view_count) if self.view_count else 0
        except:
            return 0
    
    def get_likes(self) -> int:
        """Get like count as integer."""
        try:
            return int(self.like_count) if self.like_count else 0
        except:
            return 0
    
    def get_comments(self) -> int:
        """Get comment count as integer."""
        try:
            return int(self.comment_count) if self.comment_count else 0
        except:
            return 0


class YouTubeVideo(YouTubeBaseModel):
    """
    YouTube video model.
    
    Represents a video on YouTube.
    """
    id: str = Field(..., description="Video ID")
    snippet: YouTubeVideoSnippet = Field(..., description="Video snippet")
    statistics: Optional[YouTubeVideoStatistics] = Field(None, description="Video statistics")
    
    def get_url(self) -> str:
        """Get video URL."""
        return f"https://youtube.com/watch?v={self.id}"
    
    def get_title(self) -> str:
        """Get video title."""
        return self.snippet.title
    
    def get_description(self) -> str:
        """Get video description."""
        return self.snippet.description


# ============================================
# YOUTUBE COMMENT
# ============================================

class YouTubeCommentSnippet(YouTubeBaseModel):
    """Comment snippet."""
    text_display: str = Field(..., description="Comment text (HTML)")
    text_original: str = Field(..., description="Comment text (plain)")
    author_display_name: str = Field(..., description="Author name")
    author_channel_id: Optional[Dict[str, str]] = Field(None, description="Author channel ID")
    like_count: Optional[int] = Field(0, description="Like count")
    published_at: str = Field(..., description="Publication timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    # Parent reference
    parent_id: Optional[str] = Field(None, description="Parent comment ID (for replies)")
    
    # Video reference
    video_id: Optional[str] = Field(None, description="Video ID")
    
    def get_author_id(self) -> Optional[str]:
        """Get author channel ID."""
        if self.author_channel_id and "value" in self.author_channel_id:
            return self.author_channel_id["value"]
        return None


class YouTubeComment(YouTubeBaseModel):
    """
    YouTube comment model.
    
    Represents a comment on a video.
    """
    id: str = Field(..., description="Comment ID")
    snippet: YouTubeCommentSnippet = Field(..., description="Comment snippet")
    
    def get_text(self) -> str:
        """Get comment text (plain)."""
        return self.snippet.text_original
    
    def get_author(self) -> str:
        """Get author name."""
        return self.snippet.author_display_name
    
    def get_likes(self) -> int:
        """Get like count."""
        return self.snippet.like_count or 0
    
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment."""
        return self.snippet.parent_id is not None


# ============================================
# YOUTUBE COMMENT THREAD
# ============================================

class YouTubeCommentThread(YouTubeBaseModel):
    """
    YouTube comment thread model.
    
    A thread consists of a top-level comment and its replies.
    """
    id: str = Field(..., description="Thread ID")
    snippet: Dict[str, Any] = Field(..., description="Thread snippet")
    
    # Top-level comment
    top_level_comment: Optional[YouTubeComment] = Field(
        None, 
        description="Top-level comment"
    )
    
    # Replies
    replies: Optional[Dict[str, Any]] = Field(None, description="Reply comments")
    
    def get_video_id(self) -> Optional[str]:
        """Get video ID this thread is on."""
        return self.snippet.get("videoId")
    
    def get_total_reply_count(self) -> int:
        """Get total number of replies."""
        return self.snippet.get("totalReplyCount", 0)
    
    def has_replies(self) -> bool:
        """Check if thread has replies."""
        return self.get_total_reply_count() > 0


# ============================================
# YOUTUBE API RESPONSE
# ============================================

class YouTubePageInfo(YouTubeBaseModel):
    """Pagination info."""
    total_results: Optional[int] = Field(None, description="Total results")
    results_per_page: Optional[int] = Field(None, description="Results per page")


class YouTubeResponse(YouTubeBaseModel):
    """
    Generic YouTube API response.
    """
    kind: str = Field(..., description="Response type")
    etag: str = Field(..., description="ETag")
    items: Optional[List[Dict[str, Any]]] = Field(None, description="Response items")
    next_page_token: Optional[str] = Field(None, description="Next page token")
    prev_page_token: Optional[str] = Field(None, description="Previous page token")
    page_info: Optional[YouTubePageInfo] = Field(None, description="Page info")
    
    def has_items(self) -> bool:
        """Check if response has items."""
        return bool(self.items)
    
    def has_next_page(self) -> bool:
        """Check if there's a next page."""
        return self.next_page_token is not None


# ============================================
# YOUTUBE ERROR
# ============================================

class YouTubeError(YouTubeBaseModel):
    """YouTube API error."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Error details")
