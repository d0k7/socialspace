"""
SocialSpace Agent - Platform Factory
=====================================

Factory for creating platform adapters dynamically.

Design Pattern:
---------------
Factory Pattern - Creates objects without specifying exact class

Benefits:
---------
- Centralized platform creation logic
- Easy to add new platforms
- Type-safe platform instantiation
- Automatic configuration handling

Author: Dheeraj Mishra
Created: February 7, 2026
Session: 2
"""

from typing import Dict, Type, Optional
import logging

from socialspace_agent.models import PlatformType
from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.utils.config import PlatformConfig, get_settings
from socialspace_agent.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class PlatformFactory:
    """
    Factory for creating platform adapters.
    
    Dynamically creates the correct platform adapter based on platform name.
    
    How it works:
    -------------
    1. Register platform classes (done once at startup)
    2. Call create_platform("whatsapp", config)
    3. Factory returns WhatsAppPlatform instance
    
    Example:
        >>> # Register platforms (done in __init__)
        >>> factory = PlatformFactory()
        >>> factory.register("whatsapp", WhatsAppPlatform)
        >>> 
        >>> # Create platform instance
        >>> config = PlatformConfig(platform="whatsapp", api_key="...")
        >>> whatsapp = factory.create_platform("whatsapp", config)
        >>> 
        >>> # Or create from settings
        >>> whatsapp = factory.create_from_settings("whatsapp")
    
    Future (Session 3+):
        When we implement WhatsApp, Instagram, etc., we register them here:
        
        >>> from socialspace_agent.platforms.whatsapp import WhatsAppPlatform
        >>> from socialspace_agent.platforms.instagram import InstagramPlatform
        >>> 
        >>> factory.register("whatsapp", WhatsAppPlatform)
        >>> factory.register("instagram", InstagramPlatform)
    """
    
    def __init__(self):
        """
        Initialize platform factory.
        
        Sets up:
            - Platform registry (empty for now)
            - Logging
        """
        # Registry: platform_name → PlatformClass
        self._registry: Dict[str, Type[BasePlatform]] = {}
        
        logger.info("Platform factory initialized")
    
    def register(
        self,
        platform_name: str,
        platform_class: Type[BasePlatform]
    ) -> None:
        """
        Register a platform adapter class.
        
        Args:
            platform_name: Platform identifier (e.g., "whatsapp")
            platform_class: Platform adapter class (must inherit from BasePlatform)
            
        Raises:
            ValueError: If platform_class doesn't inherit from BasePlatform
            
        Example:
            >>> from socialspace_agent.platforms.whatsapp import WhatsAppPlatform
            >>> factory = PlatformFactory()
            >>> factory.register("whatsapp", WhatsAppPlatform)
        """
        # Validate that class inherits from BasePlatform
        if not issubclass(platform_class, BasePlatform):
            raise ValueError(
                f"{platform_class.__name__} must inherit from BasePlatform"
            )
        
        # Register the platform
        self._registry[platform_name] = platform_class
        
        logger.info(
            f"Registered platform: {platform_name} → {platform_class.__name__}"
        )
    
    def create_platform(
        self,
        platform_name: str,
        config: Optional[PlatformConfig] = None
    ) -> BasePlatform:
        """
        Create a platform adapter instance.
        
        Args:
            platform_name: Platform to create (e.g., "whatsapp")
            config: Platform configuration (optional, loads from settings if None)
            
        Returns:
            Platform adapter instance
            
        Raises:
            ConfigurationError: If platform not registered or config invalid
            
        Example:
            >>> # With explicit config
            >>> config = PlatformConfig(platform="whatsapp", api_key="...")
            >>> whatsapp = factory.create_platform("whatsapp", config)
            >>> 
            >>> # Load config from environment
            >>> whatsapp = factory.create_platform("whatsapp")
        """
        # Check if platform is registered
        if platform_name not in self._registry:
            available = list(self._registry.keys())
            raise ConfigurationError(
                f"Platform '{platform_name}' not registered. "
                f"Available platforms: {available}"
            )
        
        # Get or create configuration
        if config is None:
            settings = get_settings()
            config = settings.get_platform_config(platform_name)
        
        # Validate configuration
        if not config.enabled:
            raise ConfigurationError(
                f"Platform '{platform_name}' is disabled in configuration"
            )
        
        # Get platform class
        platform_class = self._registry[platform_name]
        
        # Create instance
        logger.info(f"Creating {platform_name} platform adapter")
        platform = platform_class(config)
        
        return platform
    
    def create_from_settings(self, platform_name: str) -> BasePlatform:
        """
        Create platform adapter from global settings.
        
        Convenience method that loads configuration from environment.
        
        Args:
            platform_name: Platform to create
            
        Returns:
            Platform adapter instance
            
        Example:
            >>> # Assumes WHATSAPP_API_KEY is in .env
            >>> whatsapp = factory.create_from_settings("whatsapp")
        """
        return self.create_platform(platform_name, config=None)
    
    def is_registered(self, platform_name: str) -> bool:
        """
        Check if platform is registered.
        
        Args:
            platform_name: Platform to check
            
        Returns:
            True if platform is registered
            
        Example:
            >>> if factory.is_registered("whatsapp"):
            ...     whatsapp = factory.create_platform("whatsapp")
        """
        return platform_name in self._registry
    
    def list_platforms(self) -> list[str]:
        """
        List all registered platforms.
        
        Returns:
            List of platform names
            
        Example:
            >>> platforms = factory.list_platforms()
            >>> print(platforms)
            ['whatsapp', 'instagram', 'twitter']
        """
        return list(self._registry.keys())
    
    def get_platform_class(self, platform_name: str) -> Type[BasePlatform]:
        """
        Get platform adapter class.
        
        Args:
            platform_name: Platform name
            
        Returns:
            Platform adapter class
            
        Raises:
            ConfigurationError: If platform not registered
            
        Example:
            >>> WhatsAppPlatform = factory.get_platform_class("whatsapp")
            >>> print(WhatsAppPlatform.__name__)
            WhatsAppPlatform
        """
        if platform_name not in self._registry:
            raise ConfigurationError(f"Platform '{platform_name}' not registered")
        
        return self._registry[platform_name]


