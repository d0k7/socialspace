"""
Discord Platform - Platform Adapter
====================================

Discord platform adapter implementing BasePlatform interface.

This integrates Discord Bot API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 6
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.discord.client import DiscordClient
from socialspace_agent.platforms.discord.models import DiscordMessage, DiscordEmbed
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


class DiscordPlatform(BasePlatform):
    """
    Discord Bot API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify bot token
    - fetch_messages(): Get messages from channels
    - send_message(): Send messages to channels
    - normalize_message(): Convert Discord format to UnifiedMessage
    
    Features:
    ---------
    - Text messages
    - Rich embeds (formatted messages)
    - File attachments
    - Reactions
    - Reply to messages
    - Channel management
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="discord",
    ...     api_key="YOUR_BOT_TOKEN",
    ...     mock_mode=True
    ... )
    >>> 
    >>> discord = DiscordPlatform(config)
    >>> await discord.authenticate()
    >>> 
    >>> # Fetch messages from channel
    >>> messages = await discord.fetch_messages(
    ...     user_id="channel_123456789",
    ...     limit=50
    ... )
    >>> 
    >>> # Send message to channel
    >>> msg = UnifiedMessage(...)
    >>> result = await discord.send_message(msg, recipient_id="channel_123")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Discord platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: Discord bot token
        """
        super().__init__(config)
        
        # Extract Discord-specific config
        self.bot_token = config.api_key
        
        if not self.bot_token:
            raise ValidationError(
                "bot_token (api_key) is required for Discord",
                context={"platform": "discord"}
            )
        
        # Discord client (initialized on authenticate)
        self._discord_client: Optional[DiscordClient] = None
        
        # Bot user info (from getCurrentUser)
        self._bot_user: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._message_cache: List[DiscordMessage] = []
        
        logger.info("Discord platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Discord Bot API.
        
        Verifies bot token by fetching bot user information.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Discord Bot API...")
            
            # Create Discord client
            self._discord_client = DiscordClient(
                bot_token=self.bot_token,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify bot token by getting bot user
            bot_user = await self._discord_client.get_current_user()
            self._bot_user = bot_user.model_dump()
            
            self._is_authenticated = True
            self._client = self._discord_client
            
            logger.info(
                f"✅ Discord authentication successful "
                f"({bot_user.get_tag()})"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Discord authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Discord: {e}",
                context={"platform": "discord"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Discord.
        
        For Discord, user_id is the channel_id to fetch from.
        
        Args:
            user_id: Channel ID to fetch messages from
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters (optional)
            
        Returns:
            List of UnifiedMessage objects
            
        Example:
            >>> # Get messages from a channel
            >>> messages = await discord.fetch_messages(
            ...     user_id="123456789",  # channel_id
            ...     limit=50
            ... )
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Discord messages from channel {user_id}")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit
        )
        
        # Channel ID
        channel_id = user_id
        
        # Get messages from Discord
        discord_messages = await self._discord_client.get_messages(
            channel_id=channel_id,
            limit=min(limit, 100)
        )
        
        unified_messages = []
        
        for discord_msg in discord_messages:
            # Filter by timestamp if specified
            if since:
                msg_timestamp = datetime.fromisoformat(
                    discord_msg.timestamp.replace('Z', '+00:00')
                )
                if msg_timestamp < since:
                    continue
            
            # Normalize to UnifiedMessage
            unified_msg = self.normalize_message(discord_msg.model_dump())
            unified_messages.append(unified_msg)
            
            # Add to cache
            self._message_cache.append(discord_msg)
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Discord messages")
        
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
        Send a message via Discord.
        
        For Discord, recipient_id is the channel_id to send to.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Channel ID to send to
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (Discord message ID)
                - timestamp: datetime
                - metadata: Dict
                
        Example:
            >>> msg = UnifiedMessage(
            ...     platform_message_id="temp",
            ...     platform=PlatformType.DISCORD,
            ...     type=MessageType.TEXT,
            ...     sender=UserInfo(id="bot", display_name="Bot"),
            ...     content="Hello Discord!",
            ...     timestamp=datetime.now(timezone.utc)
            ... )
            >>> 
            >>> result = await discord.send_message(msg, "channel_123")
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Discord message to channel {recipient_id}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Discord message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send Discord message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        channel_id: str
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        # Prepare content
        content = message.content
        embed = None
        reply_to = None
        
        # Check if this is a reply
        if message.is_reply and message.parent_id:
            reply_to = message.parent_id
        
        # Create embed if message has rich content
        if message.metadata and message.metadata.get("use_embed"):
            embed = DiscordEmbed(
                title=message.metadata.get("embed_title"),
                description=content,
                color=message.metadata.get("embed_color", 0x00ff00)
            )
            content = None  # Don't send content if using embed
        
        # Send message
        discord_msg = await self._discord_client.send_message(
            channel_id=channel_id,
            content=content,
            embed=embed,
            reply_to=reply_to
        )
        
        # Return formatted response
        return {
            "success": True,
            "message_id": discord_msg.id,
            "timestamp": datetime.fromisoformat(
                discord_msg.timestamp.replace('Z', '+00:00')
            ),
            "metadata": {
                "platform": "discord",
                "channel_id": channel_id,
                "has_embed": embed is not None
            }
        }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Discord message to UnifiedMessage.
        
        Args:
            raw_message: Raw Discord message dictionary
            
        Returns:
            UnifiedMessage object
            
        Example:
            >>> raw = {
            ...     "id": "123456789",
            ...     "channel_id": "987654321",
            ...     "author": {
            ...         "id": "111111111",
            ...         "username": "john",
            ...         "discriminator": "0001"
            ...     },
            ...     "content": "Hello Discord!",
            ...     "timestamp": "2026-02-21T01:30:00+00:00"
            ... }
            >>> 
            >>> unified = discord.normalize_message(raw)
            >>> print(unified.content)
            Hello Discord!
        """
        try:
            # Parse as Discord message
            discord_msg = DiscordMessage(**raw_message)
            
            # Extract sender info
            author = discord_msg.author
            sender = UserInfo(
                id=author.id,
                username=author.username,
                display_name=author.get_tag(),
                avatar_url=author.get_avatar_url(),
                is_bot=author.bot or False
            )
            
            # Determine message type
            if discord_msg.has_attachments():
                # Has file attachments
                message_type = MessageType.DOCUMENT
                if discord_msg.attachments:
                    first_attachment = discord_msg.attachments[0]
                    if first_attachment.content_type:
                        if first_attachment.content_type.startswith("image/"):
                            message_type = MessageType.IMAGE
                        elif first_attachment.content_type.startswith("video/"):
                            message_type = MessageType.VIDEO
                        elif first_attachment.content_type.startswith("audio/"):
                            message_type = MessageType.AUDIO
            else:
                message_type = MessageType.TEXT
            
            # Extract content
            content = discord_msg.get_content()
            
            # Extract media attachments
            media_list = []
            if discord_msg.has_attachments():
                for attachment in discord_msg.attachments:
                    media = MediaAttachment(
                        url=attachment.url,
                        type=attachment.content_type or "file",
                        size_bytes=attachment.size,
                        width=attachment.width,
                        height=attachment.height
                    )
                    media_list.append(media)
            
            # Convert timestamp
            timestamp = datetime.fromisoformat(
                discord_msg.timestamp.replace('Z', '+00:00')
            )
            
            # Check if edited
            is_edited = discord_msg.edited_timestamp is not None
            
            # Extract mentions
            mentions = []
            if discord_msg.mentions:
                for mentioned_user in discord_msg.mentions:
                    mention = UserInfo(
                        id=mentioned_user.id,
                        username=mentioned_user.username,
                        display_name=mentioned_user.get_tag()
                    )
                    mentions.append(mention)
            
            # Create UnifiedMessage
            unified_message = UnifiedMessage(
                platform_message_id=discord_msg.id,
                platform=PlatformType.DISCORD,
                type=message_type,
                sender=sender,
                content=content,
                media=media_list,
                timestamp=timestamp,
                is_edited=is_edited,
                is_reply=discord_msg.is_reply(),
                parent_id=discord_msg.referenced_message.id if discord_msg.referenced_message else None,
                mentions=mentions,
                metadata={
                    "discord_channel_id": discord_msg.channel_id,
                    "discord_guild_id": discord_msg.guild_id,
                    "has_embeds": discord_msg.has_embeds(),
                    "embed_count": len(discord_msg.embeds) if discord_msg.embeds else 0,
                    "mention_everyone": discord_msg.mention_everyone
                }
            )
            
            return unified_message
            
        except Exception as e:
            logger.error(f"Failed to normalize Discord message: {e}")
            raise ValidationError(
                f"Invalid Discord message format: {e}",
                context={"raw_message": raw_message}
            )
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Discord and cleanup."""
        if self._discord_client:
            await self._discord_client.close()
            self._discord_client = None
        
        self._is_authenticated = False
        self._bot_user = None
        self._message_cache.clear()
        
        logger.info("Disconnected from Discord")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Discord.
        
        Note: Requires user to be cached or in a mutual guild.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "discord",
            "display_name": user_id,
        }
    
    def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """
        Get bot user information.
        
        Returns:
            Bot info (username, id, discriminator, etc.)
        """
        return self._bot_user
    
    async def send_embed_message(
        self,
        channel_id: str,
        title: str,
        description: str,
        color: int = 0x00ff00,
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a rich embed message.
        
        Convenience method for sending Discord embeds.
        
        Args:
            channel_id: Channel ID to send to
            title: Embed title
            description: Embed description
            color: Embed color (decimal, default: green)
            fields: List of field dictionaries
            
        Returns:
            Message result dictionary
            
        Example:
            >>> result = await discord.send_embed_message(
            ...     channel_id="123456789",
            ...     title="Alert!",
            ...     description="Something important happened",
            ...     color=0xff0000,  # Red
            ...     fields=[
            ...         {"name": "Status", "value": "Active", "inline": True},
            ...         {"name": "Count", "value": "42", "inline": True}
            ...     ]
            ... )
        """
        self._ensure_authenticated()
        
        from socialspace_agent.platforms.discord.models import (
            DiscordEmbedField
        )
        
        # Create embed
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=color
        )
        
        # Add fields if provided
        if fields:
            embed.fields = []
            for field_data in fields:
                field = DiscordEmbedField(**field_data)
                embed.fields.append(field)
        
        # Send message
        discord_msg = await self._discord_client.send_message(
            channel_id=channel_id,
            embed=embed
        )
        
        return {
            "success": True,
            "message_id": discord_msg.id,
            "timestamp": discord_msg.timestamp,
            "channel_id": channel_id
        }
    
    async def add_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> bool:
        """
        Add a reaction to a message.
        
        Args:
            channel_id: Channel ID
            message_id: Message ID
            emoji: Emoji to react with (e.g., "👍", "❤️", "🎉")
            
        Returns:
            True if successful
            
        Example:
            >>> await discord.add_reaction(
            ...     channel_id="123456789",
            ...     message_id="987654321",
            ...     emoji="👍"
            ... )
        """
        self._ensure_authenticated()
        
        await self._discord_client.add_reaction(
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )
        
        return True
