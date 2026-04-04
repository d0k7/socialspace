"""
WhatsApp Platform - Platform Adapter
=====================================

WhatsApp platform adapter implementing BasePlatform interface.

This is the main class that integrates WhatsApp with SocialSpace Agent.
It inherits from BasePlatform and implements all required methods.

Author: Dheeraj Mishra
Created: February 19, 2026
Session: 3
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.whatsapp.client import WhatsAppClient
from socialspace_agent.platforms.whatsapp.models import WhatsAppMessage
from socialspace_agent.models import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
    MediaAttachment,
)
from socialspace_agent.exceptions import (
    WhatsAppError,
    AuthenticationError,
    ValidationError,
)
from socialspace_agent.utils.config import PlatformConfig

logger = logging.getLogger(__name__)


class WhatsAppPlatform(BasePlatform):
    """
    WhatsApp Business API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Connect to WhatsApp Business API
    - fetch_messages(): Fetch messages from WhatsApp
    - send_message(): Send messages via WhatsApp
    - normalize_message(): Convert WhatsApp format to UnifiedMessage
    
    Features:
    ---------
    - Text messages
    - Media messages (image, video, audio, document)
    - Location sharing
    - Message status tracking
    - Automatic rate limiting (inherited from BasePlatform)
    - Automatic retry logic (inherited from BasePlatform)
    
    Usage:
    ------
    >>> # Create configuration
    >>> config = PlatformConfig(
    ...     platform="whatsapp",
    ...     api_key="YOUR_ACCESS_TOKEN",
    ...     metadata={"phone_number_id": "YOUR_PHONE_NUMBER_ID"}
    ... )
    >>> 
    >>> # Create platform instance
    >>> whatsapp = WhatsAppPlatform(config)
    >>> 
    >>> # Authenticate
    >>> await whatsapp.authenticate()
    >>> 
    >>> # Fetch messages
    >>> messages = await whatsapp.fetch_messages(
    ...     user_id="919876543210",
    ...     limit=50
    ... )
    >>> 
    >>> # Send a message
    >>> msg = UnifiedMessage(...)
    >>> result = await whatsapp.send_message(msg, recipient_id="919876543210")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize WhatsApp platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: WhatsApp access token
                - metadata.phone_number_id: WhatsApp Business phone number ID
        """
        super().__init__(config)
        
        # Extract WhatsApp-specific config
        self.access_token = config.api_key
        self.phone_number_id = config.metadata.get("phone_number_id")
        
        if not self.phone_number_id:
            raise ValidationError(
                "phone_number_id is required in config.metadata",
                context={"platform": "whatsapp"}
            )
        
        # WhatsApp client (will be initialized on authenticate)
        self._whatsapp_client: Optional[WhatsAppClient] = None
        
        # Message cache for pagination/fetching
        self._message_cache: List[WhatsAppMessage] = []
        
        logger.info(
            f"WhatsApp platform initialized "
            f"(phone_number_id={self.phone_number_id[:8]}...)"
        )
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS FROM BASEPLATFORM
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with WhatsApp Business API.
        
        Creates WhatsApp client and validates credentials.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with WhatsApp Business API...")
            
            # Create WhatsApp client
            self._whatsapp_client = WhatsAppClient(
                access_token=self.access_token,
                phone_number_id=self.phone_number_id,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Test connection with a simple API call
            # (In real implementation, you'd call a health check endpoint)
            # For now, we just verify client was created
            
            self._is_authenticated = True
            self._client = self._whatsapp_client  # Store in base class
            
            logger.info("✅ WhatsApp authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ WhatsApp authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with WhatsApp: {e}",
                context={"platform": "whatsapp"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from WhatsApp.
        
        Note: WhatsApp uses webhook-based messaging, so this method
        returns cached messages received via webhooks.
        
        In production, you'd integrate with your webhook system to
        populate the message cache.
        
        Args:
            user_id: Phone number (with country code, no +)
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages to fetch
            filters: Additional filters (optional)
            
        Returns:
            List of UnifiedMessage objects
            
        Raises:
            AuthenticationError: If not authenticated
            
        Example:
            >>> messages = await whatsapp.fetch_messages(
            ...     user_id="919876543210",
            ...     limit=50
            ... )
            >>> print(f"Fetched {len(messages)} messages")
        """
        # Ensure authenticated
        self._ensure_authenticated()
        
        logger.info(f"Fetching WhatsApp messages for user {user_id}")
        
        # Use rate limiting (inherited from BasePlatform)
        await self._rate_limited_call(self._fetch_messages_impl, user_id, since, limit)
        
        # For this implementation, we'll return cached messages
        # In production, this would integrate with webhook message storage
        
        unified_messages = []
        
        for wa_message in self._message_cache[:limit]:
            # Filter by user if specified
            if user_id and wa_message.from_number != user_id:
                continue
            
            # Filter by timestamp if specified
            if since:
                msg_timestamp = datetime.fromtimestamp(
                    int(wa_message.timestamp),
                    tz=timezone.utc
                )
                if msg_timestamp < since:
                    continue
            
            # Normalize to UnifiedMessage
            unified_msg = self.normalize_message(wa_message.model_dump())
            unified_messages.append(unified_msg)
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} WhatsApp messages")
        
        return unified_messages
    
    async def _fetch_messages_impl(
        self,
        user_id: str,
        since: Optional[datetime],
        limit: int
    ) -> None:
        """
        Internal message fetching implementation.
        
        In production, this would:
        1. Query your database for webhook messages
        2. Filter by user_id and since
        3. Populate self._message_cache
        
        For now, it's a placeholder for the rate-limited wrapper.
        """
        # This is where you'd implement actual message fetching
        # from your webhook message storage (database, cache, etc.)
        pass
    
    async def send_message(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """
        Send a message via WhatsApp.
        
        Converts UnifiedMessage to WhatsApp format and sends via API.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Recipient phone number (with country code, no +)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (WhatsApp message ID)
                - timestamp: datetime
                - metadata: Dict
                
        Raises:
            AuthenticationError: If not authenticated
            WhatsAppError: If sending fails
            
        Example:
            >>> msg = UnifiedMessage(
            ...     platform_message_id="temp_123",
            ...     platform=PlatformType.WHATSAPP,
            ...     type=MessageType.TEXT,
            ...     sender=UserInfo(id="me", display_name="Me"),
            ...     content="Hello from SocialSpace!",
            ...     timestamp=datetime.now(timezone.utc)
            ... )
            >>> 
            >>> result = await whatsapp.send_message(msg, "919876543210")
            >>> print(f"Message sent: {result['message_id']}")
        """
        # Ensure authenticated
        self._ensure_authenticated()
        
        logger.info(f"Sending WhatsApp message to {recipient_id}")
        
        try:
            # Use rate limiting (inherited from BasePlatform)
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ WhatsApp message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """
        Internal message sending implementation.
        
        Converts UnifiedMessage to WhatsApp format and sends.
        """
        # Determine message type and send accordingly
        if message.type == MessageType.TEXT:
            # Send text message
            response = await self._whatsapp_client.send_text_message(
                to=recipient_id,
                text=message.content or ""
            )
            
        elif message.type in [MessageType.IMAGE, MessageType.VIDEO, MessageType.AUDIO, MessageType.DOCUMENT]:
            # Send media message
            if not message.media or len(message.media) == 0:
                raise ValidationError(
                    f"{message.type} message must have media attachment",
                    context={"message_id": message.id}
                )
            
            media = message.media[0]  # Get first media
            
            # Map MessageType to WhatsApp media type
            media_type_map = {
                MessageType.IMAGE: "image",
                MessageType.VIDEO: "video",
                MessageType.AUDIO: "audio",
                MessageType.DOCUMENT: "document"
            }
            
            response = await self._whatsapp_client.send_media_message(
                to=recipient_id,
                media_type=media_type_map[message.type],
                media_link=media.url,
                caption=message.content
            )
            
        else:
            raise ValidationError(
                f"Unsupported message type for WhatsApp: {message.type}",
                context={"message_id": message.id}
            )
        
        # Return formatted response
        return {
            "success": True,
            "message_id": response.get_message_id(),
            "timestamp": datetime.now(timezone.utc),
            "metadata": {
                "platform": "whatsapp",
                "recipient": recipient_id
            }
        }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert WhatsApp message to UnifiedMessage.
        
        This is THE KEY method that makes the adapter pattern work!
        
        Args:
            raw_message: Raw WhatsApp message dictionary
            
        Returns:
            UnifiedMessage object
            
        Raises:
            ValidationError: If message format is invalid
            
        Example:
            >>> raw_wa_msg = {
            ...     "id": "wamid.XXX",
            ...     "from": "919876543210",
            ...     "timestamp": "1708300000",
            ...     "type": "text",
            ...     "text": {"body": "Hello!"}
            ... }
            >>> 
            >>> unified = whatsapp.normalize_message(raw_wa_msg)
            >>> print(unified.content)
            Hello!
        """
        try:
            # Parse as WhatsApp message first
            wa_message = WhatsAppMessage(**raw_message)
            
            # Extract sender info
            sender = UserInfo(
                id=wa_message.from_number,
                display_name=wa_message.from_number,  # WhatsApp doesn't provide name
                username=wa_message.from_number
            )
            
            # Map WhatsApp message type to MessageType
            type_mapping = {
                "text": MessageType.TEXT,
                "image": MessageType.IMAGE,
                "video": MessageType.VIDEO,
                "audio": MessageType.AUDIO,
                "document": MessageType.DOCUMENT,
                "location": MessageType.TEXT,  # Location as text for now
                "contacts": MessageType.TEXT,  # Contacts as text for now
            }
            
            message_type = type_mapping.get(wa_message.type, MessageType.TEXT)
            
            # Extract content
            content = wa_message.get_content()
            
            # Extract media if present
            media_list = []
            media_url = wa_message.get_media_url()
            if media_url:
                media = MediaAttachment(
                    url=media_url,
                    type=wa_message.type
                )
                media_list.append(media)
            
            # Convert timestamp
            timestamp = datetime.fromtimestamp(
                int(wa_message.timestamp),
                tz=timezone.utc
            )
            
            # Create UnifiedMessage
            unified_message = UnifiedMessage(
                platform_message_id=wa_message.id,
                platform=PlatformType.WHATSAPP,
                type=message_type,
                sender=sender,
                content=content,
                media=media_list,
                timestamp=timestamp,
                metadata={
                    "whatsapp_type": wa_message.type,
                    "context": wa_message.context
                }
            )
            
            return unified_message
            
        except Exception as e:
            logger.error(f"Failed to normalize WhatsApp message: {e}")
            raise ValidationError(
                f"Invalid WhatsApp message format: {e}",
                context={"raw_message": raw_message}
            )
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """
        Disconnect from WhatsApp and cleanup resources.
        
        Closes HTTP client and clears state.
        """
        if self._whatsapp_client:
            await self._whatsapp_client.close()
            self._whatsapp_client = None
        
        self._is_authenticated = False
        self._message_cache.clear()
        
        logger.info("Disconnected from WhatsApp")
    
    def add_webhook_message(self, wa_message: WhatsAppMessage) -> None:
        """
        Add a message received via webhook to cache.
        
        In production, this would be called by your webhook handler
        when WhatsApp sends a new message.
        
        Args:
            wa_message: WhatsAppMessage from webhook
        """
        self._message_cache.append(wa_message)
        self._stats["messages_received"] += 1
        
        logger.debug(f"Added webhook message to cache: {wa_message.id}")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from WhatsApp.
        
        WhatsApp doesn't provide rich user profiles via API,
        so we return basic info.
        
        Args:
            user_id: Phone number
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "whatsapp",
            "phone_number": user_id,
            "display_name": user_id,  # WhatsApp doesn't expose names
        }
