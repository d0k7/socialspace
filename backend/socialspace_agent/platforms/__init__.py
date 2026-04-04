"""
SocialSpace Agent - Platforms Package
======================================

Platform adapters for all 12 social media platforms.
"""

from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.factory import (
    PlatformFactory,
    get_factory,
    register_platform,
    create_platform,
)

# Import WhatsApp platform
from socialspace_agent.platforms.whatsapp import WhatsAppPlatform

# Auto-register WhatsApp on import
_factory = get_factory()
_factory.register("whatsapp", WhatsAppPlatform)

__all__ = [
    # Base
    "BasePlatform",
    
    # Factory
    "PlatformFactory",
    "get_factory",
    "register_platform",
    "create_platform",
    
    # Platforms
    "WhatsAppPlatform",
]


from socialspace_agent.platforms.telegram import TelegramPlatform
_factory.register("telegram", TelegramPlatform)


from socialspace_agent.platforms.instagram import InstagramPlatform
_factory.register("instagram", InstagramPlatform)


from socialspace_agent.platforms.discord import DiscordPlatform
_factory.register("discord", DiscordPlatform)


from socialspace_agent.platforms.reddit import RedditPlatform
_factory.register("reddit", RedditPlatform)


from socialspace_agent.platforms.twitter import TwitterPlatform
_factory.register("twitter", TwitterPlatform)


from socialspace_agent.platforms.youtube import YouTubePlatform
_factory.register("youtube", YouTubePlatform)


from socialspace_agent.platforms.facebook import FacebookPlatform
_factory.register("facebook", FacebookPlatform)


from socialspace_agent.platforms.linkedin import LinkedInPlatform
_factory.register("linkedin", LinkedInPlatform)



from socialspace_agent.platforms.tiktok import TikTokPlatform
_factory.register("tiktok", TikTokPlatform)



from socialspace_agent.platforms.snapchat import SnapchatPlatform
_factory.register("snapchat", SnapchatPlatform)


from socialspace_agent.platforms.pinterest import PinterestPlatform
_factory.register("pinterest", PinterestPlatform)