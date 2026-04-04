"""
SocialSpace Agent - Base Platform Adapter
==========================================

Abstract base class for all platform integrations.

Design Pattern:
---------------
Adapter Pattern - Provides uniform interface for different platforms

Every platform (WhatsApp, Instagram, Twitter, etc.) implements this interface,
making them interchangeable and consistent.

Responsibilities:
-----------------
1. Define common interface for all platforms
2. Handle rate limiting automatically
3. Provide retry logic
4. Normalize messages to UnifiedMessage format
5. Manage authentication and connection

Author: Dheeraj Mishra
Created: February 7, 2026
Session: 2
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from socialspace_agent.models import UnifiedMessage, PlatformType
from socialspace_agent.exceptions import (
    PlatformError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)
from socialspace_agent.utils.config import PlatformConfig
from socialspace_agent.utils.rate_limiter import RateLimiter, create_rate_limiter
from socialspace_agent.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


class BasePlatform(ABC):
    """
    Abstract base class for platform integrations.
    
    All platform clients (WhatsApp, Instagram, Twitter, etc.) must
    implement this interface to ensure consistent behavior.
    
    Design Pattern: Adapter Pattern
    --------------------------------
    - Adapts different platform APIs to unified interface
    - Normalizes data into UnifiedMessage format
    - Handles platform-specific authentication
    
    Built-in Features:
    ------------------
    - Automatic rate limiting
    - Retry logic with exponential backoff
    - Comprehensive logging
    - Error handling
    - Health checking
    
    Usage Example (Future Sessions):
    ---------------------------------
    >>> # WhatsApp adapter (we'll build in Session 3)
    >>> class WhatsAppPlatform(BasePlatform):
    ...     async def authenticate(self):
    ...         # WhatsApp-specific auth logic
    ...         pass
    ...     
    ...     async def fetch_messages(self, user_id, since, limit):
    ...         # WhatsApp-specific fetch logic
    ...         pass
    >>> 
    >>> # Using the adapter
    >>> config = PlatformConfig(platform="whatsapp", api_key="...")
    >>> whatsapp = WhatsAppPlatform(config)
    >>> await whatsapp.authenticate()
    >>> messages = await whatsapp.fetch_messages(user_id="123", limit=50)
    """
    
    def __init__(self, config: PlatformConfig):
        """
        Initialize platform adapter.
        
        Args:
            config: Platform-specific configuration
            
        Sets up:
            - Configuration
            - Rate limiter
            - Authentication state
            - Logging
        """
        self.config = config
        self.platform_type = config.platform
        
        # Rate limiting
        self.rate_limiter = create_rate_limiter(
            requests_per_minute=config.rate_limit,
            burst_factor=1.5
        )
        
        # Authentication state
        self._is_authenticated = False
        self._client = None  # Platform-specific client instance
        
        # Statistics
        self._stats = {
            "messages_fetched": 0,
            "messages_sent": 0,
            "api_calls": 0,
            "errors": 0,
            "last_activity": None,
        }
        
        logger.info(
            f"Initialized {self.platform_type} platform adapter "
            f"(rate_limit={config.rate_limit}/min)"
        )
    
    # ============================================
    # ABSTRACT METHODS (Must be implemented by each platform)
    # ============================================
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Each platform implements its own authentication logic:
        - WhatsApp: Phone number verification
        - Twitter: OAuth flow
        - Instagram: Access token validation
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
            
        Example Implementation:
            >>> async def authenticate(self):
            ...     try:
            ...         self._client = WhatsAppClient(self.config.api_key)
            ...         await self._client.connect()
            ...         self._is_authenticated = True
            ...         return True
            ...     except Exception as e:
            ...         raise AuthenticationError(f"WhatsApp auth failed: {e}")
        """
        pass
    
    @abstractmethod
    async def fetch_messages(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from the platform.
        
        This is the CORE method. Each platform implements message fetching
        and normalizes results to UnifiedMessage format.
        
        Args:
            user_id: User's identifier on this platform
            since: Fetch messages since this timestamp (optional)
            limit: Maximum number of messages to fetch
            filters: Platform-specific filters (optional)
                Examples:
                - {"unread_only": True}
                - {"conversation_id": "thread_123"}
                - {"message_types": ["text", "image"]}
                
        Returns:
            List of UnifiedMessage objects
            
        Raises:
            ServiceUnavailableError: If platform is down
            RateLimitError: If rate limited
            AuthenticationError: If not authenticated
            
        Example Implementation:
            >>> async def fetch_messages(self, user_id, since, limit, filters):
            ...     # 1. Check authentication
            ...     if not self._is_authenticated:
            ...         raise AuthenticationError("Not authenticated")
            ...     
            ...     # 2. Fetch from platform API
            ...     raw_messages = await self._client.get_messages(
            ...         user=user_id,
            ...         since=since,
            ...         limit=limit
            ...     )
            ...     
            ...     # 3. Normalize to UnifiedMessage
            ...     unified_messages = []
            ...     for raw_msg in raw_messages:
            ...         unified_msg = self.normalize_message(raw_msg)
            ...         unified_messages.append(unified_msg)
            ...     
            ...     return unified_messages
        """
        pass
    
    @abstractmethod
    async def send_message(
        self,
        message: UnifiedMessage,
        recipient_id: str
    ) -> Dict[str, Any]:
        """
        Send a message on the platform.
        
        Takes a UnifiedMessage and sends it using platform-specific API.
        
        Args:
            message: UnifiedMessage to send
            recipient_id: Recipient's platform ID
            
        Returns:
            Dictionary with:
                - success: bool
                - message_id: str (platform's message ID)
                - timestamp: datetime
                - metadata: Dict (platform-specific)
                
        Raises:
            PlatformError: If sending fails
            ValidationError: If message format invalid
            
        Example Implementation:
            >>> async def send_message(self, message, recipient_id):
            ...     # 1. Convert to platform format
            ...     platform_message = self._to_platform_format(message)
            ...     
            ...     # 2. Send via API
            ...     response = await self._client.send(
            ...         to=recipient_id,
            ...         message=platform_message
            ...     )
            ...     
            ...     # 3. Return result
            ...     return {
            ...         "success": True,
            ...         "message_id": response.id,
            ...         "timestamp": datetime.now(),
            ...         "metadata": {"status": response.status}
            ...     }
        """
        pass
    
    @abstractmethod
    def normalize_message(self, raw_message: Dict) -> UnifiedMessage:
        """
        Convert platform-specific message to UnifiedMessage.
        
        This is THE KEY method that makes the adapter pattern work.
        Each platform converts its unique format to our universal format.
        
        Args:
            raw_message: Raw message data from platform API
            
        Returns:
            UnifiedMessage object
            
        Raises:
            ValidationError: If message cannot be normalized
            
        Example Implementation:
            >>> def normalize_message(self, raw_message):
            ...     # WhatsApp format → UnifiedMessage
            ...     return UnifiedMessage(
            ...         platform_message_id=raw_message['id'],
            ...         platform=PlatformType.WHATSAPP,
            ...         type=self._map_message_type(raw_message['type']),
            ...         sender=UserInfo(
            ...             id=raw_message['from'],
            ...             display_name=raw_message.get('name')
            ...         ),
            ...         content=raw_message.get('text'),
            ...         timestamp=datetime.fromisoformat(raw_message['timestamp'])
            ...     )
        """
        pass
    
    # ============================================
    # OPTIONAL METHODS (Platform can override if needed)
    # ============================================
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from platform.
        
        Optional method - platforms can override for richer user data.
        
        Args:
            user_id: User's platform identifier
            
        Returns:
            Dictionary with user info
            
        Default implementation returns minimal info.
        """
        return {
            "id": user_id,
            "platform": self.platform_type,
        }
    
    async def health_check(self) -> bool:
        """
        Check if platform API is accessible.
        
        Optional method - platforms can override for custom health checks.
        
        Returns:
            True if platform is healthy
            
        Default implementation checks authentication status.
        """
        return self._is_authenticated
    
    async def disconnect(self) -> None:
        """
        Disconnect from platform and cleanup resources.
        
        Optional method - platforms can override for custom cleanup.
        
        Default implementation marks as not authenticated.
        """
        self._is_authenticated = False
        self._client = None
        logger.info(f"Disconnected from {self.platform_type}")
    
    # ============================================
    # BUILT-IN HELPERS (Available to all platforms)
    # ============================================
    
    async def _rate_limited_call(self, func, *args, **kwargs):
        """
        Execute function with rate limiting.
        
        Automatically enforces rate limits before making API calls.
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Usage:
            >>> result = await self._rate_limited_call(
            ...     self._client.get_messages,
            ...     user_id="123"
            ... )
        """
        # Wait for rate limit token
        await self.rate_limiter.acquire_async()
        
        # Increment API call counter
        self._stats["api_calls"] += 1
        self._stats["last_activity"] = datetime.now()
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"API call failed: {e}")
            raise
    
    @async_retry_with_backoff(max_retries=3, base_delay=1.0)
    async def _retry_on_failure(self, func, *args, **kwargs):
        """
        Execute function with automatic retry on failure.
        
        Uses exponential backoff retry strategy.
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Retries automatically on:
            - Network errors
            - Timeout errors
            - Transient service errors
        """
        return await func(*args, **kwargs)
    
    def _ensure_authenticated(self) -> None:
        """
        Ensure platform is authenticated.
        
        Raises:
            AuthenticationError: If not authenticated
            
        Usage:
            >>> async def fetch_messages(self, ...):
            ...     self._ensure_authenticated()
            ...     # Continue with fetch logic
        """
        if not self._is_authenticated:
            raise AuthenticationError(
                f"Not authenticated with {self.platform_type}. "
                f"Call authenticate() first."
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get platform adapter statistics.
        
        Returns:
            Dictionary with usage stats
            
        Example:
            >>> stats = platform.get_stats()
            >>> print(f"API calls made: {stats['api_calls']}")
        """
        return {
            **self._stats,
            "platform": self.platform_type,
            "authenticated": self._is_authenticated,
            "rate_limiter": self.rate_limiter.get_stats(),
        }
    
    def __repr__(self) -> str:
        """String representation of platform adapter."""
        auth_status = "authenticated" if self._is_authenticated else "not authenticated"
        return (
            f"<{self.__class__.__name__}("
            f"platform={self.platform_type}, "
            f"status={auth_status})>"
        )