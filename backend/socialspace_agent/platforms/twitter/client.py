"""
Twitter Platform - API Client
==============================

Twitter API v2 client.

Features:
---------
- OAuth 2.0 Bearer Token authentication
- Post tweets
- Get user timeline
- Reply to tweets
- Get user information
- Search tweets

API Documentation:
https://developer.twitter.com/en/docs/twitter-api

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 8
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from socialspace_agent.platforms.twitter.models import (
    TwitterTweet,
    TwitterUser,
    TwitterResponse,
    TwitterError,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class TwitterClient:
    """
    Twitter API v2 client.
    
    Handles all communication with Twitter API v2.
    
    Authentication:
    ---------------
    Requires:
    - Bearer Token (from Twitter Developer Portal)
    
    OR for posting:
    - API Key
    - API Secret
    - Access Token
    - Access Token Secret
    
    Example:
        >>> client = TwitterClient(
        ...     bearer_token="YOUR_BEARER_TOKEN"
        ... )
        >>> 
        >>> # Get user's tweets
        >>> tweets = await client.get_user_tweets(
        ...     user_id="123456789",
        ...     max_results=10
        ... )
        >>> 
        >>> # Post a tweet
        >>> tweet = await client.post_tweet(
        ...     text="Hello from SocialSpace! 🚀"
        ... )
    
    Rate Limits:
    ------------
    Twitter API v2 rate limits (Free tier):
    - 1,500 tweets per month (posting)
    - 500,000 tweets per month (reading)
    - 15-minute windows for most endpoints
    """
    
    # API Base URL
    API_VERSION = "2"
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(
        self,
        bearer_token: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        timeout: int = 30,
        mock_mode: bool = False
    ):
        """
        Initialize Twitter client.
        
        Args:
            bearer_token: OAuth 2.0 Bearer Token (for read-only)
            api_key: API Key (for posting)
            api_secret: API Secret (for posting)
            access_token: Access Token (for posting)
            access_token_secret: Access Token Secret (for posting)
            timeout: Request timeout in seconds (default: 30)
            mock_mode: Use mock responses for testing (default: False)
        """
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.timeout = timeout
        self.mock_mode = mock_mode
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Authenticated user info
        self._authenticated_user: Optional[TwitterUser] = None
        
        # Statistics
        self._stats = {
            "tweets_posted": 0,
            "tweets_fetched": 0,
            "api_calls": 0,
            "errors": 0,
        }
        
        logger.info(f"Twitter client initialized (mock_mode={mock_mode})")
    
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
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers
            )
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Twitter client closed")
    
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
        Make API call to Twitter with retry logic.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
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
        
        url = f"{self.BASE_URL}{endpoint}"
        
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
                # Twitter returns rate limit reset time
                reset_time = response.headers.get("x-rate-limit-reset", "")
                raise RateLimitError(
                    message="Twitter API rate limit exceeded",
                    context={"reset_time": reset_time}
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                self._stats["errors"] += 1
                raise AuthenticationError("Invalid Twitter bearer token")
            
            # Handle other errors
            if response.status_code >= 400:
                self._stats["errors"] += 1
                error_data = response.json() if response.text else {}
                raise PlatformError(
                    platform="twitter",
                    message=f"Twitter API error: {response.text}",
                    context={"status_code": response.status_code, "error": error_data}
                )
            
            # Return response
            if response.text:
                return response.json()
            return {}
            
        except httpx.TimeoutException:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Twitter API",
                message="Request timed out"
            )
        except httpx.NetworkError as e:
            self._stats["errors"] += 1
            raise ServiceUnavailableError(
                service="Twitter API",
                message=f"Network error: {e}"
            )
    
    # ============================================
    # USER INFORMATION
    # ============================================
    
    async def get_user_by_username(self, username: str) -> TwitterUser:
        """
        Get user information by username.
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            TwitterUser object
            
        Example:
            >>> user = await client.get_user_by_username("elonmusk")
            >>> print(f"User: {user.name} (@{user.username})")
        """
        if self.mock_mode:
            return self._mock_user(username)
        
        params = {
            "user.fields": "description,profile_image_url,verified,protected,"
                          "public_metrics,created_at"
        }
        
        data = await self._api_call("GET", f"/users/by/username/{username}", params=params)
        
        response = TwitterResponse(**data)
        
        if response.has_data():
            return TwitterUser(**response.data)
        
        raise PlatformError(
            platform="twitter",
            message=f"User not found: {username}"
        )
    
    async def get_user_by_id(self, user_id: str) -> TwitterUser:
        """
        Get user information by user ID.
        
        Args:
            user_id: Twitter user ID
            
        Returns:
            TwitterUser object
        """
        if self.mock_mode:
            return self._mock_user("test_user")
        
        params = {
            "user.fields": "description,profile_image_url,verified,protected,"
                          "public_metrics,created_at"
        }
        
        data = await self._api_call("GET", f"/users/{user_id}", params=params)
        
        response = TwitterResponse(**data)
        
        if response.has_data():
            return TwitterUser(**response.data)
        
        raise PlatformError(
            platform="twitter",
            message=f"User not found: {user_id}"
        )
    
    async def get_me(self) -> TwitterUser:
        """
        Get authenticated user's information.
        
        Returns:
            TwitterUser object for authenticated user
        """
        if self.mock_mode:
            return self._mock_user("socialspace_bot")
        
        params = {
            "user.fields": "description,profile_image_url,verified,protected,"
                          "public_metrics,created_at"
        }
        
        data = await self._api_call("GET", "/users/me", params=params)
        
        response = TwitterResponse(**data)
        
        if response.has_data():
            self._authenticated_user = TwitterUser(**response.data)
            return self._authenticated_user
        
        raise PlatformError(platform="twitter", message="Failed to get authenticated user")
    
    # ============================================
    # TWEETS - READ
    # ============================================
    
    async def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 10,
        pagination_token: Optional[str] = None
    ) -> List[TwitterTweet]:
        """
        Get tweets from a user's timeline.
        
        Args:
            user_id: Twitter user ID
            max_results: Number of tweets (5-100, default: 10)
            pagination_token: Token for next page
            
        Returns:
            List of TwitterTweet objects
            
        Example:
            >>> tweets = await client.get_user_tweets(
            ...     user_id="123456789",
            ...     max_results=20
            ... )
        """
        if self.mock_mode:
            return [self._mock_tweet()]
        
        params = {
            "max_results": min(max(max_results, 5), 100),
            "tweet.fields": "created_at,public_metrics,entities,referenced_tweets,"
                           "conversation_id,in_reply_to_user_id,lang,possibly_sensitive",
            "expansions": "attachments.media_keys,author_id",
            "media.fields": "url,preview_image_url,type,width,height,duration_ms"
        }
        
        if pagination_token:
            params["pagination_token"] = pagination_token
        
        data = await self._api_call("GET", f"/users/{user_id}/tweets", params=params)
        
        response = TwitterResponse(**data)
        
        tweets = []
        if response.has_data():
            # Handle both single tweet and list of tweets
            tweet_data = response.data if isinstance(response.data, list) else [response.data]
            
            for tweet_dict in tweet_data:
                tweet = TwitterTweet(**tweet_dict)
                tweets.append(tweet)
        
        self._stats["tweets_fetched"] += len(tweets)
        
        return tweets
    
    async def get_tweet(self, tweet_id: str) -> TwitterTweet:
        """
        Get a specific tweet by ID.
        
        Args:
            tweet_id: Tweet ID
            
        Returns:
            TwitterTweet object
        """
        if self.mock_mode:
            return self._mock_tweet()
        
        params = {
            "tweet.fields": "created_at,public_metrics,entities,referenced_tweets,"
                           "conversation_id,in_reply_to_user_id,lang,possibly_sensitive",
            "expansions": "attachments.media_keys,author_id",
            "media.fields": "url,preview_image_url,type,width,height,duration_ms"
        }
        
        data = await self._api_call("GET", f"/tweets/{tweet_id}", params=params)
        
        response = TwitterResponse(**data)
        
        if response.has_data():
            return TwitterTweet(**response.data)
        
        raise PlatformError(
            platform="twitter",
            message=f"Tweet not found: {tweet_id}"
        )
    
    # ============================================
    # TWEETS - WRITE
    # ============================================
    
    async def post_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None
    ) -> TwitterTweet:
        """
        Post a tweet.
        
        Args:
            text: Tweet text (max 280 characters)
            reply_to: Tweet ID to reply to (optional)
            
        Returns:
            Posted TwitterTweet
            
        Example:
            >>> # Post a tweet
            >>> tweet = await client.post_tweet(
            ...     text="Hello Twitter! 🚀"
            ... )
            >>> 
            >>> # Reply to a tweet
            >>> reply = await client.post_tweet(
            ...     text="Thanks for sharing!",
            ...     reply_to="1234567890"
            ... )
        """
        if self.mock_mode:
            self._stats["tweets_posted"] += 1
            return self._mock_tweet()
        
        payload: Dict[str, Any] = {"text": text}
        
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}
        
        data = await self._api_call("POST", "/tweets", json_data=payload)
        
        response = TwitterResponse(**data)
        
        self._stats["tweets_posted"] += 1
        
        if response.has_data():
            # Get the full tweet details
            tweet_id = response.data.get("id")
            return await self.get_tweet(tweet_id)
        
        raise PlatformError(
            platform="twitter",
            message="Failed to post tweet"
        )
    
    async def delete_tweet(self, tweet_id: str) -> bool:
        """
        Delete a tweet.
        
        Args:
            tweet_id: Tweet ID to delete
            
        Returns:
            True if deleted successfully
        """
        if self.mock_mode:
            return True
        
        data = await self._api_call("DELETE", f"/tweets/{tweet_id}")
        
        response = TwitterResponse(**data)
        
        return response.has_data() and response.data.get("deleted", False)
    
    # ============================================
    # SEARCH
    # ============================================
    
    async def search_recent_tweets(
        self,
        query: str,
        max_results: int = 10
    ) -> List[TwitterTweet]:
        """
        Search recent tweets.
        
        Args:
            query: Search query
            max_results: Number of results (10-100)
            
        Returns:
            List of TwitterTweet objects
            
        Example:
            >>> tweets = await client.search_recent_tweets(
            ...     query="python programming",
            ...     max_results=20
            ... )
        """
        if self.mock_mode:
            return [self._mock_tweet()]
        
        params = {
            "query": query,
            "max_results": min(max(max_results, 10), 100),
            "tweet.fields": "created_at,public_metrics,entities,referenced_tweets"
        }
        
        data = await self._api_call("GET", "/tweets/search/recent", params=params)
        
        response = TwitterResponse(**data)
        
        tweets = []
        if response.has_data():
            for tweet_dict in response.data:
                tweet = TwitterTweet(**tweet_dict)
                tweets.append(tweet)
        
        self._stats["tweets_fetched"] += len(tweets)
        
        return tweets
    
    # ============================================
    # MOCK RESPONSES (FOR TESTING)
    # ============================================
    
    def _mock_user(self, username: str) -> TwitterUser:
        """Generate mock user."""
        return TwitterUser(
            id="123456789",
            username=username,
            name="SocialSpace Bot",
            description="AI-powered social media management 🤖",
            verified=False,
            followers_count=1000,
            following_count=500,
            tweet_count=250
        )
    
    def _mock_tweet(self) -> TwitterTweet:
        """Generate mock tweet."""
        return TwitterTweet(
            id=str(int(datetime.now().timestamp())),
            text="Hello from SocialSpace! 🚀 Check out our amazing platform!",
            author_id="123456789",
            created_at=datetime.now().isoformat(),
            public_metrics={
                "like_count": 42,
                "retweet_count": 10,
                "reply_count": 5,
                "quote_count": 2
            }
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
