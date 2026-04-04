"""
YouTube Platform - API Client
==============================

YouTube Data API v3 client.

Features:
---------
- Get video information
- Fetch comments on videos
- Post comments
- Reply to comments
- Get channel information
- Search videos
- Quota management

API Documentation:
https://developers.google.com/youtube/v3

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 9
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.youtube.models import (
    YouTubeVideo,
    YouTubeComment,
    YouTubeCommentThread,
    YouTubeChannel,
    YouTubeResponse,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class YouTubeClient:
    """
    YouTube Data API v3 client.
    
    Handles all communication with YouTube Data API.
    
    Authentication:
    ---------------
    Requires:
    - API Key (from Google Cloud Console)
    
    Example:
        >>> client = YouTubeClient(api_key="YOUR_API_KEY")
        >>> 
        >>> # Get video information
        >>> video = await client.get_video("dQw4w9WgXcQ")
        >>> print(f"Title: {video.get_title()}")
        >>> 
        >>> # Get comments on video
        >>> comments = await client.get_video_comments(
        ...     video_id="dQw4w9WgXcQ",
        ...     max_results=100
        ... )
    
    Rate Limits (Quota):
    --------------------
    YouTube API uses quota system (10,000 units/day FREE):
    - Read video: 1 unit
    - Read comment: 1 unit
    - Post comment: 50 units
    - Delete comment: 50 units
    
    Example daily usage:
    - 200 comments posted = 10,000 units (max)
    - 10,000 reads = 10,000 units
    - Mix: 100 comments + 5,000 reads = 10,000 units
    """
    
    # API Base URL
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize YouTube client.
        
        Args:
            api_key: YouTube Data API key
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Quota tracking
        self._quota_used = 0
        self._daily_quota_limit = 10000
        
        # Statistics
        self._stats = {
            "videos_fetched": 0,
            "comments_fetched": 0,
            "comments_posted": 0,
            "api_calls": 0,
            "quota_used": 0,
            "errors": 0,
        }
        
        logger.info(f"YouTube client initialized (mock_mode={mock_mode})")
    
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
                headers={"Accept": "application/json"}
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("YouTube client closed")
    
    # ============================================
    # API CALL WRAPPER
    # ============================================
    
    @async_retry_with_backoff(max_retries=3, base_delay=1.0)
    async def _api_call(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        json_data: Optional[Dict[str, Any]] = None,
        quota_cost: int = 1
    ) -> Dict[str, Any]:
        """
        Make API call to YouTube with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., "videos")
            params: Query parameters
            method: HTTP method (GET, POST, DELETE)
            json_data: JSON payload (for POST)
            quota_cost: Quota units consumed by this call
            
        Returns:
            API response as dictionary
            
        Raises:
            AuthenticationError: On invalid API key
            RateLimitError: On quota exceeded
            ServiceUnavailableError: On service issues
            PlatformError: On other errors
        """
        await self._ensure_client()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        params["key"] = self.api_key
        
        self._track_api_usage(quota_cost)
        
        logger.debug(f"API call: {method} {endpoint} (quota: {quota_cost})")
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data
            )
            
            # Handle authentication errors
            if response.status_code == 403:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "API key invalid")
                
                # Check if it's quota exceeded
                if "quota" in error_msg.lower():
                    raise RateLimitError(
                        message="YouTube API quota exceeded",
                        context={"quota_used": self._quota_used}
                    )
                
                raise AuthenticationError(f"Invalid YouTube API key: {error_msg}")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                raise PlatformError(
                    platform="youtube",
                    message=f"YouTube API error: {response.text}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="YouTube API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="YouTube API",
                message=f"Network error: {e}"
            )

    def _track_api_usage(self, quota_cost: int) -> None:
        """Track API usage statistics and quota consumption."""
        self._stats["api_calls"] += 1
        self._quota_used += quota_cost
        self._stats["quota_used"] += quota_cost
    
    # ============================================
    # VIDEOS
    # ============================================
    
    async def get_video(self, video_id: str) -> YouTubeVideo:
        """
        Get video information.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            YouTubeVideo object
            
        Quota cost: 1 unit
            
        Example:
            >>> video = await client.get_video("dQw4w9WgXcQ")
            >>> print(f"Title: {video.get_title()}")
            >>> print(f"Views: {video.statistics.get_views()}")
        """
        if self.mock_mode:
            self._track_api_usage(1)
            video = self._mock_video(video_id)
            self._stats["videos_fetched"] += 1
            return video
        
        params = {
            "part": "snippet,statistics",
            "id": video_id
        }
        
        data = await self._api_call("videos", params=params, quota_cost=1)
        
        response = YouTubeResponse(**data)
        
        if response.has_items():
            video_data = response.items[0]
            self._stats["videos_fetched"] += 1
            return YouTubeVideo(**video_data)
        
        raise PlatformError(
            platform="youtube",
            message=f"Video not found: {video_id}"
        )
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 10
    ) -> List[YouTubeVideo]:
        """
        Search for videos.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-50)
            
        Returns:
            List of YouTubeVideo objects
            
        Quota cost: 100 units
        """
        if self.mock_mode:
            self._track_api_usage(100)
            videos = [self._mock_video("search_result")]
            self._stats["videos_fetched"] += len(videos)
            return videos
        
        # Search for video IDs
        search_params = {
            "part": "id",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50)
        }
        
        search_data = await self._api_call("search", params=search_params, quota_cost=100)
        search_response = YouTubeResponse(**search_data)
        
        if not search_response.has_items():
            return []
        
        # Extract video IDs
        video_ids = [item["id"]["videoId"] for item in search_response.items]
        
        # Get full video details
        videos_params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids)
        }
        
        videos_data = await self._api_call("videos", params=videos_params, quota_cost=1)
        videos_response = YouTubeResponse(**videos_data)
        
        videos = []
        if videos_response.has_items():
            for video_data in videos_response.items:
                video = YouTubeVideo(**video_data)
                videos.append(video)
        
        self._stats["videos_fetched"] += len(videos)
        
        return videos
    
    # ============================================
    # COMMENTS
    # ============================================
    
    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100,
        page_token: Optional[str] = None
    ) -> List[YouTubeComment]:
        """
        Get comments on a video.
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments (1-100)
            page_token: Page token for pagination
            
        Returns:
            List of YouTubeComment objects
            
        Quota cost: 1 unit
            
        Example:
            >>> comments = await client.get_video_comments(
            ...     video_id="dQw4w9WgXcQ",
            ...     max_results=50
            ... )
            >>> for comment in comments:
            ...     print(f"{comment.get_author()}: {comment.get_text()}")
        """
        if self.mock_mode:
            self._track_api_usage(1)
            comments = [self._mock_comment()]
            self._stats["comments_fetched"] += len(comments)
            return comments
        
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(max_results, 100),
            "textFormat": "plainText"
        }
        
        if page_token:
            params["pageToken"] = page_token
        
        data = await self._api_call("commentThreads", params=params, quota_cost=1)
        
        response = YouTubeResponse(**data)
        
        comments = []
        if response.has_items():
            for item in response.items:
                thread = YouTubeCommentThread(**item)
                
                # Get top-level comment
                if thread.top_level_comment:
                    comments.append(thread.top_level_comment)
                
                # Get replies if present
                if thread.has_replies() and thread.replies:
                    reply_comments = thread.replies.get("comments", [])
                    for reply_data in reply_comments:
                        reply = YouTubeComment(**reply_data)
                        comments.append(reply)
        
        self._stats["comments_fetched"] += len(comments)
        
        return comments
    
    async def post_comment(
        self,
        video_id: str,
        text: str
    ) -> YouTubeComment:
        """
        Post a comment on a video.
        
        Args:
            video_id: YouTube video ID
            text: Comment text
            
        Returns:
            Posted YouTubeComment
            
        Quota cost: 50 units
            
        Example:
            >>> comment = await client.post_comment(
            ...     video_id="dQw4w9WgXcQ",
            ...     text="Great video! Thanks for sharing!"
            ... )
        """
        if self.mock_mode:
            self._track_api_usage(50)
            self._stats["comments_posted"] += 1
            comment = self._mock_comment()
            comment.snippet.video_id = video_id
            comment.snippet.text_original = text
            comment.snippet.text_display = text
            return comment
        
        json_data = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": text
                    }
                }
            }
        }
        
        params = {"part": "snippet"}
        
        data = await self._api_call(
            "commentThreads",
            params=params,
            method="POST",
            json_data=json_data,
            quota_cost=50
        )
        
        self._stats["comments_posted"] += 1
        
        # Extract the top-level comment from the thread
        thread = YouTubeCommentThread(**data)
        if thread.top_level_comment:
            return thread.top_level_comment
        
        # Fallback: create comment from response
        return self._mock_comment()
    
    async def reply_to_comment(
        self,
        parent_id: str,
        text: str
    ) -> YouTubeComment:
        """
        Reply to a comment.
        
        Args:
            parent_id: Parent comment ID
            text: Reply text
            
        Returns:
            Posted reply comment
            
        Quota cost: 50 units
        """
        if self.mock_mode:
            self._track_api_usage(50)
            self._stats["comments_posted"] += 1
            comment = self._mock_comment()
            comment.snippet.parent_id = parent_id
            comment.snippet.text_original = text
            comment.snippet.text_display = text
            return comment
        
        json_data = {
            "snippet": {
                "parentId": parent_id,
                "textOriginal": text
            }
        }
        
        params = {"part": "snippet"}
        
        data = await self._api_call(
            "comments",
            params=params,
            method="POST",
            json_data=json_data,
            quota_cost=50
        )
        
        self._stats["comments_posted"] += 1
        
        return YouTubeComment(**data)
    
    async def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a comment.
        
        Args:
            comment_id: Comment ID to delete
            
        Returns:
            True if deleted successfully
            
        Quota cost: 50 units
        """
        if self.mock_mode:
            self._track_api_usage(50)
            return True
        
        params = {"id": comment_id}
        
        await self._api_call(
            "comments",
            params=params,
            method="DELETE",
            quota_cost=50
        )
        
        return True
    
    # ============================================
    # CHANNELS
    # ============================================
    
    async def get_channel(self, channel_id: str) -> YouTubeChannel:
        """
        Get channel information.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            YouTubeChannel object
            
        Quota cost: 1 unit
        """
        if self.mock_mode:
            self._track_api_usage(1)
            return self._mock_channel()
        
        params = {
            "part": "snippet,statistics",
            "id": channel_id
        }
        
        data = await self._api_call("channels", params=params, quota_cost=1)
        
        response = YouTubeResponse(**data)
        
        if response.has_items():
            channel_data = response.items[0]
            
            # Flatten the data
            channel_info = {
                "id": channel_data["id"],
                **channel_data["snippet"],
                **channel_data.get("statistics", {})
            }
            
            return YouTubeChannel(**channel_info)
        
        raise PlatformError(
            platform="youtube",
            message=f"Channel not found: {channel_id}"
        )
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_video(self, video_id: str) -> YouTubeVideo:
        """Generate mock video."""
        from socialspace_agent.platforms.youtube.models import (
            YouTubeVideoSnippet,
            YouTubeVideoStatistics
        )
        
        return YouTubeVideo(
            id=video_id,
            snippet=YouTubeVideoSnippet(
                published_at=datetime.now().isoformat(),
                channel_id="UC_mock_channel",
                title="SocialSpace Demo Video",
                description="This is a demo video for testing!",
                thumbnails={"default": {"url": "https://example.com/thumb.jpg"}},
                channel_title="SocialSpace Channel",
                tags=["demo", "test"]
            ),
            statistics=YouTubeVideoStatistics(
                view_count="1000",
                like_count="100",
                comment_count="50"
            )
        )
    
    def _mock_comment(self) -> YouTubeComment:
        """Generate mock comment."""
        from socialspace_agent.platforms.youtube.models import YouTubeCommentSnippet
        
        return YouTubeComment(
            id=f"mock_comment_{int(datetime.now().timestamp())}",
            snippet=YouTubeCommentSnippet(
                text_display="Great video! Thanks for sharing!",
                text_original="Great video! Thanks for sharing!",
                author_display_name="Test User",
                author_channel_id={"value": "UC_test_channel"},
                like_count=5,
                published_at=datetime.now().isoformat(),
                video_id="test_video"
            )
        )
    
    def _mock_channel(self) -> YouTubeChannel:
        """Generate mock channel."""
        return YouTubeChannel(
            id="UC_mock_channel",
            title="SocialSpace Channel",
            description="AI-powered social media management",
            subscriber_count="10000",
            video_count="100",
            view_count="1000000"
        )
    
    # ============================================
    # QUOTA MANAGEMENT
    # ============================================
    
    def get_quota_remaining(self) -> int:
        """Get remaining quota units."""
        return max(0, self._daily_quota_limit - self._quota_used)
    
    def reset_quota(self) -> None:
        """Reset quota counter (for testing or daily reset)."""
        self._quota_used = 0
        self._stats["quota_used"] = 0
        logger.info("Quota counter reset")
    
    # ============================================
    # STATISTICS
    # ============================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "quota_remaining": self.get_quota_remaining(),
            "quota_limit": self._daily_quota_limit,
            "mock_mode": self.mock_mode,
        }
