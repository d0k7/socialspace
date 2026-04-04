"""
YouTube Platform - Utility Functions
=====================================

Helper functions for YouTube integration.

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 9
"""

import re
from typing import Optional, List


def format_video_id(video_id: str) -> str:
    """
    Format YouTube video ID (ensure it's clean).
    
    Args:
        video_id: Video ID
        
    Returns:
        Cleaned video ID
    """
    return str(video_id).strip()


def extract_video_id_from_url(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID or None
        
    Examples:
        >>> extract_video_id_from_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        
        >>> extract_video_id_from_url("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
    """
    # Pattern for youtube.com/watch?v=VIDEO_ID
    pattern1 = r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern1, url)
    if match:
        return match.group(1)
    
    # Pattern for youtu.be/VIDEO_ID
    pattern2 = r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern2, url)
    if match:
        return match.group(1)
    
    # Pattern for youtube.com/embed/VIDEO_ID
    pattern3 = r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern3, url)
    if match:
        return match.group(1)
    
    return None


def is_valid_video_id(video_id: str) -> bool:
    """
    Validate YouTube video ID format.
    
    Args:
        video_id: Video ID to validate
        
    Returns:
        True if valid
        
    YouTube video IDs are 11 characters: letters, numbers, hyphens, underscores
    """
    if len(video_id) != 11:
        return False
    
    pattern = r'^[a-zA-Z0-9_-]{11}$'
    return bool(re.match(pattern, video_id))


def create_video_url(video_id: str) -> str:
    """
    Create YouTube video URL.
    
    Args:
        video_id: Video ID
        
    Returns:
        Full YouTube URL
        
    Example:
        >>> create_video_url("dQw4w9WgXcQ")
        'https://youtube.com/watch?v=dQw4w9WgXcQ'
    """
    return f"https://youtube.com/watch?v={video_id}"


def create_channel_url(channel_id: str) -> str:
    """
    Create YouTube channel URL.
    
    Args:
        channel_id: Channel ID or custom URL
        
    Returns:
        Full YouTube channel URL
    """
    if channel_id.startswith("@"):
        return f"https://youtube.com/{channel_id}"
    elif channel_id.startswith("UC"):
        return f"https://youtube.com/channel/{channel_id}"
    else:
        return f"https://youtube.com/@{channel_id}"


def format_duration(duration_seconds: int) -> str:
    """
    Format video duration for display.
    
    Args:
        duration_seconds: Duration in seconds
        
    Returns:
        Formatted duration string
        
    Examples:
        >>> format_duration(90)
        '1:30'
        
        >>> format_duration(3665)
        '1:01:05'
    """
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def format_view_count(views: int) -> str:
    """
    Format view count for display.
    
    Args:
        views: View count
        
    Returns:
        Formatted string
        
    Examples:
        >>> format_view_count(1234)
        '1.2K views'
        
        >>> format_view_count(1234567)
        '1.2M views'
    """
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    elif views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    else:
        return f"{views} views"


def truncate_comment(text: str, max_length: int = 100) -> str:
    """
    Truncate comment text for preview.
    
    Args:
        text: Comment text
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def extract_timestamps(text: str) -> List[str]:
    """
    Extract timestamps from comment text.
    
    Args:
        text: Comment text
        
    Returns:
        List of timestamps (e.g., ["1:23", "5:45"])
        
    Examples:
        >>> extract_timestamps("Check 1:23 and 5:45 in the video!")
        ['1:23', '5:45']
    """
    # Pattern for MM:SS or H:MM:SS
    pattern = r'\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b'
    
    timestamps = re.findall(pattern, text)
    
    return timestamps


def calculate_quota_cost(operation: str, count: int = 1) -> int:
    """
    Calculate quota cost for operations.
    
    Args:
        operation: Operation type (read, write, search, etc.)
        count: Number of operations
        
    Returns:
        Total quota units
        
    Quota costs:
    - read: 1 unit
    - write (comment): 50 units
    - search: 100 units
    """
    costs = {
        "read": 1,
        "write": 50,
        "search": 100,
        "delete": 50
    }
    
    cost_per_operation = costs.get(operation, 1)
    return cost_per_operation * count


def is_quota_available(used: int, required: int, limit: int = 10000) -> bool:
    """
    Check if enough quota is available for operation.
    
    Args:
        used: Quota already used
        required: Quota required for operation
        limit: Daily quota limit (default: 10000)
        
    Returns:
        True if quota available
    """
    return (used + required) <= limit