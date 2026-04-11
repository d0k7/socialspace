"""
SocialSpace Agent - Test Suite for Core Models
================================================

Comprehensive tests for UnifiedMessage and exception hierarchy.

Test Coverage:
--------------
1. UnifiedMessage creation and validation
2. All 12 platforms
3. All message types
4. Edge cases and error handling
5. Exception hierarchy

Run tests:
    pytest test_core_models.py -v
    pytest test_core_models.py --cov=socialspace_agent

Author: Dheeraj Mishra
Created: February 6, 2026
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from socialspace_agent.models.unified_message import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UrgencyLevel,
    SentimentType,
    UserInfo,
    MediaAttachment,
)
from socialspace_agent.exceptions import (
    SocialSpaceError,
    ValidationError,
    AuthenticationError,
    WhatsAppError,
    InstagramError,
    TwitterError,
    RateLimitError,
)


# ============================================
# TEST FIXTURES
# ============================================

@pytest.fixture
def sample_user() -> UserInfo:
    """Create a sample user for testing."""
    return UserInfo(
        id="user_123",
        username="testuser",
        display_name="Test User",
        avatar_url="https://example.com/avatar.jpg",
        is_verified=False,
        is_bot=False,
    )


@pytest.fixture
def sample_media() -> MediaAttachment:
    """Create a sample media attachment."""
    return MediaAttachment(
        url="https://example.com/image.jpg",
        type="image",
        size_bytes=1024000,
        width=1920,
        height=1080,
    )


@pytest.fixture
def base_message_data(sample_user) -> Dict[str, Any]:
    """Base message data for testing."""
    return {
        "platform_message_id": "msg_123",
        "platform": PlatformType.WHATSAPP,
        "type": MessageType.TEXT,
        "sender": sample_user,
        "content": "Hello, this is a test message!",
        "timestamp": datetime.now(timezone.utc),
    }


# ============================================
# TEST: UNIFIED MESSAGE CREATION
# ============================================

class TestUnifiedMessageCreation:
    """Test creating UnifiedMessage instances."""
    
    def test_create_simple_text_message(self, base_message_data):
        """Test creating a basic text message."""
        msg = UnifiedMessage(**base_message_data)
        
        assert msg.platform == PlatformType.WHATSAPP
        assert msg.type == MessageType.TEXT
        assert msg.content == "Hello, this is a test message!"
        assert msg.sender.id == "user_123"
        assert msg.timestamp.tzinfo == timezone.utc
    
    def test_auto_generated_id(self, base_message_data):
        """Test that ID is auto-generated if not provided."""
        msg1 = UnifiedMessage(**base_message_data)
        msg2 = UnifiedMessage(**base_message_data)
        
        assert msg1.id != msg2.id
        assert len(msg1.id) == 36  # UUID length
    
    def test_create_with_media(self, base_message_data, sample_media):
        """Test creating message with media attachment."""
        base_message_data['type'] = MessageType.IMAGE
        base_message_data['media'] = [sample_media]
        
        msg = UnifiedMessage(**base_message_data)
        
        assert len(msg.media) == 1
        assert msg.media[0].url == "https://example.com/image.jpg"
        assert msg.media[0].width == 1920
    
    def test_create_reply_message(self, base_message_data):
        """Test creating a reply message."""
        base_message_data['is_reply'] = True
        base_message_data['parent_id'] = "parent_msg_123"
        
        msg = UnifiedMessage(**base_message_data)
        
        assert msg.is_reply is True
        assert msg.parent_id == "parent_msg_123"


# ============================================
# TEST: PLATFORM SUPPORT
# ============================================

class TestPlatformSupport:
    """Test all 12 platforms are supported."""
    
    @pytest.mark.parametrize("platform", [
        PlatformType.WHATSAPP,
        PlatformType.TELEGRAM,
        PlatformType.DISCORD,
        PlatformType.WECHAT,
        PlatformType.FACEBOOK,
        PlatformType.INSTAGRAM,
        PlatformType.SNAPCHAT,
        PlatformType.LINKEDIN,
        PlatformType.YOUTUBE,
        PlatformType.TIKTOK,
        PlatformType.PINTEREST,
        PlatformType.REDDIT,
        PlatformType.TWITTER,
    ])
    def test_all_platforms_supported(self, platform, base_message_data):
        """Test message creation for all 12 platforms."""
        base_message_data['platform'] = platform
        
        msg = UnifiedMessage(**base_message_data)
        
        assert msg.platform == platform
        print(f"✅ {platform.value} platform supported")


# ============================================
# TEST: MESSAGE TYPES
# ============================================

class TestMessageTypes:
    """Test different message types."""
    
    def test_text_message(self, base_message_data):
        """Test TEXT message type."""
        msg = UnifiedMessage(**base_message_data)
        assert msg.type == MessageType.TEXT
        assert msg.content is not None
    
    def test_image_message(self, base_message_data, sample_media):
        """Test IMAGE message type."""
        base_message_data['type'] = MessageType.IMAGE
        base_message_data['media'] = [sample_media]
        
        msg = UnifiedMessage(**base_message_data)
        assert msg.type == MessageType.IMAGE
        assert len(msg.media) > 0
    
    def test_comment_message(self, base_message_data):
        """Test COMMENT message type (YouTube, Instagram)."""
        base_message_data['type'] = MessageType.COMMENT
        base_message_data['platform'] = PlatformType.YOUTUBE
        base_message_data['parent_id'] = "video_123"
        
        msg = UnifiedMessage(**base_message_data)
        assert msg.type == MessageType.COMMENT
        assert msg.parent_id == "video_123"
    
    def test_dm_message(self, base_message_data, sample_user):
        """Test DM (Direct Message) type."""
        base_message_data['type'] = MessageType.DM
        base_message_data['recipient'] = sample_user
        
        msg = UnifiedMessage(**base_message_data)
        assert msg.type == MessageType.DM
        assert msg.recipient is not None


# ============================================
# TEST: VALIDATION
# ============================================

class TestValidation:
    """Test Pydantic validation."""
    
    def test_text_message_requires_content(self, base_message_data):
        """Test that TEXT messages require content."""
        base_message_data['content'] = None
        
        with pytest.raises(ValueError, match="must have non-empty content"):
            UnifiedMessage(**base_message_data)
    
    def test_image_message_requires_media(self, base_message_data):
        """Test that IMAGE messages require media."""
        base_message_data['type'] = MessageType.IMAGE
        base_message_data['media'] = []
        
        with pytest.raises(ValueError, match="must have media attachments"):
            UnifiedMessage(**base_message_data)
    
    def test_reply_requires_parent_id(self, base_message_data):
        """Test that replies require parent_id."""
        base_message_data['is_reply'] = True
        base_message_data['parent_id'] = None
        
        with pytest.raises(ValueError, match="parent_id is not set"):
            UnifiedMessage(**base_message_data)
    
    def test_negative_engagement_counts(self, base_message_data):
        """Test that engagement counts cannot be negative."""
        base_message_data['likes'] = -5
        
        with pytest.raises(ValueError, match="cannot be negative"):
            UnifiedMessage(**base_message_data)
    
    def test_timezone_aware_timestamps(self, base_message_data):
        """Test that timestamps are converted to timezone-aware."""
        # Create naive datetime
        naive_dt = datetime(2026, 2, 6, 14, 45, 0)
        base_message_data['timestamp'] = naive_dt
        
        msg = UnifiedMessage(**base_message_data)
        
        assert msg.timestamp.tzinfo == timezone.utc


# ============================================
# TEST: AI CLASSIFICATION
# ============================================

class TestAIClassification:
    """Test AI classification fields."""
    
    def test_urgency_classification(self, base_message_data):
        """Test urgency level classification."""
        msg = UnifiedMessage(**base_message_data)
        
        msg.urgency = UrgencyLevel.HIGH
        assert msg.urgency == UrgencyLevel.HIGH
        
        msg.urgency = UrgencyLevel.SPAM
        assert msg.urgency == UrgencyLevel.SPAM
    
    def test_sentiment_classification(self, base_message_data):
        """Test sentiment classification."""
        msg = UnifiedMessage(**base_message_data)
        
        msg.sentiment = SentimentType.POSITIVE
        assert msg.sentiment == SentimentType.POSITIVE
    
    def test_suggested_reply(self, base_message_data):
        """Test AI-generated reply suggestion."""
        msg = UnifiedMessage(**base_message_data)
        
        msg.suggested_reply = "Thank you for your message!"
        assert msg.suggested_reply == "Thank you for your message!"
    
    def test_confidence_score(self, base_message_data):
        """Test confidence score validation."""
        msg = UnifiedMessage(**base_message_data)
        
        msg.confidence_score = 0.95
        assert msg.confidence_score == 0.95
        
        # Test invalid range
        with pytest.raises(ValueError):
            msg.confidence_score = 1.5  # > 1.0


# ============================================
# TEST: HELPER METHODS
# ============================================

class TestHelperMethods:
    """Test UnifiedMessage helper methods."""
    
    def test_age_in_seconds(self, base_message_data):
        """Test age_in_seconds() method."""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        base_message_data['timestamp'] = past_time
        
        msg = UnifiedMessage(**base_message_data)
        age = msg.age_in_seconds()
        
        assert 59 <= age <= 61  # Allow 1 second tolerance
    
    def test_is_expired(self, base_message_data):
        """Test is_expired() method for stories."""
        base_message_data['type'] = MessageType.STORY
        base_message_data['expires_at'] = datetime.now(timezone.utc) - timedelta(hours=1)
        
        msg = UnifiedMessage(**base_message_data)
        assert msg.is_expired() is True
    
    def test_not_expired(self, base_message_data):
        """Test message not expired."""
        base_message_data['expires_at'] = datetime.now(timezone.utc) + timedelta(hours=23)
        
        msg = UnifiedMessage(**base_message_data)
        assert msg.is_expired() is False
    
    def test_needs_reply_dm(self, base_message_data):
        """Test needs_reply() for DMs."""
        base_message_data['type'] = MessageType.DM
        base_message_data['urgency'] = UrgencyLevel.NORMAL
        
        msg = UnifiedMessage(**base_message_data)
        assert msg.needs_reply() is True
    
    def test_needs_reply_spam(self, base_message_data):
        """Test needs_reply() returns False for spam."""
        base_message_data['urgency'] = UrgencyLevel.SPAM
        
        msg = UnifiedMessage(**base_message_data)
        assert msg.needs_reply() is False


# ============================================
# TEST: EXCEPTION HIERARCHY
# ============================================

class TestExceptions:
    """Test custom exception hierarchy."""
    
    def test_base_exception(self):
        """Test SocialSpaceError base exception."""
        error = SocialSpaceError("Test error", code=500)
        
        assert error.message == "Test error"
        assert error.code == 500
        assert error.timestamp is not None
    
    def test_exception_to_dict(self):
        """Test exception serialization."""
        error = ValidationError(
            "Invalid data",
            context={"field": "username"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict['error_type'] == "ValidationError"
        assert error_dict['message'] == "Invalid data"
        assert error_dict['code'] == 422
        assert error_dict['context']['field'] == "username"
    
    def test_platform_specific_errors(self):
        """Test platform-specific exceptions."""
        wa_error = WhatsAppError("Connection failed")
        assert wa_error.context['platform'] == 'whatsapp'
        assert wa_error.code == 502
        
        ig_error = InstagramError("API rate limit")
        assert ig_error.context['platform'] == 'instagram'
        
        tw_error = TwitterError("Invalid credentials")
        assert tw_error.context['platform'] == 'twitter'
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry information."""
        error = RateLimitError(
            retry_after=60,
            limit=100,
            remaining=0
        )
        
        assert error.code == 429
        assert error.retry_after == 60
        assert error.limit == 100
        assert error.remaining == 0


# ============================================
# TEST: SERIALIZATION
# ============================================

class TestSerialization:
    """Test model serialization/deserialization."""
    
    def test_message_to_dict(self, base_message_data):
        """Test converting message to dictionary."""
        msg = UnifiedMessage(**base_message_data)
        msg_dict = msg.model_dump()
        
        assert isinstance(msg_dict, dict)
        assert msg_dict['platform'] == 'whatsapp'
        assert msg_dict['type'] == 'text'
    
    def test_message_to_json(self, base_message_data):
        """Test JSON serialization."""
        msg = UnifiedMessage(**base_message_data)
        json_str = msg.model_dump_json()
        
        assert isinstance(json_str, str)
        assert 'whatsapp' in json_str
    
    def test_message_from_dict(self, base_message_data):
        """Test creating message from dictionary."""
        msg1 = UnifiedMessage(**base_message_data)
        msg_dict = msg1.model_dump()
        
        msg2 = UnifiedMessage(**msg_dict)
        
        assert msg1.platform == msg2.platform
        assert msg1.content == msg2.content


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
