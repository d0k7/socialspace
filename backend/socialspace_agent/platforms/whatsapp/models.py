"""
WhatsApp Platform - Data Models
================================

WhatsApp-specific data models and message types.

WhatsApp Message Types:
-----------------------
- text: Plain text messages
- image: Image with optional caption
- video: Video with optional caption
- audio: Voice messages
- document: File attachments
- location: Shared location
- contacts: Shared contact cards
- interactive: Buttons, lists

Author: Dheeraj Mishra
Created: February 19, 2026
Session: 3
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# WHATSAPP MESSAGE TYPES
# ============================================

class WhatsAppText(BaseModel):
    """WhatsApp text message."""
    body: str = Field(..., description="Message text content")
    preview_url: bool = Field(default=False, description="Enable URL preview")


class WhatsAppMedia(BaseModel):
    """WhatsApp media message (image/video/audio/document)."""
    id: Optional[str] = Field(None, description="Media ID from WhatsApp")
    link: Optional[str] = Field(None, description="Public URL to media")
    caption: Optional[str] = Field(None, description="Media caption")
    filename: Optional[str] = Field(None, description="File name")
    mime_type: Optional[str] = Field(None, description="MIME type")


class WhatsAppLocation(BaseModel):
    """WhatsApp location message."""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")


class WhatsAppContact(BaseModel):
    """WhatsApp contact card."""
    name: str = Field(..., description="Contact name")
    phone: str = Field(..., description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email")


# ============================================
# WHATSAPP MESSAGE
# ============================================

class WhatsAppMessage(BaseModel):
    """
    WhatsApp message model (from API).
    
    This represents the raw message format from WhatsApp API.
    We'll convert this to UnifiedMessage for processing.
    
    Example from WhatsApp API:
        {
            "id": "wamid.XXX",
            "from": "919876543210",
            "timestamp": "1708300000",
            "type": "text",
            "text": {"body": "Hello!"}
        }
    """
    
    # Message identification
    id: str = Field(..., description="WhatsApp message ID (wamid)")
    from_number: str = Field(..., alias="from", description="Sender phone number")
    to_number: Optional[str] = Field(None, description="Recipient phone number")
    timestamp: str = Field(..., description="Unix timestamp")
    
    # Message type and content
    type: Literal[
        "text", "image", "video", "audio", "document",
        "location", "contacts", "interactive", "button",
        "sticker", "reaction"
    ] = Field(..., description="Message type")
    
    # Content (type-specific)
    text: Optional[WhatsAppText] = None
    image: Optional[WhatsAppMedia] = None
    video: Optional[WhatsAppMedia] = None
    audio: Optional[WhatsAppMedia] = None
    document: Optional[WhatsAppMedia] = None
    location: Optional[WhatsAppLocation] = None
    contacts: Optional[List[WhatsAppContact]] = None
    
    # Metadata
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Context (for replies)"
    )
    
    def get_content(self) -> Optional[str]:
        """
        Extract text content from message.
        
        Returns:
            Text content or None
        """
        if self.text:
            return self.text.body
        elif self.image and self.image.caption:
            return self.image.caption
        elif self.video and self.video.caption:
            return self.video.caption
        elif self.document and self.document.caption:
            return self.document.caption
        return None
    
    def get_media_url(self) -> Optional[str]:
        """
        Get media URL if message contains media.
        
        Returns:
            Media URL or None
        """
        for media_type in ['image', 'video', 'audio', 'document']:
            media = getattr(self, media_type, None)
            if media:
                return media.link or media.id
        return None


# ============================================
# WHATSAPP WEBHOOK PAYLOAD
# ============================================

class WhatsAppWebhookEntry(BaseModel):
    """WhatsApp webhook entry."""
    id: str = Field(..., description="WhatsApp Business Account ID")
    changes: List[Dict[str, Any]] = Field(..., description="Changes array")


class WhatsAppWebhook(BaseModel):
    """
    WhatsApp webhook payload.
    
    When WhatsApp sends messages to your webhook, this is the structure.
    
    Example:
        {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messages": [...]
                    }
                }]
            }]
        }
    """
    
    object: str = Field(..., description="Object type (whatsapp_business_account)")
    entry: List[WhatsAppWebhookEntry] = Field(..., description="Webhook entries")
    
    def get_messages(self) -> List[WhatsAppMessage]:
        """
        Extract messages from webhook payload.
        
        Returns:
            List of WhatsAppMessage objects
        """
        messages = []
        
        for entry in self.entry:
            for change in entry.changes:
                value = change.get('value', {})
                raw_messages = value.get('messages', [])
                
                for raw_msg in raw_messages:
                    try:
                        msg = WhatsAppMessage(**raw_msg)
                        messages.append(msg)
                    except Exception as e:
                        # Log error but continue processing other messages
                        print(f"Error parsing message: {e}")
                        continue
        
        return messages


# ============================================
# WHATSAPP API RESPONSE
# ============================================

class WhatsAppSendResponse(BaseModel):
    """Response from WhatsApp send message API."""
    
    messaging_product: str = Field(..., description="Always 'whatsapp'")
    contacts: List[Dict[str, str]] = Field(..., description="Recipient info")
    messages: List[Dict[str, str]] = Field(..., description="Message info with ID")
    
    def get_message_id(self) -> Optional[str]:
        """Get the WhatsApp message ID (wamid)."""
        if self.messages and len(self.messages) > 0:
            return self.messages[0].get('id')
        return None


# ============================================
# WHATSAPP ERROR
# ============================================

class WhatsAppError(BaseModel):
    """WhatsApp API error response."""
    
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    code: int = Field(..., description="Error code")
    error_subcode: Optional[int] = Field(None, description="Error subcode")
    fbtrace_id: Optional[str] = Field(None, description="Facebook trace ID")