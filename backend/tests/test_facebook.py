"""
Facebook Platform Tests
========================

Comprehensive tests for Facebook integration.

Run:
    pytest tests/test_facebook.py -v

Author: Dheeraj Mishra
Created: February 22, 2026
Session: 10
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.facebook import (
    FacebookPlatform,
    FacebookClient,
    FacebookPost,
    FacebookComment,
)
from socialspace_agent.platforms.facebook.utils import (
    parse_post_id,
    create_facebook_url,
    extract_hashtags,
    extract_mentions,
    format_engagement_count,
    is_valid_access_token,
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
# TEST: FACEBOOK UTILITIES
# ============================================

class TestFacebookUtils:
    """Test Facebook utility functions."""
    
    def test_parse_post_id(self):
        """Test parsing post ID."""
        page_id, post_num = parse_post_id("123456789_987654321")
        assert page_id == "123456789"
        assert post_num == "987654321"
    
    def test_create_facebook_url(self):
        """Test creating Facebook URLs."""
        url = create_facebook_url("page", "123456789")
        assert "facebook.com/123456789" in url
        
        url = create_facebook_url("post", "123_456")
        assert "facebook.com/123_456" in url
    
    def test_extract_hashtags(self):
        """Test extracting hashtags."""
        text = "Great post! #facebook #social #media"
        hashtags = extract_hashtags(text)
        assert hashtags == ["facebook", "social", "media"]
    
    def test_extract_mentions(self):
        """Test extracting mentions."""
        text = "Hey @John and @Jane, check this out!"
        mentions = extract_mentions(text)
        assert mentions == ["John", "Jane"]
    
    def test_format_engagement_count(self):
        """Test engagement count formatting."""
        assert format_engagement_count(1234) == "1.2K"
        assert format_engagement_count(1234567) == "1.2M"
        assert format_engagement_count(42) == "42"
    
    def test_is_valid_access_token(self):
        """Test access token validation."""
        # Mock token format
        valid_token = "a" * 100
        assert is_valid_access_token(valid_token) is True
        
        assert is_valid_access_token("short") is False
        assert is_valid_access_token("") is False


# ============================================
# TEST: FACEBOOK MODELS
# ============================================

class TestFacebookModels:
    """Test Facebook data models."""
    
    def test_create_facebook_post(self):
        """Test creating Facebook post."""
        post = FacebookPost(
            id="123456_789012",
            message="Hello Facebook!",
            **{"from": {"id": "123456", "name": "Test Page"}},
            created_time="2026-02-22T18:00:00+0000",
            type="status",
            likes={"summary": {"total_count": 42}}
        )
        
        assert post.id == "123456_789012"
        assert post.message == "Hello Facebook!"
        assert post.get_like_count() == 42
        assert post.get_author_name() == "Test Page"
    
    def test_create_facebook_comment(self):
        """Test creating Facebook comment."""
        comment = FacebookComment(
            id="comment_123",
            message="Great post!",
            **{"from": {"id": "111", "name": "Test User"}},
            created_time="2026-02-22T18:00:00+0000",
            like_count=5
        )
        
        assert comment.id == "comment_123"
        assert comment.message == "Great post!"
        assert comment.get_author_name() == "Test User"
        assert comment.like_count == 5


# ============================================
# TEST: FACEBOOK CLIENT
# ============================================

class TestFacebookClient:
    """Test Facebook API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = FacebookClient(
            access_token="test_token",
            page_id="test_page",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.access_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_get_page_info_mock(self):
        """Test getting page info in mock mode."""
        async with FacebookClient(
            access_token="test_token",
            page_id="test_page",
            mock_mode=True
        ) as client:
            page = await client.get_page_info()
            
            assert page.name == "SocialSpace Test Page"
            assert page.category == "Software"
    
    @pytest.mark.asyncio
    async def test_get_page_posts_mock(self):
        """Test getting page posts in mock mode."""
        async with FacebookClient(
            access_token="test_token",
            page_id="test_page",
            mock_mode=True
        ) as client:
            posts = await client.get_page_posts(limit=10)
            
            assert isinstance(posts, list)
            assert len(posts) > 0
    
    @pytest.mark.asyncio
    async def test_create_post_mock(self):
        """Test creating post in mock mode."""
        async with FacebookClient(
            access_token="test_token",
            page_id="test_page",
            mock_mode=True
        ) as client:
            post = await client.create_post(
                message="Test post from SocialSpace!"
            )
            
            assert "SocialSpace" in post.message
    
    @pytest.mark.asyncio
    async def test_get_post_comments_mock(self):
        """Test getting post comments in mock mode."""
        async with FacebookClient(
            access_token="test_token",
            page_id="test_page",
            mock_mode=True
        ) as client:
            comments = await client.get_post_comments(
                post_id="test_post",
                limit=10
            )
            
            assert isinstance(comments, list)
            assert len(comments) > 0
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with FacebookClient(
            access_token="test_token",
            page_id="test_page",
            mock_mode=True
        ) as client:
            await client.get_page_posts(limit=5)
            
            stats = client.get_stats()
            
            assert stats["posts_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: FACEBOOK PLATFORM
# ============================================

class TestFacebookPlatform:
    """Test Facebook platform adapter."""
    
    def test_create_platform(self):
        """Test creating Facebook platform instance."""
        config = PlatformConfig(
            platform="facebook",
            api_key="test_token",
            metadata={"page_id": "test_page"},
            mock_mode=True
        )
        
        platform = FacebookPlatform(config)
        
        assert platform.platform_type == "facebook"
        assert platform.access_token == "test_token"
    
    def test_create_platform_missing_token(self):
        """Test that access token is required."""
        config = PlatformConfig(
            platform="facebook",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            FacebookPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Facebook authentication."""
        config = PlatformConfig(
            platform="facebook",
            api_key="test_token",
            metadata={"page_id": "test_page"},
            mock_mode=True
        )
        
        platform = FacebookPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_post(self):
        """Test normalizing Facebook post to UnifiedMessage."""
        config = PlatformConfig(
            platform="facebook",
            api_key="test_token",
            metadata={"page_id": "test_page"},
            mock_mode=True
        )
        
        platform = FacebookPlatform(config)
        
        raw_message = {
            "id": "123456_789012",
            "message": "Hello Facebook! #social",
            "from": {"id": "123456", "name": "Test Page"},
            "created_time": "2026-02-22T18:00:00+0000",
            "type": "status",
            "likes": {"summary": {"total_count": 42}},
            "comments": {"summary": {"total_count": 5}},
            "permalink_url": "https://facebook.com/123456_789012"
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.FACEBOOK
        assert unified.type == MessageType.POST
        assert "Hello Facebook!" in unified.content
        assert unified.likes == 42
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message (creating post) via Facebook."""
        config = PlatformConfig(
            platform="facebook",
            api_key="test_token",
            metadata={"page_id": "test_page"},
            mock_mode=True
        )
        
        platform = FacebookPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.FACEBOOK,
            type=MessageType.POST,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Hello Facebook from SocialSpace! 🚀",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="test_page")
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="facebook",
            api_key="test_token",
            metadata={"page_id": "test_page"},
            mock_mode=True
        )
        
        platform = FacebookPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="test_page")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Facebook."""
        config = PlatformConfig(
            platform="facebook",
            api_key="test_token",
            metadata={"page_id": "test_page"},
            mock_mode=True
        )
        
        platform = FacebookPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])