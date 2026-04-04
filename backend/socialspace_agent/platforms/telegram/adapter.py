"""
Telegram Platform - Platform Adapter
=====================================

Telegram platform adapter implementing BasePlatform interface.

This integrates Telegram Bot API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 4
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.telegram.client import TelegramClient
from socialspace_agent.platforms.telegram.models import TelegramMessage, TelegramUpdate
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


class TelegramPlatform(BasePlatform):
    """
    Telegram Bot API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify bot token
    - fetch_messages(): Get updates via polling
    - send_message(): Send messages via Telegram
    - normalize_message(): Convert Telegram format to UnifiedMessage
    
    Features:
    ---------
    - Text messages
    - Media messages (photo, video, audio, document)
    - Location sharing
    - Reply to messages
    - Long polling for updates
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="telegram",
    ...     api_key="123456:ABC-DEF...",
    ...     mock_mode=True
    ... )
    >>> 
    >>> telegram = TelegramPlatform(config)
    >>> await telegram.authenticate()
    >>> 
    >>> # Fetch messages
    >>> messages = await telegram.fetch_messages(user_id="123456789", limit=50)
    >>> 
    >>> # Send message
    >>> msg = UnifiedMessage(...)
    >>> result = await telegram.send_message(msg, recipient_id="123456789")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Telegram platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: Telegram bot token
        """
        super().__init__(config)
        
        # Extract Telegram-specific config
        self.bot_token = config.api_key
        
        if not self.bot_token:
            raise ValidationError(
                "bot_token (api_key) is required for Telegram",
                context={"platform": "telegram"}
            )
        
        # Telegram client (initialized on authenticate)
        self._telegram_client: Optional[TelegramClient] = None
        
        # Bot info (from getMe)
        self._bot_info: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._message_cache: List[TelegramMessage] = []
        
        logger.info("Telegram platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Telegram Bot API.
        
        Verifies bot token by calling getMe endpoint.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Telegram Bot API...")
            
            # Create Telegram client
            self._telegram_client = TelegramClient(
                bot_token=self.bot_token,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify bot token with getMe
            self._bot_info = await self._telegram_client.get_me()
            
            self._is_authenticated = True
            self._client = self._telegram_client
            
            logger.info(
                f"✅ Telegram authentication successful "
                f"(@{self._bot_info.get('username', 'unknown')})"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Telegram authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Telegram: {e}",
                context={"platform": "telegram"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Telegram.
        
        Uses long polling (getUpdates) to retrieve new messages.
        
        Args:
            user_id: Telegram user ID (optional - fetches all if not specified)
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters (optional)
            
        Returns:
            List of UnifiedMessage objects
            
        Example:
            >>> # Get all new messages
            >>> messages = await telegram.fetch_messages(user_id=None, limit=100)
            >>> 
            >>> # Get messages from specific user
            >>> messages = await telegram.fetch_messages(user_id="123456789")
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Telegram messages (user_id={user_id}, limit={limit})")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit
        )
        
        # Get updates from Telegram
        updates = await self._telegram_client.get_updates(limit=limit)
        
        unified_messages = []
        
        for update in updates:
            message = update.get_message()
            if not message:
                continue
            
            # Filter by user_id if specified
            if user_id:
                sender_id = str(message.from_user.id) if message.from_user else None
                if sender_id != user_id:
                    continue
            
            # Filter by timestamp if specified
            if since:
                msg_timestamp = datetime.fromtimestamp(message.date, tz=timezone.utc)
                if msg_timestamp < since:
                    continue
            
            # Normalize to UnifiedMessage
            unified_msg = self.normalize_message(message.model_dump())
            unified_messages.append(unified_msg)
            
            # Add to cache
            self._message_cache.append(message)
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Telegram messages")
        
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
        Send a message via Telegram.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Telegram chat_id (user ID or group ID)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: int (Telegram message ID)
                - timestamp: datetime
                - metadata: Dict
                
        Example:
            >>> msg = UnifiedMessage(
            ...     platform_message_id="temp",
            ...     platform=PlatformType.TELEGRAM,
            ...     type=MessageType.TEXT,
            ...     sender=UserInfo(id="bot", display_name="Bot"),
            ...     content="Hello from SocialSpace!",
            ...     timestamp=datetime.now(timezone.utc)
            ... )
            >>> 
            >>> result = await telegram.send_message(msg, "123456789")
            >>> print(f"Sent: {result['message_id']}")
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Telegram message to {recipient_id}")
        
        try:
            # Parse chat_id as integer
            chat_id = int(recipient_id)
            
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                chat_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Telegram message sent: {response['message_id']}")
            
            return response
            
        except ValueError:
            raise ValidationError(
                f"Invalid Telegram chat_id: {recipient_id}",
                context={"recipient_id": recipient_id}
            )
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        chat_id: int
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        # Determine message type and send accordingly
        if message.type == MessageType.TEXT:
            # Send text message
            response = await self._telegram_client.send_message(
                chat_id=chat_id,
                text=message.content or ""
            )
            
        elif message.type == MessageType.IMAGE:
            # Send photo
            if not message.media or len(message.media) == 0:
                raise ValidationError(
                    "Image message must have media attachment",
                    context={"message_id": message.id}
                )
            
            media = message.media[0]
            response = await self._telegram_client.send_photo(
                chat_id=chat_id,
                photo=media.url,
                caption=message.content
            )
            
        elif message.type == MessageType.VIDEO:
            # Send video
            if not message.media or len(message.media) == 0:
                raise ValidationError(
                    "Video message must have media attachment",
                    context={"message_id": message.id}
                )
            
            media = message.media[0]
            response = await self._telegram_client.send_video(
                chat_id=chat_id,
                video=media.url,
                caption=message.content
            )
            
        elif message.type == MessageType.AUDIO:
            # Send audio
            if not message.media or len(message.media) == 0:
                raise ValidationError(
                    "Audio message must have media attachment",
                    context={"message_id": message.id}
                )
            
            media = message.media[0]
            response = await self._telegram_client.send_audio(
                chat_id=chat_id,
                audio=media.url,
                caption=message.content
            )
            
        elif message.type == MessageType.DOCUMENT:
            # Send document
            if not message.media or len(message.media) == 0:
                raise ValidationError(
                    "Document message must have media attachment",
                    context={"message_id": message.id}
                )
            
            media = message.media[0]
            response = await self._telegram_client.send_document(
                chat_id=chat_id,
                document=media.url,
                caption=message.content
            )
            
        else:
            raise ValidationError(
                f"Unsupported message type for Telegram: {message.type}",
                context={"message_id": message.id}
            )
        
        # Return formatted response
        return {
            "success": True,
            "message_id": response.message_id,
            "timestamp": datetime.fromtimestamp(response.date, tz=timezone.utc),
            "metadata": {
                "platform": "telegram",
                "recipient": chat_id
            }
        }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Telegram message to UnifiedMessage.
        
        Args:
            raw_message: Raw Telegram message dictionary
            
        Returns:
            UnifiedMessage object
            
        Example:
            >>> raw = {
            ...     "message_id": 123,
            ...     "from": {"id": 456, "first_name": "John"},
            ...     "chat": {"id": 456, "type": "private"},
            ...     "date": 1708300000,
            ...     "text": "Hello!"
            ... }
            >>> 
            >>> unified = telegram.normalize_message(raw)
            >>> print(unified.content)
            Hello!
        """
        try:
            # Parse as Telegram message
            tg_message = TelegramMessage(**raw_message)
            
            # Extract sender info
            if tg_message.from_user:
                sender = UserInfo(
                    id=str(tg_message.from_user.id),
                    username=tg_message.from_user.username,
                    display_name=tg_message.from_user.get_full_name(),
                    is_verified=False,
                    is_bot=tg_message.from_user.is_bot
                )
            else:
                # Anonymous/channel message
                sender = UserInfo(
                    id=str(tg_message.chat.id),
                    display_name=tg_message.chat.title or "Unknown"
                )
            
            # Map Telegram message type to MessageType
            media_type = tg_message.get_media_type()
            
            if media_type == "photo":
                message_type = MessageType.IMAGE
            elif media_type == "video":
                message_type = MessageType.VIDEO
            elif media_type == "audio":
                message_type = MessageType.AUDIO
            elif media_type == "voice":
                message_type = MessageType.AUDIO
            elif media_type == "document":
                message_type = MessageType.DOCUMENT
            else:
                message_type = MessageType.TEXT
            
            # Extract content
            content = tg_message.get_content()
            
            # Extract media if present
            media_list = []
            file_id = tg_message.get_file_id()
            if file_id:
                media = MediaAttachment(
                    url=file_id,  # Telegram uses file_id instead of URL
                    type=media_type or "file"
                )
                media_list.append(media)
            
            # Convert timestamp
            timestamp = datetime.fromtimestamp(tg_message.date, tz=timezone.utc)
            
            # Check if it's a reply
            is_reply = tg_message.reply_to_message is not None
            parent_id = None
            if is_reply:
                parent_id = str(tg_message.reply_to_message.message_id)
            
            # Create UnifiedMessage
            unified_message = UnifiedMessage(
                platform_message_id=str(tg_message.message_id),
                platform=PlatformType.TELEGRAM,
                type=message_type,
                sender=sender,
                content=content,
                media=media_list,
                timestamp=timestamp,
                is_reply=is_reply,
                parent_id=parent_id,
                metadata={
                    "telegram_chat_id": tg_message.chat.id,
                    "telegram_chat_type": tg_message.chat.type,
                    "media_type": media_type
                }
            )
            
            return unified_message
            
        except Exception as e:
            logger.error(f"Failed to normalize Telegram message: {e}")
            raise ValidationError(
                f"Invalid Telegram message format: {e}",
                context={"raw_message": raw_message}
            )
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram and cleanup."""
        if self._telegram_client:
            await self._telegram_client.close()
            self._telegram_client = None
        
        self._is_authenticated = False
        self._bot_info = None
        self._message_cache.clear()
        
        logger.info("Disconnected from Telegram")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Telegram.
        
        Note: Telegram Bot API doesn't provide a way to get arbitrary
        user info. We can only get info about users who have interacted
        with the bot.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "telegram",
            "display_name": user_id,
        }
    
    def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """
        Get bot information.
        
        Returns:
            Bot info from getMe (username, id, etc.)
        """
        return self._bot_info