"""
YouTube Platform Tests
=======================

Comprehensive tests for YouTube integration.

Run:
    pytest tests/test_youtube.py -v

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 9
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.youtube import (
    YouTubePlatform,
    YouTubeClient,
    YouTubeVideo,
    YouTubeComment,
)
from socialspace_agent.platforms.youtube.utils import (
    extract_video_id_from_url,
    is_valid_video_id,
    create_video_url,
    format_view_count,
    extract_timestamps,
    calculate_quota_cost,
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
# TEST: YOUTUBE UTILITIES
# ============================================

class TestYouTubeUtils:
    """Test YouTube utility functions."""
    
    def test_extract_video_id_from_url(self):
        """Test extracting video ID from URL."""
        url1 = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id_from_url(url1) == "dQw4w9WgXcQ"
        
        url2 = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id_from_url(url2) == "dQw4w9WgXcQ"
    
    def test_is_valid_video_id(self):
        """Test video ID validation."""
        assert is_valid_video_id("dQw4w9WgXcQ") is True
        assert is_valid_video_id("invalid") is False
        assert is_valid_video_id("toolongvideoid123") is False
    
    def test_create_video_url(self):
        """Test creating video URL."""
        url = create_video_url("dQw4w9WgXcQ")
        assert "youtube.com/watch?v=dQw4w9WgXcQ" in url
    
    def test_format_view_count(self):
        """Test view count formatting."""
        assert format_view_count(1234) == "1.2K views"
        assert format_view_count(1234567) == "1.2M views"
        assert format_view_count(42) == "42 views"
    
    def test_extract_timestamps(self):
        """Test timestamp extraction."""
        text = "Check 1:23 and 5:45 in the video!"
        timestamps = extract_timestamps(text)
        assert "1:23" in timestamps
        assert "5:45" in timestamps
    
    def test_calculate_quota_cost(self):
        """Test quota cost calculation."""
        assert calculate_quota_cost("read", 10) == 10
        assert calculate_quota_cost("write", 2) == 100
        assert calculate_quota_cost("search", 1) == 100


# ============================================
# TEST: YOUTUBE MODELS
# ============================================

class TestYouTubeModels:
    """Test YouTube data models."""
    
    def test_create_youtube_video(self):
        """Test creating YouTube video."""
        from socialspace_agent.platforms.youtube.models import (
            YouTubeVideoSnippet,
            YouTubeVideoStatistics
        )
        
        video = YouTubeVideo(
            id="dQw4w9WgXcQ",
            snippet=YouTubeVideoSnippet(
                published_at="2026-02-22T12:00:00Z",
                channel_id="UC_test",
                title="Test Video",
                description="This is a test",
                thumbnails={},
                channel_title="Test Channel"
            ),
            statistics=YouTubeVideoStatistics(
                view_count="1000",
                like_count="100",
                comment_count="50"
            )
        )
        
        assert video.id == "dQw4w9WgXcQ"
        assert video.get_title() == "Test Video"
        assert "youtube.com/watch?v=" in video.get_url()
    
    def test_create_youtube_comment(self):
        """Test creating YouTube comment."""
        from socialspace_agent.platforms.youtube.models import YouTubeCommentSnippet
        
        comment = YouTubeComment(
            id="comment_123",
            snippet=YouTubeCommentSnippet(
                text_display="Great video!",
                text_original="Great video!",
                author_display_name="Test User",
                like_count=5,
                published_at="2026-02-22T12:00:00Z"
            )
        )
        
        assert comment.id == "comment_123"
        assert comment.get_text() == "Great video!"
        assert comment.get_likes() == 5


# ============================================
# TEST: YOUTUBE CLIENT
# ============================================

class TestYouTubeClient:
    """Test YouTube API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = YouTubeClient(
            api_key="test_api_key",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.api_key == "test_api_key"
    
    @pytest.mark.asyncio
    async def test_get_video_mock(self):
        """Test getting video in mock mode."""
        async with YouTubeClient(
            api_key="test_api_key",
            mock_mode=True
        ) as client:
            video = await client.get_video("dQw4w9WgXcQ")
            
            assert video.id == "dQw4w9WgXcQ"
            assert "SocialSpace" in video.get_title()
    
    @pytest.mark.asyncio
    async def test_get_video_comments_mock(self):
        """Test getting video comments in mock mode."""
        async with YouTubeClient(
            api_key="test_api_key",
            mock_mode=True
        ) as client:
            comments = await client.get_video_comments(
                video_id="dQw4w9WgXcQ",
                max_results=10
            )
            
            assert isinstance(comments, list)
            assert len(comments) > 0
    
    @pytest.mark.asyncio
    async def test_post_comment_mock(self):
        """Test posting comment in mock mode."""
        async with YouTubeClient(
            api_key="test_api_key",
            mock_mode=True
        ) as client:
            comment = await client.post_comment(
                video_id="dQw4w9WgXcQ",
                text="Great video!"
            )
            
            assert "Great video!" in comment.get_text()
    
    @pytest.mark.asyncio
    async def test_quota_tracking(self):
        """Test quota tracking."""
        async with YouTubeClient(
            api_key="test_api_key",
            mock_mode=True
        ) as client:
            await client.get_video("dQw4w9WgXcQ")
            await client.post_comment("dQw4w9WgXcQ", "Test")
            
            stats = client.get_stats()
            
            assert stats["quota_used"] > 0
            assert stats["quota_remaining"] < 10000
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with YouTubeClient(
            api_key="test_api_key",
            mock_mode=True
        ) as client:
            await client.get_video_comments("dQw4w9WgXcQ", max_results=5)
            
            stats = client.get_stats()
            
            assert stats["comments_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: YOUTUBE PLATFORM
# ============================================

class TestYouTubePlatform:
    """Test YouTube platform adapter."""
    
    def test_create_platform(self):
        """Test creating YouTube platform instance."""
        config = PlatformConfig(
            platform="youtube",
            api_key="test_api_key",
            mock_mode=True
        )
        
        platform = YouTubePlatform(config)
        
        assert platform.platform_type == "youtube"
        assert platform.api_key == "test_api_key"
    
    def test_create_platform_missing_api_key(self):
        """Test that API key is required."""
        config = PlatformConfig(
            platform="youtube",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            YouTubePlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test YouTube authentication."""
        config = PlatformConfig(
            platform="youtube",
            api_key="test_api_key",
            mock_mode=True
        )
        
        platform = YouTubePlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_message(self):
        """Test normalizing YouTube comment to UnifiedMessage."""
        config = PlatformConfig(
            platform="youtube",
            api_key="test_api_key",
            mock_mode=True
        )
        
        platform = YouTubePlatform(config)
        
        raw_message = {
            "id": "comment_123",
            "snippet": {
                "textOriginal": "Great video! Thanks for sharing!",
                "textDisplay": "Great video! Thanks for sharing!",
                "authorDisplayName": "John Doe",
                "likeCount": 5,
                "publishedAt": "2026-02-22T12:00:00Z",
                "videoId": "dQw4w9WgXcQ"
            }
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.YOUTUBE
        assert unified.type == MessageType.COMMENT
        assert "Great video!" in unified.content
        assert unified.likes == 5
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message (posting comment) via YouTube."""
        config = PlatformConfig(
            platform="youtube",
            api_key="test_api_key",
            mock_mode=True
        )
        
        platform = YouTubePlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.YOUTUBE,
            type=MessageType.COMMENT,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Great video! Thanks for sharing!",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="dQw4w9WgXcQ")
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="youtube",
            api_key="test_api_key",
            mock_mode=True
        )
        
        platform = YouTubePlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="dQw4w9WgXcQ")
    
    @pytest.mark.asyncio
    async def test_get_video_info(self):
        """Test getting video information."""
        config = PlatformConfig(
            platform="youtube",
            api_key="test_api_key",
            mock_mode=True
        )
        
        platform = YouTubePlatform(config)
        await platform.authenticate()
        
        info = await platform.get_video_info("dQw4w9WgXcQ")
        
        assert info["id"] == "dQw4w9WgXcQ"
        assert "title" in info
        assert "views" in info
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from YouTube."""
        config = PlatformConfig(
            platform="youtube",
            api_key="test_api_key",
            mock_mode=True
        )
        
        platform = YouTubePlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])