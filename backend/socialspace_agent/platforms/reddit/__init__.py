"""
Reddit Platform Package
========================

Reddit OAuth API integration for SocialSpace Agent.

Main Classes:
-------------
- RedditPlatform: Main platform adapter
- RedditClient: Low-level OAuth API client
- RedditSubmission: Submission/post models
- RedditComment: Comment models

Usage:
------
>>> from socialspace_agent.platforms.reddit import RedditPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="reddit",
...     api_key="YOUR_CLIENT_ID",
...     metadata={
...         "client_secret": "YOUR_CLIENT_SECRET",
...         "user_agent": "SocialSpace/1.0",
...         "username": "your_username",
...         "password": "your_password"
...     }
... )
>>> 
>>> reddit = RedditPlatform(config)
>>> await reddit.authenticate()

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 7
"""

from socialspace_agent.platforms.reddit.adapter import RedditPlatform
from socialspace_agent.platforms.reddit.client import RedditClient
from socialspace_agent.platforms.reddit.models import (
    RedditSubmission,
    RedditComment,
    RedditUser,
    RedditSubreddit,
)

__all__ = [
    "RedditPlatform",
    "RedditClient",
    "RedditSubmission",
    "RedditComment",
    "RedditUser",
    "RedditSubreddit",
]