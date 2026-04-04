"""
WhatsApp Platform - Utility Functions
======================================

Helper functions for WhatsApp integration.

Author: Dheeraj Mishra
Created: February 19, 2026
Session: 3
"""

import re
from typing import Optional


def format_phone_number(phone: str) -> str:
    """
    Format phone number for WhatsApp API.
    
    WhatsApp expects phone numbers with country code, no + or spaces.
    
    Args:
        phone: Phone number in various formats
        
    Returns:
        Formatted phone number (digits only with country code)
        
    Examples:
        >>> format_phone_number("+91 98765 43210")
        '919876543210'
        
        >>> format_phone_number("91-9876543210")
        '919876543210'
        
        >>> format_phone_number("+1 (555) 123-4567")
        '15551234567'
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Remove leading + if present (already removed by regex but just to be safe)
    if digits.startswith('+'):
        digits = digits[1:]
    
    return digits


def validate_phone_number(phone: str) -> bool:
    """
    Validate if phone number is in correct format for WhatsApp.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid
        
    Rules:
        - Must contain only digits (after formatting)
        - Must be at least 10 digits (local number)
        - Must be at most 15 digits (international limit)
    """
    formatted = format_phone_number(phone)
    
    # Check length
    if len(formatted) < 10 or len(formatted) > 15:
        return False
    
    # Check if all digits
    return formatted.isdigit()


def extract_country_code(phone: str) -> Optional[str]:
    """
    Extract country code from phone number.
    
    Args:
        phone: Phone number with country code
        
    Returns:
        Country code (e.g., "91" for India, "1" for US) or None
        
    Note:
        This is a simple implementation. For production,
        use a library like phonenumbers for accurate parsing.
    """
    formatted = format_phone_number(phone)
    
    # Common country codes
    country_codes = {
        '1': 1,      # US, Canada
        '7': 1,      # Russia, Kazakhstan
        '20': 2,     # Egypt
        '27': 2,     # South Africa
        '30': 2,     # Greece
        '31': 2,     # Netherlands
        '32': 2,     # Belgium
        '33': 2,     # France
        '34': 2,     # Spain
        '36': 2,     # Hungary
        '39': 2,     # Italy
        '40': 2,     # Romania
        '41': 2,     # Switzerland
        '43': 2,     # Austria
        '44': 2,     # UK
        '45': 2,     # Denmark
        '46': 2,     # Sweden
        '47': 2,     # Norway
        '48': 2,     # Poland
        '49': 2,     # Germany
        '51': 2,     # Peru
        '52': 2,     # Mexico
        '53': 2,     # Cuba
        '54': 2,     # Argentina
        '55': 2,     # Brazil
        '56': 2,     # Chile
        '57': 2,     # Colombia
        '58': 2,     # Venezuela
        '60': 2,     # Malaysia
        '61': 2,     # Australia
        '62': 2,     # Indonesia
        '63': 2,     # Philippines
        '64': 2,     # New Zealand
        '65': 2,     # Singapore
        '66': 2,     # Thailand
        '81': 2,     # Japan
        '82': 2,     # South Korea
        '84': 2,     # Vietnam
        '86': 2,     # China
        '90': 2,     # Turkey
        '91': 2,     # India
        '92': 2,     # Pakistan
        '93': 2,     # Afghanistan
        '94': 2,     # Sri Lanka
        '95': 2,     # Myanmar
        '98': 2,     # Iran
        '212': 3,    # Morocco
        '213': 3,    # Algeria
        '216': 3,    # Tunisia
        '218': 3,    # Libya
        '220': 3,    # Gambia
        '221': 3,    # Senegal
        '234': 3,    # Nigeria
        '254': 3,    # Kenya
        '255': 3,    # Tanzania
        '256': 3,    # Uganda
        '351': 3,    # Portugal
        '353': 3,    # Ireland
        '354': 3,    # Iceland
        '355': 3,    # Albania
        '370': 3,    # Lithuania
        '371': 3,    # Latvia
        '372': 3,    # Estonia
        '373': 3,    # Moldova
        '374': 3,    # Armenia
        '375': 3,    # Belarus
        '376': 3,    # Andorra
        '380': 3,    # Ukraine
        '381': 3,    # Serbia
        '382': 3,    # Montenegro
        '383': 3,    # Kosovo
        '385': 3,    # Croatia
        '386': 3,    # Slovenia
        '387': 3,    # Bosnia
        '389': 3,    # North Macedonia
        '420': 3,    # Czech Republic
        '421': 3,    # Slovakia
        '423': 3,    # Liechtenstein
        '880': 3,    # Bangladesh
        '886': 3,    # Taiwan
        '960': 3,    # Maldives
        '961': 3,    # Lebanon
        '962': 3,    # Jordan
        '963': 3,    # Syria
        '964': 3,    # Iraq
        '965': 3,    # Kuwait
        '966': 3,    # Saudi Arabia
        '967': 3,    # Yemen
        '968': 3,    # Oman
        '971': 3,    # UAE
        '972': 3,    # Israel
        '973': 3,    # Bahrain
        '974': 3,    # Qatar
        '975': 3,    # Bhutan
        '976': 3,    # Mongolia
        '977': 3,    # Nepal
    }
    
    # Try to extract country code
    for code, length in country_codes.items():
        if formatted.startswith(code) and len(code) == length:
            return code
    
    return None


def is_valid_whatsapp_id(message_id: str) -> bool:
    """
    Check if string is a valid WhatsApp message ID.
    
    Args:
        message_id: Message ID to validate
        
    Returns:
        True if valid WhatsApp message ID format
        
    WhatsApp message IDs typically start with "wamid."
    """
    return isinstance(message_id, str) and message_id.startswith("wamid.")