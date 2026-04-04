"""
TikTok Platform - Platform Adapter
===================================

TikTok platform adapter implementing BasePlatform interface.

This integrates TikTok Business API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 12
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.tiktok.client import TikTokClient
from socialspace_agent.platforms.tiktok.models import TikTokVideo, TikTokComment
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


class TikTokPlatform(BasePlatform):
    """
    TikTok Business API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify access token
    - fetch_messages(): Get videos and comments
    - send_message(): Create videos or comments
    - normalize_message(): Convert TikTok format to UnifiedMessage
    
    Features:
    ---------
    - Fetch user videos
    - Fetch comments on videos
    - Post videos
    - Post comments
    - Get user info
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="tiktok",
    ...     api_key="YOUR_ACCESS_TOKEN",
    ...     mock_mode=True
    ... )
    >>> 
    >>> tiktok = TikTokPlatform(config)
    >>> await tiktok.authenticate()
    >>> 
    >>> # Fetch videos
    >>> messages = await tiktok.fetch_messages(
    ...     user_id="me",
    ...     limit=10
    ... )
    >>> 
    >>> # Create comment
    >>> msg = UnifiedMessage(...)
    >>> result = await tiktok.send_message(msg, recipient_id="video_id")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize TikTok platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: TikTok access token
        """
        super().__init__(config)
        
        # Extract TikTok-specific config
        self.access_token = config.api_key or config.access_token
        
        if not self.access_token:
            raise ValidationError(
                "access_token (api_key) is required for TikTok",
                context={"platform": "tiktok"}
            )
        
        # TikTok client (initialized on authenticate)
        self._tiktok_client: Optional[TikTokClient] = None
        
        # User info cache
        self._user_info: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._video_cache: List[TikTokVideo] = []
        self._comment_cache: List[TikTokComment] = []
        
        logger.info("TikTok platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with TikTok Business API.
        
        Verifies access token by fetching user information.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with TikTok Business API...")
            
            # Create TikTok client
            self._tiktok_client = TikTokClient(
                access_token=self.access_token,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify token by getting user info
            user = await self._tiktok_client.get_user_info()
            self._user_info = user.model_dump()
            
            self._is_authenticated = True
            self._client = self._tiktok_client
            
            logger.info(f"✅ TikTok authentication successful ({user.display_name})")
            return True
            
        except Exception as e:
            logger.error(f"❌ TikTok authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with TikTok: {e}",
                context={"platform": "tiktok"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from TikTok.
        
        For TikTok, user_id can be:
        - "me" (to fetch own videos)
        - Video ID (to fetch comments)
        
        Args:
            user_id: User ID or video ID
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters:
                - fetch_type: "videos" or "comments" (default: "videos")
            
        Returns:
            List of UnifiedMessage objects
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching TikTok messages from {user_id}")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit,
            filters
        )
        
        unified_messages = []
        
        # Parse filters
        filters = filters or {}
        fetch_type = filters.get("fetch_type", "videos")
        
        if fetch_type == "comments":
            # Fetch comments from video
            comments = await self._tiktok_client.get_comments(
                video_id=user_id,
                limit=min(limit, 20)
            )
            
            for comment in comments:
                # Filter by timestamp if specified
                if since and comment.create_time:
                    comment_time = datetime.fromtimestamp(
                        comment.create_time,
                        tz=timezone.utc
                    )
                    if comment_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_comment(comment)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._comment_cache.append(comment)
        
        else:
            # Fetch videos
            videos = await self._tiktok_client.get_videos(
                limit=min(limit, 20)
            )
            
            for video in videos:
                # Filter by timestamp if specified
                if since and video.create_time:
                    video_time = datetime.fromtimestamp(
                        video.create_time,
                        tz=timezone.utc
                    )
                    if video_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_video(video)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._video_cache.append(video)
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} TikTok messages")
        
        return unified_messages[:limit]
    
    async def _fetch_messages_impl(
        self,
        user_id: str,
        since: Optional[datetime],
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> None:
        """Internal fetch implementation (for rate limiting wrapper)."""
        pass
    
    async def send_message(
        self,
        message: UnifiedMessage,
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message via TikTok.
        
        Can create a video or a comment.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Video ID (for comment) or None (for video)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (video/comment ID)
                - timestamp: datetime
                - metadata: Dict
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending TikTok message to {recipient_id or 'timeline'}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ TikTok message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send TikTok message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: Optional[str]
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        if not message.content:
            raise ValidationError(
                "TikTok message must have content",
                context={"message_id": message.id}
            )
        
        if recipient_id:
            # Create comment on video
            comment = await self._tiktok_client.create_comment(
                video_id=recipient_id,
                text=message.content
            )
            
            timestamp = datetime.fromtimestamp(
                comment.create_time,
                tz=timezone.utc
            ) if comment.create_time else datetime.now(timezone.utc)
            
            return {
                "success": True,
                "message_id": comment.id,
                "timestamp": timestamp,
                "metadata": {
                    "platform": "tiktok",
                    "type": "comment",
                    "video_id": recipient_id
                }
            }
        
        else:
            # Create video (not fully implemented - requires video file)
            logger.warning("Video creation requires video file upload")
            
            raise ValidationError(
                "Video creation not supported in current implementation",
                context={"platform": "tiktok"}
            )
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert TikTok video or comment to UnifiedMessage.
        
        Args:
            raw_message: Raw TikTok video or comment dictionary
            
        Returns:
            UnifiedMessage object
        """
        try:
            # Check if it's a video or comment
            if "video_id" in raw_message and "text" in raw_message:
                # It's a comment
                comment = TikTokComment(**raw_message)
                return self._normalize_comment(comment)
            else:
                # It's a video
                video = TikTokVideo(**raw_message)
                return self._normalize_video(video)
                
        except Exception as e:
            logger.error(f"Failed to normalize TikTok message: {e}")
            raise ValidationError(
                f"Invalid TikTok message format: {e}",
                context={"raw_message": raw_message}
            )
    
    def _normalize_video(self, video: TikTokVideo) -> UnifiedMessage:
        """Convert TikTok video to UnifiedMessage."""
        
        # Extract author info
        author_name = "Unknown"
        author_id = "unknown"
        
        if video.author:
            author_name = video.author.get("display_name") or video.author.get("username", "Unknown")
            author_id = video.author.get("id", "unknown")
        
        sender = UserInfo(
            id=author_id,
            username=author_name,
            display_name=author_name
        )
        
        # Extract content
        content = video.description or ""
        
        # Extract media
        media_list = []
        media_url = video.video_url or video.get_url()
        media = MediaAttachment(
            url=media_url,
            type="video",
            thumbnail_url=video.cover_image_url
        )
        media_list.append(media)
        
        # Convert timestamp
        if video.create_time:
            timestamp = datetime.fromtimestamp(
                video.create_time,
                tz=timezone.utc
            )
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=video.id,
            platform=PlatformType.TIKTOK,
            type=MessageType.VIDEO,
            sender=sender,
            content=content,
            media=media_list,
            timestamp=timestamp,
            likes=video.get_like_count(),
            shares=video.get_share_count(),
            metadata={
                "tiktok_video_id": video.id,
                "view_count": video.get_view_count(),
                "comment_count": video.get_comment_count(),
                "duration": video.duration,
                "hashtags": video.hashtags or []
            }
        )
        
        return unified_message
    
    def _normalize_comment(self, comment: TikTokComment) -> UnifiedMessage:
        """Convert TikTok comment to UnifiedMessage."""
        
        # Extract sender info
        sender = UserInfo(
            id=comment.user.get("id", "unknown") if comment.user else "unknown",
            username=comment.get_author_name(),
            display_name=comment.get_author_name()
        )
        
        # Convert timestamp
        if comment.create_time:
            timestamp = datetime.fromtimestamp(
                comment.create_time,
                tz=timezone.utc
            )
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=comment.id,
            platform=PlatformType.TIKTOK,
            type=MessageType.COMMENT,
            sender=sender,
            content=comment.text,
            timestamp=timestamp,
            is_reply=comment.is_reply(),
            parent_id=comment.parent_comment_id,
            likes=comment.like_count,
            metadata={
                "tiktok_comment_id": comment.id,
                "video_id": comment.video_id,
                "reply_count": comment.reply_count
            }
        )
        
        return unified_message
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from TikTok and cleanup."""
        if self._tiktok_client:
            await self._tiktok_client.close()
            self._tiktok_client = None
        
        self._is_authenticated = False
        self._user_info = None
        self._video_cache.clear()
        self._comment_cache.clear()
        
        logger.info("Disconnected from TikTok")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from TikTok.
        
        Args:
            user_id: TikTok user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "tiktok"
        }
    
    def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """
        Get cached user information.
        
        Returns:
            User info dictionary or None
        """
        return self._user_info
    
    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        Get video information.
        
        Args:
            video_id: TikTok video ID
            
        Returns:
            Dictionary with video info
        """
        self._ensure_authenticated()
        
        video = await self._tiktok_client.get_video(video_id)
        
        return {
            "id": video.id,
            "description": video.description,
            "duration": video.duration,
            "url": video.get_url(),
            "views": video.get_view_count(),
            "likes": video.get_like_count(),
            "comments": video.get_comment_count(),
            "shares": video.get_share_count(),
            "platform": "tiktok"
        }
