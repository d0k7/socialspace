"""
Discord Platform - API Client
==============================

Discord Bot API client.

Features:
---------
- Send messages (text, embeds, files)
- Fetch messages from channels
- Manage guilds and channels
- Handle interactions
- Support webhooks

API Documentation:
https://discord.com/developers/docs/

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 6
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.discord.models import (
    DiscordMessage,
    DiscordUser,
    DiscordGuild,
    DiscordChannel,
    DiscordEmbed,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class DiscordClient:
    """
    Discord Bot API client.
    
    Handles all communication with Discord API.
    
    Authentication:
    ---------------
    Requires:
    - Bot Token (from Discord Developer Portal)
    
    Example:
        >>> client = DiscordClient(bot_token="YOUR_BOT_TOKEN")
        >>> 
        >>> # Send a message
        >>> message = await client.send_message(
        ...     channel_id="123456789",
        ...     content="Hello from SocialSpace!"
        ... )
        >>> 
        >>> # Send with embed
        >>> embed = DiscordEmbed(
        ...     title="Hello!",
        ...     description="This is an embed",
        ...     color=0x00ff00
        ... )
        >>> message = await client.send_message(
        ...     channel_id="123456789",
        ...     embed=embed
        ... )
    
    Rate Limits:
    ------------
    Discord API rate limits:
    - 50 requests per second per route
    - 5 messages per 5 seconds per channel
    - Global limit: 50/second
    """
    
    # API Base URL
    API_VERSION = "v10"
    BASE_URL = f"https://discord.com/api/{API_VERSION}"
    
    def __init__(
        self,
        bot_token: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Discord client.
        
        Args:
            bot_token: Discord bot token
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.bot_token = bot_token
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Bot user info (from getMe)
        self._bot_user: Optional[DiscordUser] = None
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"Discord client initialized (mock_mode={mock_mode})")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bot {self.bot_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "SocialSpace-Agent/1.0"
                }
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Discord client closed")
    
    # ============================================
    # API CALL WRAPPER
    # ============================================
    
    @async_retry_with_backoff(max_retries=3, base_delay=1.0)
    async def _api_call(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API call to Discord with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/channels/123/messages")
            json_data: JSON payload
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            AuthenticationError: On invalid token
            RateLimitError: On rate limit
            ServiceUnavailableError: On service issues
            PlatformError: On other errors
        """
        await self._ensure_client()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        self._stats["api_calls"] += 1
        
        logger.debug(f"API call: {method} {endpoint}")
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=json_data,
                params=params
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                self._stats["errors"] += 1
                retry_after = response.json().get("retry_after", 1)
                raise RateLimitError(
                    message="Discord API rate limit exceeded",
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid Discord bot token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                raise PlatformError(
                    platform="discord",
                    message=f"Discord API error: {error_data.get('message', response.text)}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response (can be empty for some endpoints)
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Discord API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Discord API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # BOT INFORMATION
    # ============================================
    
    async def get_current_user(self) -> DiscordUser:
        """
        Get current bot user information.
        
        Returns:
            DiscordUser representing the bot
            
        Example:
            >>> bot = await client.get_current_user()
            >>> print(f"Bot: {bot.get_tag()}")
        """
        if self.mock_mode:
            return self._mock_bot_user()
        
        data = await self._api_call("GET", "/users/@me")
        
        self._bot_user = DiscordUser(**data)
        return self._bot_user
    
    # ============================================
    # GUILDS (SERVERS)
    # ============================================
    
    async def get_guilds(self) -> List[DiscordGuild]:
        """
        Get list of guilds the bot is in.
        
        Returns:
            List of DiscordGuild objects
        """
        if self.mock_mode:
            return [self._mock_guild()]
        
        data = await self._api_call("GET", "/users/@me/guilds")
        
        guilds = []
        for guild_data in data:
            guild = DiscordGuild(**guild_data)
            guilds.append(guild)
        
        return guilds
    
    # ============================================
    # CHANNELS
    # ============================================
    
    async def get_channel(self, channel_id: str) -> DiscordChannel:
        """
        Get channel information.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            DiscordChannel object
        """
        if self.mock_mode:
            return self._mock_channel(channel_id)
        
        data = await self._api_call("GET", f"/channels/{channel_id}")
        
        return DiscordChannel(**data)
    
    # ============================================
    # MESSAGES
    # ============================================
    
    async def get_messages(
        self,
        channel_id: str,
        limit: int = 50,
        before: Optional[str] = None,
        after: Optional[str] = None
    ) -> List[DiscordMessage]:
        """
        Get messages from a channel.
        
        Args:
            channel_id: Channel ID
            limit: Number of messages (1-100, default: 50)
            before: Get messages before this message ID
            after: Get messages after this message ID
            
        Returns:
            List of DiscordMessage objects
            
        Example:
            >>> messages = await client.get_messages("123456789", limit=10)
            >>> for msg in messages:
            ...     print(f"{msg.author.username}: {msg.content}")
        """
        if self.mock_mode:
            messages = [self._mock_message(channel_id)]
            self._stats["messages_received"] += len(messages)
            return messages
        
        params = {"limit": min(limit, 100)}
        
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        
        data = await self._api_call(
            "GET",
            f"/channels/{channel_id}/messages",
            params=params
        )
        
        messages = []
        for msg_data in data:
            message = DiscordMessage(**msg_data)
            messages.append(message)
        
        self._stats["messages_received"] += len(messages)
        
        return messages
    
    async def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        embed: Optional[DiscordEmbed] = None,
        embeds: Optional[List[DiscordEmbed]] = None,
        reply_to: Optional[str] = None
    ) -> DiscordMessage:
        """
        Send a message to a channel.
        
        Args:
            channel_id: Channel ID to send to
            content: Message text (up to 2000 characters)
            embed: Single embed (will be converted to list)
            embeds: List of embeds (up to 10)
            reply_to: Message ID to reply to
            
        Returns:
            Sent DiscordMessage
            
        Example:
            >>> # Simple text message
            >>> msg = await client.send_message(
            ...     channel_id="123456789",
            ...     content="Hello Discord!"
            ... )
            >>> 
            >>> # Message with embed
            >>> embed = DiscordEmbed(
            ...     title="Alert!",
            ...     description="Something happened",
            ...     color=0xff0000
            ... )
            >>> msg = await client.send_message(
            ...     channel_id="123456789",
            ...     embed=embed
            ... )
        """
        if self.mock_mode:
            message = self._mock_message(channel_id, content)
            self._stats["messages_sent"] += 1
            return message
        
        payload: Dict[str, Any] = {}
        
        if content:
            payload["content"] = content
        
        # Handle embeds
        if embed:
            payload["embeds"] = [embed.model_dump(exclude_none=True)]
        elif embeds:
            payload["embeds"] = [e.model_dump(exclude_none=True) for e in embeds]
        
        # Handle reply
        if reply_to:
            payload["message_reference"] = {
                "message_id": reply_to
            }
        
        data = await self._api_call(
            "POST",
            f"/channels/{channel_id}/messages",
            json_data=payload
        )
        
        self._stats["messages_sent"] += 1
        
        return DiscordMessage(**data)
    
    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        embed: Optional[DiscordEmbed] = None
    ) -> DiscordMessage:
        """
        Edit a message.
        
        Args:
            channel_id: Channel ID
            message_id: Message ID to edit
            content: New message content
            embed: New embed
            
        Returns:
            Edited DiscordMessage
        """
        if self.mock_mode:
            return self._mock_message(channel_id, content)
        
        payload: Dict[str, Any] = {}
        
        if content is not None:
            payload["content"] = content
        
        if embed:
            payload["embeds"] = [embed.model_dump(exclude_none=True)]
        
        data = await self._api_call(
            "PATCH",
            f"/channels/{channel_id}/messages/{message_id}",
            json_data=payload
        )
        
        return DiscordMessage(**data)
    
    async def delete_message(
        self,
        channel_id: str,
        message_id: str
    ) -> None:
        """
        Delete a message.
        
        Args:
            channel_id: Channel ID
            message_id: Message ID to delete
        """
        if self.mock_mode:
            return
        
        await self._api_call(
            "DELETE",
            f"/channels/{channel_id}/messages/{message_id}"
        )
    
    # ============================================
    # REACTIONS
    # ============================================
    
    async def add_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> None:
        """
        Add a reaction to a message.
        
        Args:
            channel_id: Channel ID
            message_id: Message ID
            emoji: Emoji (e.g., "👍" or "custom_emoji:123456")
        """
        if self.mock_mode:
            return
        
        # URL encode emoji
        import urllib.parse
        emoji_encoded = urllib.parse.quote(emoji)
        
        await self._api_call(
            "PUT",
            f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_encoded}/@me"
        )
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_bot_user(self) -> DiscordUser:
        """Generate mock bot user."""
        return DiscordUser(
            id="987654321",
            username="SocialSpace Bot",
            discriminator="0001",
            bot=True
        )
    
    def _mock_guild(self) -> DiscordGuild:
        """Generate mock guild."""
        return DiscordGuild(
            id="111111111",
            name="SocialSpace Test Server",
            member_count=100
        )
    
    def _mock_channel(self, channel_id: str) -> DiscordChannel:
        """Generate mock channel."""
        return DiscordChannel(
            id=channel_id,
            type=0,  # Text channel
            name="general"
        )
    
    def _mock_message(
        self,
        channel_id: str,
        content: Optional[str] = None
    ) -> DiscordMessage:
        """Generate mock message."""
        return DiscordMessage(
            id=str(int(datetime.now().timestamp())),
            channel_id=channel_id,
            author=self._mock_bot_user(),
            content=content or "Mock message from SocialSpace! 🚀",
            timestamp=datetime.now().isoformat()
        )
    
    # ============================================
    # STATISTICS
    # ============================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "mock_mode": self.mock_mode,
        }

