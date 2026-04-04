"""
TikTok Platform Package
========================

TikTok Business API integration for SocialSpace Agent.

Main Classes:
-------------
- TikTokPlatform: Main platform adapter
- TikTokClient: Low-level Business API client
- TikTokVideo: Video models
- TikTokComment: Comment models

Usage:
------
>>> from socialspace_agent.platforms.tiktok import TikTokPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="tiktok",
...     api_key="YOUR_ACCESS_TOKEN",
...     mock_mode=True
... )
>>> 
>>> tiktok = TikTokPlatform(config)
>>> await tiktok.authenticate()

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 12
"""

from socialspace_agent.platforms.tiktok.adapter import TikTokPlatform
from socialspace_agent.platforms.tiktok.client import TikTokClient
from socialspace_agent.platforms.tiktok.models import (
    TikTokVideo,
    TikTokComment,
    TikTokUser,
)

__all__ = [
    "TikTokPlatform",
    "TikTokClient",
    "TikTokVideo",
    "TikTokComment",
    "TikTokUser",
]