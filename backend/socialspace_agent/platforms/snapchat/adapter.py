"""
Snapchat Platform - Platform Adapter
=====================================

Snapchat platform adapter implementing BasePlatform interface.

This integrates Snap Kit API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 13
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.snapchat.client import SnapchatClient
from socialspace_agent.platforms.snapchat.models import SnapchatStory, SnapchatSnap
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


class SnapchatPlatform(BasePlatform):
    """
    Snapchat Snap Kit API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify access token
    - fetch_messages(): Get stories and snaps
    - send_message(): Create stories
    - normalize_message(): Convert Snapchat format to UnifiedMessage
    
    Features:
    ---------
    - Fetch user stories
    - Fetch snaps
    - Create stories
    - Get Bitmoji
    - Get user info
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="snapchat",
    ...     api_key="YOUR_ACCESS_TOKEN",
    ...     mock_mode=True
    ... )
    >>> 
    >>> snapchat = SnapchatPlatform(config)
    >>> await snapchat.authenticate()
    >>> 
    >>> # Fetch stories
    >>> messages = await snapchat.fetch_messages(
    ...     user_id="me",
    ...     limit=10
    ... )
    >>> 
    >>> # Create story
    >>> msg = UnifiedMessage(...)
    >>> result = await snapchat.send_message(msg)
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Snapchat platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: Snapchat access token
        """
        super().__init__(config)
        
        # Extract Snapchat-specific config
        self.access_token = config.api_key or config.access_token
        
        if not self.access_token:
            raise ValidationError(
                "access_token (api_key) is required for Snapchat",
                context={"platform": "snapchat"}
            )
        
        # Snapchat client (initialized on authenticate)
        self._snapchat_client: Optional[SnapchatClient] = None
        
        # User info cache
        self._user_info: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._story_cache: List[SnapchatStory] = []
        self._snap_cache: List[SnapchatSnap] = []
        
        logger.info("Snapchat platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Snapchat Snap Kit API.
        
        Verifies access token by fetching user information.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Snapchat Snap Kit API...")
            
            # Create Snapchat client
            self._snapchat_client = SnapchatClient(
                access_token=self.access_token,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify token by getting user info
            user = await self._snapchat_client.get_user_info()
            self._user_info = user.model_dump()
            
            self._is_authenticated = True
            self._client = self._snapchat_client
            
            logger.info(f"✅ Snapchat authentication successful ({user.display_name})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Snapchat authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Snapchat: {e}",
                context={"platform": "snapchat"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Snapchat.
        
        For Snapchat, typically fetches stories (24-hour content).
        
        Args:
            user_id: User ID (typically "me")
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters:
                - fetch_type: "stories" or "snaps" (default: "stories")
            
        Returns:
            List of UnifiedMessage objects
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Snapchat messages from {user_id}")
        
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
        fetch_type = filters.get("fetch_type", "stories")
        
        if fetch_type == "snaps":
            # Fetch snaps (limited by ephemeral nature)
            snaps = await self._snapchat_client.get_snaps()
            
            for snap in snaps:
                # Filter by timestamp if specified
                if since and snap.created_at:
                    snap_time = datetime.fromisoformat(
                        snap.created_at.replace('Z', '+00:00')
                    )
                    if snap_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_snap(snap)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._snap_cache.append(snap)
        
        else:
            # Fetch stories
            stories = await self._snapchat_client.get_stories()
            
            for story in stories:
                # Filter by timestamp if specified
                if since:
                    story_time = datetime.fromisoformat(
                        story.created_at.replace('Z', '+00:00')
                    )
                    if story_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_story(story)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._story_cache.append(story)
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Snapchat messages")
        
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
        Send a message via Snapchat.
        
        Creates a story with the provided content.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Not used (Snapchat doesn't support direct posting)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (story ID)
                - timestamp: datetime
                - metadata: Dict
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Snapchat story")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Snapchat story sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send Snapchat story: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: Optional[str]
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        # Extract media URL from message
        media_url = None
        media_type = "IMAGE"
        
        if message.media and len(message.media) > 0:
            media_url = message.media[0].url
            media_type = "VIDEO" if message.media[0].type == "video" else "IMAGE"
        else:
            # No media - Snapchat requires media for stories
            raise ValidationError(
                "Snapchat stories require media (image or video)",
                context={"message_id": message.id}
            )
        
        # Create story
        story = await self._snapchat_client.create_story(
            media_url=media_url,
            media_type=media_type
        )
        
        timestamp = datetime.fromisoformat(
            story.created_at.replace('Z', '+00:00')
        )
        
        return {
            "success": True,
            "message_id": story.id,
            "timestamp": timestamp,
            "metadata": {
                "platform": "snapchat",
                "type": "story",
                "expires_at": story.expires_at
            }
        }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Snapchat story or snap to UnifiedMessage.
        
        Args:
            raw_message: Raw Snapchat story or snap dictionary
            
        Returns:
            UnifiedMessage object
        """
        try:
            # Check if it's a story or snap
            if "expires_at" in raw_message:
                # It's a story
                story = SnapchatStory(**raw_message)
                return self._normalize_story(story)
            else:
                # It's a snap
                snap = SnapchatSnap(**raw_message)
                return self._normalize_snap(snap)
                
        except Exception as e:
            logger.error(f"Failed to normalize Snapchat message: {e}")
            raise ValidationError(
                f"Invalid Snapchat message format: {e}",
                context={"raw_message": raw_message}
            )
    
    def _normalize_story(self, story: SnapchatStory) -> UnifiedMessage:
        """Convert Snapchat story to UnifiedMessage."""
        
        # Extract sender info
        sender = UserInfo(
            id=story.username,
            username=story.username,
            display_name=story.username
        )
        
        # Extract media
        media_list = []
        if story.media_url:
            media = MediaAttachment(
                url=story.media_url,
                type="video" if story.media_type == "VIDEO" else "image"
            )
            media_list.append(media)
        
        # Convert timestamp
        timestamp = datetime.fromisoformat(
            story.created_at.replace('Z', '+00:00')
        )
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=story.id,
            platform=PlatformType.SNAPCHAT,
            type=MessageType.STORY,
            sender=sender,
            content="",  # Stories don't have text content
            media=media_list,
            timestamp=timestamp,
            metadata={
                "snapchat_story_id": story.id,
                "expires_at": story.expires_at,
                "view_count": story.view_count,
                "is_expired": story.is_expired()
            }
        )
        
        return unified_message
    
    def _normalize_snap(self, snap: SnapchatSnap) -> UnifiedMessage:
        """Convert Snapchat snap to UnifiedMessage."""
        
        # Extract media
        media_list = []
        if snap.media_url:
            media = MediaAttachment(
                url=snap.media_url,
                type="video" if snap.is_video() else "image"
            )
            media_list.append(media)
        
        # Convert timestamp
        if snap.created_at:
            timestamp = datetime.fromisoformat(
                snap.created_at.replace('Z', '+00:00')
            )
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=snap.id,
            platform=PlatformType.SNAPCHAT,
            type=MessageType.IMAGE if snap.is_image() else MessageType.VIDEO,
            sender=UserInfo(id="unknown", username="unknown", display_name="Unknown"),
            content="",  # Snaps don't have text content
            media=media_list,
            timestamp=timestamp,
            metadata={
                "snapchat_snap_id": snap.id,
                "duration": snap.duration,
                "is_opened": snap.is_opened,
                "expires_at": snap.expires_at
            }
        )
        
        return unified_message
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Snapchat and cleanup."""
        if self._snapchat_client:
            await self._snapchat_client.close()
            self._snapchat_client = None
        
        self._is_authenticated = False
        self._user_info = None
        self._story_cache.clear()
        self._snap_cache.clear()
        
        logger.info("Disconnected from Snapchat")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Snapchat.
        
        Args:
            user_id: Snapchat user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "snapchat"
        }
    
    def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """
        Get cached user information.
        
        Returns:
            User info dictionary or None
        """
        return self._user_info
    
    async def get_bitmoji(self) -> Dict[str, Any]:
        """
        Get user's Bitmoji.
        
        Returns:
            Dictionary with Bitmoji info
        """
        self._ensure_authenticated()
        
        bitmoji = await self._snapchat_client.get_bitmoji()
        
        return {
            "avatar_id": bitmoji.avatar_id,
            "avatar_url": bitmoji.avatar_url,
            "background_color": bitmoji.background_color,
            "platform": "snapchat"
        }
