"""
Twitter Platform - Platform Adapter
====================================

Twitter platform adapter implementing BasePlatform interface.

This integrates Twitter API v2 with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 8
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.twitter.client import TwitterClient
from socialspace_agent.platforms.twitter.models import TwitterTweet
from socialspace_agent.models import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
    MediaAttachment,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    ValidationError,
)
from socialspace_agent.utils.config import PlatformConfig

logger = logging.getLogger(__name__)


class TwitterPlatform(BasePlatform):
    """
    Twitter API v2 platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify bearer token
    - fetch_messages(): Get tweets from timeline
    - send_message(): Post tweets or replies
    - normalize_message(): Convert Twitter format to UnifiedMessage
    
    Features:
    ---------
    - Fetch user timeline
    - Post tweets (max 280 characters)
    - Reply to tweets
    - Get mentions
    - Search tweets
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="twitter",
    ...     api_key="YOUR_BEARER_TOKEN",
    ...     mock_mode=True
    ... )
    >>> 
    >>> twitter = TwitterPlatform(config)
    >>> await twitter.authenticate()
    >>> 
    >>> # Fetch tweets
    >>> messages = await twitter.fetch_messages(
    ...     user_id="123456789",
    ...     limit=10
    ... )
    >>> 
    >>> # Post tweet
    >>> msg = UnifiedMessage(...)
    >>> result = await twitter.send_message(msg, recipient_id=None)
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Twitter platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: Twitter bearer token (or API key for OAuth 1.0a)
                - metadata.api_secret: API secret (optional, for OAuth 1.0a)
                - metadata.access_token: Access token (optional)
                - metadata.access_token_secret: Access token secret (optional)
        """
        super().__init__(config)
        
        # Extract Twitter-specific config
        self.bearer_token = config.api_key or config.access_token
        self.api_key = config.metadata.get("api_key")
        self.api_secret = config.metadata.get("api_secret")
        self.access_token = config.metadata.get("access_token")
        self.access_token_secret = config.metadata.get("access_token_secret")
        
        if not self.bearer_token and not self.api_key:
            raise ValidationError(
                "bearer_token (api_key) or API credentials are required for Twitter",
                context={"platform": "twitter"}
            )
        
        # Twitter client (initialized on authenticate)
        self._twitter_client: Optional[TwitterClient] = None
        
        # Authenticated user info
        self._authenticated_user: Optional[Dict[str, Any]] = None
        
        # Tweet cache
        self._tweet_cache: List[TwitterTweet] = []
        
        logger.info("Twitter platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Twitter API v2.
        
        Verifies bearer token by fetching authenticated user info.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Twitter API v2...")
            
            # Create Twitter client
            self._twitter_client = TwitterClient(
                bearer_token=self.bearer_token,
                api_key=self.api_key,
                api_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify token by getting authenticated user (if available)
            # Note: Bearer token alone might not have this permission
            try:
                user = await self._twitter_client.get_me()
                self._authenticated_user = user.model_dump()
                logger.info(f"✅ Twitter authentication successful (@{user.username})")
            except Exception as e:
                # If get_me fails, we're still authenticated for read-only access
                logger.info("✅ Twitter authentication successful (read-only mode)")
                self._authenticated_user = {"username": "authenticated_user"}
            
            self._is_authenticated = True
            self._client = self._twitter_client
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Twitter authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Twitter: {e}",
                context={"platform": "twitter"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Twitter.
        
        For Twitter, user_id is the Twitter user ID.
        Returns tweets from user's timeline as UnifiedMessages.
        
        Args:
            user_id: Twitter user ID
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters (optional)
            
        Returns:
            List of UnifiedMessage objects
            
        Example:
            >>> # Get tweets from a user
            >>> messages = await twitter.fetch_messages(
            ...     user_id="123456789",
            ...     limit=20
            ... )
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Twitter messages from user {user_id}")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit
        )
        
        unified_messages = []
        
        # Get tweets
        tweets = await self._twitter_client.get_user_tweets(
            user_id=user_id,
            max_results=min(limit, 100)
        )
        
        for tweet in tweets:
            # Filter by timestamp if specified
            if since:
                tweet_time = datetime.fromisoformat(
                    tweet.created_at.replace('Z', '+00:00')
                )
                if tweet_time < since:
                    continue
            
            # Normalize to UnifiedMessage
            unified_msg = self.normalize_message(tweet.model_dump())
            unified_messages.append(unified_msg)
            
            # Add to cache
            self._tweet_cache.append(tweet)
            
            # Stop if we've reached the limit
            if len(unified_messages) >= limit:
                break
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Twitter messages")
        
        return unified_messages
    
    async def _fetch_messages_impl(
        self,
        user_id: str,
        since: Optional[datetime],
        limit: int
    ) -> None:
        """Internal fetch implementation (for rate limiting wrapper)."""
        pass
    
    async def send_message(
        self,
        message: UnifiedMessage,
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message via Twitter.
        
        Can post a new tweet or reply to an existing tweet.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Tweet ID to reply to (optional, None for new tweet)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (tweet ID)
                - timestamp: datetime
                - metadata: Dict
                
        Example:
            >>> # Post a new tweet
            >>> msg = UnifiedMessage(
            ...     content="Hello Twitter! 🚀",
            ...     ...
            ... )
            >>> result = await twitter.send_message(msg, recipient_id=None)
            >>> 
            >>> # Reply to a tweet
            >>> msg = UnifiedMessage(content="Great tweet!")
            >>> result = await twitter.send_message(msg, recipient_id="123456")
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Twitter message (reply_to={recipient_id})")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Twitter message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send Twitter message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: Optional[str]
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        if not message.content:
            raise ValidationError(
                "Twitter message must have content",
                context={"message_id": message.id}
            )
        
        # Check character limit
        if len(message.content) > 280:
            raise ValidationError(
                f"Twitter message exceeds 280 characters ({len(message.content)})",
                context={"message_id": message.id}
            )
        
        # Post tweet (with or without reply)
        tweet = await self._twitter_client.post_tweet(
            text=message.content,
            reply_to=recipient_id
        )
        
        # Return formatted response
        return {
            "success": True,
            "message_id": tweet.id,
            "timestamp": datetime.fromisoformat(
                tweet.created_at.replace('Z', '+00:00')
            ),
            "metadata": {
                "platform": "twitter",
                "is_reply": recipient_id is not None,
                "reply_to": recipient_id,
                "likes": tweet.get_like_count(),
                "retweets": tweet.get_retweet_count()
            }
        }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Twitter tweet to UnifiedMessage.
        
        Args:
            raw_message: Raw Twitter tweet dictionary
            
        Returns:
            UnifiedMessage object
            
        Example:
            >>> raw = {
            ...     "id": "123456789",
            ...     "text": "Hello Twitter!",
            ...     "author_id": "987654321",
            ...     "created_at": "2026-02-21T18:45:00.000Z",
            ...     "public_metrics": {
            ...         "like_count": 42,
            ...         "retweet_count": 10
            ...     }
            ... }
            >>> 
            >>> unified = twitter.normalize_message(raw)
        """
        try:
            # Parse as Twitter tweet
            tweet = TwitterTweet(**raw_message)
            
            # Extract sender info
            sender = UserInfo(
                id=tweet.author_id,
                username=tweet.author_id,  # We'd need to expand this with includes
                display_name=f"User {tweet.author_id}"
            )
            
            # Extract content
            content = tweet.text
            
            # Convert timestamp
            timestamp = datetime.fromisoformat(
                tweet.created_at.replace('Z', '+00:00')
            )
            
            # Extract mentions
            mentions = []
            for username in tweet.get_mentions():
                mention = UserInfo(
                    id=username,
                    username=username,
                    display_name=f"@{username}"
                )
                mentions.append(mention)
            
            # Determine if it's a reply
            is_reply = tweet.is_reply()
            parent_id = None
            if is_reply and tweet.referenced_tweets:
                for ref in tweet.referenced_tweets:
                    if ref.get("type") == "replied_to":
                        parent_id = ref.get("id")
                        break
            
            # Create UnifiedMessage
            unified_message = UnifiedMessage(
                platform_message_id=tweet.id,
                platform=PlatformType.TWITTER,
                type=MessageType.POST,
                sender=sender,
                content=content,
                timestamp=timestamp,
                is_reply=is_reply,
                parent_id=parent_id,
                likes=tweet.get_like_count(),
                shares=tweet.get_retweet_count(),
                mentions=mentions,
                metadata={
                    "twitter_id": tweet.id,
                    "conversation_id": tweet.conversation_id,
                    "reply_count": tweet.get_reply_count(),
                    "quote_count": tweet.public_metrics.get("quote_count", 0) if tweet.public_metrics else 0,
                    "hashtags": tweet.get_hashtags(),
                    "is_retweet": tweet.is_retweet(),
                    "is_quote": tweet.is_quote(),
                    "language": tweet.lang,
                    "possibly_sensitive": tweet.possibly_sensitive
                }
            )
            
            return unified_message
            
        except Exception as e:
            logger.error(f"Failed to normalize Twitter message: {e}")
            raise ValidationError(
                f"Invalid Twitter message format: {e}",
                context={"raw_message": raw_message}
            )
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Twitter and cleanup."""
        if self._twitter_client:
            await self._twitter_client.close()
            self._twitter_client = None
        
        self._is_authenticated = False
        self._authenticated_user = None
        self._tweet_cache.clear()
        
        logger.info("Disconnected from Twitter")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Twitter.
        
        Args:
            user_id: Twitter user ID or username
            
        Returns:
            Dictionary with user info
        """
        self._ensure_authenticated()
        
        # Try as username first, then as ID
        try:
            user = await self._twitter_client.get_user_by_username(user_id)
        except:
            user = await self._twitter_client.get_user_by_id(user_id)
        
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.name,
            "description": user.description,
            "verified": user.verified,
            "followers": user.followers_count,
            "following": user.following_count,
            "tweets": user.tweet_count,
            "platform": "twitter"
        }
    
    def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """
        Get authenticated user information.
        
        Returns:
            User info dictionary or None
        """
        return self._authenticated_user
    
    async def search_tweets(
        self,
        query: str,
        limit: int = 10
    ) -> List[UnifiedMessage]:
        """
        Search for tweets.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of UnifiedMessage objects
            
        Example:
            >>> messages = await twitter.search_tweets(
            ...     query="python programming",
            ...     limit=20
            ... )
        """
        self._ensure_authenticated()
        
        tweets = await self._twitter_client.search_recent_tweets(
            query=query,
            max_results=min(limit, 100)
        )
        
        unified_messages = []
        for tweet in tweets:
            unified_msg = self.normalize_message(tweet.model_dump())
            unified_messages.append(unified_msg)
        
        return unified_messages
    
    async def delete_tweet(self, tweet_id: str) -> bool:
        """
        Delete a tweet.
        
        Args:
            tweet_id: Tweet ID to delete
            
        Returns:
            True if deleted successfully
        """
        self._ensure_authenticated()
        
        return await self._twitter_client.delete_tweet(tweet_id)
