"""
Instagram Platform - Platform Adapter
======================================

Instagram platform adapter implementing BasePlatform interface.

This integrates Instagram Graph API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 5
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.instagram.client import InstagramClient
from socialspace_agent.platforms.instagram.models import InstagramMedia, InstagramComment
from socialspace_agent.models import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
    MediaAttachment,
)
from socialspace_agent.exceptions import (
    InstagramError,
    AuthenticationError,
    ValidationError,
)
from socialspace_agent.utils.config import PlatformConfig

logger = logging.getLogger(__name__)


class InstagramPlatform(BasePlatform):
    """
    Instagram Graph API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify access token
    - fetch_messages(): Get comments and mentions
    - send_message(): Post comments
    - normalize_message(): Convert Instagram format to UnifiedMessage
    
    Features:
    ---------
    - Fetch media posts (feed, stories, reels)
    - Fetch and post comments
    - Handle mentions
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Note:
    -----
    Instagram's "messages" are primarily comments and mentions.
    Direct messages require special permissions and webhook setup.
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="instagram",
    ...     access_token="YOUR_ACCESS_TOKEN",
    ...     metadata={"account_id": "YOUR_IG_BUSINESS_ID"}
    ... )
    >>> 
    >>> instagram = InstagramPlatform(config)
    >>> await instagram.authenticate()
    >>> 
    >>> # Fetch comments
    >>> messages = await instagram.fetch_messages(limit=50)
    >>> 
    >>> # Post comment
    >>> msg = UnifiedMessage(...)
    >>> result = await instagram.send_message(msg, recipient_id="media_123")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Instagram platform adapter.
        
        Args:
            config: Platform configuration with:
                - access_token: Instagram/Facebook access token
                - metadata.account_id: Instagram Business Account ID
        """
        super().__init__(config)
        
        # Extract Instagram-specific config
        self.access_token = config.access_token or config.api_key
        self.account_id = config.metadata.get("account_id")
        
        if not self.access_token:
            raise ValidationError(
                "access_token is required for Instagram",
                context={"platform": "instagram"}
            )
        
        if not self.account_id:
            raise ValidationError(
                "account_id is required in config.metadata",
                context={"platform": "instagram"}
            )
        
        # Instagram client (initialized on authenticate)
        self._instagram_client: Optional[InstagramClient] = None
        
        # Account info (from API)
        self._account_info: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._comment_cache: List[InstagramComment] = []
        
        logger.info(
            f"Instagram platform initialized "
            f"(account_id={self.account_id[:8]}...)"
        )
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Instagram Graph API.
        
        Verifies access token by fetching account information.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Instagram Graph API...")
            
            # Create Instagram client
            self._instagram_client = InstagramClient(
                access_token=self.access_token,
                account_id=self.account_id,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify access token by getting account info
            account = await self._instagram_client.get_account_info()
            self._account_info = account.model_dump()
            
            self._is_authenticated = True
            self._client = self._instagram_client
            
            logger.info(
                f"✅ Instagram authentication successful "
                f"(@{self._account_info.get('username', 'unknown')})"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Instagram authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Instagram: {e}",
                context={"platform": "instagram"}
            )
    
    async def fetch_messages(
        self,
        user_id: str = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Instagram.
        
        For Instagram, "messages" are primarily comments on posts.
        
        Args:
            user_id: Not used for Instagram (comments are on our posts)
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters:
                - media_id: Specific media to get comments from
                - include_mentions: Include mentions (default: True)
            
        Returns:
            List of UnifiedMessage objects (comments as messages)
            
        Example:
            >>> # Get all recent comments
            >>> messages = await instagram.fetch_messages(limit=50)
            >>> 
            >>> # Get comments on specific post
            >>> messages = await instagram.fetch_messages(
            ...     filters={"media_id": "123456"}
            ... )
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Instagram messages (limit={limit})")
        
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
        media_id = filters.get("media_id")
        include_mentions = filters.get("include_mentions", True)
        
        if media_id:
            # Get comments from specific media
            comments = await self._instagram_client.get_comments(
                media_id=media_id,
                limit=limit
            )
            
            for comment in comments:
                unified_msg = self._normalize_comment(comment)
                unified_messages.append(unified_msg)
                self._comment_cache.append(comment)
        
        else:
            # Get recent media and their comments
            media_response = await self._instagram_client.get_media(
                limit=min(limit // 5, 20)  # Get some recent posts
            )
            
            for media_data in media_response.data:
                media = InstagramMedia(**media_data)
                
                # Get comments on this media
                comments = await self._instagram_client.get_comments(
                    media_id=media.id,
                    limit=limit
                )
                
                for comment in comments:
                    # Filter by timestamp if specified
                    if since:
                        comment_time = datetime.fromisoformat(
                            comment.timestamp.replace('Z', '+00:00')
                        )
                        if comment_time < since:
                            continue
                    
                    unified_msg = self._normalize_comment(comment, media)
                    unified_messages.append(unified_msg)
                    self._comment_cache.append(comment)
                    
                    # Stop if we've reached the limit
                    if len(unified_messages) >= limit:
                        break
                
                if len(unified_messages) >= limit:
                    break
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Instagram messages")
        
        return unified_messages
    
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
        recipient_id: str
    ) -> Dict[str, Any]:
        """
        Send a message via Instagram.
        
        For Instagram, this posts a comment on a media post.
        
        Args:
            message: UnifiedMessage to send (content = comment text)
            recipient_id: Instagram media ID (the post to comment on)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (comment ID)
                - timestamp: datetime
                - metadata: Dict
                
        Example:
            >>> msg = UnifiedMessage(
            ...     platform_message_id="temp",
            ...     platform=PlatformType.INSTAGRAM,
            ...     type=MessageType.COMMENT,
            ...     sender=UserInfo(id="bot", display_name="Bot"),
            ...     content="Great photo! 📸",
            ...     timestamp=datetime.now(timezone.utc)
            ... )
            >>> 
            >>> # Post comment on media
            >>> result = await instagram.send_message(msg, "media_123")
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Instagram message to {recipient_id}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Instagram message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send Instagram message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        media_id: str
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        if not message.content:
            raise ValidationError(
                "Instagram comment must have text content",
                context={"message_id": message.id}
            )
        
        # Check if this is a reply to another comment
        if message.is_reply and message.parent_id:
            # Reply to comment
            comment = await self._instagram_client.reply_to_comment(
                comment_id=message.parent_id,
                text=message.content
            )
        else:
            # Post new comment on media
            comment = await self._instagram_client.create_comment(
                media_id=media_id,
                text=message.content
            )
        
        # Return formatted response
        return {
            "success": True,
            "message_id": comment.id,
            "timestamp": datetime.fromisoformat(
                comment.timestamp.replace('Z', '+00:00')
            ),
            "metadata": {
                "platform": "instagram",
                "media_id": media_id,
                "comment_type": "reply" if message.is_reply else "comment"
            }
        }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Instagram comment to UnifiedMessage.
        
        Args:
            raw_message: Raw Instagram comment dictionary
            
        Returns:
            UnifiedMessage object
            
        Example:
            >>> raw = {
            ...     "id": "123",
            ...     "text": "Great post!",
            ...     "timestamp": "2026-02-20T19:30:00+0000",
            ...     "username": "john_doe"
            ... }
            >>> 
            >>> unified = instagram.normalize_message(raw)
            >>> print(unified.content)
            Great post!
        """
        try:
            # Parse as Instagram comment
            comment = InstagramComment(**raw_message)
            
            return self._normalize_comment(comment)
            
        except Exception as e:
            logger.error(f"Failed to normalize Instagram message: {e}")
            raise ValidationError(
                f"Invalid Instagram message format: {e}",
                context={"raw_message": raw_message}
            )
    
    def _normalize_comment(
        self,
        comment: InstagramComment,
        media: Optional[InstagramMedia] = None
    ) -> UnifiedMessage:
        """
        Convert Instagram comment to UnifiedMessage.
        
        Helper method with optional media context.
        """
        # Extract sender info
        if comment.from_user:
            user_data = comment.from_user
            sender = UserInfo(
                id=str(user_data.get("id", comment.username or "unknown")),
                username=user_data.get("username", comment.username),
                display_name=user_data.get("name", comment.username or "Unknown")
            )
        else:
            sender = UserInfo(
                id=comment.username or "unknown",
                username=comment.username,
                display_name=comment.username or "Unknown"
            )
        
        # Convert timestamp
        timestamp = datetime.fromisoformat(
            comment.timestamp.replace('Z', '+00:00')
        )
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=comment.id,
            platform=PlatformType.INSTAGRAM,
            type=MessageType.COMMENT,
            sender=sender,
            content=comment.text,
            timestamp=timestamp,
            is_reply=comment.is_reply(),
            parent_id=comment.parent_id,
            likes=comment.like_count or 0,
            metadata={
                "instagram_comment_id": comment.id,
                "media_id": media.id if media else None,
                "media_type": media.media_type if media else None,
                "media_permalink": media.permalink if media else None
            }
        )
        
        return unified_message
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Instagram and cleanup."""
        if self._instagram_client:
            await self._instagram_client.close()
            self._instagram_client = None
        
        self._is_authenticated = False
        self._account_info = None
        self._comment_cache.clear()
        
        logger.info("Disconnected from Instagram")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Instagram.
        
        Note: Graph API has limited access to user profiles.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "instagram",
            "display_name": user_id,
        }
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get authenticated account information.
        
        Returns:
            Account info (username, followers, etc.)
        """
        return self._account_info
    
    async def get_recent_media(self, limit: int = 10) -> List[InstagramMedia]:
        """
        Get recent media posts.
        
        Args:
            limit: Maximum number of posts
            
        Returns:
            List of InstagramMedia objects
            
        Example:
            >>> media_list = await instagram.get_recent_media(limit=5)
            >>> for media in media_list:
            ...     print(f"Post: {media.caption}")
        """
        self._ensure_authenticated()
        
        response = await self._instagram_client.get_media(limit=limit)
        
        media_list = []
        for media_data in response.data:
            media = InstagramMedia(**media_data)
            media_list.append(media)
        
        return media_list
    
    async def post_comment_on_media(
        self,
        media_id: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Post a comment on a media post.
        
        Convenience method for posting comments.
        
        Args:
            media_id: Instagram media ID
            text: Comment text
            
        Returns:
            Comment result dictionary
        """
        self._ensure_authenticated()
        
        comment = await self._instagram_client.create_comment(
            media_id=media_id,
            text=text
        )
        
        return {
            "success": True,
            "comment_id": comment.id,
            "text": comment.text,
            "timestamp": comment.timestamp
        }
