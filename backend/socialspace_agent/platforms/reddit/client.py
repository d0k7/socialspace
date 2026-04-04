"""
Reddit Platform - API Client
=============================

Reddit OAuth API client.

Features:
---------
- OAuth 2.0 authentication
- Fetch submissions from subreddits
- Fetch comments
- Post submissions
- Post comments
- Vote on posts/comments
- User information

API Documentation:
https://www.reddit.com/dev/api

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 7
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import base64

from socialspace_agent.platforms.reddit.models import (
    RedditSubmission,
    RedditComment,
    RedditUser,
    RedditSubreddit,
    RedditListing,
    RedditThing,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class RedditClient:
    """
    Reddit OAuth API client.
    
    Handles all communication with Reddit API using OAuth 2.0.
    
    Authentication:
    ---------------
    Requires:
    - Client ID (from Reddit App)
    - Client Secret (from Reddit App)
    - User Agent (custom string)
    
    Optional:
    - Username (for script apps)
    - Password (for script apps)
    
    Example:
        >>> client = RedditClient(
        ...     client_id="YOUR_CLIENT_ID",
        ...     client_secret="YOUR_CLIENT_SECRET",
        ...     user_agent="SocialSpace/1.0"
        ... )
        >>> 
        >>> # Get submissions from subreddit
        >>> submissions = await client.get_subreddit_submissions(
        ...     subreddit="python",
        ...     limit=10
        ... )
    
    Rate Limits:
    ------------
    Reddit API rate limits:
    - 60 requests per minute
    - Must include proper User-Agent
    - OAuth apps get higher limits
    """
    
    # API URLs
    OAUTH_URL = "https://oauth.reddit.com"
    BASE_URL = "https://www.reddit.com"
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Reddit client.
        
        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            user_agent: User agent string (required by Reddit)
            username: Reddit username (for script apps)
            password: Reddit password (for script apps)
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.username = username
        self.password = password
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # OAuth token
        self._access_token: Optional[str] = None
        self._token_type: str = "bearer"
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Statistics
        self._stats = {
            "submissions_fetched": 0,
            "comments_fetched": 0,
            "submissions_posted": 0,
            "comments_posted": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"Reddit client initialized (mock_mode={mock_mode})")
    
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
            headers = {
                "User-Agent": self.user_agent
            }
            
            # Add authorization if we have a token
            if self._access_token:
                headers["Authorization"] = f"{self._token_type} {self._access_token}"
            
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Reddit client closed")
    
    # ============================================
    # OAUTH 2.0 AUTHENTICATION
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Reddit OAuth 2.0.
        
        Uses "password" grant type for script apps.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self.mock_mode:
            self._access_token = "mock_access_token"
            return True
        
        try:
            await self._ensure_client()
            
            # Prepare credentials
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            # Prepare request
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "User-Agent": self.user_agent
            }
            
            # OAuth grant type
            if self.username and self.password:
                # Script app (password grant)
                data = {
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password
                }
            else:
                # Client credentials grant
                data = {
                    "grant_type": "client_credentials"
                }
            
            # Request token
            response = await self._client.post(
                self.TOKEN_URL,
                headers=headers,
                data=data
            )
            
            if response.status_code != 200:
                raise AuthenticationError(
                    f"Reddit OAuth failed: {response.text}",
                    context={"status_code": response.status_code}
                )
            
            # Parse token
            token_data = response.json()
            self._access_token = token_data["access_token"]
            self._token_type = token_data.get("token_type", "bearer")
            
            # Update client headers
            if self._client:
                self._client.headers["Authorization"] = f"{self._token_type} {self._access_token}"
            
            logger.info("✅ Reddit OAuth authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Reddit authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate with Reddit: {e}")
    
    # ============================================
    # API CALL WRAPPER
    # ============================================
    
    @async_retry_with_backoff(max_retries=3, base_delay=1.0)
    async def _api_call(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API call to Reddit with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
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
        
        url = f"{self.OAUTH_URL}{endpoint}"
        
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
                # Reddit returns retry-after in seconds
                retry_after = int(response.headers.get("X-Ratelimit-Reset", 60))
                raise RateLimitError(
                    message="Reddit API rate limit exceeded",
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid Reddit access token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                raise PlatformError(
                    platform="reddit",
                    message=f"Reddit API error: {response.text}",
                    context={"status_code": response.status_code}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Reddit API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Reddit API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # SUBREDDIT & SUBMISSIONS
    # ============================================
    
    async def get_subreddit_info(self, subreddit: str) -> RedditSubreddit:
        """
        Get subreddit information.
        
        Args:
            subreddit: Subreddit name (without r/)
            
        Returns:
            RedditSubreddit object
        """
        if self.mock_mode:
            return self._mock_subreddit(subreddit)
        
        data = await self._api_call("GET", f"/r/{subreddit}/about")
        
        return RedditSubreddit(**data["data"])
    
    async def get_subreddit_submissions(
        self,
        subreddit: str,
        sort: str = "hot",
        limit: int = 25,
        after: Optional[str] = None
    ) -> List[RedditSubmission]:
        """
        Get submissions from a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            sort: Sort method (hot, new, top, rising)
            limit: Number of submissions (1-100)
            after: Pagination cursor
            
        Returns:
            List of RedditSubmission objects
            
        Example:
            >>> submissions = await client.get_subreddit_submissions(
            ...     subreddit="python",
            ...     sort="hot",
            ...     limit=10
            ... )
        """
        if self.mock_mode:
            submissions = [self._mock_submission(subreddit)]
            self._stats["submissions_fetched"] += len(submissions)
            return submissions
        
        params = {
            "limit": min(limit, 100)
        }
        
        if after:
            params["after"] = after
        
        data = await self._api_call("GET", f"/r/{subreddit}/{sort}", params=params)
        
        submissions = []
        listing = RedditListing(**data)
        
        for child in listing.get_children():
            thing = RedditThing(**child)
            if thing.is_submission():
                submission = RedditSubmission(**thing.data)
                submissions.append(submission)
        
        self._stats["submissions_fetched"] += len(submissions)
        
        return submissions
    
    async def get_submission(self, submission_id: str) -> RedditSubmission:
        """
        Get a specific submission by ID.
        
        Args:
            submission_id: Submission ID (with or without t3_ prefix)
            
        Returns:
            RedditSubmission object
        """
        if self.mock_mode:
            return self._mock_submission("test")
        
        # Remove t3_ prefix if present
        if submission_id.startswith("t3_"):
            submission_id = submission_id[3:]
        
        data = await self._api_call("GET", f"/comments/{submission_id}")
        
        # Reddit returns [submission_listing, comments_listing]
        submission_thing = RedditThing(**data[0]["data"]["children"][0])
        
        return RedditSubmission(**submission_thing.data)
    
    # ============================================
    # COMMENTS
    # ============================================
    
    async def get_submission_comments(
        self,
        submission_id: str,
        sort: str = "best",
        limit: int = 100
    ) -> List[RedditComment]:
        """
        Get comments on a submission.
        
        Args:
            submission_id: Submission ID (with or without t3_ prefix)
            sort: Sort method (best, top, new, controversial)
            limit: Number of comments
            
        Returns:
            List of RedditComment objects
        """
        if self.mock_mode:
            comments = [self._mock_comment()]
            self._stats["comments_fetched"] += len(comments)
            return comments
        
        # Remove t3_ prefix if present
        if submission_id.startswith("t3_"):
            submission_id = submission_id[3:]
        
        params = {
            "sort": sort,
            "limit": limit
        }
        
        data = await self._api_call("GET", f"/comments/{submission_id}", params=params)
        
        comments = []
        
        # Reddit returns [submission_listing, comments_listing]
        if len(data) > 1:
            comments_listing = RedditListing(**data[1])
            
            for child in comments_listing.get_children():
                thing = RedditThing(**child)
                if thing.is_comment():
                    comment = RedditComment(**thing.data)
                    comments.append(comment)
        
        self._stats["comments_fetched"] += len(comments)
        
        return comments
    
    # ============================================
    # POST CONTENT
    # ============================================
    
    async def submit_text_post(
        self,
        subreddit: str,
        title: str,
        text: str
    ) -> RedditSubmission:
        """
        Submit a text post to a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            title: Post title
            text: Post text content (markdown)
            
        Returns:
            Created RedditSubmission
        """
        if self.mock_mode:
            self._stats["submissions_posted"] += 1
            return self._mock_submission(subreddit)
        
        json_data = {
            "sr": subreddit,
            "kind": "self",
            "title": title,
            "text": text
        }
        
        data = await self._api_call("POST", "/api/submit", json_data=json_data)
        
        self._stats["submissions_posted"] += 1
        
        # Get the created submission
        submission_id = data["json"]["data"]["id"]
        return await self.get_submission(submission_id)
    
    async def submit_link_post(
        self,
        subreddit: str,
        title: str,
        url: str
    ) -> RedditSubmission:
        """
        Submit a link post to a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            title: Post title
            url: Link URL
            
        Returns:
            Created RedditSubmission
        """
        if self.mock_mode:
            self._stats["submissions_posted"] += 1
            return self._mock_submission(subreddit)
        
        json_data = {
            "sr": subreddit,
            "kind": "link",
            "title": title,
            "url": url
        }
        
        data = await self._api_call("POST", "/api/submit", json_data=json_data)
        
        self._stats["submissions_posted"] += 1
        
        submission_id = data["json"]["data"]["id"]
        return await self.get_submission(submission_id)
    
    async def post_comment(
        self,
        parent_id: str,
        text: str
    ) -> RedditComment:
        """
        Post a comment on a submission or another comment.
        
        Args:
            parent_id: Parent ID (t3_xxxxx for submission, t1_xxxxx for comment)
            text: Comment text (markdown)
            
        Returns:
            Created RedditComment
        """
        if self.mock_mode:
            self._stats["comments_posted"] += 1
            return self._mock_comment()
        
        json_data = {
            "thing_id": parent_id,
            "text": text
        }
        
        data = await self._api_call("POST", "/api/comment", json_data=json_data)
        
        self._stats["comments_posted"] += 1
        
        # Parse the created comment
        comment_thing = RedditThing(**data["json"]["data"]["things"][0])
        
        return RedditComment(**comment_thing.data)
    
    # ============================================
    # VOTING
    # ============================================
    
    async def vote(
        self,
        thing_id: str,
        direction: int
    ) -> bool:
        """
        Vote on a submission or comment.
        
        Args:
            thing_id: Thing ID (t3_ or t1_)
            direction: Vote direction (1=upvote, 0=remove vote, -1=downvote)
            
        Returns:
            True if successful
        """
        if self.mock_mode:
            return True
        
        json_data = {
            "id": thing_id,
            "dir": direction
        }
        
        await self._api_call("POST", "/api/vote", json_data=json_data)
        
        return True
    
    # ============================================
    # USER INFO
    # ============================================
    
    async def get_user_info(self, username: str) -> RedditUser:
        """
        Get user information.
        
        Args:
            username: Reddit username (without u/)
            
        Returns:
            RedditUser object
        """
        if self.mock_mode:
            return self._mock_user(username)
        
        data = await self._api_call("GET", f"/user/{username}/about")
        
        return RedditUser(**data["data"])
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_subreddit(self, name: str) -> RedditSubreddit:
        """Generate mock subreddit."""
        return RedditSubreddit(
            id="t5_mock",
            name=name,
            display_name=name,
            title=f"r/{name}",
            subscribers=100000
        )
    
    def _mock_submission(self, subreddit: str) -> RedditSubmission:
        """Generate mock submission."""
        return RedditSubmission(
            id="mock123",
            name="t3_mock123",
            subreddit=subreddit,
            subreddit_id="t5_mock",
            author="test_user",
            title="Test submission from SocialSpace",
            selftext="This is a test post!",
            is_self=True,
            created_utc=datetime.now().timestamp(),
            score=42,
            num_comments=5,
            permalink=f"/r/{subreddit}/comments/mock123/test/"
        )
    
    def _mock_comment(self) -> RedditComment:
        """Generate mock comment."""
        return RedditComment(
            id="mock456",
            name="t1_mock456",
            parent_id="t3_mock123",
            link_id="t3_mock123",
            subreddit="test",
            subreddit_id="t5_mock",
            author="test_user",
            body="Great post! Thanks for sharing!",
            created_utc=datetime.now().timestamp(),
            score=10
        )
    
    def _mock_user(self, username: str) -> RedditUser:
        """Generate mock user."""
        return RedditUser(
            id="mock_user",
            name=username,
            link_karma=1000,
            comment_karma=500
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
