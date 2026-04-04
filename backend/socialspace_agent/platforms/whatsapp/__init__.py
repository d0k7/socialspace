"""
WhatsApp Platform Package
==========================

WhatsApp Business API integration for SocialSpace Agent.

Main Classes:
-------------
- WhatsAppPlatform: Main platform adapter
- WhatsAppClient: Low-level API client
- WhatsAppMessage: Message models

Usage:
------
>>> from socialspace_agent.platforms.whatsapp import WhatsAppPlatform
>>> from socialspace_agent.utils.config import PlatformConfig
>>> 
>>> config = PlatformConfig(
...     platform="whatsapp",
...     api_key="YOUR_TOKEN",
...     metadata={"phone_number_id": "YOUR_PHONE_ID"}
... )
>>> 
>>> whatsapp = WhatsAppPlatform(config)
>>> await whatsapp.authenticate()

Author: Dheeraj Mishra
Created: February 19, 2026
Session: 3
"""

from socialspace_agent.platforms.whatsapp.adapter import WhatsAppPlatform
from socialspace_agent.platforms.whatsapp.client import WhatsAppClient
from socialspace_agent.platforms.whatsapp.models import (
    WhatsAppMessage,
    WhatsAppText,
    WhatsAppMedia,
    WhatsAppLocation,
    WhatsAppWebhook,
)

__all__ = [
    "WhatsAppPlatform",
    "WhatsAppClient",
    "WhatsAppMessage",
    "WhatsAppText",
    "WhatsAppMedia",
    "WhatsAppLocation",
    "WhatsAppWebhook",
]