"""
Instagram Platform - API Client
================================

Instagram Graph API client.

Features:
---------
- Fetch media (posts, stories, reels)
- Fetch and post comments
- Get user information
- Handle mentions
- Pagination support

API Documentation:
https://developers.facebook.com/docs/instagram-api

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 5
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.instagram.models import (
    InstagramMedia,
    InstagramComment,
    InstagramUser,
    InstagramPaginatedResponse,
    InstagramErrorResponse,
)
from socialspace_agent.exceptions import (
    InstagramError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class InstagramClient:
    """
    Instagram Graph API client.
    
    Handles all communication with Instagram Graph API.
    
    Authentication:
    ---------------
    Requires:
    - Access Token (from Facebook App)
    - Instagram Business Account ID
    
    Example:
        >>> client = InstagramClient(
        ...     access_token="YOUR_ACCESS_TOKEN",
        ...     account_id="YOUR_IG_BUSINESS_ID"
        ... )
        >>> 
        >>> # Get recent media
        >>> media_list = await client.get_media(limit=10)
        >>> 
        >>> # Post a comment
        >>> comment = await client.create_comment(
        ...     media_id="123456",
        ...     text="Great post!"
        ... )
    
    Rate Limits:
    ------------
    Instagram Graph API rate limits:
    - 200 calls per hour per user
    - 4800 calls per hour per app
    """
    
    # API Base URL
    API_VERSION = "v21.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
    
    def __init__(
        self,
        access_token: str,
        account_id: str,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Instagram client.
        
        Args:
            access_token: Instagram/Facebook access token
            account_id: Instagram Business Account ID
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.access_token = access_token
        self.account_id = account_id
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Statistics
        self._stats = {
            "media_fetched": 0,
            "comments_fetched": 0,
            "comments_posted": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(
            f"Instagram client initialized "
            f"(account_id={account_id[:8]}..., mock_mode={mock_mode})"
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
                headers={"Content-Type": "application/json"}
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Instagram client closed")
    
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
        Make API call to Instagram Graph API with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., "/me/media")
            method: HTTP method (GET, POST, DELETE)
            params: Query parameters
            json_data: JSON payload (for POST)
            
        Returns:
            API response as dictionary
            
        Raises:
            InstagramError: On API errors
            RateLimitError: On rate limit
            AuthenticationError: On invalid token
            ServiceUnavailableError: On service issues
        """
        await self._ensure_client()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        # Add access token to params
        if params is None:
            params = {}
        params["access_token"] = self.access_token
        
        self._stats["api_calls"] += 1
        
        logger.debug(f"API call: {method} {endpoint}")
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data
            )
            
            # Parse response
            data = response.json()
            
            # Check for errors
            if "error" in data:
                self._stats["errors"] += 1
                error = InstagramErrorResponse(**data["error"])
                
                # Handle specific errors
                if error.code == 190:
                    raise AuthenticationError(
                        "Invalid Instagram access token",
                        context={"error": error.message}
                    )
                
                elif error.code == 4 or error.code == 17:
                    raise RateLimitError(
                        message="Instagram API rate limit exceeded",
                        context={"error": error.message}
                    )
                
                else:
                    raise InstagramError(
                        message=f"Instagram API error: {error.message}",
                        context={
                            "code": error.code,
                            "type": error.type,
                            "fbtrace_id": error.fbtrace_id
                        }
                    )
            
            return data
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Instagram API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Instagram API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # USER & ACCOUNT
    # ============================================
    
    async def get_account_info(self) -> InstagramUser:
        """
        Get Instagram Business Account information.
        
        Returns:
            InstagramUser with account details
            
        Example:
            >>> account = await client.get_account_info()
            >>> print(f"Username: @{account.username}")
            >>> print(f"Followers: {account.followers_count}")
        """
        if self.mock_mode:
            return self._mock_account_info()
        
        params = {
            "fields": "id,username,name,profile_picture_url,followers_count,"
                     "follows_count,media_count,biography,website"
        }
        
        data = await self._api_call(f"/{self.account_id}", params=params)
        
        return InstagramUser(**data)
    
    # ============================================
    # MEDIA (POSTS, STORIES, REELS)
    # ============================================
    
    async def get_media(
        self,
        limit: int = 25,
        after: Optional[str] = None
    ) -> InstagramPaginatedResponse:
        """
        Get media posts for the account.
        
        Args:
            limit: Maximum number of media to return (1-100)
            after: Pagination cursor for next page
            
        Returns:
            InstagramPaginatedResponse with media data
            
        Example:
            >>> # Get first page
            >>> response = await client.get_media(limit=10)
            >>> for item in response.data:
            ...     media = InstagramMedia(**item)
            ...     print(f"Post: {media.caption}")
            >>> 
            >>> # Get next page
            >>> if response.has_next_page():
            ...     cursor = response.get_next_cursor()
            ...     next_page = await client.get_media(after=cursor)
        """
        if self.mock_mode:
            response = self._mock_media_response()
            self._stats["media_fetched"] += len(response.data)
            return response
        
        params = {
            "fields": "id,media_type,media_url,thumbnail_url,permalink,caption,"
                     "timestamp,like_count,comments_count,media_product_type,children",
            "limit": min(limit, 100)
        }
        
        if after:
            params["after"] = after
        
        data = await self._api_call(f"/{self.account_id}/media", params=params)
        
        self._stats["media_fetched"] += len(data.get("data", []))
        
        return InstagramPaginatedResponse(**data)
    
    async def get_media_by_id(self, media_id: str) -> InstagramMedia:
        """
        Get a specific media post by ID.
        
        Args:
            media_id: Instagram media ID
            
        Returns:
            InstagramMedia object
        """
        if self.mock_mode:
            return self._mock_media()
        
        params = {
            "fields": "id,media_type,media_url,thumbnail_url,permalink,caption,"
                     "timestamp,like_count,comments_count,media_product_type"
        }
        
        data = await self._api_call(f"/{media_id}", params=params)
        
        return InstagramMedia(**data)
    
    # ============================================
    # COMMENTS
    # ============================================
    
    async def get_comments(
        self,
        media_id: str,
        limit: int = 25
    ) -> List[InstagramComment]:
        """
        Get comments on a media post.
        
        Args:
            media_id: Instagram media ID
            limit: Maximum number of comments
            
        Returns:
            List of InstagramComment objects
            
        Example:
            >>> comments = await client.get_comments("123456", limit=50)
            >>> for comment in comments:
            ...     print(f"{comment.username}: {comment.text}")
        """
        if self.mock_mode:
            comments = [self._mock_comment()]
            self._stats["comments_fetched"] += len(comments)
            return comments
        
        params = {
            "fields": "id,text,timestamp,username,like_count,parent_id,from",
            "limit": min(limit, 100)
        }
        
        data = await self._api_call(f"/{media_id}/comments", params=params)
        
        comments = []
        for comment_data in data.get("data", []):
            comment = InstagramComment(**comment_data)
            comments.append(comment)
        
        self._stats["comments_fetched"] += len(comments)
        
        return comments
    
    async def create_comment(
        self,
        media_id: str,
        text: str
    ) -> InstagramComment:
        """
        Post a comment on a media post.
        
        Args:
            media_id: Instagram media ID
            text: Comment text
            
        Returns:
            Created InstagramComment
            
        Example:
            >>> comment = await client.create_comment(
            ...     media_id="123456",
            ...     text="Great photo! 📸"
            ... )
            >>> print(f"Comment posted: {comment.id}")
        """
        if self.mock_mode:
            self._stats["comments_posted"] += 1
            return self._mock_comment(text=text)
        
        json_data = {"message": text}
        
        data = await self._api_call(
            f"/{media_id}/comments",
            method="POST",
            json_data=json_data
        )
        
        self._stats["comments_posted"] += 1
        
        # Get the created comment
        comment_id = data.get("id")
        if comment_id:
            params = {"fields": "id,text,timestamp,username"}
            comment_data = await self._api_call(f"/{comment_id}", params=params)
            return InstagramComment(**comment_data)
        
        # Fallback: return minimal comment
        return InstagramComment(
            id=comment_id or "mock_id",
            text=text,
            timestamp=datetime.now().isoformat()
        )
    
    async def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a comment.
        
        Args:
            comment_id: Instagram comment ID
            
        Returns:
            True if deleted successfully
        """
        if self.mock_mode:
            return True
        
        data = await self._api_call(f"/{comment_id}", method="DELETE")
        
        return data.get("success", False)
    
    async def reply_to_comment(
        self,
        comment_id: str,
        text: str
    ) -> InstagramComment:
        """
        Reply to a comment.
        
        Args:
            comment_id: Parent comment ID
            text: Reply text
            
        Returns:
            Created reply comment
        """
        if self.mock_mode:
            self._stats["comments_posted"] += 1
            comment = self._mock_comment(text=text)
            comment.parent_id = comment_id
            return comment
        
        json_data = {"message": text}
        
        data = await self._api_call(
            f"/{comment_id}/replies",
            method="POST",
            json_data=json_data
        )
        
        self._stats["comments_posted"] += 1
        
        # Get the created reply
        reply_id = data.get("id")
        if reply_id:
            params = {"fields": "id,text,timestamp,username,parent_id"}
            reply_data = await self._api_call(f"/{reply_id}", params=params)
            return InstagramComment(**reply_data)
        
        return InstagramComment(
            id=reply_id or "mock_reply",
            text=text,
            timestamp=datetime.now().isoformat(),
            parent_id=comment_id
        )
    
    # ============================================
    # MENTIONS
    # ============================================
    
    async def get_mentions(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Get mentions of the account in stories.
        
        Args:
            limit: Maximum number of mentions
            
        Returns:
            List of mention dictionaries
        """
        if self.mock_mode:
            return []
        
        params = {
            "fields": "id,media_id,timestamp,from",
            "limit": min(limit, 100)
        }
        
        data = await self._api_call(f"/{self.account_id}/mentions", params=params)
        
        return data.get("data", [])
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_account_info(self) -> InstagramUser:
        """Generate mock account info."""
        return InstagramUser(
            id=self.account_id,
            username="socialspace_demo",
            name="SocialSpace Demo Account",
            followers_count=1000,
            follows_count=500,
            media_count=50,
            biography="AI-powered social media management 🤖",
            website="https://socialspace.example.com"
        )
    
    def _mock_media_response(self) -> InstagramPaginatedResponse:
        """Generate mock media response."""
        return InstagramPaginatedResponse(
            data=[self._mock_media().model_dump()],
            paging=None
        )
    
    def _mock_media(self) -> InstagramMedia:
        """Generate mock media."""
        return InstagramMedia(
            id="mock_media_123",
            media_type="IMAGE",
            media_url="https://example.com/image.jpg",
            permalink="https://instagram.com/p/mock123",
            caption="Test post from SocialSpace! 📸",
            timestamp=datetime.now().isoformat(),
            like_count=42,
            comments_count=5,
            media_product_type="FEED"
        )
    
    def _mock_comment(self, text: Optional[str] = None) -> InstagramComment:
        """Generate mock comment."""
        return InstagramComment(
            id=f"mock_comment_{int(datetime.now().timestamp())}",
            text=text or "Great post! Thanks for sharing! 👍",
            timestamp=datetime.now().isoformat(),
            username="test_user",
            like_count=2
        )
    
    # ============================================
    # STATISTICS
    # ============================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "account_id": self.account_id[:8] + "...",
            "mock_mode": self.mock_mode,
        }
