"""
LinkedIn Platform - Utility Functions
======================================

Helper functions for LinkedIn integration.

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 11
"""

import re
from typing import Optional


def format_linkedin_urn(urn: str) -> str:
    """
    Format LinkedIn URN (ensure it's clean).
    
    Args:
        urn: LinkedIn URN
        
    Returns:
        Cleaned URN
    """
    return str(urn).strip()


def parse_urn(urn: str) -> dict:
    """
    Parse LinkedIn URN into components.
    
    Args:
        urn: LinkedIn URN (e.g., "urn:li:person:123")
        
    Returns:
        Dictionary with URN components
        
    Example:
        >>> parse_urn("urn:li:person:123")
        {'namespace': 'li', 'type': 'person', 'id': '123'}
    """
    parts = urn.split(":")
    
    if len(parts) >= 4:
        return {
            "namespace": parts[1],
            "type": parts[2],
            "id": parts[3]
        }
    
    return {}


def create_person_urn(person_id: str) -> str:
    """
    Create person URN from ID.
    
    Args:
        person_id: Person ID
        
    Returns:
        Person URN
        
    Example:
        >>> create_person_urn("123")
        'urn:li:person:123'
    """
    return f"urn:li:person:{person_id}"


def create_organization_urn(org_id: str) -> str:
    """
    Create organization URN from ID.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Organization URN
    """
    return f"urn:li:organization:{org_id}"


def create_linkedin_url(object_type: str, identifier: str) -> str:
    """
    Create LinkedIn URL for an object.
    
    Args:
        object_type: Type (profile, company, post)
        identifier: Identifier
        
    Returns:
        Full LinkedIn URL
        
    Examples:
        >>> create_linkedin_url("profile", "john-doe")
        'https://linkedin.com/in/john-doe'
        
        >>> create_linkedin_url("company", "socialspace")
        'https://linkedin.com/company/socialspace'
    """
    if object_type == "profile":
        return f"https://linkedin.com/in/{identifier}"
    elif object_type == "company":
        return f"https://linkedin.com/company/{identifier}"
    elif object_type == "post":
        return f"https://linkedin.com/feed/update/{identifier}"
    
    return f"https://linkedin.com/{identifier}"


def extract_hashtags(text: str) -> list[str]:
    """
    Extract hashtags from LinkedIn post text.
    
    Args:
        text: Post text
        
    Returns:
        List of hashtags (without #)
        
    Example:
        >>> extract_hashtags("Great post! #linkedin #professional")
        ['linkedin', 'professional']
    """
    if not text:
        return []
    
    # Match hashtags
    hashtags = re.findall(r'#(\w+)', text)
    
    return hashtags


def extract_mentions(text: str) -> list[str]:
    """
    Extract @mentions from LinkedIn text.
    
    Args:
        text: Text content
        
    Returns:
        List of mentioned names
    """
    if not text:
        return []
    
    # Match mentions
    mentions = re.findall(r'@(\w+)', text)
    
    return mentions


def truncate_post(text: str, max_length: int = 3000) -> str:
    """
    Truncate post text for LinkedIn.
    
    Args:
        text: Post text
        max_length: Maximum length (LinkedIn allows ~3000 chars)
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def is_valid_access_token(token: str) -> bool:
    """
    Basic validation for LinkedIn access token format.
    
    Args:
        token: Access token
        
    Returns:
        True if format looks valid
    """
    if not token:
        return False
    
    # LinkedIn tokens are typically long alphanumeric strings
    return len(token) > 30


def format_visibility(visibility: str) -> str:
    """
    Format visibility setting for LinkedIn API.
    
    Args:
        visibility: Visibility level
        
    Returns:
        Formatted visibility string
    """
    visibility_map = {
        "public": "PUBLIC",
        "connections": "CONNECTIONS",
        "private": "CONNECTIONS"
    }
    
    return visibility_map.get(visibility.lower(), "PUBLIC")