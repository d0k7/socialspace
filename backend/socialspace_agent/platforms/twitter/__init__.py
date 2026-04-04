"""
Twitter Platform Package
=========================

Twitter API v2 integration for SocialSpace Agent.

Main Classes:
-------------
- TwitterPlatform: Main platform adapter
- TwitterClient: Low-level API v2 client
- TwitterTweet: Tweet models
- TwitterUser: User models

Usage:
------
>>> from socialspace_agent.platforms.twitter import TwitterPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="twitter",
...     api_key="YOUR_BEARER_TOKEN",
...     mock_mode=True
... )
>>> 
>>> twitter = TwitterPlatform(config)
>>> await twitter.authenticate()

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 8
"""

from socialspace_agent.platforms.twitter.adapter import TwitterPlatform
from socialspace_agent.platforms.twitter.client import TwitterClient
from socialspace_agent.platforms.twitter.models import (
    TwitterTweet,
    TwitterUser,
)

__all__ = [
    "TwitterPlatform",
    "TwitterClient",
    "TwitterTweet",
    "TwitterUser",
]