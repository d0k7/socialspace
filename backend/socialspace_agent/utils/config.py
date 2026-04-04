"""
SocialSpace Agent - Configuration Management
=============================================

Handles platform credentials, API keys, and configuration settings.

Features:
---------
- Environment variable support (.env files)
- Pydantic validation for type safety
- Secure secret handling
- Platform-specific configurations
- Rate limit settings

Design Pattern:
---------------
Settings Pattern - Centralized configuration with validation

Author: Dheeraj Mishra
Created: February 7, 2026
Session: 2
"""

from typing import Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os


# ============================================
# PLATFORM CONFIGURATION
# ============================================

class PlatformConfig(BaseModel):
    """
    Configuration for a single platform.
    
    This model holds all settings needed to connect to and use
    a specific social media platform (WhatsApp, Instagram, etc.).
    
    Attributes:
        platform: Platform name (whatsapp, instagram, etc.)
        api_key: API key or access token
        api_secret: API secret (if required)
        base_url: Base URL for API endpoints
        rate_limit: Maximum requests per minute
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        enabled: Whether this platform is active
        
    Example:
        >>> config = PlatformConfig(
        ...     platform="whatsapp",
        ...     api_key="your_key_here",
        ...     rate_limit=100,
        ...     timeout=30
        ... )
        >>> print(config.platform)
        whatsapp
    
    Security Note:
        - Never commit API keys to git
        - Use environment variables for secrets
        - Rotate keys regularly
    """
    
    # Platform identification
    platform: str = Field(..., description="Platform name")
    
    # Authentication
    api_key: Optional[str] = Field(
        None,
        description="Primary API key or access token"
    )
    
    api_secret: Optional[str] = Field(
        None,
        description="API secret (if required by platform)"
    )
    
    access_token: Optional[str] = Field(
        None,
        description="OAuth access token (for OAuth platforms)"
    )
    
    refresh_token: Optional[str] = Field(
        None,
        description="OAuth refresh token"
    )
    
    # API Configuration
    base_url: Optional[str] = Field(
        None,
        description="Base URL for API endpoints"
    )
    
    # Rate Limiting
    rate_limit: int = Field(
        default=60,
        ge=1,
        le=10000,
        description="Maximum requests per minute"
    )
    
    burst_limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum requests in a burst"
    )
    
    # Timeouts & Retries
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts on failure"
    )
    
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Initial retry delay in seconds"
    )
    
    # Feature Flags
    enabled: bool = Field(
        default=True,
        description="Whether this platform is active"
    )
    
    mock_mode: bool = Field(
        default=False,
        description="Use mock responses for testing"
    )
    
    # Additional Settings
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific additional settings"
    )
    
    # Validation
    @field_validator('platform', mode='before')
    @classmethod
    def validate_platform(cls, v):
        """Ensure platform name is a non-empty string."""
        if v is None:
            raise ValueError("Platform name is required")
        if isinstance(v, Enum):
            v = v.value
        v = str(v).strip()
        if not v:
            raise ValueError("Platform name cannot be empty")
        return v.lower()

    @field_validator('api_key', 'api_secret', 'access_token')
    @classmethod
    def validate_secrets(cls, v: Optional[str]):
        """
        Validate that secrets are not placeholder values.
        
        Common mistakes:
        - Leaving default values like "your_key_here"
        - Using empty strings
        - Using test values in production
        """
        if v and v in ["your_key_here", "test", "example", "changeme", ""]:
            raise ValueError(
                f"Invalid secret value. Please use a real API key. "
                f"Never commit secrets to git!"
            )
        return v
    
    @field_validator('rate_limit', 'burst_limit')
    @classmethod
    def validate_limits(cls, v: int, info: ValidationInfo):
        """Ensure rate limits are reasonable."""
        if info.field_name == 'burst_limit':
            rate_limit = 60
            if info.data:
                rate_limit = info.data.get('rate_limit', 60)
            if v > rate_limit:
                raise ValueError(
                    f"burst_limit ({v}) cannot exceed rate_limit ({rate_limit})"
                )
        return v
    
    model_config = ConfigDict(
        validate_assignment=True  # Validate on attribute changes
    )
        
    def mask_secrets(self) -> Dict[str, Any]:
        """
        Return configuration with masked secrets.
        
        Useful for logging without exposing credentials.
        
        Returns:
            Dictionary with secrets masked as "***"
            
        Example:
            >>> config = PlatformConfig(platform="whatsapp", api_key="secret123")
            >>> config.mask_secrets()
            {'platform': 'whatsapp', 'api_key': '***', ...}
        """
        data = self.model_dump()
        
        # Mask sensitive fields
        sensitive_fields = ['api_key', 'api_secret', 'access_token', 'refresh_token']
        for field in sensitive_fields:
            if data.get(field):
                data[field] = "***"
        
        return data


# ============================================
# APPLICATION SETTINGS
# ============================================

