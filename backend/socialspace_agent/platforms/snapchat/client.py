"""
Snapchat Platform - API Client
===============================

Snap Kit API client.

Features:
---------
- Get user information
- Fetch snaps
- Fetch stories
- Create stories
- Get Bitmoji data
- Creative Kit integration

API Documentation:
https://kit.snapchat.com/docs

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 13
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.snapchat.models import (
    SnapchatUser,
    SnapchatSnap,
    SnapchatStory,
    SnapchatSpotlight,
    SnapchatBitmoji,
    SnapchatResponse,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class SnapchatClient:
    """
    Snap Kit API client.
    
    Handles all communication with Snapchat Snap Kit API.
    
    Authentication:
    ---------------
    Requires:
    - Access Token (OAuth 2.0)
    
    Example:
        >>> client = SnapchatClient(
        ...     access_token="YOUR_ACCESS_TOKEN"
        ... )
        >>> 
        >>> # Get user info
        >>> user = await client.get_user_info()
        >>> print(f"User: {user.display_name}")
        >>> 
        >>> # Get stories
        >>> stories = await client.get_stories()
    
    Rate Limits:
    ------------
    Snapchat API rate limits:
    - Varies by endpoint
    - Generally lenient for Snap Kit
    """
    
    # API Base URL
    BASE_URL = "https://kit.snapchat.com/v1"
    
    def __init__(
        self,
        access_token: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Snapchat client.
        
        Args:
            access_token: Snapchat access token
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.access_token = access_token
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # User cache
        self._user_info: Optional[SnapchatUser] = None
        
        # Statistics
        self._stats = {
            "stories_fetched": 0,
            "snaps_fetched": 0,
            "stories_created": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"Snapchat client initialized (mock_mode={mock_mode})")
    
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
        logger.info("Snapchat client closed")
    
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
        Make API call to Snapchat with retry logic.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, DELETE)
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
                    message="Snapchat API rate limit exceeded",
                    context={"status_code": 429}
                )
            
            # Handle authentication errors
            if response.status_code in [401, 403]:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid Snapchat access token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                raise PlatformError(
                    platform="snapchat",
                    message=f"Snapchat API error: {response.text}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Snapchat API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Snapchat API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # USER INFO
    # ============================================
    
    async def get_user_info(self) -> SnapchatUser:
        """
        Get authenticated user information.
        
        Returns:
            SnapchatUser object
        """
        if self.mock_mode:
            return self._mock_user()
        
        data = await self._api_call("me")
        
        response = SnapchatResponse(**data)
        
        if response.has_data():
            user_data = response.data
            user = SnapchatUser(
                id=user_data.get("id", "unknown"),
                username=user_data.get("username", "unknown"),
                display_name=user_data.get("display_name", "unknown"),
                bitmoji_avatar_id=user_data.get("bitmoji", {}).get("avatar_id")
            )
            self._user_info = user
            return user
        
        raise PlatformError(
            platform="snapchat",
            message="Failed to get user info"
        )
    
    # ============================================
    # BITMOJI
    # ============================================
    
    async def get_bitmoji(self) -> SnapchatBitmoji:
        """
        Get user's Bitmoji.
        
        Returns:
            SnapchatBitmoji object
        """
        if self.mock_mode:
            return self._mock_bitmoji()
        
        data = await self._api_call("me/bitmoji")
        
        response = SnapchatResponse(**data)
        
        if response.has_data():
            return SnapchatBitmoji(**response.data)
        
        raise PlatformError(
            platform="snapchat",
            message="Failed to get Bitmoji"
        )
    
    # ============================================
    # STORIES
    # ============================================
    
    async def get_stories(self) -> List[SnapchatStory]:
        """
        Get user's stories.
        
        Returns:
            List of SnapchatStory objects
        """
        if self.mock_mode:
            stories = [self._mock_story()]
            self._stats["stories_fetched"] += len(stories)
            return stories
        
        data = await self._api_call("me/stories")
        
        response = SnapchatResponse(**data)
        
        stories = []
        if response.has_data():
            story_list = response.data if isinstance(response.data, list) else [response.data]
            
            for story_data in story_list:
                story = SnapchatStory(**story_data)
                stories.append(story)
        
        self._stats["stories_fetched"] += len(stories)
        
        return stories
    
    async def create_story(
        self,
        media_url: str,
        media_type: str = "IMAGE"
    ) -> SnapchatStory:
        """
        Create a story.
        
        Args:
            media_url: Media URL
            media_type: Media type (IMAGE, VIDEO)
            
        Returns:
            Created SnapchatStory
            
        Note: Real implementation requires Creative Kit integration
        """
        if self.mock_mode:
            return self._mock_story()
        
        payload = {
            "media_url": media_url,
            "media_type": media_type
        }
        
        data = await self._api_call("me/stories", method="POST", json_data=payload)
        
        self._stats["stories_created"] += 1
        
        response = SnapchatResponse(**data)
        
        if response.has_data():
            return SnapchatStory(**response.data)
        
        raise PlatformError(
            platform="snapchat",
            message="Failed to create story"
        )
    
    # ============================================
    # SNAPS
    # ============================================
    
    async def get_snaps(self) -> List[SnapchatSnap]:
        """
        Get user's snaps.
        
        Returns:
            List of SnapchatSnap objects
            
        Note: Limited by Snapchat's ephemeral nature
        """
        if self.mock_mode:
            return [self._mock_snap()]
        
        data = await self._api_call("me/snaps")
        
        response = SnapchatResponse(**data)
        
        snaps = []
        if response.has_data():
            snap_list = response.data if isinstance(response.data, list) else [response.data]
            
            for snap_data in snap_list:
                snap = SnapchatSnap(**snap_data)
                snaps.append(snap)
        
        self._stats["snaps_fetched"] += len(snaps)
        
        return snaps
    
    # ============================================
    # SPOTLIGHT
    # ============================================
    
    async def get_spotlight_videos(self, limit: int = 20) -> List[SnapchatSpotlight]:
        """
        Get Spotlight videos.
        
        Args:
            limit: Number of videos
            
        Returns:
            List of SnapchatSpotlight objects
        """
        if self.mock_mode:
            return [self._mock_spotlight()]
        
        params = {"limit": limit}
        
        data = await self._api_call("spotlight", params=params)
        
        response = SnapchatResponse(**data)
        
        spotlights = []
        if response.has_data():
            spotlight_list = response.data if isinstance(response.data, list) else [response.data]
            
            for spotlight_data in spotlight_list:
                spotlight = SnapchatSpotlight(**spotlight_data)
                spotlights.append(spotlight)
        
        return spotlights
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_user(self) -> SnapchatUser:
        """Generate mock user."""
        return SnapchatUser(
            id="mock_user_123",
            username="socialspace_snap",
            display_name="SocialSpace User",
            bitmoji_avatar_id="avatar_123"
        )
    
    def _mock_bitmoji(self) -> SnapchatBitmoji:
        """Generate mock Bitmoji."""
        return SnapchatBitmoji(
            avatar_id="avatar_123",
            avatar_url="https://example.com/bitmoji.png",
            background_color="#FFFFFF"
        )
    
    def _mock_story(self) -> SnapchatStory:
        """Generate mock story."""
        now = datetime.now().isoformat()
        return SnapchatStory(
            id="story_123",
            username="socialspace_snap",
            media_url="https://example.com/story.jpg",
            media_type="IMAGE",
            created_at=now,
            expires_at=now,
            view_count=100
        )
    
    def _mock_snap(self) -> SnapchatSnap:
        """Generate mock snap."""
        return SnapchatSnap(
            id="snap_123",
            media_url="https://example.com/snap.jpg",
            media_type="IMAGE",
            duration=10,
            created_at=datetime.now().isoformat(),
            is_opened=False
        )
    
    def _mock_spotlight(self) -> SnapchatSpotlight:
        """Generate mock Spotlight."""
        return SnapchatSpotlight(
            id="spotlight_123",
            username="socialspace_snap",
            media_url="https://example.com/spotlight.mp4",
            thumbnail_url="https://example.com/spotlight_thumb.jpg",
            caption="Check this out! 👻",
            duration=15,
            created_at=datetime.now().isoformat(),
            view_count=10000,
            like_count=500
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
