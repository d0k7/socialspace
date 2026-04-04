"""
Reddit Platform - Platform Adapter
===================================

Reddit platform adapter implementing BasePlatform interface.

This integrates Reddit OAuth API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 7
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.reddit.client import RedditClient
from socialspace_agent.platforms.reddit.models import RedditSubmission, RedditComment
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


class RedditPlatform(BasePlatform):
    """
    Reddit OAuth API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify OAuth credentials
    - fetch_messages(): Get submissions and comments
    - send_message(): Post submissions or comments
    - normalize_message(): Convert Reddit format to UnifiedMessage
    
    Features:
    ---------
    - Fetch submissions from subreddits
    - Fetch comments on submissions
    - Post text/link submissions
    - Post comments
    - Vote on posts/comments
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="reddit",
    ...     api_key="client_id",
    ...     metadata={
    ...         "client_secret": "secret",
    ...         "user_agent": "SocialSpace/1.0",
    ...         "username": "your_username",
    ...         "password": "your_password"
    ...     }
    ... )
    >>> 
    >>> reddit = RedditPlatform(config)
    >>> await reddit.authenticate()
    >>> 
    >>> # Fetch submissions from subreddit
    >>> messages = await reddit.fetch_messages(
    ...     user_id="python",  # subreddit name
    ...     limit=10
    ... )
    >>> 
    >>> # Post a comment
    >>> msg = UnifiedMessage(...)
    >>> result = await reddit.send_message(msg, recipient_id="t3_xxxxx")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Reddit platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: Reddit client ID
                - metadata.client_secret: Reddit client secret
                - metadata.user_agent: User agent string
                - metadata.username: Reddit username (optional)
                - metadata.password: Reddit password (optional)
        """
        super().__init__(config)
        
        # Extract Reddit-specific config
        self.client_id = config.api_key
        self.client_secret = config.metadata.get("client_secret")
        self.user_agent = config.metadata.get("user_agent", "SocialSpace/1.0")
        self.username = config.metadata.get("username")
        self.password = config.metadata.get("password")
        
        if not self.client_id:
            raise ValidationError(
                "client_id (api_key) is required for Reddit",
                context={"platform": "reddit"}
            )
        
        if not self.client_secret:
            raise ValidationError(
                "client_secret is required in config.metadata",
                context={"platform": "reddit"}
            )
        
        # Reddit client (initialized on authenticate)
        self._reddit_client: Optional[RedditClient] = None
        
        # Message cache
        self._submission_cache: List[RedditSubmission] = []
        self._comment_cache: List[RedditComment] = []
        
        logger.info("Reddit platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Reddit OAuth API.
        
        Uses OAuth 2.0 password grant or client credentials.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Reddit OAuth API...")
            
            # Create Reddit client
            self._reddit_client = RedditClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                username=self.username,
                password=self.password,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Authenticate
            await self._reddit_client.authenticate()
            
            self._is_authenticated = True
            self._client = self._reddit_client
            
            logger.info("✅ Reddit authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Reddit authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Reddit: {e}",
                context={"platform": "reddit"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Reddit.
        
        For Reddit, user_id is the subreddit name.
        Returns submissions and their comments as UnifiedMessages.
        
        Args:
            user_id: Subreddit name (e.g., "python", "technology")
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters:
                - sort: Sort method (hot, new, top, rising)
                - include_comments: Include comments (default: True)
            
        Returns:
            List of UnifiedMessage objects
            
        Example:
            >>> # Get hot posts from r/python
            >>> messages = await reddit.fetch_messages(
            ...     user_id="python",
            ...     limit=10,
            ...     filters={"sort": "hot"}
            ... )
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Reddit messages from r/{user_id}")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit,
            filters
        )
        
        # Parse filters
        filters = filters or {}
        sort = filters.get("sort", "hot")
        include_comments = filters.get("include_comments", True)
        
        # Subreddit name
        subreddit = user_id
        
        unified_messages = []
        
        # Get submissions
        submissions = await self._reddit_client.get_subreddit_submissions(
            subreddit=subreddit,
            sort=sort,
            limit=min(limit, 100)
        )
        
        for submission in submissions:
            # Filter by timestamp if specified
            if since:
                submission_time = datetime.fromtimestamp(
                    submission.created_utc,
                    tz=timezone.utc
                )
                if submission_time < since:
                    continue
            
            # Normalize submission to UnifiedMessage
            unified_msg = self._normalize_submission(submission)
            unified_messages.append(unified_msg)
            
            # Add to cache
            self._submission_cache.append(submission)
            
            # Get comments if requested
            if include_comments:
                comments = await self._reddit_client.get_submission_comments(
                    submission_id=submission.id,
                    limit=10  # Limit comments per submission
                )
                
                for comment in comments:
                    comment_msg = self._normalize_comment(comment)
                    unified_messages.append(comment_msg)
                    self._comment_cache.append(comment)
            
            # Stop if we've reached the limit
            if len(unified_messages) >= limit:
                break
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Reddit messages")
        
        return unified_messages[:limit]
    
    async def _fetch_messages_impl(
        self,
        user_id: str,
        since: Optional[datetime],
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> None:
        """Internal fetch implementation (for rate limiting wrapper)."""
        pass
    
    async def send_message(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """
        Send a message via Reddit.
        
        Can post a submission or a comment depending on recipient_id.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Either:
                - Subreddit name (for new submission)
                - Thing ID like "t3_xxxxx" (for comment on submission)
                - Thing ID like "t1_xxxxx" (for reply to comment)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (submission/comment ID)
                - timestamp: datetime
                - metadata: Dict
                
        Example:
            >>> # Post a submission
            >>> msg = UnifiedMessage(
            ...     content="My first Reddit post!",
            ...     metadata={"title": "Hello Reddit!"}
            ... )
            >>> result = await reddit.send_message(msg, "python")
            >>> 
            >>> # Post a comment
            >>> msg = UnifiedMessage(content="Great post!")
            >>> result = await reddit.send_message(msg, "t3_xxxxx")
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Reddit message to {recipient_id}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Reddit message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send Reddit message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        if not message.content:
            raise ValidationError(
                "Reddit message must have content",
                context={"message_id": message.id}
            )
        
        # Check if recipient_id is a thing ID (comment) or subreddit (submission)
        if recipient_id.startswith("t3_") or recipient_id.startswith("t1_"):
            # Post comment
            comment = await self._reddit_client.post_comment(
                parent_id=recipient_id,
                text=message.content
            )
            
            return {
                "success": True,
                "message_id": comment.name,
                "timestamp": datetime.fromtimestamp(
                    comment.created_utc,
                    tz=timezone.utc
                ),
                "metadata": {
                    "platform": "reddit",
                    "type": "comment",
                    "parent_id": recipient_id
                }
            }
        
        else:
            # Post submission
            subreddit = recipient_id
            title = message.metadata.get("title", "Post from SocialSpace")
            
            # Check if it's a link post or text post
            if message.metadata.get("url"):
                # Link post
                submission = await self._reddit_client.submit_link_post(
                    subreddit=subreddit,
                    title=title,
                    url=message.metadata["url"]
                )
            else:
                # Text post
                submission = await self._reddit_client.submit_text_post(
                    subreddit=subreddit,
                    title=title,
                    text=message.content
                )
            
            return {
                "success": True,
                "message_id": submission.name,
                "timestamp": datetime.fromtimestamp(
                    submission.created_utc,
                    tz=timezone.utc
                ),
                "metadata": {
                    "platform": "reddit",
                    "type": "submission",
                    "subreddit": subreddit,
                    "permalink": submission.get_full_url()
                }
            }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Reddit submission or comment to UnifiedMessage.
        
        Args:
            raw_message: Raw Reddit submission or comment dictionary
            
        Returns:
            UnifiedMessage object
            
        Example:
            >>> raw = {
            ...     "id": "abc123",
            ...     "name": "t3_abc123",
            ...     "subreddit": "python",
            ...     "author": "john_doe",
            ...     "title": "My Python project",
            ...     "selftext": "Check out my project!",
            ...     "created_utc": 1708500000,
            ...     "score": 42
            ... }
            >>> 
            >>> unified = reddit.normalize_message(raw)
        """
        try:
            # Check if it's a submission or comment
            if "title" in raw_message:
                # It's a submission
                submission = RedditSubmission(**raw_message)
                return self._normalize_submission(submission)
            else:
                # It's a comment
                comment = RedditComment(**raw_message)
                return self._normalize_comment(comment)
                
        except Exception as e:
            logger.error(f"Failed to normalize Reddit message: {e}")
            raise ValidationError(
                f"Invalid Reddit message format: {e}",
                context={"raw_message": raw_message}
            )
    
    def _normalize_submission(self, submission: RedditSubmission) -> UnifiedMessage:
        """Convert Reddit submission to UnifiedMessage."""
        
        # Extract sender info
        sender = UserInfo(
            id=submission.author,
            username=submission.author,
            display_name=f"u/{submission.author}"
        )
        
        # Content is title + selftext
        content = submission.title
        if submission.selftext:
            content += f"\n\n{submission.selftext}"
        
        # Extract media if present
        media_list = []
        if submission.url and not submission.is_self:
            media = MediaAttachment(
                url=submission.url,
                type="link"
            )
            media_list.append(media)
        
        # Convert timestamp
        timestamp = datetime.fromtimestamp(
            submission.created_utc,
            tz=timezone.utc
        )
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=submission.name,
            platform=PlatformType.REDDIT,
            type=MessageType.POST,
            sender=sender,
            content=content,
            media=media_list,
            timestamp=timestamp,
            is_edited=submission.is_edited(),
            likes=submission.score,
            metadata={
                "reddit_id": submission.id,
                "subreddit": submission.subreddit,
                "permalink": submission.get_full_url(),
                "num_comments": submission.num_comments,
                "upvote_ratio": submission.upvote_ratio,
                "is_video": submission.is_video,
                "locked": submission.locked,
                "stickied": submission.stickied
            }
        )
        
        return unified_message
    
    def _normalize_comment(self, comment: RedditComment) -> UnifiedMessage:
        """Convert Reddit comment to UnifiedMessage."""
        
        # Extract sender info
        sender = UserInfo(
            id=comment.author,
            username=comment.author,
            display_name=f"u/{comment.author}"
        )
        
        # Convert timestamp
        timestamp = datetime.fromtimestamp(
            comment.created_utc,
            tz=timezone.utc
        )
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=comment.name,
            platform=PlatformType.REDDIT,
            type=MessageType.COMMENT,
            sender=sender,
            content=comment.body,
            timestamp=timestamp,
            is_edited=comment.is_edited(),
            is_reply=True,
            parent_id=comment.parent_id,
            likes=comment.score,
            metadata={
                "reddit_id": comment.id,
                "subreddit": comment.subreddit,
                "link_id": comment.link_id,
                "is_top_level": comment.is_top_level(),
                "controversiality": comment.controversiality,
                "stickied": comment.stickied
            }
        )
        
        return unified_message
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Reddit and cleanup."""
        if self._reddit_client:
            await self._reddit_client.close()
            self._reddit_client = None
        
        self._is_authenticated = False
        self._submission_cache.clear()
        self._comment_cache.clear()
        
        logger.info("Disconnected from Reddit")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Reddit.
        
        Args:
            user_id: Reddit username
            
        Returns:
            Dictionary with user info
        """
        self._ensure_authenticated()
        
        user = await self._reddit_client.get_user_info(user_id)
        
        return {
            "id": user.id,
            "username": user.name,
            "display_name": user.get_username(),
            "karma": user.total_karma(),
            "platform": "reddit"
        }
    
    async def vote_on_post(
        self,
        thing_id: str,
        upvote: bool = True
    ) -> bool:
        """
        Vote on a submission or comment.
        
        Args:
            thing_id: Thing ID (t3_ or t1_)
            upvote: True for upvote, False for downvote
            
        Returns:
            True if successful
            
        Example:
            >>> # Upvote a submission
            >>> await reddit.vote_on_post("t3_abc123", upvote=True)
            >>> 
            >>> # Downvote a comment
            >>> await reddit.vote_on_post("t1_xyz789", upvote=False)
        """
        self._ensure_authenticated()
        
        direction = 1 if upvote else -1
        
        return await self._reddit_client.vote(thing_id, direction)
    
    async def get_subreddit_info(self, subreddit: str) -> Dict[str, Any]:
        """
        Get subreddit information.
        
        Args:
            subreddit: Subreddit name (without r/)
            
        Returns:
            Dictionary with subreddit info
        """
        self._ensure_authenticated()
        
        sub = await self._reddit_client.get_subreddit_info(subreddit)
        
        return {
            "id": sub.id,
            "name": sub.name,
            "display_name": sub.get_subreddit_name(),
            "title": sub.title,
            "description": sub.public_description,
            "subscribers": sub.subscribers,
            "platform": "reddit"
        }
