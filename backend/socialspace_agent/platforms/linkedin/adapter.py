"""
LinkedIn Platform - Platform Adapter
=====================================

LinkedIn platform adapter implementing BasePlatform interface.

This integrates LinkedIn API with SocialSpace Agent.

Author: Dheeraj Mishra
Created: February 22-23, 2026
Session: 11
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.linkedin.client import LinkedInClient
from socialspace_agent.platforms.linkedin.models import LinkedInPost, LinkedInComment
from socialspace_agent.models import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
)
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    ValidationError,
)
from socialspace_agent.utils.config import PlatformConfig

logger = logging.getLogger(__name__)


class LinkedInPlatform(BasePlatform):
    """
    LinkedIn API platform adapter.
    
    Inherits from BasePlatform and implements:
    - authenticate(): Verify access token
    - fetch_messages(): Get posts and comments
    - send_message(): Create posts or comments
    - normalize_message(): Convert LinkedIn format to UnifiedMessage
    
    Features:
    ---------
    - Fetch user posts
    - Fetch comments on posts
    - Create posts
    - Create comments
    - Get profile info
    - Automatic rate limiting (inherited)
    - Automatic retry logic (inherited)
    
    Usage:
    ------
    >>> config = PlatformConfig(
    ...     platform="linkedin",
    ...     api_key="YOUR_ACCESS_TOKEN",
    ...     mock_mode=True
    ... )
    >>> 
    >>> linkedin = LinkedInPlatform(config)
    >>> await linkedin.authenticate()
    >>> 
    >>> # Fetch posts
    >>> messages = await linkedin.fetch_messages(
    ...     user_id="person_id",
    ...     limit=10
    ... )
    >>> 
    >>> # Create post
    >>> msg = UnifiedMessage(...)
    >>> result = await linkedin.send_message(msg)
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize LinkedIn platform adapter.
        
        Args:
            config: Platform configuration with:
                - api_key: LinkedIn access token
                - metadata.organization_id: Organization ID (optional)
        """
        super().__init__(config)
        
        # Extract LinkedIn-specific config
        self.access_token = config.api_key or config.access_token
        self.organization_id = config.metadata.get("organization_id")
        
        if not self.access_token:
            raise ValidationError(
                "access_token (api_key) is required for LinkedIn",
                context={"platform": "linkedin"}
            )
        
        # LinkedIn client (initialized on authenticate)
        self._linkedin_client: Optional[LinkedInClient] = None
        
        # Profile cache
        self._profile: Optional[Dict[str, Any]] = None
        
        # Message cache
        self._post_cache: List[LinkedInPost] = []
        self._comment_cache: List[LinkedInComment] = []
        
        logger.info("LinkedIn platform initialized")
    
    # ============================================
    # REQUIRED: ABSTRACT METHODS
    # ============================================
    
    async def authenticate(self) -> bool:
        """
        Authenticate with LinkedIn API.
        
        Verifies access token by fetching user profile.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with LinkedIn API...")
            
            # Create LinkedIn client
            self._linkedin_client = LinkedInClient(
                access_token=self.access_token,
                organization_id=self.organization_id,
                timeout=self.config.timeout,
                mock_mode=self.config.mock_mode
            )
            
            # Verify token by getting profile
            profile = await self._linkedin_client.get_profile()
            self._profile = profile.model_dump()
            
            self._is_authenticated = True
            self._client = self._linkedin_client
            
            logger.info(f"✅ LinkedIn authentication successful ({profile.get_full_name()})")
            return True
            
        except Exception as e:
            logger.error(f"❌ LinkedIn authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to authenticate with LinkedIn: {e}",
                context={"platform": "linkedin"}
            )
    
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from LinkedIn.
        
        For LinkedIn, user_id can be:
        - Person URN (to fetch posts)
        - Post URN (to fetch comments)
        
        Args:
            user_id: Person URN or Post URN
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages
            filters: Additional filters:
                - fetch_type: "posts" or "comments" (default: "posts")
            
        Returns:
            List of UnifiedMessage objects
        """
        self._ensure_authenticated()
        
        logger.info(f"Fetching LinkedIn messages from {user_id}")
        
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
            comments = await self._linkedin_client.get_comments(
                object_urn=user_id,
                count=min(limit, 100)
            )
            
            for comment in comments:
                # Filter by timestamp if specified
                if since and comment.created_at:
                    comment_time = datetime.fromtimestamp(
                        comment.created_at / 1000,
                        tz=timezone.utc
                    )
                    if comment_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_comment(comment)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._comment_cache.append(comment)
        
        else:
            # Fetch posts
            posts = await self._linkedin_client.get_posts(
                author=user_id if user_id != "me" else None,
                count=min(limit, 100)
            )
            
            for post in posts:
                # Filter by timestamp if specified
                if since and post.created_at:
                    post_time = datetime.fromtimestamp(
                        post.created_at / 1000,
                        tz=timezone.utc
                    )
                    if post_time < since:
                        continue
                
                # Normalize to UnifiedMessage
                unified_msg = self._normalize_post(post)
                unified_messages.append(unified_msg)
                
                # Add to cache
                self._post_cache.append(post)
        
        self._stats["messages_fetched"] += len(unified_messages)
        
        logger.info(f"✅ Fetched {len(unified_messages)} LinkedIn messages")
        
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
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message via LinkedIn.
        
        Can create a post or a comment.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Post URN (for comment) or None (for post)
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (post/comment ID)
                - timestamp: datetime
                - metadata: Dict
        """
        self._ensure_authenticated()
        
        logger.info(f"Sending LinkedIn message to {recipient_id or 'timeline'}")
        
        try:
            # Use rate limiting
            response = await self._rate_limited_call(
                self._send_message_impl,
                message,
                recipient_id
            )
            
            self._stats["messages_sent"] += 1
            
            logger.info(f"✅ LinkedIn message sent: {response['message_id']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to send LinkedIn message: {e}")
            raise
    
    async def _send_message_impl(
        self,
        message: UnifiedMessage,
        recipient_id: Optional[str]
    ) -> Dict[str, Any]:
        """Internal message sending implementation."""
        
        if not message.content:
            raise ValidationError(
                "LinkedIn message must have content",
                context={"message_id": message.id}
            )
        
        if recipient_id:
            # Create comment
            comment = await self._linkedin_client.create_comment(
                object_urn=recipient_id,
                text=message.content
            )
            
            timestamp = datetime.fromtimestamp(
                comment.created_at / 1000,
                tz=timezone.utc
            ) if comment.created_at else datetime.now(timezone.utc)
            
            return {
                "success": True,
                "message_id": comment.id,
                "timestamp": timestamp,
                "metadata": {
                    "platform": "linkedin",
                    "type": "comment",
                    "parent_id": recipient_id
                }
            }
        
        else:
            # Create post
            visibility = message.metadata.get("visibility", "PUBLIC") if message.metadata else "PUBLIC"
            
            post = await self._linkedin_client.create_post(
                text=message.content,
                visibility=visibility
            )
            
            timestamp = datetime.fromtimestamp(
                post.created_at / 1000,
                tz=timezone.utc
            ) if post.created_at else datetime.now(timezone.utc)
            
            return {
                "success": True,
                "message_id": post.id,
                "timestamp": timestamp,
                "metadata": {
                    "platform": "linkedin",
                    "type": "post",
                    "visibility": visibility
                }
            }
    
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert LinkedIn post or comment to UnifiedMessage.
        
        Args:
            raw_message: Raw LinkedIn post or comment dictionary
            
        Returns:
            UnifiedMessage object
        """
        try:
            # Check if it's a post or comment
            if "message" in raw_message and "actor" in raw_message:
                # It's a comment
                comment = LinkedInComment(**raw_message)
                return self._normalize_comment(comment)
            else:
                # It's a post
                post = LinkedInPost(**raw_message)
                return self._normalize_post(post)
                
        except Exception as e:
            logger.error(f"Failed to normalize LinkedIn message: {e}")
            raise ValidationError(
                f"Invalid LinkedIn message format: {e}",
                context={"raw_message": raw_message}
            )
    
    def _normalize_post(self, post: LinkedInPost) -> UnifiedMessage:
        """Convert LinkedIn post to UnifiedMessage."""
        
        # Extract sender info
        sender = UserInfo(
            id=post.author,
            username=post.author,
            display_name=post.author
        )
        
        # Extract content
        content = post.get_text()
        
        # Convert timestamp
        if post.created_at:
            timestamp = datetime.fromtimestamp(
                post.created_at / 1000,
                tz=timezone.utc
            )
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=post.id,
            platform=PlatformType.LINKEDIN,
            type=MessageType.POST,
            sender=sender,
            content=content,
            timestamp=timestamp,
            metadata={
                "linkedin_post_id": post.id,
                "lifecycle_state": post.lifecycle_state
            }
        )
        
        return unified_message
    
    def _normalize_comment(self, comment: LinkedInComment) -> UnifiedMessage:
        """Convert LinkedIn comment to UnifiedMessage."""
        
        # Extract sender info
        sender = UserInfo(
            id=comment.actor,
            username=comment.actor,
            display_name=comment.actor
        )
        
        # Convert timestamp
        if comment.created_at:
            timestamp = datetime.fromtimestamp(
                comment.created_at / 1000,
                tz=timezone.utc
            )
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Create UnifiedMessage
        unified_message = UnifiedMessage(
            platform_message_id=comment.id,
            platform=PlatformType.LINKEDIN,
            type=MessageType.COMMENT,
            sender=sender,
            content=comment.get_text(),
            timestamp=timestamp,
            is_reply=True,
            parent_id=comment.object,
            metadata={
                "linkedin_comment_id": comment.id
            }
        )
        
        return unified_message
    
    # ============================================
    # OPTIONAL: ADDITIONAL METHODS
    # ============================================
    
    async def disconnect(self) -> None:
        """Disconnect from LinkedIn and cleanup."""
        if self._linkedin_client:
            await self._linkedin_client.close()
            self._linkedin_client = None
        
        self._is_authenticated = False
        self._profile = None
        self._post_cache.clear()
        self._comment_cache.clear()
        
        logger.info("Disconnected from LinkedIn")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from LinkedIn.
        
        Args:
            user_id: LinkedIn user ID
            
        Returns:
            Dictionary with user info
        """
        return {
            "id": user_id,
            "platform": "linkedin"
        }
    
    def get_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get cached profile information.
        
        Returns:
            Profile info dictionary or None
        """
        return self._profile
    
    async def create_post(
        self,
        text: str,
        visibility: str = "PUBLIC"
    ) -> Dict[str, Any]:
        """
        Create a post on LinkedIn.
        
        Convenience method for posting.
        
        Args:
            text: Post text
            visibility: Visibility (PUBLIC, CONNECTIONS)
            
        Returns:
            Post result dictionary
        """
        self._ensure_authenticated()
        
        post = await self._linkedin_client.create_post(
            text=text,
            visibility=visibility
        )
        
        return {
            "success": True,
            "post_id": post.id,
            "visibility": visibility
        }
