"""
Instagram Platform - Utility Functions
=======================================

Helper functions for Instagram integration.

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 5
"""

import re
from typing import Dict, List, Optional


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text containing hashtags
        
    Returns:
        List of hashtags (without #)
        
    Examples:
        >>> extract_hashtags("Great photo! #travel #nature")
        ['travel', 'nature']
        
        >>> extract_hashtags("No hashtags here")
        []
    """
    if not text:
        return []
    
    # Match hashtags (# followed by alphanumeric and underscore)
    hashtags = re.findall(r'#(\w+)', text)
    
    return hashtags


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text.
    
    Args:
        text: Text containing mentions
        
    Returns:
        List of usernames (without @)
        
    Examples:
        >>> extract_mentions("Thanks @john and @jane!")
        ['john', 'jane']
    """
    if not text:
        return []
    
    # Match mentions (@ followed by alphanumeric, underscore, and period)
    mentions = re.findall(r'@([\w.]+)', text)
    
    return mentions


def format_instagram_id(instagram_id: str) -> str:
    """
    Format Instagram ID (ensure it's clean).
    
    Args:
        instagram_id: Instagram user/media ID
        
    Returns:
        Formatted ID
    """
    return str(instagram_id).strip()


def validate_instagram_id(instagram_id: str) -> bool:
    """
    Validate Instagram ID format.
    
    Args:
        instagram_id: ID to validate
        
    Returns:
        True if valid
        
    Instagram IDs are numeric strings.
    """
    try:
        # Instagram IDs are numeric
        int(instagram_id)
        return len(instagram_id) > 0
    except (ValueError, TypeError):
        return False


def truncate_caption(text: str, max_length: int = 2200) -> str:
    """
    Truncate caption to Instagram's limit.
    
    Args:
        text: Caption text
        max_length: Maximum length (default: 2200)
        
    Returns:
        Truncated text
        
    Instagram caption limit is 2,200 characters.
    """
    if len(text) <= max_length:
        return text
    
    # Truncate and add ellipsis
    return text[:max_length - 3] + "..."


def is_valid_hashtag(hashtag: str) -> bool:
    """
    Validate hashtag format.
    
    Args:
        hashtag: Hashtag to validate (with or without #)
        
    Returns:
        True if valid
        
    Rules:
    - Can contain letters, numbers, underscores
    - Cannot be only numbers
    - Cannot contain spaces or special characters
    """
    # Remove leading # if present
    if hashtag.startswith('#'):
        hashtag = hashtag[1:]
    
    # Check format
    if not hashtag:
        return False
    
    # Must contain at least one letter
    if hashtag.isdigit():
        return False
    
    # Only alphanumeric and underscore
    return bool(re.match(r'^[\w]+$', hashtag))


def parse_instagram_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse Instagram URL to extract type and ID.
    
    Args:
        url: Instagram URL
        
    Returns:
        Dictionary with 'type' and 'id', or None
        
    Examples:
        >>> parse_instagram_url("https://instagram.com/p/ABC123/")
        {'type': 'post', 'id': 'ABC123'}
        
        >>> parse_instagram_url("https://instagram.com/johndoe/")
        {'type': 'profile', 'username': 'johndoe'}
    """
    # Post URL pattern
    post_match = re.search(r'instagram\.com/p/([A-Za-z0-9_-]+)', url)
    if post_match:
        return {
            'type': 'post',
            'id': post_match.group(1)
        }
    
    # Reel URL pattern
    reel_match = re.search(r'instagram\.com/reel/([A-Za-z0-9_-]+)', url)
    if reel_match:
        return {
            'type': 'reel',
            'id': reel_match.group(1)
        }
    
    # Profile URL pattern
    profile_match = re.search(r'instagram\.com/([A-Za-z0-9_.]+)/?$', url)
    if profile_match:
        return {
            'type': 'profile',
            'username': profile_match.group(1)
        }
    
    return None


def format_comment_for_display(
    username: str,
    text: str,
    timestamp: str,
    max_length: int = 100
) -> str:
    """
    Format comment for display.
    
    Args:
        username: Username
        text: Comment text
        timestamp: Timestamp string
        max_length: Maximum text length
        
    Returns:
        Formatted comment string
        
    Example:
        >>> format_comment_for_display("john", "Great photo!", "2026-02-20")
        '@john: Great photo! (2026-02-20)'
    """
    # Truncate text if needed
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    # Format timestamp (just date)
    date = timestamp.split('T')[0] if 'T' in timestamp else timestamp
    
    return f"@{username}: {text} ({date})"
