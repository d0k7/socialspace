"""
Discord Platform - Utility Functions
=====================================

Helper functions for Discord integration.

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 6
"""

import re
from typing import Optional, List, Dict


def format_discord_id(discord_id: str) -> str:
    """
    Format Discord ID (snowflake).
    
    Args:
        discord_id: Discord ID
        
    Returns:
        Formatted ID (string)
    """
    return str(discord_id).strip()


def validate_discord_id(discord_id: str) -> bool:
    """
    Validate Discord ID (snowflake) format.
    
    Args:
        discord_id: ID to validate
        
    Returns:
        True if valid
        
    Discord IDs are snowflakes (64-bit integers as strings).
    """
    try:
        # Discord snowflakes are 17-19 digit numbers
        id_int = int(discord_id)
        return len(discord_id) >= 17 and id_int > 0
    except (ValueError, TypeError):
        return False


def parse_mention(text: str) -> List[str]:
    """
    Extract user mentions from Discord message.
    
    Args:
        text: Message text
        
    Returns:
        List of user IDs mentioned
        
    Discord mentions format: <@user_id> or <@!user_id>
    
    Examples:
        >>> parse_mention("Hello <@123456789>!")
        ['123456789']
        
        >>> parse_mention("Hi <@!111> and <@222>")
        ['111', '222']
    """
    if not text:
        return []
    
    # Match <@user_id> or <@!user_id>
    mentions = re.findall(r'<@!?(\d+)>', text)
    
    return mentions


def parse_channel_mention(text: str) -> List[str]:
    """
    Extract channel mentions from Discord message.
    
    Args:
        text: Message text
        
    Returns:
        List of channel IDs mentioned
        
    Discord channel mentions: <#channel_id>
    """
    if not text:
        return []
    
    # Match <#channel_id>
    channels = re.findall(r'<#(\d+)>', text)
    
    return channels


def parse_role_mention(text: str) -> List[str]:
    """
    Extract role mentions from Discord message.
    
    Args:
        text: Message text
        
    Returns:
        List of role IDs mentioned
        
    Discord role mentions: <@&role_id>
    """
    if not text:
        return []
    
    # Match <@&role_id>
    roles = re.findall(r'<@&(\d+)>', text)
    
    return roles


def parse_custom_emoji(text: str) -> List[Dict[str, str]]:
    """
    Extract custom emojis from Discord message.
    
    Args:
        text: Message text
        
    Returns:
        List of emoji dictionaries with name and id
        
    Discord custom emoji: <:name:id> or <a:name:id> (animated)
    
    Example:
        >>> parse_custom_emoji("Nice <:coolface:123456>!")
        [{'name': 'coolface', 'id': '123456', 'animated': False}]
    """
    if not text:
        return []
    
    emojis = []
    
    # Match <:name:id> (static) or <a:name:id> (animated)
    matches = re.findall(r'<(a?):(\w+):(\d+)>', text)
    
    for match in matches:
        animated, name, emoji_id = match
        emojis.append({
            'name': name,
            'id': emoji_id,
            'animated': bool(animated)
        })
    
    return emojis


def create_user_tag(username: str, discriminator: str) -> str:
    """
    Create Discord user tag (username#discriminator).
    
    Args:
        username: Username
        discriminator: 4-digit discriminator
        
    Returns:
        User tag
        
    Example:
        >>> create_user_tag("john", "0001")
        'john#0001'
    """
    return f"{username}#{discriminator}"


def create_user_mention(user_id: str) -> str:
    """
    Create Discord user mention string.
    
    Args:
        user_id: User ID
        
    Returns:
        Mention string
        
    Example:
        >>> create_user_mention("123456789")
        '<@123456789>'
    """
    return f"<@{user_id}>"


def create_channel_mention(channel_id: str) -> str:
    """
    Create Discord channel mention string.
    
    Args:
        channel_id: Channel ID
        
    Returns:
        Mention string
        
    Example:
        >>> create_channel_mention("987654321")
        '<#987654321>'
    """
    return f"<#{channel_id}>"


def hex_to_decimal_color(hex_color: str) -> int:
    """
    Convert hex color to decimal for Discord embeds.
    
    Args:
        hex_color: Hex color (e.g., "#00ff00" or "00ff00")
        
    Returns:
        Decimal color value
        
    Example:
        >>> hex_to_decimal_color("#00ff00")
        65280
        
        >>> hex_to_decimal_color("ff0000")
        16711680
    """
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to decimal
    return int(hex_color, 16)


def decimal_to_hex_color(decimal_color: int) -> str:
    """
    Convert decimal color to hex.
    
    Args:
        decimal_color: Decimal color value
        
    Returns:
        Hex color string with #
        
    Example:
        >>> decimal_to_hex_color(65280)
        '#00ff00'
    """
    return f"#{decimal_color:06x}"


def truncate_content(text: str, max_length: int = 2000) -> str:
    """
    Truncate message content to Discord's limit.
    
    Args:
        text: Message text
        max_length: Maximum length (default: 2000)
        
    Returns:
        Truncated text
        
    Discord message limit is 2000 characters.
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def is_valid_webhook_url(url: str) -> bool:
    """
    Validate Discord webhook URL.
    
    Args:
        url: Webhook URL
        
    Returns:
        True if valid
        
    Valid format: https://discord.com/api/webhooks/id/token
    """
    pattern = r'https://discord\.com/api/webhooks/\d+/[\w-]+'
    return bool(re.match(pattern, url))
