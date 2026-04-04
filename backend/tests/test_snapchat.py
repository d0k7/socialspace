"""
Snapchat Platform Tests
========================

Comprehensive tests for Snapchat integration.

Run:
    pytest tests/test_snapchat.py -v

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 13
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.snapchat import (
    SnapchatPlatform,
    SnapchatClient,
    SnapchatStory,
    SnapchatUser,
)
from socialspace_agent.platforms.snapchat.utils import (
    parse_username,
    create_snapcode_url,
    is_valid_username,
    format_duration,
)
from socialspace_agent.models import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
    MediaAttachment,
)
from socialspace_agent.utils.config import PlatformConfig
from socialspace_agent.exceptions import AuthenticationError, ValidationError


# ============================================
# TEST: SNAPCHAT UTILITIES
# ============================================

class TestSnapchatUtils:
    """Test Snapchat utility functions."""
    
    def test_parse_username(self):
        """Test parsing username."""
        assert parse_username("SocialSpace") == "socialspace"
        assert parse_username("  user123  ") == "user123"
    
    def test_create_snapcode_url(self):
        """Test creating Snapcode URLs."""
        url = create_snapcode_url("socialspace")
        assert "snapchat.com/add/socialspace" in url
    
    def test_is_valid_username(self):
        """Test username validation."""
        assert is_valid_username("socialspace") is True
        assert is_valid_username("user_123") is True
        assert is_valid_username("ab") is False  # Too short
        assert is_valid_username("123abc") is False  # Starts with number
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(5) == "5s"
        assert format_duration(10) == "10s"


# ============================================
# TEST: SNAPCHAT MODELS
# ============================================

class TestSnapchatModels:
    """Test Snapchat data models."""
    
    def test_create_snapchat_user(self):
        """Test creating Snapchat user."""
        user = SnapchatUser(
            id="123",
            username="socialspace",
            display_name="SocialSpace"
        )
        
        assert user.id == "123"
        assert user.username == "socialspace"
        assert "snapchat.com/add/socialspace" in user.get_snapcode_url()
    
    def test_create_snapchat_story(self):
        """Test creating Snapchat story."""
        story = SnapchatStory(
            id="story_123",
            username="socialspace",
            media_url="https://example.com/story.jpg",
            media_type="IMAGE",
            created_at=datetime.now().isoformat(),
            expires_at=datetime.now().isoformat(),
            view_count=100
        )
        
        assert story.id == "story_123"
        assert story.username == "socialspace"


# ============================================
# TEST: SNAPCHAT CLIENT
# ============================================

class TestSnapchatClient:
    """Test Snapchat API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = SnapchatClient(
            access_token="test_token",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.access_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_get_user_info_mock(self):
        """Test getting user info in mock mode."""
        async with SnapchatClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            user = await client.get_user_info()
            
            assert user.username == "socialspace_snap"
            assert user.display_name == "SocialSpace User"
    
    @pytest.mark.asyncio
    async def test_get_stories_mock(self):
        """Test getting stories in mock mode."""
        async with SnapchatClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            stories = await client.get_stories()
            
            assert isinstance(stories, list)
            assert len(stories) > 0
    
    @pytest.mark.asyncio
    async def test_get_bitmoji_mock(self):
        """Test getting Bitmoji in mock mode."""
        async with SnapchatClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            bitmoji = await client.get_bitmoji()
            
            assert bitmoji.avatar_id == "avatar_123"
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with SnapchatClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            await client.get_stories()
            
            stats = client.get_stats()
            
            assert stats["stories_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: SNAPCHAT PLATFORM
# ============================================

class TestSnapchatPlatform:
    """Test Snapchat platform adapter."""
    
    def test_create_platform(self):
        """Test creating Snapchat platform instance."""
        config = PlatformConfig(
            platform="snapchat",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = SnapchatPlatform(config)
        
        assert platform.platform_type == "snapchat"
        assert platform.access_token == "test_token"
    
    def test_create_platform_missing_token(self):
        """Test that access token is required."""
        config = PlatformConfig(
            platform="snapchat",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            SnapchatPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Snapchat authentication."""
        config = PlatformConfig(
            platform="snapchat",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = SnapchatPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_story(self):
        """Test normalizing Snapchat story to UnifiedMessage."""
        config = PlatformConfig(
            platform="snapchat",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = SnapchatPlatform(config)
        
        raw_message = {
            "id": "story_123",
            "username": "socialspace",
            "media_url": "https://example.com/story.jpg",
            "media_type": "IMAGE",
            "created_at": datetime.now().isoformat(),
            "expires_at": datetime.now().isoformat(),
            "view_count": 100
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.SNAPCHAT
        assert unified.type == MessageType.STORY
    
    @pytest.mark.asyncio
    async def test_send_story_requires_media(self):
        """Test that sending story requires media."""
        config = PlatformConfig(
            platform="snapchat",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = SnapchatPlatform(config)
        await platform.authenticate()
        
        # Message without media
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.SNAPCHAT,
            type=MessageType.STORY,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Test",
            timestamp=datetime.now(timezone.utc)
        )
        
        with pytest.raises(ValidationError):
            await platform.send_message(msg)
    
    @pytest.mark.asyncio
    async def test_send_story_with_media(self):
        """Test sending story with media."""
        config = PlatformConfig(
            platform="snapchat",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = SnapchatPlatform(config)
        await platform.authenticate()
        
        # Message with media
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.SNAPCHAT,
            type=MessageType.STORY,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="",
            media=[MediaAttachment(url="https://example.com/image.jpg", type="image")],
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg)
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="snapchat",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = SnapchatPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="me")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Snapchat."""
        config = PlatformConfig(
            platform="snapchat",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = SnapchatPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])