"""
SocialSpace Agent - Data Models Package
========================================

Pydantic data models for the entire application.

This package contains all data validation and serialization models used
throughout the SocialSpace Agent system.

Key Models:
-----------
- UnifiedMessage: Universal message format across all 12 platforms
- PlatformConfig: Platform-specific configuration
- UserProfile: User account information
- Analytics: Usage and performance metrics

Author: Dheeraj Mishra
Created: February 6, 2026
"""

from socialspace_agent.models.unified_message import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
    MediaAttachment,
    UrgencyLevel,
    SentimentType,
)

__all__ = [
    "UnifiedMessage",
    "PlatformType",
    "MessageType",
    "UserInfo",
    "MediaAttachment",
    "UrgencyLevel",
    "SentimentType",
]
