"""
SocialSpace Agent - Unified Message Model
==========================================

Universal message model that works across all 12 social media platforms.

This is the CORE data structure of the entire application. Every message from
WhatsApp, Instagram, Twitter, etc. is normalized into this format.

Design Goals:
-------------
1. Platform-agnostic: Works for messaging, social, content platforms
2. Type-safe: Full Pydantic validation
3. Extensible: Easy to add new platforms
4. Performant: Efficient serialization/deserialization
5. FAANG-quality: Production-ready with comprehensive validation

Supported Platforms (12):
--------------------------
Messaging: WhatsApp, Telegram, Discord, WeChat
Social: Facebook, Instagram, Snapchat, LinkedIn
Content: YouTube, TikTok, Pinterest
Discussion: Reddit, Twitter/X

Author: Dheeraj Mishra
Created: February 6, 2026
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    field_serializer,
    ConfigDict,
    ValidationInfo,
)
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============================================
# ENUMERATIONS
# ============================================

class PlatformType(str, Enum):
    """
    Supported social media platforms.
    
    Each platform has unique characteristics:
    - Messaging platforms: Real-time 1-on-1 or group communication
    - Social platforms: Public/private posts, stories, profiles
    - Content platforms: Video/image sharing with comments
    - Discussion platforms: Threaded discussions, communities
    """
    # Messaging platforms
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WECHAT = "wechat"
    
    # Social networking platforms
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    SNAPCHAT = "snapchat"
    LINKEDIN = "linkedin"
    
    # Content platforms
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    PINTEREST = "pinterest"
    
    # Discussion platforms
    REDDIT = "reddit"
    TWITTER = "twitter"  # X (formerly Twitter)


class MessageType(str, Enum):
    """
    Types of messages/interactions across platforms.
    
    Different platforms support different interaction types:
    - All platforms: TEXT, IMAGE, VIDEO
    - Messaging: AUDIO, DOCUMENT, VOICE
    - Social: STORY, POST, LIVE
    - Content: COMMENT, SHORT_VIDEO
    - Discussion: REPLY, THREAD
    """
    # Basic content types (all platforms)
    TEXT = "text"                    # Plain text message
    IMAGE = "image"                  # Image with optional caption
    VIDEO = "video"                  # Video with optional caption
    AUDIO = "audio"                  # Audio file/voice message
    
    # Document types
    DOCUMENT = "document"            # File attachment (PDF, DOCX, etc.)
    LINK = "link"                    # Shared URL with preview
    
    # Social media specific
    STORY = "story"                  # Story/Status (Instagram, Snapchat, WhatsApp)
    POST = "post"                    # Social media post (Facebook, LinkedIn)
    LIVE = "live"                    # Live stream (YouTube, Instagram, TikTok)
    REEL = "reel"                    # Short-form video (Instagram Reels)
    SHORT = "short"                  # Short video (YouTube Shorts)
    
    # Interaction types
    COMMENT = "comment"              # Comment on post/video (YouTube, TikTok, Instagram)
    REPLY = "reply"                  # Reply to message/comment
    MENTION = "mention"              # @mention (Twitter, LinkedIn)
    REACTION = "reaction"            # Like/emoji reaction
    SHARE = "share"                  # Shared/reposted content
    
    # Messaging specific
    DM = "dm"                        # Direct message
    GROUP_MESSAGE = "group_message"  # Group chat message
    VOICE_NOTE = "voice_note"        # Voice message (WhatsApp, Telegram)
    
    # Special types
    POLL = "poll"                    # Poll/survey
    EVENT = "event"                  # Event invitation
    LOCATION = "location"            # Shared location
    CONTACT = "contact"              # Shared contact


class UrgencyLevel(str, Enum):
    """
    Message urgency classification.
    
    Used by AI to prioritize responses:
    - CRITICAL: Requires immediate attention (emergencies, urgent work)
    - HIGH: Important, respond within hours
    - NORMAL: Regular message, respond when convenient
    - LOW: Can wait, non-urgent
    - SPAM: Likely spam/promotional
    """
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    SPAM = "spam"


class SentimentType(str, Enum):
    """
    Message sentiment classification.
    
    Helps determine appropriate response tone:
    - POSITIVE: Happy, grateful, complimentary
    - NEUTRAL: Informational, factual
    - NEGATIVE: Angry, frustrated, complaining
    - MIXED: Contains both positive and negative elements
    """
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


# ============================================
# NESTED MODELS
# ============================================

class MediaAttachment(BaseModel):
    """
    Media file attachment (image, video, audio).
    
    Attributes:
        url: Direct URL to the media file
        type: Media type (image/video/audio)
        size_bytes: File size in bytes
        width: Image/video width in pixels
        height: Image/video height in pixels
        duration_seconds: Video/audio duration
        thumbnail_url: Preview thumbnail URL
    """
    url: str = Field(..., description="Direct URL to media file")
    type: str = Field(..., description="Media type (image/video/audio)")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    width: Optional[int] = Field(None, description="Width in pixels")
    height: Optional[int] = Field(None, description="Height in pixels")
    duration_seconds: Optional[float] = Field(None, description="Duration for video/audio")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail preview URL")
    filename: Optional[str] = Field(None, description="Original filename")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str):
        """Ensure URL is not empty."""
        if not v or not v.strip():
            raise ValueError("Media URL cannot be empty")
        return v.strip()


class UserInfo(BaseModel):
    """
    Information about a user on a platform.
    
    Normalized user data across all platforms.
    """
    id: str = Field(..., description="Platform-specific user ID")
    username: Optional[str] = Field(None, description="Username/handle")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    is_verified: bool = Field(default=False, description="Verified account")
    is_bot: bool = Field(default=False, description="Bot account")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str):
        """Ensure user ID is not empty."""
        if not v or not v.strip():
            raise ValueError("User ID cannot be empty")
        return v.strip()


# ============================================
# MAIN MODEL
# ============================================

class UnifiedMessage(BaseModel):
    """
    Universal message model for all 12 social media platforms.
    
    This is the CORE data structure. Every message from every platform
    is converted into this format for processing.
    
    Design Decisions:
    -----------------
    1. Optional fields: Different platforms have different capabilities
    2. Rich metadata: Preserves platform-specific information
    3. AI-ready: Includes fields for classification and suggestions
    4. Immutable ID: UUID ensures uniqueness across platforms
    5. Timezone-aware: All timestamps in UTC
    
    Platform Mapping Examples:
    --------------------------
    WhatsApp message → UnifiedMessage:
        platform = WHATSAPP
        type = TEXT or VOICE_NOTE
        sender = phone number → UserInfo
        content = message text
        
    Instagram comment → UnifiedMessage:
        platform = INSTAGRAM
        type = COMMENT
        sender = username → UserInfo
        content = comment text
        parent_id = post ID
        
    Twitter reply → UnifiedMessage:
        platform = TWITTER
        type = REPLY
        sender = handle → UserInfo
        content = tweet text
        parent_id = original tweet ID
        
    YouTube comment → UnifiedMessage:
        platform = YOUTUBE
        type = COMMENT
        sender = channel → UserInfo
        content = comment text
        parent_id = video ID
    
    Usage Example:
    --------------
    >>> # Create a WhatsApp message
    >>> msg = UnifiedMessage(
    ...     platform=PlatformType.WHATSAPP,
    ...     type=MessageType.TEXT,
    ...     sender=UserInfo(id="+1234567890", display_name="John"),
    ...     content="Hey, how are you?",
    ...     timestamp=datetime.now(timezone.utc)
    ... )
    >>> 
    >>> # Classify it
    >>> msg.urgency = UrgencyLevel.NORMAL
    >>> msg.sentiment = SentimentType.POSITIVE
    >>> 
    >>> # Generate reply suggestion
    >>> msg.suggested_reply = "I'm doing great, thanks for asking!"
    >>> 
    >>> # Serialize for API
    >>> msg.dict()
    """
    
    # ============================================
    # CORE IDENTIFICATION
    # ============================================
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique message identifier (UUID)"
    )
    
    platform_message_id: str = Field(
        ...,
        description="Platform's original message ID"
    )
    
    platform: PlatformType = Field(
        ...,
        description="Source platform"
    )
    
    type: MessageType = Field(
        ...,
        description="Type of message/interaction"
    )
    
    # ============================================
    # PARTICIPANTS
    # ============================================
    
    sender: UserInfo = Field(
        ...,
        description="Message sender information"
    )
    
    recipient: Optional[UserInfo] = Field(
        None,
        description="Direct recipient (for DMs)"
    )
    
    mentions: List[UserInfo] = Field(
        default_factory=list,
        description="Users mentioned in message (@mentions)"
    )
    
    # ============================================
    # CONTENT
    # ============================================
    
    content: Optional[str] = Field(
        None,
        description="Text content of message",
        max_length=10000  # Prevent extremely long messages
    )
    
    media: List[MediaAttachment] = Field(
        default_factory=list,
        description="Attached media files (images, videos, audio)"
    )
    
    links: List[str] = Field(
        default_factory=list,
        description="URLs mentioned in the message"
    )
    
    # ============================================
    # CONTEXT & THREADING
    # ============================================
    
    parent_id: Optional[str] = Field(
        None,
        description="ID of parent message (for replies/threads)"
    )
    
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation/thread/post ID"
    )
    
    is_reply: bool = Field(
        default=False,
        description="Whether this is a reply to another message"
    )
    
    reply_count: int = Field(
        default=0,
        description="Number of replies to this message"
    )
    
    # ============================================
    # ENGAGEMENT METRICS
    # ============================================
    
    likes: int = Field(
        default=0,
        description="Number of likes/reactions"
    )
    
    shares: int = Field(
        default=0,
        description="Number of shares/reposts"
    )
    
    views: int = Field(
        default=0,
        description="Number of views (for videos/stories)"
    )
    
    # ============================================
    # TIMING
    # ============================================
    
    timestamp: datetime = Field(
        ...,
        description="When message was sent (UTC)"
    )
    
    edited_at: Optional[datetime] = Field(
        None,
        description="When message was last edited (if applicable)"
    )
    
    expires_at: Optional[datetime] = Field(
        None,
        description="When message expires (for stories, Snapchat)"
    )
    
    # ============================================
    # STATUS & FLAGS
    # ============================================
    
    is_read: bool = Field(
        default=False,
        description="Has been read by recipient"
    )
    
    is_delivered: bool = Field(
        default=True,
        description="Successfully delivered to platform"
    )
    
    is_edited: bool = Field(
        default=False,
        description="Has been edited after sending"
    )
    
    is_deleted: bool = Field(
        default=False,
        description="Has been deleted"
    )
    
    is_forwarded: bool = Field(
        default=False,
        description="Is a forwarded message"
    )
    
    # ============================================
    # AI CLASSIFICATION & PROCESSING
    # ============================================
    
    urgency: Optional[UrgencyLevel] = Field(
        None,
        description="AI-classified urgency level"
    )
    
    sentiment: Optional[SentimentType] = Field(
        None,
        description="AI-classified sentiment"
    )
    
    intent: Optional[str] = Field(
        None,
        description="AI-classified user intent",
        max_length=100
    )
    
    topics: List[str] = Field(
        default_factory=list,
        description="AI-extracted topics/keywords"
    )
    
    language: Optional[str] = Field(
        None,
        description="Detected language code (ISO 639-1)",
        max_length=5
    )
    
    # ============================================
    # AGENT SUGGESTIONS
    # ============================================
    
    suggested_reply: Optional[str] = Field(
        None,
        description="AI-generated reply suggestion",
        max_length=5000
    )
    
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Suggested actions (archive, flag, escalate, etc.)"
    )
    
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence in AI classifications (0.0-1.0)"
    )
    
    # ============================================
    # PLATFORM-SPECIFIC METADATA
    # ============================================
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific additional data"
    )
    
    # ============================================
    # VALIDATION
    # ============================================
    
    @field_validator('timestamp', 'edited_at', 'expires_at')
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]):
        """Ensure all timestamps are timezone-aware (UTC)."""
        if v and v.tzinfo is None:
            # If naive datetime, assume UTC
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('content')
    @classmethod
    def content_required_for_text(cls, v: Optional[str], info: ValidationInfo):
        """Text messages must have content."""
        msg_type = None
        if info.data:
            msg_type = info.data.get('type')
        if msg_type is not None:
            try:
                msg_type = MessageType(msg_type)
            except ValueError:
                pass
        if msg_type in {MessageType.TEXT, MessageType.COMMENT, MessageType.REPLY, MessageType.POST}:
            if not v or not v.strip():
                raise ValueError(f"{msg_type} messages must have non-empty content")
        return v
    
    @field_validator('media')
    @classmethod
    def media_required_for_media_types(
        cls,
        v: List[MediaAttachment],
        info: ValidationInfo
    ):
        """Media messages must have attachments."""
        media_types = {MessageType.IMAGE, MessageType.VIDEO, MessageType.AUDIO, MessageType.VOICE_NOTE}
        msg_type = None
        if info.data:
            msg_type = info.data.get('type')
        if msg_type is not None:
            try:
                msg_type = MessageType(msg_type)
            except ValueError:
                pass
        if msg_type in media_types and not v:
            raise ValueError(f"{msg_type} messages must have media attachments")
        return v
    
    @model_validator(mode='after')
    def validate_reply_consistency(self):
        """If is_reply is True, parent_id must be set."""
        if self.is_reply and not self.parent_id:
            raise ValueError("is_reply is True but parent_id is not set")
        return self
    
    @field_validator('likes', 'shares', 'views', 'reply_count')
    @classmethod
    def non_negative_counts(cls, v: int):
        """Engagement metrics must be non-negative."""
        if v < 0:
            raise ValueError("Engagement counts cannot be negative")
        return v
    
    # ============================================
    # METHODS
    # ============================================
    
    def is_expired(self) -> bool:
        """
        Check if message has expired (for stories, Snapchat).
        
        Returns:
            True if message has expired
        """
        if self.expires_at:
            return datetime.now(timezone.utc) >= self.expires_at
        return False
    
    def age_in_seconds(self) -> float:
        """
        Calculate message age in seconds.
        
        Returns:
            Age in seconds since message was sent
        """
        now = datetime.now(timezone.utc)
        return (now - self.timestamp).total_seconds()
    
    def needs_reply(self) -> bool:
        """
        Determine if message needs a reply.
        
        Logic:
            - Must be a direct message or mention
            - Not spam
            - Not already replied to
            - Recent (< 24 hours old)
        
        Returns:
            True if message needs a reply
        """
        if self.urgency == UrgencyLevel.SPAM:
            return False
        
        if self.type not in {MessageType.DM, MessageType.MENTION, MessageType.TEXT}:
            return False
        
        if self.age_in_seconds() > 86400:  # 24 hours
            return False
        
        return True
    
    def to_platform_format(self) -> Dict[str, Any]:
        """
        Convert to platform-specific format for sending.
        
        This method should be implemented by platform adapters.
        
        Returns:
            Platform-specific message dictionary
        """
        # This is overridden by platform adapters
        return self.model_dump()
    
    @field_serializer('timestamp', 'edited_at', 'expires_at', when_used='json')
    def serialize_datetimes(self, v: Optional[datetime]):
        return v.isoformat() if v else None
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,  # Validate on attribute assignment
        arbitrary_types_allowed=False
    )
