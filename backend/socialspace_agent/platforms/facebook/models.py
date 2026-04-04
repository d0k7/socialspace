"""
Facebook Platform - Data Models
================================

Facebook-specific data models.

Facebook Concepts:
------------------
- Page: Business/brand page
- Post: Content on timeline
- Comment: Discussion on posts
- User: Facebook user/profile
- Group: Community

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 10
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# FACEBOOK USER
# ============================================

class FacebookUser(BaseModel):
    """
    Facebook user model.
    
    Represents a Facebook user or page.
    """
    id: str = Field(..., description="User/Page ID")
    name: str = Field(..., description="Display name")
    
    # Profile info (optional)
    email: Optional[str] = Field(None, description="Email address")
    picture: Optional[Dict[str, Any]] = Field(None, description="Profile picture")
    
    def get_picture_url(self) -> Optional[str]:
        """Get profile picture URL."""
        if self.picture and "data" in self.picture:
            return self.picture["data"].get("url")
        return None


# ============================================
# FACEBOOK PAGE
# ============================================

class FacebookPage(BaseModel):
    """
    Facebook page model.
    
    Represents a Facebook business/brand page.
    """
    id: str = Field(..., description="Page ID")
    name: str = Field(..., description="Page name")
    category: Optional[str] = Field(None, description="Page category")
    
    # Page info
    about: Optional[str] = Field(None, description="About section")
    description: Optional[str] = Field(None, description="Description")
    phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Engagement
    fan_count: Optional[int] = Field(None, description="Number of fans/likes")
    
    # Access
    access_token: Optional[str] = Field(None, description="Page access token")
    
    def get_url(self) -> str:
        """Get page URL."""
        return f"https://facebook.com/{self.id}"


# ============================================
# FACEBOOK POST
# ============================================

class FacebookPost(BaseModel):
    """
    Facebook post model.
    
    Represents a post on Facebook.
    """
    id: str = Field(..., description="Post ID")
    
    # Content
    message: Optional[str] = Field(None, description="Post text")
    story: Optional[str] = Field(None, description="Story text (e.g., 'John shared a photo')")
    
    # Author
    from_: Optional[Dict[str, str]] = Field(None, alias="from", description="Post author")
    
    # Timestamps
    created_time: str = Field(..., description="Creation timestamp")
    updated_time: Optional[str] = Field(None, description="Last update timestamp")
    
    # Media
    full_picture: Optional[str] = Field(None, description="Full-size image URL")
    picture: Optional[str] = Field(None, description="Thumbnail image URL")
    
    # Type
    type: Optional[str] = Field(None, description="Post type (link, status, photo, video)")
    status_type: Optional[str] = Field(None, description="Status type")
    
    # Engagement
    likes: Optional[Dict[str, Any]] = Field(None, description="Likes summary")
    comments: Optional[Dict[str, Any]] = Field(None, description="Comments summary")
    shares: Optional[Dict[str, int]] = Field(None, description="Shares count")
    
    # Permalink
    permalink_url: Optional[str] = Field(None, description="Permanent link to post")
    
    def get_like_count(self) -> int:
        """Get like count."""
        if self.likes and "summary" in self.likes:
            return self.likes["summary"].get("total_count", 0)
        return 0
    
    def get_comment_count(self) -> int:
        """Get comment count."""
        if self.comments and "summary" in self.comments:
            return self.comments["summary"].get("total_count", 0)
        return 0
    
    def get_share_count(self) -> int:
        """Get share count."""
        if self.shares:
            return self.shares.get("count", 0)
        return 0
    
    def get_author_name(self) -> Optional[str]:
        """Get author name."""
        if self.from_:
            return self.from_.get("name")
        return None


# ============================================
# FACEBOOK COMMENT
# ============================================

class FacebookComment(BaseModel):
    """
    Facebook comment model.
    
    Represents a comment on a post.
    """
    id: str = Field(..., description="Comment ID")
    
    # Content
    message: str = Field(..., description="Comment text")
    
    # Author
    from_: Dict[str, str] = Field(..., alias="from", description="Comment author")
    
    # Timestamps
    created_time: str = Field(..., description="Creation timestamp")
    
    # Engagement
    like_count: Optional[int] = Field(0, description="Number of likes")
    comment_count: Optional[int] = Field(0, description="Number of replies")
    
    # Parent
    parent: Optional[Dict[str, str]] = Field(None, description="Parent comment (if reply)")
    
    # Attachment
    attachment: Optional[Dict[str, Any]] = Field(None, description="Media attachment")
    
    def get_author_name(self) -> str:
        """Get author name."""
        return self.from_.get("name", "Unknown")
    
    def get_author_id(self) -> str:
        """Get author ID."""
        return self.from_.get("id", "")
    
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment."""
        return self.parent is not None


# ============================================
# FACEBOOK ALBUM
# ============================================

class FacebookAlbum(BaseModel):
    """
    Facebook album model.
    """
    id: str = Field(..., description="Album ID")
    name: str = Field(..., description="Album name")
    description: Optional[str] = Field(None, description="Album description")
    
    # Counts
    count: Optional[int] = Field(None, description="Number of photos")
    
    # Cover
    cover_photo: Optional[Dict[str, str]] = Field(None, description="Cover photo")
    
    # Timestamps
    created_time: Optional[str] = Field(None, description="Creation timestamp")
    updated_time: Optional[str] = Field(None, description="Last update timestamp")


# ============================================
# FACEBOOK PHOTO
# ============================================

class FacebookPhoto(BaseModel):
    """
    Facebook photo model.
    """
    id: str = Field(..., description="Photo ID")
    
    # Images
    images: Optional[List[Dict[str, Any]]] = Field(None, description="Image sizes")
    picture: Optional[str] = Field(None, description="Thumbnail URL")
    
    # Content
    name: Optional[str] = Field(None, description="Photo caption")
    
    # Timestamps
    created_time: Optional[str] = Field(None, description="Creation timestamp")
    
    def get_largest_image_url(self) -> Optional[str]:
        """Get URL of largest image."""
        if self.images and len(self.images) > 0:
            # Images are sorted by size, first is largest
            return self.images[0].get("source")
        return None


# ============================================
# FACEBOOK API RESPONSE
# ============================================

class FacebookPagination(BaseModel):
    """Pagination cursors."""
    cursors: Optional[Dict[str, str]] = Field(None, description="Before/after cursors")
    next: Optional[str] = Field(None, description="Next page URL")
    previous: Optional[str] = Field(None, description="Previous page URL")


class FacebookResponse(BaseModel):
    """
    Generic Facebook API response.
    """
    data: Optional[Any] = Field(None, description="Response data")
    paging: Optional[FacebookPagination] = Field(None, description="Pagination info")
    
    def has_data(self) -> bool:
        """Check if response has data."""
        return self.data is not None
    
    def has_next_page(self) -> bool:
        """Check if there's a next page."""
        if self.paging:
            return self.paging.next is not None
        return False
    
    def get_after_cursor(self) -> Optional[str]:
        """Get 'after' cursor for pagination."""
        if self.paging and self.paging.cursors:
            return self.paging.cursors.get("after")
        return None


# ============================================
# FACEBOOK ERROR
# ============================================

class FacebookError(BaseModel):
    """Facebook API error."""
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    code: int = Field(..., description="Error code")
    error_subcode: Optional[int] = Field(None, description="Error subcode")
    fbtrace_id: Optional[str] = Field(None, description="Trace ID for debugging")
