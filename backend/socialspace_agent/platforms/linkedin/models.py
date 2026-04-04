"""
LinkedIn Platform - Data Models
================================

LinkedIn-specific data models.

LinkedIn Concepts:
------------------
- Profile: Professional profile
- Organization: Company page
- Post/Share: Content updates
- Comment: Discussion on posts
- Article: Long-form content

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 11
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# LINKEDIN PROFILE
# ============================================

class LinkedInProfile(BaseModel):
    """
    LinkedIn profile model.
    
    Represents a LinkedIn user profile.
    """
    id: str = Field(..., description="Profile ID (URN)")
    
    # Basic info
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    maiden_name: Optional[str] = Field(None, description="Maiden name")
    
    # Profile info
    headline: Optional[str] = Field(None, description="Professional headline")
    location: Optional[Dict[str, str]] = Field(None, description="Location")
    industry: Optional[str] = Field(None, description="Industry")
    
    # Profile picture
    profile_picture: Optional[Dict[str, Any]] = Field(None, description="Profile picture")
    
    def get_full_name(self) -> str:
        """Get full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p)
    
    def get_display_name(self) -> str:
        """Get display name with headline."""
        name = self.get_full_name()
        if self.headline:
            return f"{name} - {self.headline}"
        return name


# ============================================
# LINKEDIN ORGANIZATION
# ============================================

class LinkedInOrganization(BaseModel):
    """
    LinkedIn organization (company page) model.
    """
    id: str = Field(..., description="Organization ID (URN)")
    
    # Basic info
    localized_name: str = Field(..., description="Organization name")
    localized_website: Optional[str] = Field(None, description="Website URL")
    
    # Description
    localized_description: Optional[str] = Field(None, description="Description")
    
    # Vanity name (custom URL)
    vanity_name: Optional[str] = Field(None, description="Vanity name")
    
    # Logo
    logo: Optional[Dict[str, Any]] = Field(None, description="Logo")
    
    def get_url(self) -> str:
        """Get LinkedIn company page URL."""
        if self.vanity_name:
            return f"https://linkedin.com/company/{self.vanity_name}"
        return f"https://linkedin.com/company/{self.id}"


# ============================================
# LINKEDIN POST (SHARE)
# ============================================

class LinkedInPost(BaseModel):
    """
    LinkedIn post/share model.
    
    Represents a post or update on LinkedIn.
    """
    id: str = Field(..., description="Post ID (URN)")
    
    # Author
    author: str = Field(..., description="Author URN")
    
    # Content
    text: Optional[str] = Field(None, description="Post text")
    commentary: Optional[str] = Field(None, description="Commentary text")
    
    # Timestamps
    created_at: Optional[int] = Field(None, description="Creation timestamp (epoch ms)")
    last_modified_at: Optional[int] = Field(None, description="Last modified (epoch ms)")
    
    # Distribution
    distribution: Optional[Dict[str, Any]] = Field(None, description="Distribution settings")
    
    # Lifecycle state
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state (PUBLISHED, etc.)")
    
    # Content
    content: Optional[Dict[str, Any]] = Field(None, description="Rich content")
    
    def get_text(self) -> str:
        """Get post text."""
        return self.commentary or self.text or ""
    
    def is_published(self) -> bool:
        """Check if post is published."""
        return self.lifecycle_state == "PUBLISHED"


# ============================================
# LINKEDIN COMMENT
# ============================================

class LinkedInComment(BaseModel):
    """
    LinkedIn comment model.
    
    Represents a comment on a post.
    """
    id: str = Field(..., description="Comment ID (URN)")
    
    # Parent
    object: str = Field(..., description="Parent object URN (post/comment)")
    
    # Author
    actor: str = Field(..., description="Actor URN (commenter)")
    
    # Content
    message: Dict[str, str] = Field(..., description="Comment message")
    
    # Timestamps
    created_at: Optional[int] = Field(None, description="Creation timestamp (epoch ms)")
    last_modified_at: Optional[int] = Field(None, description="Last modified (epoch ms)")
    
    def get_text(self) -> str:
        """Get comment text."""
        return self.message.get("text", "")


# ============================================
# LINKEDIN ARTICLE
# ============================================

class LinkedInArticle(BaseModel):
    """
    LinkedIn article model.
    
    Represents a long-form article.
    """
    id: str = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    
    # Author
    author: Optional[Dict[str, str]] = Field(None, description="Author info")
    
    # Content
    content: Optional[str] = Field(None, description="Article content (HTML)")
    description: Optional[str] = Field(None, description="Short description")
    
    # Timestamps
    published_at: Optional[str] = Field(None, description="Publication timestamp")
    
    # Cover image
    cover_image: Optional[Dict[str, str]] = Field(None, description="Cover image")


# ============================================
# LINKEDIN API RESPONSE
# ============================================

class LinkedInPaging(BaseModel):
    """Pagination info."""
    start: Optional[int] = Field(None, description="Start index")
    count: Optional[int] = Field(None, description="Count")
    total: Optional[int] = Field(None, description="Total results")
    links: Optional[List[Dict[str, str]]] = Field(None, description="Pagination links")


class LinkedInResponse(BaseModel):
    """
    Generic LinkedIn API response.
    """
    elements: Optional[List[Dict[str, Any]]] = Field(None, description="Response elements")
    paging: Optional[LinkedInPaging] = Field(None, description="Pagination info")
    
    def has_elements(self) -> bool:
        """Check if response has elements."""
        return bool(self.elements)
    
    def get_count(self) -> int:
        """Get element count."""
        return len(self.elements) if self.elements else 0


# ============================================
# LINKEDIN ERROR
# ============================================

class LinkedInError(BaseModel):
    """LinkedIn API error."""
    status: int = Field(..., description="HTTP status code")
    code: Optional[str] = Field(None, description="Error code")
