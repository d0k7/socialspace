"""
Snapchat Platform Package
==========================

Snap Kit API integration for SocialSpace Agent.

Main Classes:
-------------
- SnapchatPlatform: Main platform adapter
- SnapchatClient: Low-level Snap Kit API client
- SnapchatStory: Story models
- SnapchatSnap: Snap models

Usage:
------
>>> from socialspace_agent.platforms.snapchat import SnapchatPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="snapchat",
...     api_key="YOUR_ACCESS_TOKEN",
...     mock_mode=True
... )
>>> 
>>> snapchat = SnapchatPlatform(config)
>>> await snapchat.authenticate()

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 13
"""

from socialspace_agent.platforms.snapchat.adapter import SnapchatPlatform
from socialspace_agent.platforms.snapchat.client import SnapchatClient
from socialspace_agent.platforms.snapchat.models import (
    SnapchatStory,
    SnapchatSnap,
    SnapchatUser,
    SnapchatBitmoji,
)

__all__ = [
    "SnapchatPlatform",
    "SnapchatClient",
    "SnapchatStory",
    "SnapchatSnap",
    "SnapchatUser",
    "SnapchatBitmoji",
]