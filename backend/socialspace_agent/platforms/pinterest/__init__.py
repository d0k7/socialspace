"""
Pinterest Platform Package
===========================

Pinterest API integration for SocialSpace Agent.

Main Classes:
-------------
- PinterestPlatform: Main platform adapter
- PinterestClient: Low-level API client
- PinterestPin: Pin models
- PinterestBoard: Board models

Usage:
------
>>> from socialspace_agent.platforms.pinterest import PinterestPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="pinterest",
...     api_key="YOUR_ACCESS_TOKEN",
...     mock_mode=True
... )
>>> 
>>> pinterest = PinterestPlatform(config)
>>> await pinterest.authenticate()

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 14 (FINAL SESSION - 100% COMPLETION!)
"""

from socialspace_agent.platforms.pinterest.adapter import PinterestPlatform
from socialspace_agent.platforms.pinterest.client import PinterestClient
from socialspace_agent.platforms.pinterest.models import (
    PinterestPin,
    PinterestBoard,
    PinterestUser,
)

__all__ = [
    "PinterestPlatform",
    "PinterestClient",
    "PinterestPin",
    "PinterestBoard",
    "PinterestUser",
]