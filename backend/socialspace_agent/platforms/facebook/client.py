"""
Facebook Platform - API Client
===============================

Facebook Graph API client.

Features:
---------
- Get page information
- Fetch posts from page
- Fetch comments
- Post to page
- Post comments
- Manage page content

API Documentation:
https://developers.facebook.com/docs/graph-api

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 10
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.facebook.models import (
    FacebookPage,
    FacebookPost,
    FacebookComment,
    FacebookUser,
    FacebookResponse,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class FacebookClient:
    """
    Facebook Graph API client.
    
    Handles all communication with Facebook Graph API.
    
    Authentication:
    ---------------
    Requires:
    - Access Token (user or page access token)
    - Page ID (for page operations)
    
    Example:
        >>> client = FacebookClient(
        ...     access_token="YOUR_ACCESS_TOKEN",
        ...     page_id="YOUR_PAGE_ID"
        ... )
        >>> 
        >>> # Get page info
        >>> page = await client.get_page_info()
        >>> print(f"Page: {page.name}")
        >>> 
        >>> # Get page posts
        >>> posts = await client.get_page_posts(limit=10)
    
    Rate Limits:
    ------------
    Facebook Graph API rate limits:
    - 200 calls per hour per user
    - Additional limits per app
    - Rate limit headers provided in response
    """
    
    # API Base URL
    API_VERSION = "v18.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
    
    def __init__(
        self,
        access_token: str,
        page_id: Optional[str] = None,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Facebook client.
        
        Args:
            access_token: Facebook access token
            page_id: Facebook page ID (optional)
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.access_token = access_token
        self.page_id = page_id
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Page info cache
        self._page_info: Optional[FacebookPage] = None
        
        # Statistics
        self._stats = {
            "posts_fetched": 0,
            "comments_fetched": 0,
            "posts_created": 0,
            "comments_created": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"Facebook client initialized (mock_mode={mock_mode})")
    
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
        logger.info("Facebook client closed")
    
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
        Make API call to Facebook with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., "me" or "PAGE_ID/feed")
            method: HTTP method (GET, POST, DELETE)
            params: Query parameters
            json_data: JSON payload (for POST)
            
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
            
            # Handle rate limiting
            if response.status_code == 429:
                self._stats["errors"] += 1
                raise RateLimitError(
                    message="Facebook API rate limit exceeded",
                    context={"status_code": 429}
                )
            
            # Handle authentication errors
            if response.status_code in [401, 403]:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid Facebook access token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get("message", response.text)
                raise PlatformError(
                    platform="facebook",
                    message=f"Facebook API error: {error_message}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Facebook API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Facebook API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # USER & PAGE INFO
    # ============================================
    
    async def get_me(self) -> FacebookUser:
        """
        Get authenticated user information.
        
        Returns:
            FacebookUser object
        """
        if self.mock_mode:
            return self._mock_user()
        
        params = {"fields": "id,name,email,picture"}
        
        data = await self._api_call("me", params=params)
        
        return FacebookUser(**data)
    
    async def get_page_info(self, page_id: Optional[str] = None) -> FacebookPage:
        """
        Get page information.
        
        Args:
            page_id: Page ID (uses self.page_id if not provided)
            
        Returns:
            FacebookPage object
        """
        if self.mock_mode:
            return self._mock_page()
        
        pid = page_id or self.page_id
        if not pid:
            raise ValueError("page_id is required")
        
        params = {
            "fields": "id,name,category,about,description,phone,website,fan_count"
        }
        
        data = await self._api_call(pid, params=params)
        
        page = FacebookPage(**data)
        self._page_info = page
        
        return page
    
    # ============================================
    # POSTS
    # ============================================
    
    async def get_page_posts(
        self,
        page_id: Optional[str] = None,
        limit: int = 25,
        after: Optional[str] = None
    ) -> List[FacebookPost]:
        """
        Get posts from a page.
        
        Args:
            page_id: Page ID (uses self.page_id if not provided)
            limit: Number of posts (default: 25)
            after: Pagination cursor
            
        Returns:
            List of FacebookPost objects
        """
        if self.mock_mode:
            posts = [self._mock_post()]
            self._stats["posts_fetched"] += len(posts)
            return posts
        
        pid = page_id or self.page_id
        if not pid:
            raise ValueError("page_id is required")
        
        params = {
            "fields": "id,message,story,from,created_time,updated_time,"
                     "full_picture,picture,type,status_type,likes.summary(true),"
                     "comments.summary(true),shares,permalink_url",
            "limit": limit
        }
        
        if after:
            params["after"] = after
        
        data = await self._api_call(f"{pid}/posts", params=params)
        
        response = FacebookResponse(**data)
        
        posts = []
        if response.has_data():
            data_list = response.data if isinstance(response.data, list) else [response.data]
            for post_data in data_list:
                post = FacebookPost(**post_data)
                posts.append(post)
        
        self._stats["posts_fetched"] += len(posts)
        
        return posts
    
    async def get_post(self, post_id: str) -> FacebookPost:
        """
        Get a specific post.
        
        Args:
            post_id: Post ID
            
        Returns:
            FacebookPost object
        """
        if self.mock_mode:
            return self._mock_post()
        
        params = {
            "fields": "id,message,story,from,created_time,updated_time,"
                     "full_picture,picture,type,status_type,likes.summary(true),"
                     "comments.summary(true),shares,permalink_url"
        }
        
        data = await self._api_call(post_id, params=params)
        
        return FacebookPost(**data)
    
    async def create_post(
        self,
        message: str,
        page_id: Optional[str] = None,
        link: Optional[str] = None
    ) -> FacebookPost:
        """
        Create a post on a page.
        
        Args:
            message: Post message/text
            page_id: Page ID (uses self.page_id if not provided)
            link: Optional link to share
            
        Returns:
            Created FacebookPost
        """
        if self.mock_mode:
            return self._mock_post()
        
        pid = page_id or self.page_id
        if not pid:
            raise ValueError("page_id is required")
        
        params = {"message": message}
        if link:
            params["link"] = link
        
        data = await self._api_call(f"{pid}/feed", method="POST", params=params)
        
        self._stats["posts_created"] += 1
        
        # Get the full post
        post_id = data.get("id")
        return await self.get_post(post_id)
    
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a post.
        
        Args:
            post_id: Post ID
            
        Returns:
            True if deleted successfully
        """
        if self.mock_mode:
            return True
        
        data = await self._api_call(post_id, method="DELETE")
        
        return data.get("success", False)
    
    # ============================================
    # COMMENTS
    # ============================================
    
    async def get_post_comments(
        self,
        post_id: str,
        limit: int = 25,
        after: Optional[str] = None
    ) -> List[FacebookComment]:
        """
        Get comments on a post.
        
        Args:
            post_id: Post ID
            limit: Number of comments
            after: Pagination cursor
            
        Returns:
            List of FacebookComment objects
        """
        if self.mock_mode:
            return [self._mock_comment()]
        
        params = {
            "fields": "id,message,from,created_time,like_count,comment_count,parent,attachment",
            "limit": limit
        }
        
        if after:
            params["after"] = after
        
        data = await self._api_call(f"{post_id}/comments", params=params)
        
        response = FacebookResponse(**data)
        
        comments = []
        if response.has_data():
            data_list = response.data if isinstance(response.data, list) else [response.data]
            for comment_data in data_list:
                comment = FacebookComment(**comment_data)
                comments.append(comment)
        
        self._stats["comments_fetched"] += len(comments)
        
        return comments
    
    async def create_comment(
        self,
        post_id: str,
        message: str
    ) -> FacebookComment:
        """
        Create a comment on a post.
        
        Args:
            post_id: Post ID or comment ID (for reply)
            message: Comment message
            
        Returns:
            Created FacebookComment
        """
        if self.mock_mode:
            return self._mock_comment()
        
        params = {"message": message}
        
        data = await self._api_call(f"{post_id}/comments", method="POST", params=params)
        
        self._stats["comments_created"] += 1
        
        # Get the full comment
        comment_id = data.get("id")
        comment_data = await self._api_call(
            comment_id,
            params={"fields": "id,message,from,created_time,like_count,comment_count,parent"}
        )
        
        return FacebookComment(**comment_data)
    
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
        
        data = await self._api_call(comment_id, method="DELETE")
        
        return data.get("success", False)
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_user(self) -> FacebookUser:
        """Generate mock user."""
        return FacebookUser(
            id="123456789",
            name="SocialSpace User"
        )
    
    def _mock_page(self) -> FacebookPage:
        """Generate mock page."""
        return FacebookPage(
            id="987654321",
            name="SocialSpace Test Page",
            category="Software",
            about="AI-powered social media management",
            fan_count=1000
        )
    
    def _mock_post(self) -> FacebookPost:
        """Generate mock post."""
        return FacebookPost(
            id="post_123456",
            message="Hello from SocialSpace! 🚀",
            **{"from": {"id": "987654321", "name": "SocialSpace Test Page"}},
            created_time=datetime.now().isoformat(),
            type="status",
            likes={"summary": {"total_count": 42}},
            comments={"summary": {"total_count": 5}}
        )
    
    def _mock_comment(self) -> FacebookComment:
        """Generate mock comment."""
        return FacebookComment(
            id="comment_123456",
            message="Great post! Thanks for sharing!",
            **{"from": {"id": "111111111", "name": "Test User"}},
            created_time=datetime.now().isoformat(),
            like_count=5
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
