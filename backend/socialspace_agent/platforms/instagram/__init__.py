"""
Instagram Platform Package
===========================

Instagram Graph API integration for SocialSpace Agent.

Main Classes:
-------------
- InstagramPlatform: Main platform adapter
- InstagramClient: Low-level API client
- InstagramMedia: Media/post models
- InstagramComment: Comment models

Usage:
------
>>> from socialspace_agent.platforms.instagram import InstagramPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="instagram",
...     access_token="YOUR_ACCESS_TOKEN",
...     metadata={"account_id": "YOUR_IG_BUSINESS_ID"}
... )
>>> 
>>> instagram = InstagramPlatform(config)
>>> await instagram.authenticate()

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 5
"""

from socialspace_agent.platforms.instagram.adapter import InstagramPlatform
from socialspace_agent.platforms.instagram.client import InstagramClient
from socialspace_agent.platforms.instagram.models import (
    InstagramMedia,
    InstagramComment,
    InstagramUser,
)

__all__ = [
    "InstagramPlatform",
    "InstagramClient",
    "InstagramMedia",
    "InstagramComment",
    "InstagramUser",
]