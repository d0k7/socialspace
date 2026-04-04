"""
SocialSpace Agent - Exception Hierarchy
========================================

Comprehensive exception system following FAANG-level practices.

Design Principles:
------------------
1. Specific exceptions for specific errors (no generic Exception)
2. Hierarchical structure (easier to catch groups of related errors)
3. Rich context in exception messages
4. HTTP-like status codes for API errors
5. Serializable for logging and monitoring

Exception Hierarchy:
-------------------
SocialSpaceError (base)
├── ConfigurationError
├── ValidationError
├── AuthenticationError
├── AuthorizationError
├── PlatformError
│   ├── WhatsAppError
│   ├── InstagramError
│   ├── TwitterError
│   ├── [... other platform errors]
├── ServiceError
│   ├── ServiceUnavailableError
│   ├── RateLimitError
│   ├── TimeoutError
│   └── NetworkError
├── AgentError
│   ├── NodeExecutionError
│   ├── GraphBuildError
│   └── WorkflowError
└── DataError
    ├── MessageParseError
    ├── MessageSendError
    └── StorageError

Author: Dheeraj Mishra
Created: February 6, 2026
"""

from typing import Optional, Dict, Any
from datetime import datetime
import traceback


class SocialSpaceError(Exception):
    """
    Base exception for all SocialSpace Agent errors.
    
    All custom exceptions inherit from this class, making it easy to catch
    all application-specific errors with a single except clause.
    
    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (HTTP-like)
        context: Additional context about the error
        timestamp: When the error occurred
        traceback_str: Stack trace (for debugging)
        
    Example:
        >>> try:
        ...     raise SocialSpaceError("Something went wrong", code=500)
        ... except SocialSpaceError as e:
        ...     print(f"Error {e.code}: {e.message}")
    """
    
    def __init__(
        self,
        message: str,
        code: int = 500,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error description
            code: Error code (HTTP-like: 400s=client, 500s=server)
            context: Additional error context (user_id, platform, etc.)
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        self.traceback_str = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize exception to dictionary.
        
        Useful for logging, API responses, and monitoring systems.
        
        Returns:
            Dictionary representation of the error
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        context_str = f" | Context: {self.context}" if self.context else ""
        return f"[{self.code}] {self.message}{context_str}"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"code={self.code}, "
            f"context={self.context})"
        )


# ============================================
# CONFIGURATION ERRORS (400-level)
# ============================================

class ConfigurationError(SocialSpaceError):
    """
    Raised when there's an issue with application configuration.
    
    Examples:
        - Missing required environment variables
        - Invalid configuration file format
        - Conflicting configuration options
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, context=context)


# ============================================
# VALIDATION ERRORS (422-level)
# ============================================

class ValidationError(SocialSpaceError):
    """
    Raised when input data fails validation.
    
    Examples:
        - Invalid message format
        - Missing required fields
        - Data type mismatches
        - Constraint violations
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=422, context=context)


# ============================================
# AUTHENTICATION & AUTHORIZATION (401/403)
# ============================================

class AuthenticationError(SocialSpaceError):
    """
    Raised when authentication fails.
    
    Examples:
        - Invalid API credentials
        - Expired tokens
        - Failed platform login
        
    Security Note:
        Be careful not to expose sensitive information in error messages.
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=401, context=context)


class AuthorizationError(SocialSpaceError):
    """
    Raised when user lacks permission for an operation.
    
    Examples:
        - Insufficient permissions
        - Access denied to resource
        - Operation not allowed for user tier
    """
    
    def __init__(
        self,
        message: str = "Authorization failed",
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=403, context=context)


# ============================================
# PLATFORM-SPECIFIC ERRORS (502-level)
# ============================================

class PlatformError(SocialSpaceError):
    """
    Base class for platform-specific errors.
    
    Raised when external platform APIs fail or behave unexpectedly.
    """
    
    def __init__(
        self,
        platform: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context['platform'] = platform
        super().__init__(message, code=502, context=context)


class WhatsAppError(PlatformError):
    """WhatsApp-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("whatsapp", message, context)


class InstagramError(PlatformError):
    """Instagram-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("instagram", message, context)


class TwitterError(PlatformError):
    """Twitter/X-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("twitter", message, context)


