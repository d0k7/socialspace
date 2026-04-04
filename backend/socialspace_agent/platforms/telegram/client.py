"""
Telegram Platform - API Client
===============================

Low-level Telegram Bot API client.

Features:
---------
- Send messages (text, media, location)
- Receive updates (polling or webhook)
- Download files
- Manage bot commands

API Documentation:
https://core.telegram.org/bots/api

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 4
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.telegram.models import (
    TelegramMessage,
    TelegramUpdate,
    TelegramResponse,
    TelegramSendMessageResponse,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class TelegramClient:
    """
    Telegram Bot API client.
    
    Handles all communication with Telegram Bot API.
    
    Authentication:
    ---------------
    Requires:
    - Bot Token (from @BotFather)
    
    Example:
        >>> client = TelegramClient(bot_token="123456:ABC-DEF...")
        >>> 
        >>> # Send a message
        >>> response = await client.send_message(
        ...     chat_id=123456789,
        ...     text="Hello from SocialSpace!"
        ... )
        >>> print(response.message_id)
    
    Rate Limits:
    ------------
    Telegram Bot API has the following limits:
    - 30 messages per second to all chats
    - 20 messages per minute to the same group
    - No limit for private chats
    """
    
    # API Base URL
    BASE_URL = "https://api.telegram.org"
    
    def __init__(
        self,
        bot_token: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Telegram client.
        
        Args:
            bot_token: Telegram bot token from @BotFather
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.bot_token = bot_token
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # Build API URL
        self.api_url = f"{self.BASE_URL}/bot{bot_token}"
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Polling state
        self._last_update_id: int = 0
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"Telegram client initialized (mock_mode={mock_mode})")
    
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
                headers={"Content-Type": "application/json"}
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Telegram client closed")
    
    # ============================================
    # API CALL WRAPPER
    # ============================================
    
    @async_retry_with_backoff(max_retries=3, base_delay=1.0)
    async def _api_call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API call to Telegram with retry logic.
        
        Args:
            method: API method name (e.g., "sendMessage")
            params: Query parameters
            json_data: JSON payload
            
        Returns:
            API response result
            
        Raises:
            AuthenticationError: On invalid bot token
            RateLimitError: On rate limit
            ServiceUnavailableError: On service issues
            PlatformError: On other API errors
        """
        await self._ensure_client()
        
        url = f"{self.api_url}/{method}"
        
        self._stats["api_calls"] += 1
        
        logger.debug(f"API call: {method}")
        
        try:
            response = await self._client.post(
                url=url,
                params=params,
                json=json_data
            )
            
            # Parse response
            data = response.json()
            telegram_response = TelegramResponse(**data)
            
            # Check if request was successful
            if not telegram_response.ok:
                self._stats["errors"] += 1
                
                # Handle specific errors
                if telegram_response.error_code == 401:
                    raise AuthenticationError(
                        "Invalid Telegram bot token",
                        context={"description": telegram_response.description}
                    )
                
                elif telegram_response.error_code == 429:
                    raise RateLimitError(
                        message="Telegram API rate limit exceeded",
                        context={"description": telegram_response.description}
                    )
                
                else:
                    raise PlatformError(
                        platform="telegram",
                        message=f"Telegram API error: {telegram_response.description}",
                        context={"error_code": telegram_response.error_code}
                    )
            
            return telegram_response.result
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Telegram API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Telegram API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # BOT INFORMATION
    # ============================================
    
    async def get_me(self) -> Dict[str, Any]:
        """
        Get bot information.
        
        Returns:
            Bot information (id, username, first_name, etc.)
            
        Example:
            >>> bot_info = await client.get_me()
            >>> print(f"Bot username: @{bot_info['username']}")
        """
        if self.mock_mode:
            return {
                "id": 123456789,
                "is_bot": True,
                "first_name": "SocialSpace Bot",
                "username": "socialspace_bot"
            }
        
        return await self._api_call("getMe")
    
    # ============================================
    # RECEIVE UPDATES
    # ============================================
    
    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 0
    ) -> List[TelegramUpdate]:
        """
        Get updates using long polling.
        
        Args:
            offset: Identifier of first update to return
            limit: Maximum number of updates (1-100, default: 100)
            timeout: Long polling timeout in seconds (default: 0)
            
        Returns:
            List of TelegramUpdate objects
            
        Example:
            >>> # Get new updates
            >>> updates = await client.get_updates()
            >>> for update in updates:
            ...     message = update.get_message()
            ...     if message:
            ...         print(f"New message: {message.text}")
        """
        if self.mock_mode:
            return []
        
        params = {
            "limit": limit,
            "timeout": timeout
        }
        
        if offset is not None:
            params["offset"] = offset
        elif self._last_update_id > 0:
            params["offset"] = self._last_update_id + 1
        
        result = await self._api_call("getUpdates", params=params)
        
        updates = []
        for update_data in result:
            update = TelegramUpdate(**update_data)
            updates.append(update)
            
            # Track last update ID
            if update.update_id > self._last_update_id:
                self._last_update_id = update.update_id
        
        self._stats["messages_received"] += len(updates)
        
        return updates
    
    # ============================================
    # SEND MESSAGES
    # ============================================
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_to_message_id: Optional[int] = None
    ) -> TelegramSendMessageResponse:
        """
        Send a text message.
        
        Args:
            chat_id: Unique identifier for the target chat
            text: Text of the message (1-4096 characters)
            parse_mode: Parse mode (Markdown, MarkdownV2, HTML)
            reply_to_message_id: If the message is a reply, ID of the original
            
        Returns:
            TelegramSendMessageResponse with message info
            
        Example:
            >>> response = await client.send_message(
            ...     chat_id=123456789,
            ...     text="Hello! *This is bold*",
            ...     parse_mode="Markdown"
            ... )
            >>> print(f"Message sent with ID: {response.message_id}")
        """
        if self.mock_mode:
            return self._mock_send_response(chat_id, text)
        
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        
        result = await self._api_call("sendMessage", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return TelegramSendMessageResponse(**result)
    
    async def send_photo(
        self,
        chat_id: int,
        photo: str,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> TelegramSendMessageResponse:
        """
        Send a photo.
        
        Args:
            chat_id: Unique identifier for the target chat
            photo: Photo to send (file_id or URL)
            caption: Photo caption (0-1024 characters)
            parse_mode: Parse mode for caption
            
        Returns:
            TelegramSendMessageResponse
        """
        if self.mock_mode:
            return self._mock_send_response(chat_id, caption or "Photo")
        
        payload = {
            "chat_id": chat_id,
            "photo": photo
        }
        
        if caption:
            payload["caption"] = caption
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        result = await self._api_call("sendPhoto", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return TelegramSendMessageResponse(**result)
    
    async def send_video(
        self,
        chat_id: int,
        video: str,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> TelegramSendMessageResponse:
        """Send a video."""
        if self.mock_mode:
            return self._mock_send_response(chat_id, caption or "Video")
        
        payload = {
            "chat_id": chat_id,
            "video": video
        }
        
        if caption:
            payload["caption"] = caption
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        result = await self._api_call("sendVideo", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return TelegramSendMessageResponse(**result)
    
    async def send_audio(
        self,
        chat_id: int,
        audio: str,
        caption: Optional[str] = None
    ) -> TelegramSendMessageResponse:
        """Send an audio file."""
        if self.mock_mode:
            return self._mock_send_response(chat_id, caption or "Audio")
        
        payload = {
            "chat_id": chat_id,
            "audio": audio
        }
        
        if caption:
            payload["caption"] = caption
        
        result = await self._api_call("sendAudio", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return TelegramSendMessageResponse(**result)
    
    async def send_document(
        self,
        chat_id: int,
        document: str,
        caption: Optional[str] = None
    ) -> TelegramSendMessageResponse:
        """Send a document."""
        if self.mock_mode:
            return self._mock_send_response(chat_id, caption or "Document")
        
        payload = {
            "chat_id": chat_id,
            "document": document
        }
        
        if caption:
            payload["caption"] = caption
        
        result = await self._api_call("sendDocument", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return TelegramSendMessageResponse(**result)
    
    async def send_location(
        self,
        chat_id: int,
        latitude: float,
        longitude: float
    ) -> TelegramSendMessageResponse:
        """Send a location."""
        if self.mock_mode:
            return self._mock_send_response(chat_id, "Location")
        
        payload = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude
        }
        
        result = await self._api_call("sendLocation", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return TelegramSendMessageResponse(**result)
    
    # ============================================
    # FILE MANAGEMENT
    # ============================================
    
    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            file_id: Telegram file ID
            
        Returns:
            File information with file_path
        """
        if self.mock_mode:
            return {
                "file_id": file_id,
                "file_path": f"mock/path/{file_id}"
            }
        
        return await self._api_call("getFile", json_data={"file_id": file_id})
    
    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file.
        
        Args:
            file_path: File path from getFile
            
        Returns:
            File content as bytes
        """
        if self.mock_mode:
            return b"mock_file_data"
        
        await self._ensure_client()
        
        url = f"{self.BASE_URL}/file/bot{self.bot_token}/{file_path}"
        
        response = await self._client.get(url)
        
        if response.status_code != 200:
            raise PlatformError(
                platform="telegram",
                message=f"Failed to download file: {response.text}"
            )
        
        return response.content
    
    # ============================================
    # MOCK RESPONSES
    # ============================================
    
    def _mock_send_response(
        self,
        chat_id: int,
        text: str
    ) -> TelegramSendMessageResponse:
        """Generate mock send response."""
        from socialspace_agent.platforms.telegram.models import TelegramChat
        
        # Keep stats behavior consistent between mock and real API paths.
        self._stats["messages_sent"] += 1
        
        return TelegramSendMessageResponse(
            message_id=int(datetime.now().timestamp()),
            date=int(datetime.now().timestamp()),
            chat=TelegramChat(
                id=chat_id,
                type="private",
                first_name="Test User"
            ),
            text=text
        )
    
    # ============================================
    # STATISTICS
    # ============================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "last_update_id": self._last_update_id,
            "mock_mode": self.mock_mode,
        }
