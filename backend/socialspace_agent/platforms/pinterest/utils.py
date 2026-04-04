"""
Pinterest Platform - Utility Functions
=======================================

Helper functions for Pinterest integration.

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 14 (FINAL SESSION - 100% COMPLETION!)
"""

import re
from typing import Optional


def format_pinterest_id(pinterest_id: str) -> str:
    """
    Format Pinterest ID (ensure it's clean).
    
    Args:
        pinterest_id: Pinterest ID
        
    Returns:
        Cleaned Pinterest ID
    """
    return str(pinterest_id).strip()


def parse_username(username: str) -> str:
    """
    Parse Pinterest username.
    
    Args:
        username: Username
        
    Returns:
        Clean username
    """
    return username.strip().lower()


def create_pin_url(pin_id: str) -> str:
    """
    Create Pinterest pin URL.
    
    Args:
        pin_id: Pin ID
        
    Returns:
        Pin URL
        
    Example:
        >>> create_pin_url("123456789")
        'https://pinterest.com/pin/123456789'
    """
    return f"https://pinterest.com/pin/{pin_id}"


def create_board_url(username: str, board_name: str) -> str:
    """
    Create Pinterest board URL.
    
    Args:
        username: Username
        board_name: Board name
        
    Returns:
        Board URL
        
    Example:
        >>> create_board_url("socialspace", "ideas")
        'https://pinterest.com/socialspace/ideas'
    """
    username = parse_username(username)
    return f"https://pinterest.com/{username}/{board_name}"


def create_profile_url(username: str) -> str:
    """
    Create Pinterest profile URL.
    
    Args:
        username: Username
        
    Returns:
        Profile URL
    """
    username = parse_username(username)
    return f"https://pinterest.com/{username}"


def is_valid_username(username: str) -> bool:
    """
    Validate Pinterest username format.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid
        
    Rules:
    - 3-30 characters
    - Letters, numbers, underscores
    """
    username = parse_username(username)
    
    if len(username) < 3 or len(username) > 30:
        return False
    
    # Check format
    pattern = r'^[a-z0-9_]+$'
    return bool(re.match(pattern, username))


def format_save_count(saves: int) -> str:
    """
    Format save count for display.
    
    Args:
        saves: Save count
        
    Returns:
        Formatted string
        
    Examples:
        >>> format_save_count(1234)
        '1.2K'
        
        >>> format_save_count(1234567)
        '1.2M'
    """
    if saves >= 1_000_000:
        return f"{saves / 1_000_000:.1f}M"
    elif saves >= 1_000:
        return f"{saves / 1_000:.1f}K"
    else:
        return str(saves)


def truncate_description(text: str, max_length: int = 500) -> str:
    """
    Truncate pin description.
    
    Args:
        text: Description text
        max_length: Maximum length (Pinterest allows 500 chars)
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def is_valid_access_token(token: str) -> bool:
    """
    Basic validation for Pinterest access token format.
    
    Args:
        token: Access token
        
    Returns:
        True if format looks valid
    """
    if not token:
        return False
    
    # Pinterest tokens are typically long alphanumeric strings
    return len(token) > 30