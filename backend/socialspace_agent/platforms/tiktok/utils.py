"""
TikTok Platform - Utility Functions
====================================

Helper functions for TikTok integration.

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 12
"""

import re
from typing import Optional, List


def format_tiktok_id(tiktok_id: str) -> str:
    """
    Format TikTok ID (ensure it's clean).
    
    Args:
        tiktok_id: TikTok ID
        
    Returns:
        Cleaned TikTok ID
    """
    return str(tiktok_id).strip()


def parse_username(username: str) -> str:
    """
    Parse TikTok username (remove @ if present).
    
    Args:
        username: Username
        
    Returns:
        Username without @
        
    Examples:
        >>> parse_username("@socialspace")
        'socialspace'
        
        >>> parse_username("socialspace")
        'socialspace'
    """
    if username.startswith("@"):
        return username[1:]
    return username


def create_tiktok_url(username: str, video_id: Optional[str] = None) -> str:
    """
    Create TikTok URL.
    
    Args:
        username: TikTok username
        video_id: Video ID (optional)
        
    Returns:
        Full TikTok URL
        
    Examples:
        >>> create_tiktok_url("socialspace")
        'https://tiktok.com/@socialspace'
        
        >>> create_tiktok_url("socialspace", "123456")
        'https://tiktok.com/@socialspace/video/123456'
    """
    username = parse_username(username)
    
    if video_id:
        return f"https://tiktok.com/@{username}/video/{video_id}"
    
    return f"https://tiktok.com/@{username}"


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from TikTok text.
    
    Args:
        text: Text content
        
    Returns:
        List of hashtags (without #)
        
    Examples:
        >>> extract_hashtags("Check this out! #fyp #foryou #trending")
        ['fyp', 'foryou', 'trending']
    """
    if not text:
        return []
    
    # Match hashtags
    hashtags = re.findall(r'#(\w+)', text)
    
    return hashtags


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from TikTok text.
    
    Args:
        text: Text content
        
    Returns:
        List of usernames (without @)
        
    Examples:
        >>> extract_mentions("Shoutout to @user1 and @user2!")
        ['user1', 'user2']
    """
    if not text:
        return []
    
    # Match mentions
    mentions = re.findall(r'@(\w+)', text)
    
    return mentions


def format_view_count(views: int) -> str:
    """
    Format view count for display.
    
    Args:
        views: View count
        
    Returns:
        Formatted string
        
    Examples:
        >>> format_view_count(1234)
        '1.2K'
        
        >>> format_view_count(1234567)
        '1.2M'
    """
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B"
    elif views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    elif views >= 1_000:
        return f"{views / 1_000:.1f}K"
    else:
        return str(views)


def format_duration(seconds: int) -> str:
    """
    Format video duration for display.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
        
    Examples:
        >>> format_duration(45)
        '0:45'
        
        >>> format_duration(125)
        '2:05'
    """
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def truncate_description(text: str, max_length: int = 150) -> str:
    """
    Truncate video description for preview.
    
    Args:
        text: Description text
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def is_valid_username(username: str) -> bool:
    """
    Validate TikTok username format.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid
        
    Rules:
    - 2-24 characters
    - Letters, numbers, underscores, periods
    """
    username = parse_username(username)
    
    if len(username) < 2 or len(username) > 24:
        return False
    
    # Check format
    pattern = r'^[a-zA-Z0-9_.]+$'
    return bool(re.match(pattern, username))


def is_valid_access_token(token: str) -> bool:
    """
    Basic validation for TikTok access token format.
    
    Args:
        token: Access token
        
    Returns:
        True if format looks valid
    """
    if not token:
        return False
    
    # TikTok tokens are typically long alphanumeric strings
    return len(token) > 30