class Settings(BaseSettings):
    """
    Global application settings.
    
    Loads configuration from:
    1. Environment variables
    2. .env file
    3. Default values
    
    Priority: Environment variables > .env file > defaults
    
    Example .env file:
        ANTHROPIC_API_KEY=sk-ant-...
        OPENAI_API_KEY=sk-...
        WHATSAPP_API_KEY=...
        DATABASE_URL=sqlite:///socialspace.db
        LOG_LEVEL=INFO
        
    Usage:
        >>> settings = Settings()
        >>> print(settings.anthropic_api_key)
        sk-ant-...
    """
    
    # ============================================
    # LLM API KEYS
    # ============================================
    
    anthropic_api_key: Optional[str] = Field(
        None,
        description="Anthropic Claude API key"
    )
    
    openai_api_key: Optional[str] = Field(
        None,
        description="OpenAI API key"
    )
    
    # ============================================
    # PLATFORM API KEYS
    # ============================================
    
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    
    telegram_bot_token: Optional[str] = None
    
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_access_token: Optional[str] = None
    
    instagram_access_token: Optional[str] = None
    
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    
    discord_bot_token: Optional[str] = None
    
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    
    youtube_api_key: Optional[str] = None
    
    # ============================================
    # DATABASE
    # ============================================
    
    database_url: str = Field(
        default="sqlite:///socialspace.db",
        description="Database connection URL"
    )
    
    # ============================================
    # LOGGING
    # ============================================
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    log_file: Optional[str] = Field(
        default="logs/socialspace.log",
        description="Log file path"
    )
    
    # ============================================
    # APPLICATION
    # ============================================
    
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # ============================================
    # RATE LIMITING DEFAULTS
    # ============================================
    
    default_rate_limit: int = Field(
        default=60,
        description="Default rate limit (requests/minute)"
    )
    
    default_timeout: int = Field(
        default=30,
        description="Default request timeout (seconds)"
    )
    
    # ============================================
    # PATHS
    # ============================================
    
    data_dir: Path = Field(
        default=Path("data"),
        description="Data directory for file storage"
    )
    
    cache_dir: Path = Field(
        default=Path("data/cache"),
        description="Cache directory"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False  # Allow lowercase env vars
    )
        
    def __init__(self, **kwargs):
        """Initialize settings and create directories."""
        super().__init__(**kwargs)
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if log_file is set
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_platform_config(self, platform: str) -> PlatformConfig:
        """
        Get configuration for a specific platform.
        
        Automatically pulls credentials from environment variables.
        
        Args:
            platform: Platform name (whatsapp, instagram, etc.)
            
        Returns:
            PlatformConfig for the platform
            
        Raises:
            ValueError: If platform is not supported
            
        Example:
            >>> settings = Settings()
            >>> whatsapp_config = settings.get_platform_config("whatsapp")
            >>> print(whatsapp_config.api_key)
        """
        # Map platform names to their credential fields
        platform_credentials = {
            "whatsapp": {
                "api_key": self.whatsapp_api_key,
                "metadata": {
                    "phone_number_id": self.whatsapp_phone_number_id
                }
            },
            "telegram": {
                "api_key": self.telegram_bot_token,
            },
            "twitter": {
                "api_key": self.twitter_api_key,
                "api_secret": self.twitter_api_secret,
                "access_token": self.twitter_bearer_token,
            },
            "facebook": {
                "api_key": self.facebook_app_id,
                "api_secret": self.facebook_app_secret,
                "access_token": self.facebook_access_token,
            },
            "instagram": {
                "access_token": self.instagram_access_token,
            },
            "linkedin": {
                "api_key": self.linkedin_client_id,
                "api_secret": self.linkedin_client_secret,
            },
            "discord": {
                "api_key": self.discord_bot_token,
            },
            "reddit": {
                "api_key": self.reddit_client_id,
                "api_secret": self.reddit_client_secret,
            },
            "youtube": {
                "api_key": self.youtube_api_key,
            },
        }
        
        if platform not in platform_credentials:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Create config with platform credentials
        config_data = {
            "platform": platform,
            "rate_limit": self.default_rate_limit,
            "timeout": self.default_timeout,
            **platform_credentials[platform]
        }
        
        return PlatformConfig(**config_data)
    
    def is_platform_configured(self, platform: str) -> bool:
        """
        Check if a platform has valid credentials configured.
        
        Args:
            platform: Platform name
            
        Returns:
            True if platform has credentials
            
        Example:
            >>> settings = Settings()
            >>> if settings.is_platform_configured("whatsapp"):
            ...     print("WhatsApp is ready!")
        """
        try:
            config = self.get_platform_config(platform)
            # Check if at least one credential is set
            return bool(
                config.api_key or 
                config.api_secret or 
                config.access_token
            )
        except ValueError:
            return False


# ============================================
# GLOBAL SETTINGS INSTANCE
# ============================================

# Singleton pattern - load settings once
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance.
    
    Uses singleton pattern - settings are loaded once and cached.
    
    Returns:
        Global Settings instance
        
    Example:
        >>> from socialspace_agent.utils.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.environment)
        development
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    Useful when environment variables change during runtime.
    
    Returns:
        Freshly loaded Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
