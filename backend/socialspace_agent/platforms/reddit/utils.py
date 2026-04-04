"""
Reddit Platform - Utility Functions
====================================

Helper functions for Reddit integration.

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 7
"""

import re
from typing import Optional, Dict, Any


def format_reddit_id(reddit_id: str) -> str:
    """
    Format Reddit ID (remove prefix if present).
    
    Args:
        reddit_id: Reddit ID (with or without prefix)
        
    Returns:
        ID without prefix
        
    Examples:
        >>> format_reddit_id("t3_abc123")
        'abc123'
        
        >>> format_reddit_id("abc123")
        'abc123'
    """
    if "_" in reddit_id:
        return reddit_id.split("_", 1)[1]
    return reddit_id


def add_thing_prefix(reddit_id: str, thing_type: str) -> str:
    """
    Add thing prefix to Reddit ID.
    
    Args:
        reddit_id: Reddit ID (without prefix)
        thing_type: Thing type (comment, submission, etc.)
        
    Returns:
        ID with prefix
        
    Thing types:
    - t1_ = Comment
    - t2_ = Redditor
    - t3_ = Submission
    - t4_ = Message
    - t5_ = Subreddit
    
    Example:
        >>> add_thing_prefix("abc123", "submission")
        't3_abc123'
    """
    prefix_map = {
        "comment": "t1_",
        "redditor": "t2_",
        "submission": "t3_",
        "message": "t4_",
        "subreddit": "t5_"
    }
    
    prefix = prefix_map.get(thing_type.lower(), "t3_")
    
    # Don't add if already has prefix
    if reddit_id.startswith(prefix):
        return reddit_id
    
    return f"{prefix}{reddit_id}"


def parse_subreddit_name(subreddit: str) -> str:
    """
    Parse subreddit name (remove r/ prefix if present).
    
    Args:
        subreddit: Subreddit name
        
    Returns:
        Subreddit name without r/
        
    Examples:
        >>> parse_subreddit_name("r/python")
        'python'
        
        >>> parse_subreddit_name("python")
        'python'
    """
    if subreddit.startswith("r/"):
        return subreddit[2:]
    return subreddit


def parse_username(username: str) -> str:
    """
    Parse username (remove u/ prefix if present).
    
    Args:
        username: Username
        
    Returns:
        Username without u/
        
    Examples:
        >>> parse_username("u/john_doe")
        'john_doe'
        
        >>> parse_username("john_doe")
        'john_doe'
    """
    if username.startswith("u/"):
        return username[2:]
    return username


def create_reddit_url(item_type: str, identifier: str) -> str:
    """
    Create Reddit URL for an item.
    
    Args:
        item_type: Type (subreddit, user, submission, comment)
        identifier: Identifier (name or ID)
        
    Returns:
        Full Reddit URL
        
    Examples:
        >>> create_reddit_url("subreddit", "python")
        'https://reddit.com/r/python'
        
        >>> create_reddit_url("user", "john_doe")
        'https://reddit.com/u/john_doe'
    """
    base_url = "https://reddit.com"
    
    if item_type == "subreddit":
        return f"{base_url}/r/{parse_subreddit_name(identifier)}"
    elif item_type == "user":
        return f"{base_url}/u/{parse_username(identifier)}"
    elif item_type == "submission":
        # Assuming identifier is submission ID
        return f"{base_url}/comments/{format_reddit_id(identifier)}"
    
    return base_url


def extract_reddit_mentions(text: str) -> Dict[str, list]:
    """
    Extract mentions from Reddit text.
    
    Args:
        text: Text content
        
    Returns:
        Dictionary with users and subreddits mentioned
        
    Example:
        >>> extract_reddit_mentions("Check u/john and r/python!")
        {'users': ['john'], 'subreddits': ['python']}
    """
    # Find user mentions (u/username)
    users = re.findall(r'u/(\w+)', text)
    
    # Find subreddit mentions (r/subreddit)
    subreddits = re.findall(r'r/(\w+)', text)
    
    return {
        "users": users,
        "subreddits": subreddits
    }


def is_valid_subreddit_name(name: str) -> bool:
    """
    Validate subreddit name format.
    
    Args:
        name: Subreddit name
        
    Returns:
        True if valid
        
    Rules:
    - 3-21 characters
    - Letters, numbers, underscores
    - Must start/end with letter or number
    """
    name = parse_subreddit_name(name)
    
    if len(name) < 3 or len(name) > 21:
        return False
    
    # Check format
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_]*[a-zA-Z0-9]$'
    return bool(re.match(pattern, name))


def format_karma(karma: int) -> str:
    """
    Format karma count for display.
    
    Args:
        karma: Karma count
        
    Returns:
        Formatted string
        
    Examples:
        >>> format_karma(1234)
        '1.2k'
        
        >>> format_karma(1234567)
        '1.2M'
    """
    if karma >= 1_000_000:
        return f"{karma / 1_000_000:.1f}M"
    elif karma >= 1_000:
        return f"{karma / 1_000:.1f}k"
    else:
        return str(karma)


def calculate_upvote_percentage(upvote_ratio: float) -> int:
    """
    Calculate upvote percentage from ratio.
    
    Args:
        upvote_ratio: Upvote ratio (0-1)
        
    Returns:
        Percentage (0-100)
        
    Example:
        >>> calculate_upvote_percentage(0.87)
        87
    """
    return int(upvote_ratio * 100)


def truncate_text(text: str, max_length: int = 300) -> str:
    """
    Truncate text for preview.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."