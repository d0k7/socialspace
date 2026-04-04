"""
Facebook Platform Package
==========================

Facebook Graph API integration for SocialSpace Agent.

Main Classes:
-------------
- FacebookPlatform: Main platform adapter
- FacebookClient: Low-level Graph API client
- FacebookPost: Post models
- FacebookComment: Comment models

Usage:
------
>>> from socialspace_agent.platforms.facebook import FacebookPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="facebook",
...     api_key="YOUR_ACCESS_TOKEN",
...     metadata={"page_id": "YOUR_PAGE_ID"},
...     mock_mode=True
... )
>>> 
>>> facebook = FacebookPlatform(config)
>>> await facebook.authenticate()

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 10
"""

from socialspace_agent.platforms.facebook.adapter import FacebookPlatform
from socialspace_agent.platforms.facebook.client import FacebookClient
from socialspace_agent.platforms.facebook.models import (
    FacebookPost,
    FacebookComment,
    FacebookPage,
    FacebookUser,
)

__all__ = [
    "FacebookPlatform",
    "FacebookClient",
    "FacebookPost",
    "FacebookComment",
    "FacebookPage",
    "FacebookUser",
]