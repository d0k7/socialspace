"""
LinkedIn Platform - API Client
===============================

LinkedIn API client.

Features:
---------
- Get profile information
- Fetch posts/shares
- Fetch comments
- Create posts
- Create comments
- Manage company pages

API Documentation:
https://docs.microsoft.com/en-us/linkedin/

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 11
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.linkedin.models import (
    LinkedInProfile,
    LinkedInOrganization,
    LinkedInPost,
    LinkedInComment,
    LinkedInResponse,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class LinkedInClient:
    """
    LinkedIn API client.
    
    Handles all communication with LinkedIn API.
    
    Authentication:
    ---------------
    Requires:
    - Access Token (OAuth 2.0)
    - Optional: Organization ID (for company pages)
    
    Example:
        >>> client = LinkedInClient(
        ...     access_token="YOUR_ACCESS_TOKEN"
        ... )
        >>> 
        >>> # Get profile
        >>> profile = await client.get_profile()
        >>> print(f"Name: {profile.get_full_name()}")
        >>> 
        >>> # Create post
        >>> post = await client.create_post(
        ...     text="Hello LinkedIn!"
        ... )
    
    Rate Limits:
    ------------
    LinkedIn API rate limits:
    - Varies by endpoint and app type
    - Throttling headers in response
    """
    
    # API Base URL
    API_VERSION = "v2"
    BASE_URL = f"https://api.linkedin.com/{API_VERSION}"
    
    def __init__(
        self,
        access_token: str,
        organization_id: Optional[str] = None,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize LinkedIn client.
        
        Args:
            access_token: LinkedIn access token
            organization_id: Organization ID (optional, for company pages)
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.access_token = access_token
        self.organization_id = organization_id
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Profile cache
        self._profile: Optional[LinkedInProfile] = None
        
        # Statistics
        self._stats = {
            "posts_fetched": 0,
            "comments_fetched": 0,
            "posts_created": 0,
            "comments_created": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"LinkedIn client initialized (mock_mode={mock_mode})")
    
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
                    "X-Restli-Protocol-Version": "2.0.0"
                }
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("LinkedIn client closed")
    
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
        Make API call to LinkedIn with retry logic.
        
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
                    message="LinkedIn API rate limit exceeded",
                    context={"status_code": 429}
                )
            
            # Handle authentication errors
            if response.status_code in [401, 403]:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid LinkedIn access token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                raise PlatformError(
                    platform="linkedin",
                    message=f"LinkedIn API error: {response.text}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="LinkedIn API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="LinkedIn API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # PROFILE
    # ============================================
    
    async def get_profile(self) -> LinkedInProfile:
        """
        Get authenticated user's profile.
        
        Returns:
            LinkedInProfile object
        """
        if self.mock_mode:
            return self._mock_profile()
        
        params = {
            "projection": "(id,firstName,lastName,maidenName,headline,location,industry,profilePicture)"
        }
        
        data = await self._api_call("me", params=params)
        
        # Flatten localized fields
        flattened_data = {
            "id": data.get("id"),
            "first_name": data.get("firstName", {}).get("localized", {}).get("en_US"),
            "last_name": data.get("lastName", {}).get("localized", {}).get("en_US"),
            "headline": data.get("headline", {}).get("localized", {}).get("en_US"),
            "industry": data.get("industry"),
            "location": data.get("location"),
            "profile_picture": data.get("profilePicture")
        }
        
        profile = LinkedInProfile(**flattened_data)
        self._profile = profile
        
        return profile
    
    # ============================================
    # POSTS (UGC - User Generated Content)
    # ============================================
    
    async def get_posts(
        self,
        author: Optional[str] = None,
        count: int = 10
    ) -> List[LinkedInPost]:
        """
        Get posts.
        
        Args:
            author: Author URN (defaults to current user)
            count: Number of posts
            
        Returns:
            List of LinkedInPost objects
        """
        if self.mock_mode:
            posts = [self._mock_post()]
            self._stats["posts_fetched"] += len(posts)
            return posts
        
        # If no author specified, use current user
        if not author:
            if not self._profile:
                await self.get_profile()
            author = f"urn:li:person:{self._profile.id}"
        
        params = {
            "q": "authors",
            "authors": author,
            "count": count
        }
        
        data = await self._api_call("ugcPosts", params=params)
        
        response = LinkedInResponse(**data)
        
        posts = []
        if response.has_elements():
            for post_data in response.elements:
                # Flatten specificContent
                if "specificContent" in post_data:
                    specific = post_data["specificContent"].get("com.linkedin.ugc.ShareContent", {})
                    post_data["text"] = specific.get("shareCommentary", {}).get("text")
                
                post = LinkedInPost(**post_data)
                posts.append(post)
        
        self._stats["posts_fetched"] += len(posts)
        
        return posts
    
    async def create_post(
        self,
        text: str,
        visibility: str = "PUBLIC"
    ) -> LinkedInPost:
        """
        Create a post (UGC share).
        
        Args:
            text: Post text
            visibility: Visibility (PUBLIC, CONNECTIONS)
            
        Returns:
            Created LinkedInPost
        """
        if self.mock_mode:
            return self._mock_post()
        
        # Get current user ID
        if not self._profile:
            await self.get_profile()
        
        author_urn = f"urn:li:person:{self._profile.id}"
        
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        data = await self._api_call("ugcPosts", method="POST", json_data=payload)
        
        self._stats["posts_created"] += 1
        
        # Parse created post
        post = LinkedInPost(**data)
        
        return post
    
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a post.
        
        Args:
            post_id: Post ID (URN)
            
        Returns:
            True if deleted successfully
        """
        if self.mock_mode:
            return True
        
        await self._api_call(f"ugcPosts/{post_id}", method="DELETE")
        
        return True
    
    # ============================================
    # COMMENTS (SOCIAL ACTIONS)
    # ============================================
    
    async def get_comments(
        self,
        object_urn: str,
        count: int = 10
    ) -> List[LinkedInComment]:
        """
        Get comments on a post.
        
        Args:
            object_urn: Object URN (post)
            count: Number of comments
            
        Returns:
            List of LinkedInComment objects
        """
        if self.mock_mode:
            return [self._mock_comment()]
        
        params = {
            "q": "object",
            "object": object_urn,
            "count": count
        }
        
        data = await self._api_call("socialActions", params=params)
        
        response = LinkedInResponse(**data)
        
        comments = []
        if response.has_elements():
            for comment_data in response.elements:
                comment = LinkedInComment(**comment_data)
                comments.append(comment)
        
        self._stats["comments_fetched"] += len(comments)
        
        return comments
    
    async def create_comment(
        self,
        object_urn: str,
        text: str
    ) -> LinkedInComment:
        """
        Create a comment on a post.
        
        Args:
            object_urn: Object URN (post or comment)
            text: Comment text
            
        Returns:
            Created LinkedInComment
        """
        if self.mock_mode:
            return self._mock_comment()
        
        # Get current user ID
        if not self._profile:
            await self.get_profile()
        
        actor_urn = f"urn:li:person:{self._profile.id}"
        
        payload = {
            "actor": actor_urn,
            "object": object_urn,
            "message": {
                "text": text
            }
        }
        
        data = await self._api_call("socialActions", method="POST", json_data=payload)
        
        self._stats["comments_created"] += 1
        
        comment = LinkedInComment(**data)
        
        return comment
    
    # ============================================
    # ORGANIZATION
    # ============================================
    
    async def get_organization(
        self,
        organization_id: Optional[str] = None
    ) -> LinkedInOrganization:
        """
        Get organization information.
        
        Args:
            organization_id: Organization ID (uses self.organization_id if not provided)
            
        Returns:
            LinkedInOrganization object
        """
        if self.mock_mode:
            return self._mock_organization()
        
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("organization_id is required")
        
        data = await self._api_call(f"organizations/{org_id}")
        
        return LinkedInOrganization(**data)
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_profile(self) -> LinkedInProfile:
        """Generate mock profile."""
        return LinkedInProfile(
            id="mock_profile_123",
            first_name="John",
            last_name="Doe",
            headline="Software Engineer at SocialSpace"
        )
    
    def _mock_post(self) -> LinkedInPost:
        """Generate mock post."""
        return LinkedInPost(
            id="urn:li:ugcPost:mock_post_123",
            author="urn:li:person:mock_profile_123",
            text="Hello LinkedIn! 🚀",
            commentary="Hello LinkedIn! 🚀",
            created_at=int(datetime.now().timestamp() * 1000),
            lifecycle_state="PUBLISHED"
        )
    
    def _mock_comment(self) -> LinkedInComment:
        """Generate mock comment."""
        return LinkedInComment(
            id="urn:li:comment:mock_comment_123",
            object="urn:li:ugcPost:mock_post_123",
            actor="urn:li:person:mock_profile_123",
            message={"text": "Great post! Thanks for sharing!"},
            created_at=int(datetime.now().timestamp() * 1000)
        )
    
    def _mock_organization(self) -> LinkedInOrganization:
        """Generate mock organization."""
        return LinkedInOrganization(
            id="mock_org_123",
            localized_name="SocialSpace",
            vanity_name="socialspace"
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
