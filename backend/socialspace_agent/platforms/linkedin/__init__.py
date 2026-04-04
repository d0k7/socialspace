"""
LinkedIn Platform Package
==========================

LinkedIn API integration for SocialSpace Agent.

Main Classes:
-------------
- LinkedInPlatform: Main platform adapter
- LinkedInClient: Low-level API client
- LinkedInPost: Post models
- LinkedInComment: Comment models

Usage:
------
>>> from socialspace_agent.platforms.linkedin import LinkedInPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="linkedin",
...     api_key="YOUR_ACCESS_TOKEN",
...     mock_mode=True
... )
>>> 
>>> linkedin = LinkedInPlatform(config)
>>> await linkedin.authenticate()

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 11
"""

from socialspace_agent.platforms.linkedin.adapter import LinkedInPlatform
from socialspace_agent.platforms.linkedin.client import LinkedInClient
from socialspace_agent.platforms.linkedin.models import (
    LinkedInPost,
    LinkedInComment,
    LinkedInProfile,
    LinkedInOrganization,
)

__all__ = [
    "LinkedInPlatform",
    "LinkedInClient",
    "LinkedInPost",
    "LinkedInComment",
    "LinkedInProfile",
    "LinkedInOrganization",
]