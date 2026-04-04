"""
Twitter Platform - Data Models
===============================

Twitter-specific data models.

Twitter Concepts:
-----------------
- Tweet: A post (max 280 characters)
- User: Twitter user account
- Timeline: Feed of tweets
- Mention: @username reference
- Hashtag: #topic reference
- Media: Images, videos, GIFs

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 8
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# TWITTER USER
# ============================================

class TwitterUser(BaseModel):
    """
    Twitter user model.
    
    Represents a Twitter account.
    """
    id: str = Field(..., description="Twitter user ID")
    username: str = Field(..., description="Username (handle without @)")
    name: str = Field(..., description="Display name")
    
    # Profile info
    description: Optional[str] = Field(None, description="Bio")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    verified: Optional[bool] = Field(False, description="Verified account")
    protected: Optional[bool] = Field(False, description="Protected/private account")
    
    # Stats
    followers_count: Optional[int] = Field(None, description="Number of followers")
    following_count: Optional[int] = Field(None, description="Number of following")
    tweet_count: Optional[int] = Field(None, description="Number of tweets")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Account creation date")
    
    def get_handle(self) -> str:
        """Get username with @ prefix."""
        return f"@{self.username}"
    
    def get_profile_url(self) -> str:
        """Get profile URL."""
        return f"https://twitter.com/{self.username}"


# ============================================
# TWITTER MEDIA
# ============================================

class TwitterMedia(BaseModel):
    """
    Twitter media attachment.
    """
    media_key: str = Field(..., description="Media identifier")
    type: Literal["photo", "video", "animated_gif"] = Field(..., description="Media type")
    url: Optional[str] = Field(None, description="Media URL")
    preview_image_url: Optional[str] = Field(None, description="Preview image URL")
    
    # Dimensions
    width: Optional[int] = Field(None, description="Width in pixels")
    height: Optional[int] = Field(None, description="Height in pixels")
    
    # Video info
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    
    def is_image(self) -> bool:
        """Check if media is an image."""
        return self.type == "photo"
    
    def is_video(self) -> bool:
        """Check if media is a video."""
        return self.type in ["video", "animated_gif"]


# ============================================
# TWITTER ENTITIES
# ============================================

class TwitterHashtag(BaseModel):
    """Twitter hashtag."""
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    tag: str = Field(..., description="Hashtag text (without #)")


class TwitterMention(BaseModel):
    """Twitter user mention."""
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    username: str = Field(..., description="Mentioned username")


class TwitterUrl(BaseModel):
    """Twitter URL."""
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    url: str = Field(..., description="Shortened URL (t.co)")
    expanded_url: Optional[str] = Field(None, description="Full URL")
    display_url: Optional[str] = Field(None, description="Display URL")


class TwitterEntities(BaseModel):
    """
    Twitter entities (hashtags, mentions, URLs).
    """
    hashtags: Optional[List[TwitterHashtag]] = Field(default_factory=list)
    mentions: Optional[List[TwitterMention]] = Field(default_factory=list)
    urls: Optional[List[TwitterUrl]] = Field(default_factory=list)


# ============================================
# TWITTER TWEET
# ============================================

class TwitterTweet(BaseModel):
    """
    Twitter tweet model.
    
    Represents a tweet (post on Twitter).
    """
    id: str = Field(..., description="Tweet ID")
    text: str = Field(..., description="Tweet text")
    
    # Author
    author_id: str = Field(..., description="Author's user ID")
    
    # Timestamps
    created_at: str = Field(..., description="ISO 8601 timestamp")
    
    # Engagement
    public_metrics: Optional[Dict[str, int]] = Field(
        None,
        description="Public metrics (retweet_count, reply_count, like_count, quote_count)"
    )
    
    # Entities
    entities: Optional[TwitterEntities] = Field(None, description="Hashtags, mentions, URLs")
    
    # Referenced tweets (replies, retweets, quotes)
    referenced_tweets: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Referenced tweets"
    )
    
    # Media
    attachments: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Media attachments (media_keys)"
    )
    
    # Conversation
    conversation_id: Optional[str] = Field(None, description="Conversation thread ID")
    in_reply_to_user_id: Optional[str] = Field(None, description="User being replied to")
    
    # Additional
    lang: Optional[str] = Field(None, description="Language code")
    possibly_sensitive: Optional[bool] = Field(False, description="Sensitive content flag")
    
    def get_like_count(self) -> int:
        """Get like count."""
        if self.public_metrics:
            return self.public_metrics.get("like_count", 0)
        return 0
    
    def get_retweet_count(self) -> int:
        """Get retweet count."""
        if self.public_metrics:
            return self.public_metrics.get("retweet_count", 0)
        return 0
    
    def get_reply_count(self) -> int:
        """Get reply count."""
        if self.public_metrics:
            return self.public_metrics.get("reply_count", 0)
        return 0
    
    def is_reply(self) -> bool:
        """Check if this is a reply."""
        if self.referenced_tweets:
            return any(ref.get("type") == "replied_to" for ref in self.referenced_tweets)
        return False
    
    def is_retweet(self) -> bool:
        """Check if this is a retweet."""
        if self.referenced_tweets:
            return any(ref.get("type") == "retweeted" for ref in self.referenced_tweets)
        return False
    
    def is_quote(self) -> bool:
        """Check if this is a quote tweet."""
        if self.referenced_tweets:
            return any(ref.get("type") == "quoted" for ref in self.referenced_tweets)
        return False
    
    def get_hashtags(self) -> List[str]:
        """Get list of hashtags in tweet."""
        if self.entities and self.entities.hashtags:
            return [tag.tag for tag in self.entities.hashtags]
        return []
    
    def get_mentions(self) -> List[str]:
        """Get list of mentioned usernames."""
        if self.entities and self.entities.mentions:
            return [mention.username for mention in self.entities.mentions]
        return []
    
    def get_tweet_url(self, username: str) -> str:
        """Get URL to this tweet."""
        return f"https://twitter.com/{username}/status/{self.id}"


# ============================================
# TWITTER API RESPONSE
# ============================================

class TwitterResponse(BaseModel):
    """
    Generic Twitter API response.
    """
    data: Optional[Any] = Field(None, description="Response data")
    includes: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        None,
        description="Included data (users, media, etc.)"
    )
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Errors")
    
    def has_data(self) -> bool:
        """Check if response has data."""
        return self.data is not None
    
    def has_errors(self) -> bool:
        """Check if response has errors."""
        return bool(self.errors)
    
    def get_next_token(self) -> Optional[str]:
        """Get pagination token for next page."""
        if self.meta:
            return self.meta.get("next_token")
        return None


class TwitterError(BaseModel):
    """Twitter API error."""
    title: str = Field(..., description="Error title")
    detail: str = Field(..., description="Error detail")
    type: str = Field(..., description="Error type")
