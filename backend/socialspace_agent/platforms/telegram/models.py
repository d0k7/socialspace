"""
Telegram Platform - Data Models
================================

Telegram-specific data models and message types.

Telegram Message Types:
-----------------------
- text: Plain text messages
- photo: Images
- video: Videos
- audio: Audio files
- voice: Voice messages
- document: File attachments
- sticker: Stickers
- animation: GIFs
- location: Shared location
- contact: Shared contact

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 4
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# TELEGRAM USER
# ============================================

class TelegramUser(BaseModel):
    """
    Telegram user model.
    
    Represents a Telegram user (sender/recipient).
    """
    id: int = Field(..., description="Telegram user ID")
    is_bot: bool = Field(default=False, description="True if user is a bot")
    first_name: str = Field(..., description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    username: Optional[str] = Field(None, description="User's @username")
    language_code: Optional[str] = Field(None, description="User's language code")
    
    def get_full_name(self) -> str:
        """Get user's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    def get_mention(self) -> str:
        """Get @username or full name."""
        if self.username:
            return f"@{self.username}"
        return self.get_full_name()


# ============================================
# TELEGRAM CHAT
# ============================================

class TelegramChat(BaseModel):
    """
    Telegram chat model.
    
    Represents a chat (private, group, supergroup, channel).
    """
    id: int = Field(..., description="Telegram chat ID")
    type: Literal["private", "group", "supergroup", "channel"] = Field(
        ..., description="Type of chat"
    )
    title: Optional[str] = Field(None, description="Chat title (for groups)")
    username: Optional[str] = Field(None, description="Chat @username")
    first_name: Optional[str] = Field(None, description="First name (private chats)")
    last_name: Optional[str] = Field(None, description="Last name (private chats)")


# ============================================
# TELEGRAM MEDIA
# ============================================

class TelegramPhotoSize(BaseModel):
    """Telegram photo size (one resolution of a photo)."""
    file_id: str = Field(..., description="Telegram file ID")
    file_unique_id: str = Field(..., description="Unique file ID")
    width: int = Field(..., description="Photo width")
    height: int = Field(..., description="Photo height")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class TelegramDocument(BaseModel):
    """Telegram document/file."""
    file_id: str = Field(..., description="Telegram file ID")
    file_unique_id: str = Field(..., description="Unique file ID")
    file_name: Optional[str] = Field(None, description="Original filename")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class TelegramVoice(BaseModel):
    """Telegram voice message."""
    file_id: str = Field(..., description="Telegram file ID")
    file_unique_id: str = Field(..., description="Unique file ID")
    duration: int = Field(..., description="Duration in seconds")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class TelegramVideo(BaseModel):
    """Telegram video."""
    file_id: str = Field(..., description="Telegram file ID")
    file_unique_id: str = Field(..., description="Unique file ID")
    width: int = Field(..., description="Video width")
    height: int = Field(..., description="Video height")
    duration: int = Field(..., description="Duration in seconds")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class TelegramAudio(BaseModel):
    """Telegram audio file."""
    file_id: str = Field(..., description="Telegram file ID")
    file_unique_id: str = Field(..., description="Unique file ID")
    duration: int = Field(..., description="Duration in seconds")
    performer: Optional[str] = Field(None, description="Performer")
    title: Optional[str] = Field(None, description="Title")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class TelegramLocation(BaseModel):
    """Telegram location."""
    longitude: float = Field(..., description="Longitude")
    latitude: float = Field(..., description="Latitude")


# ============================================
# TELEGRAM MESSAGE
# ============================================

class TelegramMessage(BaseModel):
    """
    Telegram message model.
    
    Represents a message from Telegram Bot API.
    
    Example from Telegram API:
        {
            "message_id": 123,
            "from": {"id": 123456, "first_name": "John", "username": "john"},
            "chat": {"id": 123456, "type": "private"},
            "date": 1708300000,
            "text": "Hello from Telegram!"
        }
    """
    
    # Message identification
    message_id: int = Field(..., description="Telegram message ID")
    date: int = Field(..., description="Unix timestamp")
    
    # Participants
    from_user: Optional[TelegramUser] = Field(None, alias="from", description="Sender")
    chat: TelegramChat = Field(..., description="Chat where message was sent")
    
    # Reply info
    reply_to_message: Optional['TelegramMessage'] = Field(
        None, description="Original message (if this is a reply)"
    )
    
    # Text content
    text: Optional[str] = Field(None, description="Text content")
    caption: Optional[str] = Field(None, description="Media caption")
    
    # Media
    photo: Optional[List[TelegramPhotoSize]] = Field(None, description="Photo (array of sizes)")
    video: Optional[TelegramVideo] = Field(None, description="Video")
    audio: Optional[TelegramAudio] = Field(None, description="Audio")
    voice: Optional[TelegramVoice] = Field(None, description="Voice message")
    document: Optional[TelegramDocument] = Field(None, description="Document")
    
    # Location
    location: Optional[TelegramLocation] = Field(None, description="Shared location")
    
    # Other
    sticker: Optional[Dict[str, Any]] = Field(None, description="Sticker")
    animation: Optional[Dict[str, Any]] = Field(None, description="Animation (GIF)")
    
    def get_content(self) -> Optional[str]:
        """Extract text content from message."""
        return self.text or self.caption
    
    def get_media_type(self) -> Optional[str]:
        """Get media type if message contains media."""
        if self.photo:
            return "photo"
        elif self.video:
            return "video"
        elif self.audio:
            return "audio"
        elif self.voice:
            return "voice"
        elif self.document:
            return "document"
        elif self.sticker:
            return "sticker"
        elif self.animation:
            return "animation"
        return None
    
    def get_file_id(self) -> Optional[str]:
        """Get Telegram file_id for media."""
        if self.photo and len(self.photo) > 0:
            # Get largest photo
            return max(self.photo, key=lambda p: p.file_size or 0).file_id
        elif self.video:
            return self.video.file_id
        elif self.audio:
            return self.audio.file_id
        elif self.voice:
            return self.voice.file_id
        elif self.document:
            return self.document.file_id
        return None


# ============================================
# TELEGRAM UPDATE
# ============================================

class TelegramUpdate(BaseModel):
    """
    Telegram update model.
    
    Represents an update from getUpdates API.
    """
    update_id: int = Field(..., description="Update ID")
    message: Optional[TelegramMessage] = Field(None, description="New message")
    edited_message: Optional[TelegramMessage] = Field(None, description="Edited message")
    
    def get_message(self) -> Optional[TelegramMessage]:
        """Get the message from update (new or edited)."""
        return self.message or self.edited_message


# ============================================
# TELEGRAM API RESPONSE
# ============================================

class TelegramResponse(BaseModel):
    """Response from Telegram Bot API."""
    ok: bool = Field(..., description="Success status")
    result: Optional[Any] = Field(None, description="Result data")
    description: Optional[str] = Field(None, description="Error description")
    error_code: Optional[int] = Field(None, description="Error code")


class TelegramSendMessageResponse(BaseModel):
    """Response from sendMessage API."""
    message_id: int = Field(..., description="Sent message ID")
    date: int = Field(..., description="Unix timestamp")
    chat: TelegramChat = Field(..., description="Chat")
    text: Optional[str] = Field(None, description="Message text")


# Allow forward references for reply_to_message
TelegramMessage.model_rebuild()