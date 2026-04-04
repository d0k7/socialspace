"""
LinkedIn Platform Tests
========================

Comprehensive tests for LinkedIn integration.

Run:
    pytest tests/test_linkedin.py -v

Author: Dheeraj Mishra
Created: February 23, 2026
Session: 11
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.linkedin import (
    LinkedInPlatform,
    LinkedInClient,
    LinkedInPost,
    LinkedInComment,
)
from socialspace_agent.platforms.linkedin.utils import (
    parse_urn,
    create_person_urn,
    create_linkedin_url,
    extract_hashtags,
    extract_mentions,
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
# TEST: LINKEDIN UTILITIES
# ============================================

class TestLinkedInUtils:
    """Test LinkedIn utility functions."""
    
    def test_parse_urn(self):
        """Test parsing URN."""
        result = parse_urn("urn:li:person:123")
        assert result["namespace"] == "li"
        assert result["type"] == "person"
        assert result["id"] == "123"
    
    def test_create_person_urn(self):
        """Test creating person URN."""
        urn = create_person_urn("123")
        assert urn == "urn:li:person:123"
    
    def test_create_linkedin_url(self):
        """Test creating LinkedIn URLs."""
        url = create_linkedin_url("profile", "john-doe")
        assert "linkedin.com/in/john-doe" in url
        
        url = create_linkedin_url("company", "socialspace")
        assert "linkedin.com/company/socialspace" in url
    
    def test_extract_hashtags(self):
        """Test extracting hashtags."""
        text = "Great post! #linkedin #professional #network"
        hashtags = extract_hashtags(text)
        assert hashtags == ["linkedin", "professional", "network"]
    
    def test_extract_mentions(self):
        """Test extracting mentions."""
        text = "Hey @John and @Jane, check this out!"
        mentions = extract_mentions(text)
        assert mentions == ["John", "Jane"]
    
    def test_is_valid_access_token(self):
        """Test access token validation."""
        valid_token = "a" * 50
        assert is_valid_access_token(valid_token) is True
        
        assert is_valid_access_token("short") is False
        assert is_valid_access_token("") is False


# ============================================
# TEST: LINKEDIN MODELS
# ============================================

class TestLinkedInModels:
    """Test LinkedIn data models."""
    
    def test_create_linkedin_profile(self):
        """Test creating LinkedIn profile."""
        from socialspace_agent.platforms.linkedin.models import LinkedInProfile
        
        profile = LinkedInProfile(
            id="123",
            first_name="John",
            last_name="Doe",
            headline="Software Engineer"
        )
        
        assert profile.id == "123"
        assert profile.get_full_name() == "John Doe"
        assert "Software Engineer" in profile.get_display_name()
    
    def test_create_linkedin_post(self):
        """Test creating LinkedIn post."""
        post = LinkedInPost(
            id="urn:li:ugcPost:123",
            author="urn:li:person:456",
            text="Hello LinkedIn!",
            lifecycle_state="PUBLISHED",
            created_at=int(datetime.now().timestamp() * 1000)
        )
        
        assert post.id == "urn:li:ugcPost:123"
        assert post.get_text() == "Hello LinkedIn!"
        assert post.is_published() is True


# ============================================
# TEST: LINKEDIN CLIENT
# ============================================

class TestLinkedInClient:
    """Test LinkedIn API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = LinkedInClient(
            access_token="test_token",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.access_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_get_profile_mock(self):
        """Test getting profile in mock mode."""
        async with LinkedInClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            profile = await client.get_profile()
            
            assert profile.first_name == "John"
            assert profile.last_name == "Doe"
    
    @pytest.mark.asyncio
    async def test_get_posts_mock(self):
        """Test getting posts in mock mode."""
        async with LinkedInClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            posts = await client.get_posts(count=10)
            
            assert isinstance(posts, list)
            assert len(posts) > 0
    
    @pytest.mark.asyncio
    async def test_create_post_mock(self):
        """Test creating post in mock mode."""
        async with LinkedInClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            post = await client.create_post(
                text="Test post from SocialSpace!"
            )
            
            assert "LinkedIn" in post.get_text()
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with LinkedInClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            await client.get_posts(count=5)
            
            stats = client.get_stats()
            
            assert stats["posts_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: LINKEDIN PLATFORM
# ============================================

class TestLinkedInPlatform:
    """Test LinkedIn platform adapter."""
    
    def test_create_platform(self):
        """Test creating LinkedIn platform instance."""
        config = PlatformConfig(
            platform="linkedin",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = LinkedInPlatform(config)
        
        assert platform.platform_type == "linkedin"
        assert platform.access_token == "test_token"
    
    def test_create_platform_missing_token(self):
        """Test that access token is required."""
        config = PlatformConfig(
            platform="linkedin",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            LinkedInPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test LinkedIn authentication."""
        config = PlatformConfig(
            platform="linkedin",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = LinkedInPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_post(self):
        """Test normalizing LinkedIn post to UnifiedMessage."""
        config = PlatformConfig(
            platform="linkedin",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = LinkedInPlatform(config)
        
        raw_message = {
            "id": "urn:li:ugcPost:123",
            "author": "urn:li:person:456",
            "text": "Hello LinkedIn! #professional",
            "lifecycle_state": "PUBLISHED",
            "created_at": int(datetime.now().timestamp() * 1000)
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.LINKEDIN
        assert unified.type == MessageType.POST
        assert "Hello LinkedIn!" in unified.content
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message (creating post) via LinkedIn."""
        config = PlatformConfig(
            platform="linkedin",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = LinkedInPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.LINKEDIN,
            type=MessageType.POST,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Hello LinkedIn from SocialSpace! 🚀",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg)
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="linkedin",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = LinkedInPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="me")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from LinkedIn."""
        config = PlatformConfig(
            platform="linkedin",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = LinkedInPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])