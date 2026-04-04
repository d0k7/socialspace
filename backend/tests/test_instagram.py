"""
Instagram Platform Tests
=========================

Comprehensive tests for Instagram integration.

Run:
    pytest tests/test_instagram.py -v

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 5
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.instagram import (
    InstagramPlatform,
    InstagramClient,
    InstagramMedia,
    InstagramComment,
)
from socialspace_agent.platforms.instagram.utils import (
    extract_hashtags,
    extract_mentions,
    validate_instagram_id,
    is_valid_hashtag,
    parse_instagram_url,
)
from socialspace_agent.models import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UserInfo,
)
from socialspace_agent.utils.config import PlatformConfig
from socialspace_agent.exceptions import AuthenticationError, ValidationError


# ============================================
# TEST: INSTAGRAM UTILITIES
# ============================================

class TestInstagramUtils:
    """Test Instagram utility functions."""
    
    def test_extract_hashtags(self):
        """Test extracting hashtags from text."""
        assert extract_hashtags("Great! #travel #nature") == ["travel", "nature"]
        assert extract_hashtags("No hashtags") == []
        assert extract_hashtags("#single") == ["single"]
    
    def test_extract_mentions(self):
        """Test extracting mentions from text."""
        assert extract_mentions("Thanks @john and @jane!") == ["john", "jane"]
        assert extract_mentions("No mentions") == []
        assert extract_mentions("Hi @user.name") == ["user.name"]
    
    def test_validate_instagram_id(self):
        """Test Instagram ID validation."""
        assert validate_instagram_id("123456789") is True
        assert validate_instagram_id("abc") is False
        assert validate_instagram_id("") is False
    
    def test_is_valid_hashtag(self):
        """Test hashtag validation."""
        assert is_valid_hashtag("#travel") is True
        assert is_valid_hashtag("travel") is True
        assert is_valid_hashtag("#123") is False  # Only numbers
        assert is_valid_hashtag("#hello world") is False  # Contains space
    
    def test_parse_instagram_url(self):
        """Test parsing Instagram URLs."""
        result = parse_instagram_url("https://instagram.com/p/ABC123/")
        assert result["type"] == "post"
        assert result["id"] == "ABC123"
        
        result = parse_instagram_url("https://instagram.com/johndoe/")
        assert result["type"] == "profile"
        assert result["username"] == "johndoe"


# ============================================
# TEST: INSTAGRAM MODELS
# ============================================

class TestInstagramModels:
    """Test Instagram data models."""
    
    def test_create_instagram_media(self):
        """Test creating Instagram media."""
        media = InstagramMedia(
            id="123456",
            media_type="IMAGE",
            media_url="https://example.com/image.jpg",
            permalink="https://instagram.com/p/ABC123",
            caption="Great photo! #travel",
            timestamp="2026-02-20T19:30:00+0000",
            like_count=42,
            comments_count=5,
            media_product_type="FEED"
        )
        
        assert media.id == "123456"
        assert media.media_type == "IMAGE"
        assert media.is_feed_post() is True
        assert media.is_story() is False
    
    def test_create_instagram_comment(self):
        """Test creating Instagram comment."""
        comment = InstagramComment(
            id="comment_123",
            text="Great post!",
            timestamp="2026-02-20T19:30:00+0000",
            username="johndoe",
            like_count=3
        )
        
        assert comment.id == "comment_123"
        assert comment.text == "Great post!"
        assert comment.is_reply() is False


# ============================================
# TEST: INSTAGRAM CLIENT
# ============================================

class TestInstagramClient:
    """Test Instagram API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = InstagramClient(
            access_token="test_token",
            account_id="123456789",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.account_id == "123456789"
    
    @pytest.mark.asyncio
    async def test_get_account_info_mock(self):
        """Test getting account info in mock mode."""
        async with InstagramClient(
            access_token="test_token",
            account_id="123456789",
            mock_mode=True
        ) as client:
            account = await client.get_account_info()
            
            assert account.username == "socialspace_demo"
            assert account.followers_count == 1000
    
    @pytest.mark.asyncio
    async def test_get_media_mock(self):
        """Test getting media in mock mode."""
        async with InstagramClient(
            access_token="test_token",
            account_id="123456789",
            mock_mode=True
        ) as client:
            response = await client.get_media(limit=10)
            
            assert len(response.data) > 0
            assert "data" in response.model_dump()
    
    @pytest.mark.asyncio
    async def test_create_comment_mock(self):
        """Test posting comment in mock mode."""
        async with InstagramClient(
            access_token="test_token",
            account_id="123456789",
            mock_mode=True
        ) as client:
            comment = await client.create_comment(
                media_id="media_123",
                text="Great post!"
            )
            
            assert comment.text == "Great post!"
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with InstagramClient(
            access_token="test_token",
            account_id="123456789",
            mock_mode=True
        ) as client:
            await client.get_media(limit=5)
            
            stats = client.get_stats()
            
            assert stats["media_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: INSTAGRAM PLATFORM
# ============================================

class TestInstagramPlatform:
    """Test Instagram platform adapter."""
    
    def test_create_platform(self):
        """Test creating Instagram platform instance."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        platform = InstagramPlatform(config)
        
        assert platform.platform_type == "instagram"
        assert platform.account_id == "123456789"
    
    def test_create_platform_missing_access_token(self):
        """Test that access token is required."""
        config = PlatformConfig(
            platform="instagram",
            access_token=None,
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            InstagramPlatform(config)
    
    def test_create_platform_missing_account_id(self):
        """Test that account_id is required."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={},
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            InstagramPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Instagram authentication."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        platform = InstagramPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
        assert platform._account_info is not None
    
    @pytest.mark.asyncio
    async def test_normalize_message(self):
        """Test normalizing Instagram comment to UnifiedMessage."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        platform = InstagramPlatform(config)
        
        raw_message = {
            "id": "comment_123",
            "text": "Amazing photo! 📸",
            "timestamp": "2026-02-20T19:30:00+0000",
            "username": "johndoe",
            "like_count": 5
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.INSTAGRAM
        assert unified.type == MessageType.COMMENT
        assert unified.content == "Amazing photo! 📸"
        assert unified.sender.username == "johndoe"
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message (posting comment) via Instagram."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        platform = InstagramPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.INSTAGRAM,
            type=MessageType.COMMENT,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Great post! Thanks for sharing! 📸",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="media_123")
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        platform = InstagramPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages()
    
    @pytest.mark.asyncio
    async def test_get_recent_media(self):
        """Test getting recent media posts."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        platform = InstagramPlatform(config)
        await platform.authenticate()
        
        media_list = await platform.get_recent_media(limit=5)
        
        assert isinstance(media_list, list)
        assert len(media_list) > 0
        assert isinstance(media_list[0], InstagramMedia)
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Instagram."""
        config = PlatformConfig(
            platform="instagram",
            access_token="test_token",
            metadata={"account_id": "123456789"},
            mock_mode=True
        )
        
        platform = InstagramPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])