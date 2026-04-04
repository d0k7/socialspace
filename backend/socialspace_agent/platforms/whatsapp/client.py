"""
WhatsApp Platform - API Client
===============================

Low-level WhatsApp Business API client.

Features:
---------
- Send messages (text, media, location)
- Fetch messages
- Download media
- Manage templates
- Handle webhooks

API Documentation:
https://developers.facebook.com/docs/whatsapp/cloud-api

Author: Dheeraj Mishra
Created: February 19, 2026
Session: 3
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.whatsapp.models import (
    WhatsAppMessage,
    WhatsAppSendResponse,
    WhatsAppError,
)
from socialspace_agent.exceptions import (
    WhatsAppError as WhatsAppException,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """
    WhatsApp Business API client.
    
    Handles all communication with WhatsApp Cloud API.
    
    Authentication:
    ---------------
    Requires:
    - Access Token (from Meta Business Account)
    - Phone Number ID (your WhatsApp Business phone number)
    
    Example:
        >>> client = WhatsAppClient(
        ...     access_token="YOUR_ACCESS_TOKEN",
        ...     phone_number_id="YOUR_PHONE_NUMBER_ID"
        ... )
        >>> 
        >>> # Send a message
        >>> response = await client.send_text_message(
        ...     to="919876543210",
        ...     text="Hello from SocialSpace!"
        ... )
        >>> print(response.get_message_id())
    
    Rate Limits:
    ------------
    WhatsApp Cloud API has the following limits:
    - 1000 messages per second (business verification required)
    - 250,000 messages per day (higher limits available)
    - 100 API calls per second
    """
    
    # API Base URL
    API_VERSION = "v21.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
    
    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize WhatsApp client.
        
        Args:
            access_token: WhatsApp Business API access token
            phone_number_id: Your WhatsApp Business phone number ID
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(
            f"WhatsApp client initialized "
            f"(phone_number_id={phone_number_id[:8]}..., mock_mode={mock_mode})"
        )
    
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
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                }
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("WhatsApp client closed")
    
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
        Make API call to WhatsApp with retry logic.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (e.g., "/messages")
            json_data: JSON payload (for POST/PUT)
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            WhatsAppException: On API errors
            RateLimitError: On rate limit
            ServiceUnavailableError: On service issues
        """
        await self._ensure_client()
        
        url = f"{self.BASE_URL}/{self.phone_number_id}{endpoint}"
        
        self._stats["api_calls"] += 1
        
        logger.debug(f"API call: {method} {url}")
        
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
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    message="WhatsApp API rate limit exceeded",
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid WhatsApp access token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json()
                
                # Parse WhatsApp error
                if "error" in error_data:
                    error = WhatsAppError(**error_data["error"])
                    raise WhatsAppException(
                        message=f"WhatsApp API error: {error.message}",
                        context={
                            "code": error.code,
                            "type": error.type,
                            "fbtrace_id": error.fbtrace_id
                        }
                    )
                
                raise WhatsAppException(
                    message=f"WhatsApp API error: {response.text}",
                    context={"status_code": response.status_code}
                )
            
            return response.json()
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="WhatsApp API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="WhatsApp API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # SEND MESSAGES
    # ============================================
    
    async def send_text_message(
        self,
        to: str,
        text: str,
        preview_url: bool = False
    ) -> WhatsAppSendResponse:
        """
        Send a text message.
        
        Args:
            to: Recipient phone number (with country code, no +)
            text: Message text (max 4096 characters)
            preview_url: Enable URL preview (default: False)
            
        Returns:
            WhatsAppSendResponse with message ID
            
        Example:
            >>> response = await client.send_text_message(
            ...     to="919876543210",
            ...     text="Hello! This is a test message."
            ... )
            >>> print(f"Message sent: {response.get_message_id()}")
        """
        if self.mock_mode:
            return self._mock_send_response()
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": text,
                "preview_url": preview_url
            }
        }
        
        response_data = await self._api_call("POST", "/messages", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return WhatsAppSendResponse(**response_data)
    
    async def send_media_message(
        self,
        to: str,
        media_type: str,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None
    ) -> WhatsAppSendResponse:
        """
        Send a media message (image, video, audio, document).
        
        Args:
            to: Recipient phone number
            media_type: Type of media (image, video, audio, document)
            media_id: WhatsApp media ID (from upload)
            media_link: Public URL to media (alternative to media_id)
            caption: Optional caption for image/video/document
            
        Returns:
            WhatsAppSendResponse with message ID
            
        Note:
            Either media_id OR media_link must be provided.
            
        Example:
            >>> # Using media ID (uploaded media)
            >>> response = await client.send_media_message(
            ...     to="919876543210",
            ...     media_type="image",
            ...     media_id="123456789",
            ...     caption="Check this out!"
            ... )
            
            >>> # Using public URL
            >>> response = await client.send_media_message(
            ...     to="919876543210",
            ...     media_type="image",
            ...     media_link="https://example.com/image.jpg",
            ...     caption="Beautiful!"
            ... )
        """
        if self.mock_mode:
            return self._mock_send_response()
        
        if not media_id and not media_link:
            raise ValueError("Either media_id or media_link must be provided")
        
        media_object = {}
        if media_id:
            media_object["id"] = media_id
        elif media_link:
            media_object["link"] = media_link
        
        if caption:
            media_object["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": media_type,
            media_type: media_object
        }
        
        response_data = await self._api_call("POST", "/messages", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return WhatsAppSendResponse(**response_data)
    
    async def send_location_message(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None
    ) -> WhatsAppSendResponse:
        """
        Send a location message.
        
        Args:
            to: Recipient phone number
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            name: Location name (optional)
            address: Location address (optional)
            
        Returns:
            WhatsAppSendResponse with message ID
        """
        if self.mock_mode:
            return self._mock_send_response()
        
        location_obj = {
            "latitude": latitude,
            "longitude": longitude
        }
        
        if name:
            location_obj["name"] = name
        if address:
            location_obj["address"] = address
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "location",
            "location": location_obj
        }
        
        response_data = await self._api_call("POST", "/messages", json_data=payload)
        
        self._stats["messages_sent"] += 1
        
        return WhatsAppSendResponse(**response_data)
    
    # ============================================
    # MEDIA MANAGEMENT
    # ============================================
    
    async def download_media(self, media_id: str) -> bytes:
        """
        Download media file from WhatsApp.
        
        Args:
            media_id: WhatsApp media ID
            
        Returns:
            Media file content as bytes
            
        Example:
            >>> # Get media from incoming message
            >>> message = ...  # WhatsAppMessage with image
            >>> media_id = message.image.id
            >>> 
            >>> # Download the media
            >>> media_bytes = await client.download_media(media_id)
            >>> 
            >>> # Save to file
            >>> with open("image.jpg", "wb") as f:
            ...     f.write(media_bytes)
        """
        if self.mock_mode:
            return b"mock_media_data"
        
        # Step 1: Get media URL
        url = f"{self.BASE_URL}/{media_id}"
        response = await self._client.get(url)
        
        if response.status_code != 200:
            raise WhatsAppException(
                message=f"Failed to get media URL: {response.text}"
            )
        
        media_info = response.json()
        media_url = media_info.get("url")
        
        if not media_url:
            raise WhatsAppException(
                message="No URL in media response"
            )
        
        # Step 2: Download media from URL
        media_response = await self._client.get(media_url)
        
        if media_response.status_code != 200:
            raise WhatsAppException(
                message=f"Failed to download media: {media_response.text}"
            )
        
        return media_response.content
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_send_response(self) -> WhatsAppSendResponse:
        """Generate mock send response."""
        self._stats["messages_sent"] += 1
        return WhatsAppSendResponse(
            messaging_product="whatsapp",
            contacts=[{"input": "919876543210", "wa_id": "919876543210"}],
            messages=[{"id": f"wamid.mock_{datetime.now().timestamp()}"}]
        )
    
    # ============================================
    # STATISTICS
    # ============================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with usage stats
        """
        return {
            **self._stats,
            "phone_number_id": self.phone_number_id[:8] + "...",
            "mock_mode": self.mock_mode,
        }
