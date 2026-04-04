"""
Telegram Platform - Utility Functions
======================================

Helper functions for Telegram integration.

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 4
"""

import re
from typing import Optional


def format_telegram_id(telegram_id: str) -> str:
    """
    Format Telegram ID (remove non-numeric characters).
    
    Args:
        telegram_id: Telegram user/chat ID
        
    Returns:
        Formatted ID (digits only)
        
    Examples:
        >>> format_telegram_id("123456789")
        '123456789'
        
        >>> format_telegram_id("user_123456")
        '123456'
    """
    return re.sub(r'\D', '', str(telegram_id))


def validate_telegram_id(telegram_id: str) -> bool:
    """
    Validate if string is a valid Telegram ID.
    
    Args:
        telegram_id: ID to validate
        
    Returns:
        True if valid
        
    Telegram user/chat IDs are positive integers.
    """
    try:
        id_int = int(telegram_id)
        return id_int > 0
    except (ValueError, TypeError):
        return False


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
        
    Markdown special characters: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special_chars = r'_*[]()~`>#+-=|{}.!'
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def is_valid_bot_token(token: str) -> bool:
    """
    Validate Telegram bot token format.
    
    Args:
        token: Bot token to validate
        
    Returns:
        True if valid format
        
    Valid format: <bot_id>:<token>
    Example: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    """
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token))


def extract_command(text: str) -> Optional[str]:
    """
    Extract command from message text.
    
    Args:
        text: Message text
        
    Returns:
        Command without / or None
        
    Examples:
        >>> extract_command("/start")
        'start'
        
        >>> extract_command("/help@mybot some args")
        'help'
        
        >>> extract_command("Hello world")
        None
    """
    if not text or not text.startswith('/'):
        return None
    
    # Remove leading /
    text = text[1:]
    
    # Handle bot username (@botname)
    if '@' in text:
        text = text.split('@')[0]
    
    # Get first word (command)
    command = text.split()[0] if text else None
    
    return command.lower() if command else None


def get_command_args(text: str) -> list[str]:
    """
    Extract command arguments.
    
    Args:
        text: Message text
        
    Returns:
        List of arguments
        
    Examples:
        >>> get_command_args("/start arg1 arg2")
        ['arg1', 'arg2']
        
        >>> get_command_args("/help")
        []
    """
    if not text or not text.startswith('/'):
        return []
    
    parts = text.split()
    
    # Return all parts except the command
    return parts[1:] if len(parts) > 1 else []