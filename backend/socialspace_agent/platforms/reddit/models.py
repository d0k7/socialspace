"""
Reddit Platform - Data Models
==============================

Reddit-specific data models.

Reddit Concepts:
----------------
- Subreddit: Community (r/Python, r/technology)
- Submission: Post/thread in a subreddit
- Comment: Reply to submission or another comment
- Redditor: Reddit user
- Thing: Base Reddit object (t1_=comment, t3_=submission)

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 7
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# REDDIT USER (REDDITOR)
# ============================================

class RedditUser(BaseModel):
    """
    Reddit user (Redditor) model.
    """
    id: str = Field(..., description="Reddit user ID")
    name: str = Field(..., description="Username (without u/ prefix)")
    created: Optional[float] = Field(None, description="Account creation timestamp")
    link_karma: Optional[int] = Field(None, description="Post karma")
    comment_karma: Optional[int] = Field(None, description="Comment karma")
    is_gold: Optional[bool] = Field(False, description="Has Reddit Premium")
    is_mod: Optional[bool] = Field(False, description="Is moderator")
    icon_img: Optional[str] = Field(None, description="Profile icon URL")
    
    def get_username(self) -> str:
        """Get username with u/ prefix."""
        return f"u/{self.name}"
    
    def total_karma(self) -> int:
        """Get total karma."""
        return (self.link_karma or 0) + (self.comment_karma or 0)


# ============================================
# REDDIT SUBREDDIT
# ============================================

class RedditSubreddit(BaseModel):
    """
    Reddit subreddit model.
    """
    id: str = Field(..., description="Subreddit ID")
    name: str = Field(..., description="Subreddit name (without r/ prefix)")
    display_name: str = Field(..., description="Display name")
    title: Optional[str] = Field(None, description="Subreddit title")
    public_description: Optional[str] = Field(None, description="Public description")
    subscribers: Optional[int] = Field(None, description="Number of subscribers")
    created: Optional[float] = Field(None, description="Creation timestamp")
    over18: Optional[bool] = Field(False, description="NSFW subreddit")
    
    def get_subreddit_name(self) -> str:
        """Get subreddit name with r/ prefix."""
        return f"r/{self.name}"


# ============================================
# REDDIT SUBMISSION (POST)
# ============================================

class RedditSubmission(BaseModel):
    """
    Reddit submission (post) model.
    
    Represents a post in a subreddit.
    """
    id: str = Field(..., description="Submission ID (without t3_ prefix)")
    name: str = Field(..., description="Full ID with prefix (t3_xxxxx)")
    
    # Subreddit info
    subreddit: str = Field(..., description="Subreddit name")
    subreddit_id: str = Field(..., description="Subreddit ID")
    
    # Author
    author: str = Field(..., description="Author username")
    
    # Content
    title: str = Field(..., description="Submission title")
    selftext: Optional[str] = Field(None, description="Text content (for text posts)")
    url: Optional[str] = Field(None, description="URL (for link posts)")
    
    # Type
    is_self: bool = Field(..., description="Is text post (vs link post)")
    is_video: Optional[bool] = Field(False, description="Is video post")
    
    # Timestamps
    created_utc: float = Field(..., description="Creation timestamp (UTC)")
    edited: Optional[float] = Field(None, description="Edit timestamp")
    
    # Engagement
    score: int = Field(default=0, description="Upvotes - downvotes")
    upvote_ratio: Optional[float] = Field(None, description="Ratio of upvotes (0-1)")
    num_comments: int = Field(default=0, description="Number of comments")
    
    # Media
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    preview: Optional[Dict[str, Any]] = Field(None, description="Preview images")
    
    # Status
    locked: Optional[bool] = Field(False, description="Is locked")
    stickied: Optional[bool] = Field(False, description="Is stickied/pinned")
    over_18: Optional[bool] = Field(False, description="NSFW content")
    spoiler: Optional[bool] = Field(False, description="Marked as spoiler")
    
    # Permalink
    permalink: str = Field(..., description="Permalink to submission")
    
    def get_full_url(self) -> str:
        """Get full Reddit URL."""
        return f"https://reddit.com{self.permalink}"
    
    def is_edited(self) -> bool:
        """Check if submission was edited."""
        return self.edited is not None and self.edited is not False


# ============================================
# REDDIT COMMENT
# ============================================

class RedditComment(BaseModel):
    """
    Reddit comment model.
    
    Represents a comment on a submission or another comment.
    """
    id: str = Field(..., description="Comment ID (without t1_ prefix)")
    name: str = Field(..., description="Full ID with prefix (t1_xxxxx)")
    
    # Parent info
    parent_id: str = Field(..., description="Parent ID (t3_ for submission, t1_ for comment)")
    link_id: str = Field(..., description="Submission ID this comment is in")
    
    # Subreddit
    subreddit: str = Field(..., description="Subreddit name")
    subreddit_id: str = Field(..., description="Subreddit ID")
    
    # Author
    author: str = Field(..., description="Author username")
    
    # Content
    body: str = Field(..., description="Comment text (markdown)")
    body_html: Optional[str] = Field(None, description="Comment text (HTML)")
    
    # Timestamps
    created_utc: float = Field(..., description="Creation timestamp (UTC)")
    edited: Optional[float] = Field(None, description="Edit timestamp")
    
    # Engagement
    score: int = Field(default=0, description="Upvotes - downvotes")
    controversiality: Optional[int] = Field(0, description="Controversy score")
    
    # Status
    stickied: Optional[bool] = Field(False, description="Is stickied")
    locked: Optional[bool] = Field(False, description="Is locked")
    
    # Replies
    replies: Optional[Any] = Field(None, description="Nested replies (if fetched)")
    
    # Permalink
    permalink: Optional[str] = Field(None, description="Permalink to comment")
    
    def is_top_level(self) -> bool:
        """Check if this is a top-level comment (direct reply to submission)."""
        return self.parent_id.startswith("t3_")
    
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment."""
        return self.parent_id.startswith("t1_")
    
    def is_edited(self) -> bool:
        """Check if comment was edited."""
        return self.edited is not None and self.edited is not False


# ============================================
# REDDIT API RESPONSE
# ============================================

class RedditListing(BaseModel):
    """
    Reddit listing response.
    
    Reddit returns paginated data as "listings".
    """
    kind: str = Field(..., description="Listing type (Listing)")
    data: Dict[str, Any] = Field(..., description="Listing data")
    
    def get_children(self) -> List[Dict[str, Any]]:
        """Get list of items in listing."""
        return self.data.get("children", [])
    
    def get_after(self) -> Optional[str]:
        """Get pagination cursor for next page."""
        return self.data.get("after")
    
    def get_before(self) -> Optional[str]:
        """Get pagination cursor for previous page."""
        return self.data.get("before")
    
    def has_more(self) -> bool:
        """Check if there are more items."""
        return self.get_after() is not None


class RedditThing(BaseModel):
    """
    Reddit "Thing" - base object type.
    
    All Reddit objects are "things" with a kind and data.
    - t1_ = Comment
    - t2_ = Redditor
    - t3_ = Submission
    - t4_ = Message
    - t5_ = Subreddit
    """
    kind: str = Field(..., description="Thing type (t1_, t3_, etc.)")
    data: Dict[str, Any] = Field(..., description="Thing data")
    
    def is_comment(self) -> bool:
        """Check if this is a comment (t1_)."""
        return self.kind == "t1"
    
    def is_submission(self) -> bool:
        """Check if this is a submission (t3_)."""
        return self.kind == "t3"
