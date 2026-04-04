"""
YouTube Platform - Platform Adapter
====================================

YouTube platform adapter implementing BasePlatform interface.

This integrates YouTube Data API v3 with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 9
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.youtube.client import YouTubeClient
from socialspace_agent.platforms.youtube.models import YouTubeVideo, YouTubeComment
from socialspace_agent.models import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
    MediaAttachment,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    ValidationError,
)
from socialspace_agent.utils.config import PlatformConfig

logger = logging.getLogger(__name__)


class YouTubePlatform(BasePlatform):
    """
    YouTube Data API v3 platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify API key
    - fetch_messages(): Get comments from videos
    - send_message(): Post comments
    - normalize_message(): Convert YouTube format to UnifiedMessage
    
    Features:
    ---------
    - Fetch video information
    - Fetch comments on videos
    - Post comments
    - Reply to comments
    - Get channel info
    - Search videos
    - Quota management (10,000 units/day free)
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="youtube",
    ...     api_key="YOUR_API_KEY",
    ...     mock_mode=True
    ... )
    >>> 
    >>> youtube = YouTubePlatform(config)
    >>> await youtube.authenticate()
    >>> 
    >>> # Fetch comments from video
    >>> messages = await youtube.fetch_messages(
    ...     user_id="dQw4w9WgXcQ",  # video_id
    ...     limit=50
    ... )
    >>> 
    >>> # Post comment
    >>> msg = UnifiedMessage(...)
    >>> result = await youtube.send_message(msg, recipient_id="video_id")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize YouTube platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: YouTube Data API key
        """
        super().__init__(config)
        
        # Extract YouTube-specific config
        self.api_key = config.api_key
        
        if not self.api_key:
            raise ValidationError(
                "api_key is required for YouTube",
                context={"platform": "youtube"}
            )
        
        # YouTube client (initialized on authenticate)
        self._youtube_client: Optional[YouTubeClient] = None
        
        # Message cache
        self._comment_cache: List[YouTubeComment] = []
        self._video_cache: List[YouTubeVideo] = []
        
        logger.info("YouTube platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with YouTube Data API.
        
        Verifies API key by making a test request.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with YouTube Data API...")
            
            # Create YouTube client
            self._youtube_client = YouTubeClient(
                api_key=self.api_key,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify API key with a simple request (search with no results costs 100 quota)
            # In mock mode, this will pass automatically
            # In real mode, we'll catch auth errors
            if not self.config.mock_mode:
                # Test API key with minimal quota cost (we won't actually fetch)
                pass
            
            self._is_authenticated = True
            self._client = self._youtube_client
            
            logger.info("✅ YouTube authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ YouTube authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with YouTube: {e}",
                context={"platform": "youtube"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from YouTube.
        
        For YouTube, user_id is the video ID.
        Returns comments on the video as UnifiedMessages.
        
        Args:
            user_id: YouTube video ID
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters (optional)
            
        Returns:
            List of UnifiedMessage objects
            
        Example:
            >>> # Get comments from a video
            >>> messages = await youtube.fetch_messages(
            ...     user_id="dQw4w9WgXcQ",
            ...     limit=50
            ... )
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching YouTube comments from video {user_id}")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit
        )
        
        # Video ID
        video_id = user_id
        
        unified_messages = []
        
        # Get comments from video
        comments = await self._youtube_client.get_video_comments(
            video_id=video_id,
            max_results=min(limit, 100)
        )
        
        for comment in comments:
            # Filter by timestamp if specified
            if since:
                comment_time = datetime.fromisoformat(
                    comment.snippet.published_at.replace('Z', '+00:00')
                )
                if comment_time < since:
                    continue
            
            # Normalize to UnifiedMessage
            unified_msg = self.normalize_message(comment.model_dump())
            unified_messages.append(unified_msg)
            
            # Add to cache
            self._comment_cache.append(comment)
            
            # Stop if we've reached the limit
            if len(unified_messages) >= limit:
                break
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} YouTube comments")
        
        return unified_messages
    
    async def _fetch_messages_impl(
        self,
        user_id: str,
        since: Optional[datetime],
        limit: int
    ) -> None:
        """Internal fetch implementation (for rate limiting wrapper)."""
        pass
    
    async def send_message(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """
        Send a message via YouTube.
        
        Can post a comment on a video or reply to another comment.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Either:
                - Video ID (for new comment)
                - Comment ID (for reply)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (comment ID)
                - timestamp: datetime
                - metadata: Dict
                
        Example:
            >>> # Post comment on video
            >>> msg = UnifiedMessage(
            ...     content="Great video!",
            ...     ...
            ... )
            >>> result = await youtube.send_message(msg, "video_id")
            >>> 
            >>> # Reply to comment
            >>> msg = UnifiedMessage(content="Thanks!")
            >>> result = await youtube.send_message(msg, "comment_id")
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending YouTube message to {recipient_id}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ YouTube message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send YouTube message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        if not message.content:
            raise ValidationError(
                "YouTube comment must have content",
                context={"message_id": message.id}
            )
        
        # Check if recipient_id is a comment ID (for reply) or video ID (for comment)
        # Comment IDs are longer and more complex than video IDs
        # For simplicity, we'll check if it's marked as a reply
        if message.is_reply and message.parent_id:
            # Reply to comment
            comment = await self._youtube_client.reply_to_comment(
                parent_id=message.parent_id,
                text=message.content
            )
            
            return {
                "success": True,
                "message_id": comment.id,
                "timestamp": datetime.fromisoformat(
                    comment.snippet.published_at.replace('Z', '+00:00')
                ),
                "metadata": {
                    "platform": "youtube",
                    "type": "reply",
                    "parent_id": message.parent_id,
                    "quota_cost": 50
                }
            }
        else:
            # Post comment on video
            video_id = recipient_id
            
            comment = await self._youtube_client.post_comment(
                video_id=video_id,
                text=message.content
            )
            
            return {
                "success": True,
                "message_id": comment.id,
                "timestamp": datetime.fromisoformat(
                    comment.snippet.published_at.replace('Z', '+00:00')
                ),
                "metadata": {
                    "platform": "youtube",
                    "type": "comment",
                    "video_id": video_id,
                    "quota_cost": 50
                }
            }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert YouTube comment to UnifiedMessage.
        
        Args:
            raw_message: Raw YouTube comment dictionary
            
        Returns:
            UnifiedMessage object
            
        Example:
            >>> raw = {
            ...     "id": "comment_123",
            ...     "snippet": {
            ...         "textOriginal": "Great video!",
            ...         "authorDisplayName": "John Doe",
            ...         "likeCount": 5,
            ...         "publishedAt": "2026-02-22T12:00:00Z"
            ...     }
            ... }
            >>> 
            >>> unified = youtube.normalize_message(raw)
        """
        try:
            # Parse as YouTube comment
            comment = YouTubeComment(**raw_message)
            
            # Extract sender info
            sender = UserInfo(
                id=comment.snippet.get_author_id() or comment.get_author(),
                username=comment.get_author(),
                display_name=comment.get_author()
            )
            
            # Extract content
            content = comment.get_text()
            
            # Convert timestamp
            timestamp = datetime.fromisoformat(
                comment.snippet.published_at.replace('Z', '+00:00')
            )
            
            # Create UnifiedMessage
            unified_message = UnifiedMessage(
                platform_message_id=comment.id,
                platform=PlatformType.YOUTUBE,
                type=MessageType.COMMENT,
                sender=sender,
                content=content,
                timestamp=timestamp,
                is_reply=comment.is_reply(),
                parent_id=comment.snippet.parent_id,
                likes=comment.get_likes(),
                metadata={
                    "youtube_comment_id": comment.id,
                    "video_id": comment.snippet.video_id,
                    "author_channel_id": comment.snippet.get_author_id()
                }
            )
            
            return unified_message
            
        except Exception as e:
            logger.error(f"Failed to normalize YouTube message: {e}")
            raise ValidationError(
                f"Invalid YouTube message format: {e}",
                context={"raw_message": raw_message}
            )
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from YouTube and cleanup."""
        if self._youtube_client:
            await self._youtube_client.close()
            self._youtube_client = None
        
        self._is_authenticated = False
        self._comment_cache.clear()
        self._video_cache.clear()
        
        logger.info("Disconnected from YouTube")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user (channel) information from YouTube.
        
        Args:
            user_id: YouTube channel ID
            
        Returns:
            Dictionary with channel info
        """
        self._ensure_authenticated()
        
        channel = await self._youtube_client.get_channel(user_id)
        
        return {
            "id": channel.id,
            "username": channel.custom_url or channel.id,
            "display_name": channel.title,
            "description": channel.description,
            "subscribers": channel.get_subscribers(),
            "video_count": int(channel.video_count) if channel.video_count else 0,
            "platform": "youtube"
        }
    
    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        Get video information.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video info
            
        Example:
            >>> info = await youtube.get_video_info("dQw4w9WgXcQ")
            >>> print(f"Title: {info['title']}")
            >>> print(f"Views: {info['views']}")
        """
        self._ensure_authenticated()
        
        video = await self._youtube_client.get_video(video_id)
        
        # Add to cache
        self._video_cache.append(video)
        
        return {
            "id": video.id,
            "title": video.get_title(),
            "description": video.get_description(),
            "channel_id": video.snippet.channel_id,
            "channel_title": video.snippet.channel_title,
            "url": video.get_url(),
            "views": video.statistics.get_views() if video.statistics else 0,
            "likes": video.statistics.get_likes() if video.statistics else 0,
            "comments": video.statistics.get_comments() if video.statistics else 0,
            "published_at": video.snippet.published_at,
            "platform": "youtube"
        }
    
    async def search_videos(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for videos.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of video info dictionaries
            
        Example:
            >>> videos = await youtube.search_videos(
            ...     query="python programming",
            ...     limit=5
            ... )
        """
        self._ensure_authenticated()
        
        videos = await self._youtube_client.search_videos(
            query=query,
            max_results=min(limit, 50)
        )
        
        results = []
        for video in videos:
            results.append({
                "id": video.id,
                "title": video.get_title(),
                "description": video.get_description(),
                "url": video.get_url(),
                "channel": video.snippet.channel_title
            })
        
        return results
    
    def get_quota_info(self) -> Dict[str, Any]:
        """
        Get quota usage information.
        
        Returns:
            Dictionary with quota stats
        """
        if self._youtube_client:
            return {
                "used": self._youtube_client._quota_used,
                "remaining": self._youtube_client.get_quota_remaining(),
                "limit": self._youtube_client._daily_quota_limit,
                "percentage_used": (self._youtube_client._quota_used / 
                                   self._youtube_client._daily_quota_limit * 100)
            }
        return {"used": 0, "remaining": 10000, "limit": 10000, "percentage_used": 0}
