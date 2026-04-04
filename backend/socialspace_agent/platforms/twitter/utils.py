"""
Twitter Platform - Utility Functions
=====================================

Helper functions for Twitter integration.

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 8
"""

import re
from typing import List, Dict, Any, Optional


def format_tweet_id(tweet_id: str) -> str:
    """
    Format tweet ID (ensure it's clean).
    
    Args:
        tweet_id: Tweet ID
        
    Returns:
        Cleaned tweet ID
    """
    return str(tweet_id).strip()


def validate_tweet_length(text: str) -> bool:
    """
    Validate tweet length (max 280 characters).
    
    Args:
        text: Tweet text
        
    Returns:
        True if valid length
    """
    return len(text) <= 280


def truncate_tweet(text: str, max_length: int = 280) -> str:
    """
    Truncate text to Twitter's character limit.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default: 280)
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from tweet text.
    
    Args:
        text: Tweet text
        
    Returns:
        List of hashtags (without #)
        
    Examples:
        >>> extract_hashtags("Great post! #python #coding")
        ['python', 'coding']
    """
    if not text:
        return []
    
    # Match hashtags (# followed by alphanumeric and underscore)
    hashtags = re.findall(r'#(\w+)', text)
    
    return hashtags


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from tweet text.
    
    Args:
        text: Tweet text
        
    Returns:
        List of usernames (without @)
        
    Examples:
        >>> extract_mentions("Hey @john and @jane!")
        ['john', 'jane']
    """
    if not text:
        return []
    
    # Match mentions (@ followed by alphanumeric and underscore)
    mentions = re.findall(r'@(\w+)', text)
    
    return mentions


def parse_twitter_username(username: str) -> str:
    """
    Parse Twitter username (remove @ if present).
    
    Args:
        username: Username
        
    Returns:
        Username without @
        
    Examples:
        >>> parse_twitter_username("@elonmusk")
        'elonmusk'
        
        >>> parse_twitter_username("elonmusk")
        'elonmusk'
    """
    if username.startswith("@"):
        return username[1:]
    return username


def create_twitter_url(username: str, tweet_id: Optional[str] = None) -> str:
    """
    Create Twitter URL.
    
    Args:
        username: Twitter username
        tweet_id: Tweet ID (optional)
        
    Returns:
        Full Twitter URL
        
    Examples:
        >>> create_twitter_url("elonmusk")
        'https://twitter.com/elonmusk'
        
        >>> create_twitter_url("elonmusk", "123456789")
        'https://twitter.com/elonmusk/status/123456789'
    """
    username = parse_twitter_username(username)
    
    if tweet_id:
        return f"https://twitter.com/{username}/status/{tweet_id}"
    
    return f"https://twitter.com/{username}"


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


def is_valid_twitter_username(username: str) -> bool:
    """
    Validate Twitter username format.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid
        
    Rules:
    - 1-15 characters
    - Letters, numbers, underscores
    - Cannot be all numbers
    """
    username = parse_twitter_username(username)
    
    if len(username) < 1 or len(username) > 15:
        return False
    
    # Check if all numbers
    if username.isdigit():
        return False
    
    # Check format
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))


def create_thread(tweets: List[str]) -> List[str]:
    """
    Create a thread by numbering tweets.
    
    Args:
        tweets: List of tweet texts
        
    Returns:
        List of numbered tweets
        
    Example:
        >>> tweets = ["First tweet", "Second tweet", "Third tweet"]
        >>> thread = create_thread(tweets)
        >>> print(thread)
        ['1/ First tweet', '2/ Second tweet', '3/ Third tweet']
    """
    if len(tweets) <= 1:
        return tweets
    
    numbered_tweets = []
    for i, tweet in enumerate(tweets, 1):
        numbered_tweets.append(f"{i}/ {tweet}")
    
    return numbered_tweets


def split_long_text(text: str, max_length: int = 280) -> List[str]:
    """
    Split long text into tweet-sized chunks.
    
    Args:
        text: Long text to split
        max_length: Maximum length per tweet
        
    Returns:
        List of tweet texts
    """
    if len(text) <= max_length:
        return [text]
    
    # Split by sentences
    sentences = re.split(r'[.!?]\s+', text)
    
    tweets = []
    current_tweet = ""
    
    for sentence in sentences:
        # Add period back if not present
        if sentence and not sentence[-1] in '.!?':
            sentence += "."
        
        if len(current_tweet) + len(sentence) + 1 <= max_length:
            current_tweet += " " + sentence if current_tweet else sentence
        else:
            if current_tweet:
                tweets.append(current_tweet.strip())
            current_tweet = sentence
    
    if current_tweet:
        tweets.append(current_tweet.strip())
    
    return tweets
