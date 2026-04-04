"""
Facebook Platform - Platform Adapter
=====================================

Facebook platform adapter implementing BasePlatform interface.

This integrates Facebook Graph API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 10
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.facebook.client import FacebookClient
from socialspace_agent.platforms.facebook.models import FacebookPost, FacebookComment
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


class FacebookPlatform(BasePlatform):
    """
    Facebook Graph API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify access token
    - fetch_messages(): Get posts and comments
    - send_message(): Create posts or comments
    - normalize_message(): Convert Facebook format to UnifiedMessage
    
    Features:
    ---------
    - Fetch page posts
    - Fetch comments on posts
    - Create posts
    - Create comments
    - Get page info
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="facebook",
    ...     api_key="YOUR_ACCESS_TOKEN",
    ...     metadata={"page_id": "YOUR_PAGE_ID"},
    ...     mock_mode=True
    ... )
    >>> 
    >>> facebook = FacebookPlatform(config)
    >>> await facebook.authenticate()
    >>> 
    >>> # Fetch posts from page
    >>> messages = await facebook.fetch_messages(
    ...     user_id="page_id",
    ...     limit=10
    ... )
    >>> 
    >>> # Create post
    >>> msg = UnifiedMessage(...)
    >>> result = await facebook.send_message(msg, recipient_id="page_id")
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize Facebook platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: Facebook access token
                - metadata.page_id: Facebook page ID
        """
        super().__init__(config)
        
        # Extract Facebook-specific config
        self.access_token = config.api_key or config.access_token
        self.page_id = config.metadata.get("page_id")
        
        if not self.access_token:
            raise ValidationError(
                "access_token (api_key) is required for Facebook",
                context={"platform": "facebook"}
            )
        
        # Facebook client (initialized on authenticate)
        self._facebook_client: Optional[FacebookClient] = None
        
        # Page info cache
        self._page_info: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._post_cache: List[FacebookPost] = []
        self._comment_cache: List[FacebookComment] = []
        
        logger.info("Facebook platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Facebook Graph API.
        
        Verifies access token by fetching user/page information.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Facebook Graph API...")
            
            # Create Facebook client
            self._facebook_client = FacebookClient(
                access_token=self.access_token,
                page_id=self.page_id,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify token by getting user info
            user = await self._facebook_client.get_me()
            
            # If page_id is provided, get page info too
            if self.page_id:
                page = await self._facebook_client.get_page_info()
                self._page_info = page.model_dump()
                logger.info(f"✅ Facebook authentication successful (Page: {page.name})")
            else:
                logger.info(f"✅ Facebook authentication successful (User: {user.name})")
            
            self._is_authenticated = True
            self._client = self._facebook_client
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Facebook authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with Facebook: {e}",
                context={"platform": "facebook"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Facebook.
        
        For Facebook, user_id can be:
        - Page ID (to fetch posts)
        - Post ID (to fetch comments)
        
        Args:
            user_id: Page ID or Post ID
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters:
                - fetch_type: "posts" or "comments" (default: "posts")
            
        Returns:
            List of UnifiedMessage objects
            
        Example:
            >>> # Get posts from page
            >>> messages = await facebook.fetch_messages(
            ...     user_id="page_id",
            ...     limit=10
            ... )
            >>> 
            >>> # Get comments from post
            >>> messages = await facebook.fetch_messages(
            ...     user_id="post_id",
            ...     limit=50,
            ...     filters={"fetch_type": "comments"}
            ... )
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching Facebook messages from {user_id}")
        
        # Use rate limiting
        await self._rate_limited_call(
            self._fetch_messages_impl,
            user_id,
            since,
            limit,
            filters
        )
        
        unified_messages = []
        
        # Parse filters
        filters = filters or {}
        fetch_type = filters.get("fetch_type", "posts")
        
        if fetch_type == "comments":
            # Fetch comments from post
            comments = await self._facebook_client.get_post_comments(
                post_id=user_id,
                limit=min(limit, 100)
            )
            
            for comment in comments:
                # Filter by timestamp if specified
                if since:
                    comment_time = datetime.fromisoformat(
                        comment.created_time.replace('Z', '+00:00')
                    )
                    if comment_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_comment(comment)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._comment_cache.append(comment)
        
        else:
            # Fetch posts from page
            posts = await self._facebook_client.get_page_posts(
                page_id=user_id,
                limit=min(limit, 100)
            )
            
            for post in posts:
                # Filter by timestamp if specified
                if since:
                    post_time = datetime.fromisoformat(
                        post.created_time.replace('Z', '+00:00')
                    )
                    if post_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_post(post)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._post_cache.append(post)
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} Facebook messages")
        
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
        Send a message via Facebook.
        
        Can create a post or a comment depending on recipient_id.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Either:
                - Page ID (for new post)
                - Post ID (for comment on post)
                - Comment ID (for reply to comment)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (post/comment ID)
                - timestamp: datetime
                - metadata: Dict
                
        Example:
            >>> # Create post
            >>> msg = UnifiedMessage(content="Hello Facebook!")
            >>> result = await facebook.send_message(msg, "page_id")
            >>> 
            >>> # Create comment
            >>> msg = UnifiedMessage(content="Great post!")
            >>> result = await facebook.send_message(msg, "post_id")
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending Facebook message to {recipient_id}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ Facebook message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send Facebook message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        if not message.content:
            raise ValidationError(
                "Facebook message must have content",
                context={"message_id": message.id}
            )
        
        # Check if recipient_id looks like a post/comment ID (contains underscore)
        # or a page ID (numeric only)
        if "_" in recipient_id or message.is_reply:
            # Create comment on post or reply to comment
            comment = await self._facebook_client.create_comment(
                post_id=recipient_id,
                message=message.content
            )
            
            return {
                "success": True,
                "message_id": comment.id,
                "timestamp": datetime.fromisoformat(
                    comment.created_time.replace('Z', '+00:00')
                ),
                "metadata": {
                    "platform": "facebook",
                    "type": "comment",
                    "parent_id": recipient_id
                }
            }
        
        else:
            # Create post on page
            link = message.metadata.get("link") if message.metadata else None
            
            post = await self._facebook_client.create_post(
                message=message.content,
                page_id=recipient_id,
                link=link
            )
            
            return {
                "success": True,
                "message_id": post.id,
                "timestamp": datetime.fromisoformat(
                    post.created_time.replace('Z', '+00:00')
                ),
                "metadata": {
                    "platform": "facebook",
                    "type": "post",
                    "page_id": recipient_id,
                    "permalink": post.permalink_url
                }
            }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert Facebook post or comment to UnifiedMessage.
        
        Args:
            raw_message: Raw Facebook post or comment dictionary
            
        Returns:
            UnifiedMessage object
            
        Example:
            >>> raw = {
            ...     "id": "123456_789012",
            ...     "message": "Hello Facebook!",
            ...     "from": {"id": "123456", "name": "John Doe"},
            ...     "created_time": "2026-02-22T18:00:00+0000"
            ... }
            >>> 
            >>> unified = facebook.normalize_message(raw)
        """
        try:
            # Check if it's a post or comment based on structure
            if "story" in raw_message or "permalink_url" in raw_message:
                # It's a post
                post = FacebookPost(**raw_message)
                return self._normalize_post(post)
            else:
                # It's a comment
                comment = FacebookComment(**raw_message)
                return self._normalize_comment(comment)
                
        except Exception as e:
            logger.error(f"Failed to normalize Facebook message: {e}")
            raise ValidationError(
                f"Invalid Facebook message format: {e}",
                context={"raw_message": raw_message}
            )
    
    def _normalize_post(self, post: FacebookPost) -> UnifiedMessage:
        """Convert Facebook post to UnifiedMessage."""
        
        # Extract sender info
        author_name = post.get_author_name() or "Unknown"
        author_id = post.from_.get("id") if post.from_ else "unknown"
        
        sender = UserInfo(
            id=author_id,
            username=author_id,
            display_name=author_name
        )
        
        # Extract content
        content = post.message or post.story or ""
        
        # Extract media if present
        media_list = []
        if post.full_picture:
            media = MediaAttachment(
                url=post.full_picture,
                type="image"
            )
            media_list.append(media)
        
        # Convert timestamp
        timestamp = datetime.fromisoformat(
            post.created_time.replace('Z', '+00:00')
        )
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=post.id,
            platform=PlatformType.FACEBOOK,
            type=MessageType.POST,
            sender=sender,
            content=content,
            media=media_list,
            timestamp=timestamp,
            likes=post.get_like_count(),
            shares=post.get_share_count(),
            metadata={
                "facebook_post_id": post.id,
                "post_type": post.type,
                "comment_count": post.get_comment_count(),
                "permalink": post.permalink_url
            }
        )
        
        return unified_message
    
    def _normalize_comment(self, comment: FacebookComment) -> UnifiedMessage:
        """Convert Facebook comment to UnifiedMessage."""
        
        # Extract sender info
        sender = UserInfo(
            id=comment.get_author_id(),
            username=comment.get_author_name(),
            display_name=comment.get_author_name()
        )
        
        # Convert timestamp
        timestamp = datetime.fromisoformat(
            comment.created_time.replace('Z', '+00:00')
        )
        
        # Check if reply
        is_reply = comment.is_reply()
        parent_id = comment.parent.get("id") if comment.parent else None
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=comment.id,
            platform=PlatformType.FACEBOOK,
            type=MessageType.COMMENT,
            sender=sender,
            content=comment.message,
            timestamp=timestamp,
            is_reply=is_reply,
            parent_id=parent_id,
            likes=comment.like_count,
            metadata={
                "facebook_comment_id": comment.id,
                "reply_count": comment.comment_count
            }
        )
        
        return unified_message
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from Facebook and cleanup."""
        if self._facebook_client:
            await self._facebook_client.close()
            self._facebook_client = None
        
        self._is_authenticated = False
        self._page_info = None
        self._post_cache.clear()
        self._comment_cache.clear()
        
        logger.info("Disconnected from Facebook")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Facebook.
        
        Args:
            user_id: Facebook user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "facebook"
        }
    
    def get_page_info(self) -> Optional[Dict[str, Any]]:
        """
        Get cached page information.
        
        Returns:
            Page info dictionary or None
        """
        return self._page_info
    
    async def create_post(
        self,
        text: str,
        link: Optional[str] = None,
        page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a post on Facebook page.
        
        Convenience method for posting.
        
        Args:
            text: Post text
            link: Optional link to share
            page_id: Page ID (uses self.page_id if not provided)
            
        Returns:
            Post result dictionary
        """
        self._ensure_authenticated()
        
        pid = page_id or self.page_id
        if not pid:
            raise ValueError("page_id is required")
        
        post = await self._facebook_client.create_post(
            message=text,
            page_id=pid,
            link=link
        )
        
        return {
            "success": True,
            "post_id": post.id,
            "permalink": post.permalink_url
        }
    
    async def get_post_info(self, post_id: str) -> Dict[str, Any]:
        """
        Get post information.
        
        Args:
            post_id: Facebook post ID
            
        Returns:
            Dictionary with post info
        """
        self._ensure_authenticated()
        
        post = await self._facebook_client.get_post(post_id)
        
        return {
            "id": post.id,
            "message": post.message,
            "author": post.get_author_name(),
            "created_time": post.created_time,
            "likes": post.get_like_count(),
            "comments": post.get_comment_count(),
            "shares": post.get_share_count(),
            "permalink": post.permalink_url,
            "platform": "facebook"
        }
