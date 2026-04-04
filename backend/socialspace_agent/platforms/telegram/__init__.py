"""
Telegram Platform Package
==========================

Telegram Bot API integration for SocialSpace Agent.

Main Classes:
-------------
- TelegramPlatform: Main platform adapter
- TelegramClient: Low-level API client
- TelegramMessage: Message models

Usage:
------
>>> from socialspace_agent.platforms.telegram import TelegramPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="telegram",
...     api_key="123456:ABC-DEF...",
...     mock_mode=True
... )
>>> 
>>> telegram = TelegramPlatform(config)
>>> await telegram.authenticate()

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 4
"""

from socialspace_agent.platforms.telegram.adapter import TelegramPlatform
from socialspace_agent.platforms.telegram.client import TelegramClient
from socialspace_agent.platforms.telegram.models import (
    TelegramMessage,
    TelegramUser,
    TelegramChat,
    TelegramUpdate,
)

__all__ = [
    "TelegramPlatform",
    "TelegramClient",
    "TelegramMessage",
    "TelegramUser",
    "TelegramChat",
    "TelegramUpdate",
]