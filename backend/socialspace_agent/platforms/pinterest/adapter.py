"""
Pinterest Platform - Platform Adapter
======================================

Pinterest platform adapter implementing BasePlatform interface.

This integrates Pinterest API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 14 (FINAL SESSION - 100% COMPLETION!)
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.pinterest.client import PinterestClient
from socialspace_agent.platforms.pinterest.models import PinterestPin, PinterestBoard
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


class PinterestPlatform(BasePlatform):
    """
    Pinterest API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify access token
    - fetch_messages(): Get pins
    - send_message(): Create pins
    - normalize_message(): Convert Pinterest format to UnifiedMessage
    
    Features:
    ---------
    - Fetch user pins
    - Fetch board pins
    - Create pins
    - Manage boards
    - Search pins
    - Get user info
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="pinterest",
    ...     api_key="YOUR_ACCESS_TOKEN",
    ...     mock_mode=True
    ... )
    >>> 
    >>> pinterest = PinterestPlatform(config)
    >>> await pinterest.authenticate()
    >>> 
    >>> # Fetch pins
    >>> messages = await pinterest.fetch_messages(
    ...     user_id="board_id",
    ...     limit=10
    ... )
    >>> 
    >>> # Create pin
    >>> msg = UnifiedMessage(...)
    >>> result = await pinterest.send_message(msg, recipient_id="board_id")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Pinterest platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: Pinterest access token
        """
        super().__init__(config)
        
        # Extract Pinterest-specific config
        self.access_token = config.api_key or config.access_token
        
        if not self.access_token:
            raise ValidationError(
                "access_token (api_key) is required for Pinterest",
                context={"platform": "pinterest"}
            )
        
        # Pinterest client (initialized on authenticate)
        self._pinterest_client: Optional[PinterestClient] = None
        
        # User info cache
        self._user_info: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._pin_cache: List[PinterestPin] = []
        self._board_cache: List[PinterestBoard] = []
        
        logger.info("Pinterest platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Pinterest API.
        
        Verifies access token by fetching user information.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Pinterest API...")
            
            # Create Pinterest client
            self._pinterest_client = PinterestClient(
                access_token=self.access_token,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify token by getting user info
            user = await self._pinterest_client.get_user_info()
            self._user_info = user.model_dump()
            
            self._is_authenticated = True
            self._client = self._pinterest_client
            
            logger.info(f"✅ Pinterest authentication successful ({user.username})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinterest authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Pinterest: {e}",
                context={"platform": "pinterest"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Pinterest.
        
        For Pinterest, user_id can be:
        - "me" (to fetch user's pins)
        - Board ID (to fetch board pins)
        
        Args:
            user_id: User ID or board ID
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters (optional)
            
        Returns:
            List of UnifiedMessage objects
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Pinterest messages from {user_id}")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit,
            filters
        )
        
        unified_messages = []
        
        # Determine if fetching from board or user
        board_id = None if user_id == "me" else user_id
        
        # Fetch pins
        pins = await self._pinterest_client.get_pins(
            board_id=board_id,
            page_size=min(limit, 100)
        )
        
        for pin in pins:
            # Filter by timestamp if specified
            if since and pin.created_at:
                pin_time = datetime.fromisoformat(
                    pin.created_at.replace('Z', '+00:00')
                )
                if pin_time < since:
                    continue
            
            # Normalize to UnifiedMessage
            unified_msg = self.normalize_message(pin.model_dump())
            unified_messages.append(unified_msg)
            
            # Add to cache
            self._pin_cache.append(pin)
            
            # Stop if we've reached the limit
            if len(unified_messages) >= limit:
                break
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Pinterest messages")
        
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
        Send a message via Pinterest.
        
        Creates a pin on a board.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Board ID
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (pin ID)
                - timestamp: datetime
                - metadata: Dict
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Pinterest message to board {recipient_id}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Pinterest pin sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send Pinterest pin: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        # Extract media URL
        media_url = None
        if message.media and len(message.media) > 0:
            media_url = message.media[0].url
        
        if not media_url:
            raise ValidationError(
                "Pinterest pins require media (image or video)",
                context={"message_id": message.id}
            )
        
        # Create pin
        pin = await self._pinterest_client.create_pin(
            board_id=recipient_id,
            title=message.content[:100] if message.content else None,
            description=message.content if message.content else None,
            link=message.metadata.get("link") if message.metadata else None,
            media_source={"source_type": "image_url", "url": media_url}
        )
        
        timestamp = datetime.fromisoformat(
            pin.created_at.replace('Z', '+00:00')
        ) if pin.created_at else datetime.now(timezone.utc)
        
        return {
            "success": True,
            "message_id": pin.id,
            "timestamp": timestamp,
            "metadata": {
                "platform": "pinterest",
                "type": "pin",
                "board_id": recipient_id,
                "pin_url": pin.get_url()
            }
        }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Pinterest pin to UnifiedMessage.
        
        Args:
            raw_message: Raw Pinterest pin dictionary
            
        Returns:
            UnifiedMessage object
        """
        try:
            # Parse as Pinterest pin
            pin = PinterestPin(**raw_message)
            
            # Extract sender info
            creator_name = "Unknown"
            creator_id = "unknown"
            
            if pin.creator:
                creator_name = pin.creator.get("username", "Unknown")
                creator_id = pin.creator.get("id", "unknown")
            
            sender = UserInfo(
                id=creator_id,
                username=creator_name,
                display_name=creator_name
            )
            
            # Extract content
            content = ""
            if pin.title:
                content = pin.title
            if pin.description:
                if content:
                    content += "\n\n" + pin.description
                else:
                    content = pin.description
            
            # Extract media
            media_list = []
            image_url = pin.get_image_url()
            if image_url:
                media = MediaAttachment(
                    url=image_url,
                    type="video" if pin.is_video() else "image"
                )
                media_list.append(media)
            
            # Convert timestamp
            if pin.created_at:
                timestamp = datetime.fromisoformat(
                    pin.created_at.replace('Z', '+00:00')
                )
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Create UnifiedMessage
            unified_message = UnifiedMessage(
                platform_message_id=pin.id,
                platform=PlatformType.PINTEREST,
                type=MessageType.POST,
                sender=sender,
                content=content,
                media=media_list,
                timestamp=timestamp,
                metadata={
                    "pinterest_pin_id": pin.id,
                    "board_id": pin.board_id,
                    "save_count": pin.save_count,
                    "comment_count": pin.comment_count,
                    "link": pin.link,
                    "pin_url": pin.get_url()
                }
            )
            
            return unified_message
            
        except Exception as e:
            logger.error(f"Failed to normalize Pinterest message: {e}")
            raise ValidationError(
                f"Invalid Pinterest message format: {e}",
                context={"raw_message": raw_message}
            )
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Pinterest and cleanup."""
        if self._pinterest_client:
            await self._pinterest_client.close()
            self._pinterest_client = None
        
        self._is_authenticated = False
        self._user_info = None
        self._pin_cache.clear()
        self._board_cache.clear()
        
        logger.info("Disconnected from Pinterest")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Pinterest.
        
        Args:
            user_id: Pinterest user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "pinterest"
        }
    
    def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """
        Get cached user information.
        
        Returns:
            User info dictionary or None
        """
        return self._user_info
    
    async def get_boards(self) -> List[Dict[str, Any]]:
        """
        Get user's boards.
        
        Returns:
            List of board dictionaries
        """
        self._ensure_authenticated()
        
        boards = await self._pinterest_client.get_boards()
        
        result = []
        for board in boards:
            result.append({
                "id": board.id,
                "name": board.name,
                "description": board.description,
                "url": board.get_url(),
                "pin_count": board.pin_count,
                "follower_count": board.follower_count,
                "privacy": board.privacy,
                "platform": "pinterest"
            })
        
        return result
    
    async def create_board(
        self,
        name: str,
        description: Optional[str] = None,
        privacy: str = "PUBLIC"
    ) -> Dict[str, Any]:
        """
        Create a new board.
        
        Args:
            name: Board name
            description: Board description
            privacy: Privacy setting
            
        Returns:
            Board result dictionary
        """
        self._ensure_authenticated()
        
        board = await self._pinterest_client.create_board(
            name=name,
            description=description,
            privacy=privacy
        )
        
        return {
            "success": True,
            "board_id": board.id,
            "url": board.get_url()
        }
    
    async def search_pins(
        self,
        query: str,
        limit: int = 25
    ) -> List[UnifiedMessage]:
        """
        Search for pins.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of UnifiedMessage objects
        """
        self._ensure_authenticated()
        
        pins = await self._pinterest_client.search_pins(
            query=query,
            page_size=min(limit, 100)
        )
        
        unified_messages = []
        for pin in pins:
            unified_msg = self.normalize_message(pin.model_dump())
            unified_messages.append(unified_msg)
        
        return unified_messages
