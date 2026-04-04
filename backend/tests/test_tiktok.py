"""
TikTok Platform Tests
======================

Comprehensive tests for TikTok integration.

Run:
    pytest tests/test_tiktok.py -v

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 12
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.tiktok import (
    TikTokPlatform,
    TikTokClient,
    TikTokVideo,
    TikTokComment,
)
from socialspace_agent.platforms.tiktok.utils import (
    parse_username,
    create_tiktok_url,
    extract_hashtags,
    extract_mentions,
    format_view_count,
    format_duration,
    is_valid_username,
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
# TEST: TIKTOK UTILITIES
# ============================================

class TestTikTokUtils:
    """Test TikTok utility functions."""
    
    def test_parse_username(self):
        """Test parsing username."""
        assert parse_username("@socialspace") == "socialspace"
        assert parse_username("socialspace") == "socialspace"
    
    def test_create_tiktok_url(self):
        """Test creating TikTok URLs."""
        url = create_tiktok_url("socialspace")
        assert "tiktok.com/@socialspace" in url
        
        url = create_tiktok_url("socialspace", "123456")
        assert "tiktok.com/@socialspace/video/123456" in url
    
    def test_extract_hashtags(self):
        """Test extracting hashtags."""
        text = "Check this out! #fyp #foryou #trending"
        hashtags = extract_hashtags(text)
        assert hashtags == ["fyp", "foryou", "trending"]
    
    def test_extract_mentions(self):
        """Test extracting mentions."""
        text = "Shoutout to @user1 and @user2!"
        mentions = extract_mentions(text)
        assert mentions == ["user1", "user2"]
    
    def test_format_view_count(self):
        """Test view count formatting."""
        assert format_view_count(1234) == "1.2K"
        assert format_view_count(1234567) == "1.2M"
        assert format_view_count(42) == "42"
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(45) == "0:45"
        assert format_duration(125) == "2:05"
    
    def test_is_valid_username(self):
        """Test username validation."""
        assert is_valid_username("socialspace") is True
        assert is_valid_username("user_123") is True
        assert is_valid_username("a") is False  # Too short
        assert is_valid_username("a" * 30) is False  # Too long


# ============================================
# TEST: TIKTOK MODELS
# ============================================

class TestTikTokModels:
    """Test TikTok data models."""
    
    def test_create_tiktok_user(self):
        """Test creating TikTok user."""
        from socialspace_agent.platforms.tiktok.models import TikTokUser
        
        user = TikTokUser(
            id="123",
            username="socialspace",
            display_name="SocialSpace",
            follower_count=10000,
            video_count=100
        )
        
        assert user.id == "123"
        assert user.get_handle() == "@socialspace"
        assert "tiktok.com/@socialspace" in user.get_profile_url()
    
    def test_create_tiktok_video(self):
        """Test creating TikTok video."""
        from socialspace_agent.platforms.tiktok.models import TikTokVideoStats
        
        video = TikTokVideo(
            id="video_123",
            description="Great content! #fyp",
            duration=30,
            create_time=int(datetime.now().timestamp()),
            stats=TikTokVideoStats(
                view_count=10000,
                like_count=500,
                comment_count=50,
                share_count=20
            )
        )
        
        assert video.id == "video_123"
        assert video.get_view_count() == 10000
        assert video.get_like_count() == 500


# ============================================
# TEST: TIKTOK CLIENT
# ============================================

class TestTikTokClient:
    """Test TikTok API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = TikTokClient(
            access_token="test_token",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.access_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_get_user_info_mock(self):
        """Test getting user info in mock mode."""
        async with TikTokClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            user = await client.get_user_info()
            
            assert user.username == "socialspace_user"
            assert user.display_name == "SocialSpace User"
    
    @pytest.mark.asyncio
    async def test_get_videos_mock(self):
        """Test getting videos in mock mode."""
        async with TikTokClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            videos = await client.get_videos(limit=10)
            
            assert isinstance(videos, list)
            assert len(videos) > 0
    
    @pytest.mark.asyncio
    async def test_get_comments_mock(self):
        """Test getting comments in mock mode."""
        async with TikTokClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            comments = await client.get_comments(
                video_id="test_video",
                limit=10
            )
            
            assert isinstance(comments, list)
            assert len(comments) > 0
    
    @pytest.mark.asyncio
    async def test_create_comment_mock(self):
        """Test creating comment in mock mode."""
        async with TikTokClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            comment = await client.create_comment(
                video_id="test_video",
                text="Great video!"
            )
            
            assert "Great video!" in comment.text
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with TikTokClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            await client.get_videos(limit=5)
            
            stats = client.get_stats()
            
            assert stats["videos_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: TIKTOK PLATFORM
# ============================================

class TestTikTokPlatform:
    """Test TikTok platform adapter."""
    
    def test_create_platform(self):
        """Test creating TikTok platform instance."""
        config = PlatformConfig(
            platform="tiktok",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = TikTokPlatform(config)
        
        assert platform.platform_type == "tiktok"
        assert platform.access_token == "test_token"
    
    def test_create_platform_missing_token(self):
        """Test that access token is required."""
        config = PlatformConfig(
            platform="tiktok",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            TikTokPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test TikTok authentication."""
        config = PlatformConfig(
            platform="tiktok",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = TikTokPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_video(self):
        """Test normalizing TikTok video to UnifiedMessage."""
        config = PlatformConfig(
            platform="tiktok",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = TikTokPlatform(config)
        
        raw_message = {
            "id": "video_123",
            "description": "Great content! #fyp #foryou",
            "author": {"username": "test_user", "display_name": "Test User"},
            "duration": 30,
            "create_time": int(datetime.now().timestamp()),
            "stats": {
                "view_count": 10000,
                "like_count": 500,
                "comment_count": 50,
                "share_count": 20
            }
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.TIKTOK
        assert unified.type == MessageType.VIDEO
        assert "Great content!" in unified.content
        assert unified.likes == 500
    
    @pytest.mark.asyncio
    async def test_send_comment(self):
        """Test sending message (creating comment) via TikTok."""
        config = PlatformConfig(
            platform="tiktok",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = TikTokPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.TIKTOK,
            type=MessageType.COMMENT,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Great video! 🔥",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="test_video")
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="tiktok",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = TikTokPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="me")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from TikTok."""
        config = PlatformConfig(
            platform="tiktok",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = TikTokPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])