"""
Snapchat Platform - Data Models
================================

Snapchat-specific data models.

Snapchat Concepts:
------------------
- User: Snapchat user/profile
- Snap: Photo/video message (ephemeral)
- Story: 24-hour content
- Bitmoji: Personalized avatar
- Spotlight: Public short videos

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 13
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# SNAPCHAT USER
# ============================================

class SnapchatUser(BaseModel):
    """
    Snapchat user model.
    
    Represents a Snapchat user/profile.
    """
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: str = Field(..., description="Display name")
    
    # Profile
    bitmoji_avatar_id: Optional[str] = Field(None, description="Bitmoji avatar ID")
    
    def get_snapcode_url(self) -> str:
        """Get Snapcode URL."""
        return f"https://snapchat.com/add/{self.username}"


# ============================================
# SNAPCHAT SNAP
# ============================================

class SnapchatSnap(BaseModel):
    """
    Snapchat snap model.
    
    Represents a snap (photo/video message).
    """
    id: str = Field(..., description="Snap ID")
    
    # Media
    media_url: Optional[str] = Field(None, description="Media URL")
    media_type: str = Field(..., description="Media type (IMAGE, VIDEO)")
    
    # Duration
    duration: Optional[int] = Field(None, description="Snap duration in seconds")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    
    # Status
    is_opened: Optional[bool] = Field(False, description="Has been opened")
    
    def is_image(self) -> bool:
        """Check if snap is an image."""
        return self.media_type == "IMAGE"
    
    def is_video(self) -> bool:
        """Check if snap is a video."""
        return self.media_type == "VIDEO"


# ============================================
# SNAPCHAT STORY
# ============================================

class SnapchatStory(BaseModel):
    """
    Snapchat story model.
    
    Represents a story (24-hour content).
    """
    id: str = Field(..., description="Story ID")
    
    # Author
    username: str = Field(..., description="Story author username")
    
    # Media
    media_url: str = Field(..., description="Media URL")
    media_type: str = Field(..., description="Media type")
    
    # Timestamps
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: str = Field(..., description="Expiration timestamp (24h)")
    
    # Engagement
    view_count: Optional[int] = Field(0, description="Number of views")
    
    def is_expired(self) -> bool:
        """Check if story is expired."""
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.now(expiry.tzinfo) > expiry
        except:
            return False


# ============================================
# SNAPCHAT SPOTLIGHT
# ============================================

class SnapchatSpotlight(BaseModel):
    """
    Snapchat Spotlight model.
    
    Represents a public short video (like TikTok).
    """
    id: str = Field(..., description="Spotlight ID")
    
    # Creator
    username: str = Field(..., description="Creator username")
    
    # Media
    media_url: str = Field(..., description="Video URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    
    # Content
    caption: Optional[str] = Field(None, description="Caption/description")
    
    # Duration
    duration: int = Field(..., description="Video duration in seconds")
    
    # Timestamps
    created_at: str = Field(..., description="Creation timestamp")
    
    # Engagement
    view_count: Optional[int] = Field(0, description="View count")
    like_count: Optional[int] = Field(0, description="Like count")


# ============================================
# SNAPCHAT BITMOJI
# ============================================

class SnapchatBitmoji(BaseModel):
    """
    Snapchat Bitmoji model.
    
    Represents a Bitmoji avatar.
    """
    avatar_id: str = Field(..., description="Avatar ID")
    
    # Images
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    
    # Metadata
    background_color: Optional[str] = Field(None, description="Background color")


# ============================================
# SNAPCHAT API RESPONSE
# ============================================

class SnapchatResponse(BaseModel):
    """
    Generic Snapchat API response.
    """
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error info")
    paging: Optional[Dict[str, str]] = Field(None, description="Pagination info")
    
    def has_data(self) -> bool:
        """Check if response has data."""
        return self.data is not None
    
    def has_error(self) -> bool:
        """Check if response has error."""
        return self.error is not None


# ============================================
# SNAPCHAT ERROR
# ============================================

class SnapchatError(BaseModel):
    """Snapchat API error."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    debug_id: Optional[str] = Field(None, description="Debug ID")