# ============================================
# GLOBAL FACTORY INSTANCE
# ============================================

# Singleton pattern - one factory for the entire application
_factory: Optional[PlatformFactory] = None


def get_factory() -> PlatformFactory:
    """
    Get global platform factory instance.
    
    Uses singleton pattern - factory is created once and cached.
    
    Returns:
        Global PlatformFactory instance
        
    Example:
        >>> from socialspace_agent.platforms.factory import get_factory
        >>> factory = get_factory()
        >>> whatsapp = factory.create_platform("whatsapp")
    """
    global _factory
    if _factory is None:
        _factory = PlatformFactory()
        # Future: Register platforms here
        # _factory.register("whatsapp", WhatsAppPlatform)
        # _factory.register("instagram", InstagramPlatform)
        # etc.
    return _factory


def register_platform(platform_name: str, platform_class: Type[BasePlatform]) -> None:
    """
    Register a platform with the global factory.
    
    Convenience function for registering platforms.
    
    Args:
        platform_name: Platform identifier
        platform_class: Platform adapter class
        
    Example:
        >>> from socialspace_agent.platforms.factory import register_platform
        >>> from socialspace_agent.platforms.whatsapp import WhatsAppPlatform
        >>> 
        >>> register_platform("whatsapp", WhatsAppPlatform)
    """
    factory = get_factory()
    factory.register(platform_name, platform_class)


def create_platform(
    platform_name: str,
    config: Optional[PlatformConfig] = None
) -> BasePlatform:
    """
    Create a platform adapter using the global factory.
    
    Convenience function for platform creation.
    
    Args:
        platform_name: Platform to create
        config: Platform configuration (optional)
        
    Returns:
        Platform adapter instance
        
    Example:
        >>> from socialspace_agent.platforms.factory import create_platform
        >>> whatsapp = create_platform("whatsapp")
    """
    factory = get_factory()
    return factory.create_platform(platform_name, config)