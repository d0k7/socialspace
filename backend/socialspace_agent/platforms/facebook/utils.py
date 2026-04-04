"""
Facebook Platform - Utility Functions
======================================

Helper functions for Facebook integration.

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 10
"""

import re
from typing import Optional, List


def format_facebook_id(facebook_id: str) -> str:
    """
    Format Facebook ID (ensure it's clean).
    
    Args:
        facebook_id: Facebook ID
        
    Returns:
        Cleaned Facebook ID
    """
    return str(facebook_id).strip()


def parse_post_id(post_id: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse Facebook post ID into page ID and post number.
    
    Args:
        post_id: Post ID (format: PAGE_ID_POST_NUMBER)
        
    Returns:
        Tuple of (page_id, post_number)
        
    Example:
        >>> parse_post_id("123456789_987654321")
        ('123456789', '987654321')
    """
    if "_" in post_id:
        parts = post_id.split("_", 1)
        return parts[0], parts[1]
    return None, None


def create_facebook_url(object_type: str, object_id: str) -> str:
    """
    Create Facebook URL for an object.
    
    Args:
        object_type: Type (page, post, photo, video)
        object_id: Object ID
        
    Returns:
        Full Facebook URL
        
    Examples:
        >>> create_facebook_url("page", "123456789")
        'https://facebook.com/123456789'
        
        >>> create_facebook_url("post", "123_456")
        'https://facebook.com/123_456'
    """
    if object_type == "page":
        return f"https://facebook.com/{object_id}"
    elif object_type == "post":
        return f"https://facebook.com/{object_id}"
    elif object_type == "photo":
        return f"https://facebook.com/photo.php?fbid={object_id}"
    
    return f"https://facebook.com/{object_id}"


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from Facebook post text.
    
    Args:
        text: Post text
        
    Returns:
        List of hashtags (without #)
        
    Example:
        >>> extract_hashtags("Great post! #facebook #social")
        ['facebook', 'social']
    """
    if not text:
        return []
    
    # Match hashtags
    hashtags = re.findall(r'#(\w+)', text)
    
    return hashtags


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from Facebook text.
    
    Args:
        text: Text content
        
    Returns:
        List of mentioned names
        
    Example:
        >>> extract_mentions("Hey @John and @Jane!")
        ['John', 'Jane']
    """
    if not text:
        return []
    
    # Match mentions
    mentions = re.findall(r'@(\w+)', text)
    
    return mentions


def format_engagement_count(count: int) -> str:
    """
    Format engagement count for display.
    
    Args:
        count: Engagement count
        
    Returns:
        Formatted string
        
    Examples:
        >>> format_engagement_count(1234)
        '1.2K'
        
        >>> format_engagement_count(1234567)
        '1.2M'
    """
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    else:
        return str(count)


def truncate_post(text: str, max_length: int = 500) -> str:
    """
    Truncate post text for preview.
    
    Args:
        text: Post text
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def is_valid_access_token(token: str) -> bool:
    """
    Basic validation for Facebook access token format.
    
    Args:
        token: Access token
        
    Returns:
        True if format looks valid
    """
    if not token:
        return False
    
    # Facebook tokens are typically long strings with alphanumeric chars
    return len(token) > 50 and token.replace("|", "").replace("-", "").isalnum()


def parse_graph_api_error(error_data: dict) -> dict:
    """
    Parse Facebook Graph API error response.
    
    Args:
        error_data: Error data from API response
        
    Returns:
        Parsed error dictionary
    """
    error = error_data.get("error", {})
    
    return {
        "message": error.get("message", "Unknown error"),
        "type": error.get("type", "unknown"),
        "code": error.get("code", 0),
        "subcode": error.get("error_subcode"),
        "trace_id": error.get("fbtrace_id")
    }