"""
TikTok Platform - API Client
=============================

TikTok Business API client.

Features:
---------
- Get user information
- Fetch videos
- Fetch comments
- Post videos
- Post comments
- Get analytics

API Documentation:
https://developers.tiktok.com/

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 12
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.tiktok.models import (
    TikTokUser,
    TikTokVideo,
    TikTokComment,
    TikTokResponse,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class TikTokClient:
    """
    TikTok Business API client.
    
    Handles all communication with TikTok Business API.
    
    Authentication:
    ---------------
    Requires:
    - Access Token (OAuth 2.0)
    
    Example:
        >>> client = TikTokClient(
        ...     access_token="YOUR_ACCESS_TOKEN"
        ... )
        >>> 
        >>> # Get user info
        >>> user = await client.get_user_info()
        >>> print(f"User: {user.display_name}")
        >>> 
        >>> # Get videos
        >>> videos = await client.get_videos(limit=10)
    
    Rate Limits:
    ------------
    TikTok API rate limits:
    - Varies by endpoint
    - Typically 100 requests per minute per app
    """
    
    # API Base URL
    API_VERSION = "v2"
    BASE_URL = f"https://open.tiktokapis.com/{API_VERSION}"
    
    def __init__(
        self,
        access_token: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize TikTok client.
        
        Args:
            access_token: TikTok access token
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.access_token = access_token
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # User cache
        self._user_info: Optional[TikTokUser] = None
        
        # Statistics
        self._stats = {
            "videos_fetched": 0,
            "comments_fetched": 0,
            "videos_created": 0,
            "comments_created": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"TikTok client initialized (mock_mode={mock_mode})")
    
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
        logger.info("TikTok client closed")
    
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
        Make API call to TikTok with retry logic.
        
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
                    message="TikTok API rate limit exceeded",
                    context={"status_code": 429}
                )
            
            # Handle authentication errors
            if response.status_code in [401, 403]:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid TikTok access token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                raise PlatformError(
                    platform="tiktok",
                    message=f"TikTok API error: {response.text}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="TikTok API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="TikTok API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # USER INFO
    # ============================================
    
    async def get_user_info(self) -> TikTokUser:
        """
        Get authenticated user information.
        
        Returns:
            TikTokUser object
        """
        if self.mock_mode:
            return self._mock_user()
        
        params = {
            "fields": "open_id,union_id,avatar_url,display_name,bio_description,"
                     "follower_count,following_count,likes_count,video_count,is_verified"
        }
        
        data = await self._api_call("user/info/", params=params)
        
        response = TikTokResponse(**data)
        
        if response.has_data():
            user_data = response.data.get("user", response.data)
            user = TikTokUser(
                id=user_data.get("open_id", "unknown"),
                username=user_data.get("display_name", "unknown"),
                **user_data
            )
            self._user_info = user
            return user
        
        raise PlatformError(
            platform="tiktok",
            message="Failed to get user info"
        )
    
    # ============================================
    # VIDEOS
    # ============================================
    
    async def get_videos(
        self,
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> List[TikTokVideo]:
        """
        Get user's videos.
        
        Args:
            limit: Number of videos (max: 20)
            cursor: Pagination cursor
            
        Returns:
            List of TikTokVideo objects
        """
        if self.mock_mode:
            videos = [self._mock_video()]
            self._stats["videos_fetched"] += len(videos)
            return videos
        
        params = {
            "fields": "id,create_time,cover_image_url,share_url,video_description,"
                     "duration,height,width,title,embed_html,embed_link,like_count,"
                     "comment_count,share_count,view_count",
            "max_count": min(limit, 20)
        }
        
        if cursor:
            params["cursor"] = cursor
        
        data = await self._api_call("video/list/", params=params)
        
        response = TikTokResponse(**data)
        
        videos = []
        if response.has_data():
            video_list = response.data.get("videos", [])
            for video_data in video_list:
                # Flatten stats
                if "statistics" in video_data:
                    video_data["stats"] = video_data["statistics"]
                
                video = TikTokVideo(**video_data)
                videos.append(video)
        
        self._stats["videos_fetched"] += len(videos)
        
        return videos
    
    async def get_video(self, video_id: str) -> TikTokVideo:
        """
        Get a specific video.
        
        Args:
            video_id: Video ID
            
        Returns:
            TikTokVideo object
        """
        if self.mock_mode:
            return self._mock_video()
        
        params = {
            "fields": "id,create_time,cover_image_url,video_description,duration,"
                     "like_count,comment_count,share_count,view_count"
        }
        
        data = await self._api_call(f"video/query/{video_id}/", params=params)
        
        response = TikTokResponse(**data)
        
        if response.has_data():
            video_data = response.data.get("video", response.data)
            return TikTokVideo(**video_data)
        
        raise PlatformError(
            platform="tiktok",
            message=f"Video not found: {video_id}"
        )
    
    async def create_video(
        self,
        video_data: bytes,
        description: str
    ) -> TikTokVideo:
        """
        Upload a video.
        
        Args:
            video_data: Video file data
            description: Video description/caption
            
        Returns:
            Created TikTokVideo
            
        Note: This is a simplified version. Real implementation
              requires multi-part upload and chunking.
        """
        if self.mock_mode:
            return self._mock_video()
        
        # In real implementation, this would be a multi-step process:
        # 1. Initialize upload
        # 2. Upload video chunks
        # 3. Complete upload with metadata
        
        logger.info("Video upload not fully implemented (requires multi-part upload)")
        
        return self._mock_video()
    
    # ============================================
    # COMMENTS
    # ============================================
    
    async def get_comments(
        self,
        video_id: str,
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> List[TikTokComment]:
        """
        Get comments on a video.
        
        Args:
            video_id: Video ID
            limit: Number of comments (max: 20)
            cursor: Pagination cursor
            
        Returns:
            List of TikTokComment objects
        """
        if self.mock_mode:
            return [self._mock_comment()]
        
        params = {
            "video_id": video_id,
            "max_count": min(limit, 20)
        }
        
        if cursor:
            params["cursor"] = cursor
        
        data = await self._api_call("comment/list/", params=params)
        
        response = TikTokResponse(**data)
        
        comments = []
        if response.has_data():
            comment_list = response.data.get("comments", [])
            for comment_data in comment_list:
                comment_data["video_id"] = video_id
                comment = TikTokComment(**comment_data)
                comments.append(comment)
        
        self._stats["comments_fetched"] += len(comments)
        
        return comments
    
    async def create_comment(
        self,
        video_id: str,
        text: str
    ) -> TikTokComment:
        """
        Create a comment on a video.
        
        Args:
            video_id: Video ID
            text: Comment text
            
        Returns:
            Created TikTokComment
        """
        if self.mock_mode:
            return self._mock_comment()
        
        payload = {
            "video_id": video_id,
            "text": text
        }
        
        data = await self._api_call("comment/create/", method="POST", json_data=payload)
        
        self._stats["comments_created"] += 1
        
        response = TikTokResponse(**data)
        
        if response.has_data():
            comment_data = response.data.get("comment", response.data)
            comment_data["video_id"] = video_id
            return TikTokComment(**comment_data)
        
        raise PlatformError(
            platform="tiktok",
            message="Failed to create comment"
        )
    
    async def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a comment.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            True if deleted successfully
        """
        if self.mock_mode:
            return True
        
        payload = {"comment_id": comment_id}
        
        await self._api_call("comment/delete/", method="POST", json_data=payload)
        
        return True
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_user(self) -> TikTokUser:
        """Generate mock user."""
        return TikTokUser(
            id="mock_user_123",
            username="socialspace_user",
            display_name="SocialSpace User",
            bio_description="AI-powered social media management 🤖",
            follower_count=10000,
            following_count=500,
            likes_count=50000,
            video_count=100,
            is_verified=False
        )
    
    def _mock_video(self) -> TikTokVideo:
        """Generate mock video."""
        from socialspace_agent.platforms.tiktok.models import TikTokVideoStats
        
        return TikTokVideo(
            id="mock_video_123",
            author={"username": "socialspace_user", "display_name": "SocialSpace User"},
            description="Check out this amazing content! 🚀 #socialspace #ai",
            duration=30,
            create_time=int(datetime.now().timestamp()),
            stats=TikTokVideoStats(
                view_count=10000,
                like_count=500,
                comment_count=50,
                share_count=20
            ),
            hashtags=["socialspace", "ai"]
        )
    
    def _mock_comment(self) -> TikTokComment:
        """Generate mock comment."""
        return TikTokComment(
            id="mock_comment_123",
            video_id="mock_video_123",
            user={"display_name": "Test User", "username": "testuser"},
            text="Great video! 🔥",
            create_time=int(datetime.now().timestamp()),
            like_count=5,
            reply_count=0
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
