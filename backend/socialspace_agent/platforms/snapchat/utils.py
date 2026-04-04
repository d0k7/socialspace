"""
Snapchat Platform - Utility Functions
======================================

Helper functions for Snapchat integration.

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 13
"""

import re
from typing import Optional


def format_snapchat_id(snapchat_id: str) -> str:
    """
    Format Snapchat ID (ensure it's clean).
    
    Args:
        snapchat_id: Snapchat ID
        
    Returns:
        Cleaned Snapchat ID
    """
    return str(snapchat_id).strip()


def parse_username(username: str) -> str:
    """
    Parse Snapchat username.
    
    Args:
        username: Username
        
    Returns:
        Clean username
    """
    return username.strip().lower()


def create_snapcode_url(username: str) -> str:
    """
    Create Snapcode URL for adding user.
    
    Args:
        username: Snapchat username
        
    Returns:
        Snapcode URL
        
    Example:
        >>> create_snapcode_url("socialspace")
        'https://snapchat.com/add/socialspace'
    """
    username = parse_username(username)
    return f"https://snapchat.com/add/{username}"


def is_valid_username(username: str) -> bool:
    """
    Validate Snapchat username format.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid
        
    Rules:
    - 3-15 characters
    - Letters, numbers, underscores, hyphens, periods
    - Must start with letter
    """
    username = parse_username(username)
    
    if len(username) < 3 or len(username) > 15:
        return False
    
    # Must start with letter
    if not username[0].isalpha():
        return False
    
    # Check format
    pattern = r'^[a-z][a-z0-9._-]*$'
    return bool(re.match(pattern, username))


def format_duration(seconds: int) -> str:
    """
    Format snap duration for display.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds <= 10:
        return f"{seconds}s"
    else:
        return f"{seconds}s"


def is_valid_access_token(token: str) -> bool:
    """
    Basic validation for Snapchat access token format.
    
    Args:
        token: Access token
        
    Returns:
        True if format looks valid
    """
    if not token:
        return False
    
    # Snapchat tokens are typically long strings
    return len(token) > 30


def calculate_expiry(hours: int = 24) -> str:
    """
    Calculate expiry timestamp for stories.
    
    Args:
        hours: Hours until expiry (default: 24)
        
    Returns:
        ISO format timestamp
    """
    from datetime import datetime, timedelta
    
    expiry = datetime.now() + timedelta(hours=hours)
    return expiry.isoformat()