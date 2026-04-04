"""
YouTube Platform Package
=========================

YouTube Data API v3 integration for SocialSpace Agent.

Main Classes:
-------------
- YouTubePlatform: Main platform adapter
- YouTubeClient: Low-level Data API v3 client
- YouTubeVideo: Video models
- YouTubeComment: Comment models

Usage:
------
>>> from socialspace_agent.platforms.youtube import YouTubePlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="youtube",
...     api_key="YOUR_API_KEY",
...     mock_mode=True
... )
>>> 
>>> youtube = YouTubePlatform(config)
>>> await youtube.authenticate()

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 9
"""

from socialspace_agent.platforms.youtube.adapter import YouTubePlatform
from socialspace_agent.platforms.youtube.client import YouTubeClient
from socialspace_agent.platforms.youtube.models import (
    YouTubeVideo,
    YouTubeComment,
    YouTubeChannel,
)

__all__ = [
    "YouTubePlatform",
    "YouTubeClient",
    "YouTubeVideo",
    "YouTubeComment",
    "YouTubeChannel",
]