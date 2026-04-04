"""
Pinterest Platform - API Client
================================

Pinterest API client.

Features:
---------
- Get user information
- Fetch pins
- Create pins
- Manage boards
- Get analytics
- Search pins

API Documentation:
https://developers.pinterest.com/docs/

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 14 (FINAL SESSION!)
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.pinterest.models import (
    PinterestUser,
    PinterestBoard,
    PinterestPin,
    PinterestResponse,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class PinterestClient:
    """
    Pinterest API client.
    
    Handles all communication with Pinterest API.
    
    Authentication:
    ---------------
    Requires:
    - Access Token (OAuth 2.0)
    
    Example:
        >>> client = PinterestClient(
        ...     access_token="YOUR_ACCESS_TOKEN"
        ... )
        >>> 
        >>> # Get user info
        >>> user = await client.get_user_info()
        >>> print(f"User: {user.username}")
        >>> 
        >>> # Get boards
        >>> boards = await client.get_boards()
    
    Rate Limits:
    ------------
    Pinterest API rate limits:
    - 1000 calls per hour per access token
    - 200 calls per hour per IP address
    """
    
    # API Base URL
    API_VERSION = "v5"
    BASE_URL = f"https://api.pinterest.com/{API_VERSION}"
    
    def __init__(
        self,
        access_token: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Pinterest client.
        
        Args:
            access_token: Pinterest access token
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.access_token = access_token
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # User cache
        self._user_info: Optional[PinterestUser] = None
        
        # Statistics
        self._stats = {
            "pins_fetched": 0,
            "boards_fetched": 0,
            "pins_created": 0,
            "boards_created": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"Pinterest client initialized (mock_mode={mock_mode})")
    
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
                    "Content-Type": "application/json"
                }
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Pinterest client closed")
    
    # ============================================
    # API CALL WRAPPER
    # ============================================
    
    @async_retry_with_backoff(max_retries=3, base_delay=1.0)
    async def _api_call(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API call to Pinterest with retry logic.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, PATCH, DELETE)
            params: Query parameters
            json_data: JSON payload
            
        Returns:
            API response as dictionary
            
        Raises:
            AuthenticationError: On invalid token
            RateLimitError: On rate limit
            ServiceUnavailableError: On service issues
            PlatformError: On other errors
        """
        await self._ensure_client()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        self._stats["api_calls"] += 1
        
        logger.debug(f"API call: {method} {endpoint}")
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                self._stats["errors"] += 1
                raise RateLimitError(
                    message="Pinterest API rate limit exceeded",
                    context={"status_code": 429}
                )
            
            # Handle authentication errors
            if response.status_code in [401, 403]:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid Pinterest access token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                raise PlatformError(
                    platform="pinterest",
                    message=f"Pinterest API error: {response.text}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Pinterest API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Pinterest API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # USER INFO
    # ============================================
    
    async def get_user_info(self) -> PinterestUser:
        """
        Get authenticated user information.
        
        Returns:
            PinterestUser object
        """
        if self.mock_mode:
            return self._mock_user()
        
        data = await self._api_call("user_account")
        
        user = PinterestUser(**data)
        self._user_info = user
        
        return user
    
    # ============================================
    # BOARDS
    # ============================================
    
    async def get_boards(
        self,
        bookmark: Optional[str] = None,
        page_size: int = 25
    ) -> List[PinterestBoard]:
        """
        Get user's boards.
        
        Args:
            bookmark: Pagination bookmark
            page_size: Number of boards per page
            
        Returns:
            List of PinterestBoard objects
        """
        if self.mock_mode:
            return [self._mock_board()]
        
        params = {"page_size": page_size}
        if bookmark:
            params["bookmark"] = bookmark
        
        data = await self._api_call("boards", params=params)
        
        response = PinterestResponse(**data)
        
        boards = []
        if response.has_items():
            for board_data in response.items:
                board = PinterestBoard(**board_data)
                boards.append(board)
        
        self._stats["boards_fetched"] += len(boards)
        
        return boards
    
    async def get_board(self, board_id: str) -> PinterestBoard:
        """
        Get a specific board.
        
        Args:
            board_id: Board ID
            
        Returns:
            PinterestBoard object
        """
        if self.mock_mode:
            return self._mock_board()
        
        data = await self._api_call(f"boards/{board_id}")
        
        return PinterestBoard(**data)
    
    async def create_board(
        self,
        name: str,
        description: Optional[str] = None,
        privacy: str = "PUBLIC"
    ) -> PinterestBoard:
        """
        Create a new board.
        
        Args:
            name: Board name
            description: Board description
            privacy: Privacy setting (PUBLIC, PROTECTED, SECRET)
            
        Returns:
            Created PinterestBoard
        """
        if self.mock_mode:
            return self._mock_board()
        
        payload = {
            "name": name,
            "description": description,
            "privacy": privacy
        }
        
        data = await self._api_call("boards", method="POST", json_data=payload)
        
        self._stats["boards_created"] += 1
        
        return PinterestBoard(**data)
    
    # ============================================
    # PINS
    # ============================================
    
    async def get_pins(
        self,
        board_id: Optional[str] = None,
        bookmark: Optional[str] = None,
        page_size: int = 25
    ) -> List[PinterestPin]:
        """
        Get pins (from board or user).
        
        Args:
            board_id: Board ID (if None, gets user's pins)
            bookmark: Pagination bookmark
            page_size: Number of pins per page
            
        Returns:
            List of PinterestPin objects
        """
        if self.mock_mode:
            pins = [self._mock_pin()]
            self._stats["pins_fetched"] += len(pins)
            return pins
        
        params = {"page_size": page_size}
        if bookmark:
            params["bookmark"] = bookmark
        
        if board_id:
            endpoint = f"boards/{board_id}/pins"
        else:
            endpoint = "pins"
        
        data = await self._api_call(endpoint, params=params)
        
        response = PinterestResponse(**data)
        
        pins = []
        if response.has_items():
            for pin_data in response.items:
                pin = PinterestPin(**pin_data)
                pins.append(pin)
        
        self._stats["pins_fetched"] += len(pins)
        
        return pins
    
    async def get_pin(self, pin_id: str) -> PinterestPin:
        """
        Get a specific pin.
        
        Args:
            pin_id: Pin ID
            
        Returns:
            PinterestPin object
        """
        if self.mock_mode:
            return self._mock_pin()
        
        data = await self._api_call(f"pins/{pin_id}")
        
        return PinterestPin(**data)
    
    async def create_pin(
        self,
        board_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        link: Optional[str] = None,
        media_source: Optional[Dict[str, str]] = None
    ) -> PinterestPin:
        """
        Create a new pin.
        
        Args:
            board_id: Board ID
            title: Pin title
            description: Pin description
            link: Destination link
            media_source: Media source (url or base64)
            
        Returns:
            Created PinterestPin
        """
        if self.mock_mode:
            return self._mock_pin()
        
        payload = {
            "board_id": board_id,
            "title": title,
            "description": description,
            "link": link,
            "media_source": media_source
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        data = await self._api_call("pins", method="POST", json_data=payload)
        
        self._stats["pins_created"] += 1
        
        return PinterestPin(**data)
    
    async def delete_pin(self, pin_id: str) -> bool:
        """
        Delete a pin.
        
        Args:
            pin_id: Pin ID
            
        Returns:
            True if deleted successfully
        """
        if self.mock_mode:
            return True
        
        await self._api_call(f"pins/{pin_id}", method="DELETE")
        
        return True
    
    # ============================================
    # SEARCH
    # ============================================
    
    async def search_pins(
        self,
        query: str,
        bookmark: Optional[str] = None,
        page_size: int = 25
    ) -> List[PinterestPin]:
        """
        Search for pins.
        
        Args:
            query: Search query
            bookmark: Pagination bookmark
            page_size: Number of results
            
        Returns:
            List of PinterestPin objects
        """
        if self.mock_mode:
            return [self._mock_pin()]
        
        params = {
            "query": query,
            "page_size": page_size
        }
        if bookmark:
            params["bookmark"] = bookmark
        
        data = await self._api_call("search/pins", params=params)
        
        response = PinterestResponse(**data)
        
        pins = []
        if response.has_items():
            for pin_data in response.items:
                pin = PinterestPin(**pin_data)
                pins.append(pin)
        
        return pins
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_user(self) -> PinterestUser:
        """Generate mock user."""
        return PinterestUser(
            id="mock_user_123",
            username="socialspace_pin",
            first_name="SocialSpace",
            last_name="User",
            bio="AI-powered social media management 📌",
            pin_count=100,
            board_count=10,
            follower_count=1000,
            following_count=500
        )
    
    def _mock_board(self) -> PinterestBoard:
        """Generate mock board."""
        return PinterestBoard(
            id="board_123",
            name="SocialSpace Ideas",
            description="Inspiration for social media management",
            owner={"username": "socialspace_pin"},
            privacy="PUBLIC",
            pin_count=50,
            follower_count=100
        )
    
    def _mock_pin(self) -> PinterestPin:
        """Generate mock pin."""
        from socialspace_agent.platforms.pinterest.models import PinterestMedia
        
        return PinterestPin(
            id="pin_123",
            title="Amazing Social Media Strategy",
            description="Check out this great strategy for managing social media! 📌",
            link="https://example.com",
            media=PinterestMedia(
                media_type="image",
                images={"original": {"url": "https://example.com/image.jpg"}}
            ),
            board_id="board_123",
            save_count=42,
            comment_count=5,
            created_at=datetime.now().isoformat()
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
