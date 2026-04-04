"""
Discord Platform Package
=========================

Discord Bot API integration for SocialSpace Agent.

Main Classes:
-------------
- DiscordPlatform: Main platform adapter
- DiscordClient: Low-level API client
- DiscordMessage: Message models
- DiscordEmbed: Rich embed models

Usage:
------
>>> from socialspace_agent.platforms.discord import DiscordPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="discord",
...     api_key="YOUR_BOT_TOKEN",
...     mock_mode=True
... )
>>> 
>>> discord = DiscordPlatform(config)
>>> await discord.authenticate()

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 6
"""

from socialspace_agent.platforms.discord.adapter import DiscordPlatform
from socialspace_agent.platforms.discord.client import DiscordClient
from socialspace_agent.platforms.discord.models import (
    DiscordMessage,
    DiscordEmbed,
    DiscordUser,
    DiscordGuild,
    DiscordChannel,
)

__all__ = [
    "DiscordPlatform",
    "DiscordClient",
    "DiscordMessage",
    "DiscordEmbed",
    "DiscordUser",
    "DiscordGuild",
    "DiscordChannel",
]