class TelegramError(PlatformError):
    """Telegram-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("telegram", message, context)


class FacebookError(PlatformError):
    """Facebook-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("facebook", message, context)


class LinkedInError(PlatformError):
    """LinkedIn-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("linkedin", message, context)


class DiscordError(PlatformError):
    """Discord-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("discord", message, context)


class RedditError(PlatformError):
    """Reddit-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("reddit", message, context)


class YouTubeError(PlatformError):
    """YouTube-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("youtube", message, context)


class TikTokError(PlatformError):
    """TikTok-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("tiktok", message, context)


class SnapchatError(PlatformError):
    """Snapchat-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("snapchat", message, context)


class PinterestError(PlatformError):
    """Pinterest-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("pinterest", message, context)


class WeChatError(PlatformError):
    """WeChat-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__("wechat", message, context)


# ============================================
# SERVICE ERRORS (500-level)
# ============================================

class ServiceError(SocialSpaceError):
    """Base class for service-related errors."""
    pass


class ServiceUnavailableError(ServiceError):
    """
    Raised when a required service is unavailable.
    
    Examples:
        - Database connection failed
        - External API is down
        - Cache server unreachable
        
    Retry Strategy:
        These errors should typically trigger retry logic with exponential backoff.
    """
    
    def __init__(
        self,
        service: str,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        message = message or f"{service} service is unavailable"
        context = context or {}
        context['service'] = service
        super().__init__(message, code=503, context=context)


class RateLimitError(ServiceError):
    """
    Raised when rate limit is exceeded.
    
    Attributes:
        retry_after: Seconds until rate limit resets
        limit: Maximum allowed requests
        remaining: Remaining requests in current window
        
    Retry Strategy:
        Wait for 'retry_after' seconds before retrying.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: int = 0,
        context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context.update({
            'retry_after': retry_after,
            'limit': limit,
            'remaining': remaining,
        })
        super().__init__(message, code=429, context=context)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining


class TimeoutError(ServiceError):
    """
    Raised when an operation times out.
    
    Examples:
        - API request exceeded timeout
        - Database query took too long
        - Message send operation timed out
    """
    
    def __init__(
        self,
        operation: str,
        timeout_seconds: float,
        context: Optional[Dict[str, Any]] = None
    ):
        message = f"{operation} timed out after {timeout_seconds}s"
        context = context or {}
        context.update({
            'operation': operation,
            'timeout_seconds': timeout_seconds,
        })
        super().__init__(message, code=504, context=context)


class NetworkError(ServiceError):
    """
    Raised when network communication fails.
    
    Examples:
        - Connection refused
        - DNS resolution failed
        - Network unreachable
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=503, context=context)


# ============================================
# AGENT ERRORS (500-level)
# ============================================

class AgentError(SocialSpaceError):
    """Base class for agent execution errors."""
    pass


class NodeExecutionError(AgentError):
    """
    Raised when a node fails to execute.
    
    Attributes:
        node_name: Name of the failed node
        node_input: Input data that caused the failure
    """
    
    def __init__(
        self,
        node_name: str,
        message: str,
        node_input: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context.update({
            'node_name': node_name,
            'node_input': str(node_input) if node_input else None,
        })
        super().__init__(message, code=500, context=context)


class GraphBuildError(AgentError):
    """
    Raised when agent graph construction fails.
    
    Examples:
        - Invalid node connections
        - Circular dependencies
        - Missing required nodes
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, context=context)


class WorkflowError(AgentError):
    """
    Raised when workflow execution fails.
    
    Examples:
        - Workflow timeout
        - Invalid workflow state
        - Workflow terminated unexpectedly
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, context=context)


# ============================================
# DATA ERRORS (400/500-level)
# ============================================

class DataError(SocialSpaceError):
    """Base class for data-related errors."""
    pass


class MessageParseError(DataError):
    """
    Raised when message parsing fails.
    
    Examples:
        - Invalid JSON format
        - Unexpected message structure
        - Encoding issues
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=422, context=context)


class MessageSendError(DataError):
    """
    Raised when message sending fails.
    
    Examples:
        - Recipient not found
        - Message too large
        - Invalid recipient ID
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, context=context)


class StorageError(DataError):
    """
    Raised when data storage operations fail.
    
    Examples:
        - Database write failed
        - Cache update failed
        - File save failed
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, context=context)
