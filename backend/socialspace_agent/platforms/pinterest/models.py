"""
Pinterest Platform - Data Models
=================================

Pinterest-specific data models.

Pinterest Concepts:
-------------------
- User: Pinterest user/profile
- Pin: Visual bookmark
- Board: Collection of pins
- Section: Subsection of board
- IdeaPin: Multi-page story-like content

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 14 (FINAL SESSION!)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# PINTEREST USER
# ============================================

class PinterestUser(BaseModel):
    """
    Pinterest user model.
    
    Represents a Pinterest user/profile.
    """
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    
    # Profile
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    bio: Optional[str] = Field(None, description="Bio/description")
    
    # Profile image
    profile_image: Optional[str] = Field(None, description="Profile image URL")
    
    # Stats
    pin_count: Optional[int] = Field(0, description="Number of pins")
    board_count: Optional[int] = Field(0, description="Number of boards")
    follower_count: Optional[int] = Field(0, description="Number of followers")
    following_count: Optional[int] = Field(0, description="Number of following")
    
    def get_display_name(self) -> str:
        """Get display name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_profile_url(self) -> str:
        """Get profile URL."""
        return f"https://pinterest.com/{self.username}"


# ============================================
# PINTEREST BOARD
# ============================================

class PinterestBoard(BaseModel):
    """
    Pinterest board model.
    
    Represents a Pinterest board (collection).
    """
    id: str = Field(..., description="Board ID")
    name: str = Field(..., description="Board name")
    description: Optional[str] = Field(None, description="Board description")
    
    # Owner
    owner: Optional[Dict[str, str]] = Field(None, description="Board owner")
    
    # Privacy
    privacy: Optional[str] = Field("PUBLIC", description="Privacy setting")
    
    # Stats
    pin_count: Optional[int] = Field(0, description="Number of pins")
    follower_count: Optional[int] = Field(0, description="Number of followers")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    
    def get_url(self) -> str:
        """Get board URL."""
        if self.owner and "username" in self.owner:
            return f"https://pinterest.com/{self.owner['username']}/{self.name}"
        return f"https://pinterest.com/board/{self.id}"
    
    def is_public(self) -> bool:
        """Check if board is public."""
        return self.privacy == "PUBLIC"


# ============================================
# PINTEREST PIN
# ============================================

class PinterestMedia(BaseModel):
    """Pin media model."""
    media_type: str = Field(..., description="Media type (image, video)")
    
    # Images
    images: Optional[Dict[str, Any]] = Field(None, description="Image sizes")
    
    # Video
    video_url: Optional[str] = Field(None, description="Video URL")
    duration: Optional[int] = Field(None, description="Video duration in ms")


class PinterestPin(BaseModel):
    """
    Pinterest pin model.
    
    Represents a Pinterest pin (visual bookmark).
    """
    id: str = Field(..., description="Pin ID")
    
    # Content
    title: Optional[str] = Field(None, description="Pin title")
    description: Optional[str] = Field(None, description="Pin description")
    alt_text: Optional[str] = Field(None, description="Alt text")
    
    # Media
    media: Optional[PinterestMedia] = Field(None, description="Media content")
    
    # Link
    link: Optional[str] = Field(None, description="Destination link")
    
    # Board
    board_id: Optional[str] = Field(None, description="Board ID")
    board_section_id: Optional[str] = Field(None, description="Board section ID")
    
    # Creator
    creator: Optional[Dict[str, str]] = Field(None, description="Pin creator")
    
    # Stats
    save_count: Optional[int] = Field(0, description="Number of saves")
    comment_count: Optional[int] = Field(0, description="Number of comments")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    
    def get_url(self) -> str:
        """Get pin URL."""
        return f"https://pinterest.com/pin/{self.id}"
    
    def get_image_url(self) -> Optional[str]:
        """Get pin image URL."""
        if self.media and self.media.images:
            # Get original or largest image
            if "originals" in self.media.images:
                return self.media.images["originals"].get("url")
            elif "original" in self.media.images:
                return self.media.images["original"].get("url")
        return None
    
    def is_video(self) -> bool:
        """Check if pin is a video."""
        return self.media and self.media.media_type == "video"


# ============================================
# PINTEREST IDEA PIN
# ============================================

class PinterestIdeaPin(BaseModel):
    """
    Pinterest Idea Pin model.
    
    Represents a multi-page story-like pin.
    """
    id: str = Field(..., description="Idea Pin ID")
    
    # Content
    title: Optional[str] = Field(None, description="Title")
    description: Optional[str] = Field(None, description="Description")
    
    # Pages
    pages: Optional[List[Dict[str, Any]]] = Field(None, description="Pin pages")
    
    # Stats
    save_count: Optional[int] = Field(0, description="Number of saves")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Creation timestamp")


# ============================================
# PINTEREST API RESPONSE
# ============================================

class PinterestResponse(BaseModel):
    """
    Generic Pinterest API response.
    """
    items: Optional[List[Any]] = Field(None, description="Response items")
    bookmark: Optional[str] = Field(None, description="Pagination bookmark")
    
    def has_items(self) -> bool:
        """Check if response has items."""
        return bool(self.items)
    
    def has_more(self) -> bool:
        """Check if there are more results."""
        return self.bookmark is not None


# ============================================
# PINTEREST ERROR
# ============================================

class PinterestError(BaseModel):
    """Pinterest API error."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
