"""
Pinterest Platform Tests
=========================

Comprehensive tests for Pinterest integration.

Run:
    pytest tests/test_pinterest.py -v

Author: Dheeraj Mishra
Created: February 24, 2026
Session: 14 (FINAL SESSION - 100% COMPLETION!)
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.pinterest import (
    PinterestPlatform,
    PinterestClient,
    PinterestPin,
    PinterestBoard,
)
from socialspace_agent.platforms.pinterest.utils import (
    parse_username,
    create_pin_url,
    create_board_url,
    create_profile_url,
    is_valid_username,
    format_save_count,
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
# TEST: PINTEREST UTILITIES
# ============================================

class TestPinterestUtils:
    """Test Pinterest utility functions."""
    
    def test_parse_username(self):
        """Test parsing username."""
        assert parse_username("SocialSpace") == "socialspace"
        assert parse_username("  user123  ") == "user123"
    
    def test_create_pin_url(self):
        """Test creating pin URLs."""
        url = create_pin_url("123456789")
        assert "pinterest.com/pin/123456789" in url
    
    def test_create_board_url(self):
        """Test creating board URLs."""
        url = create_board_url("socialspace", "ideas")
        assert "pinterest.com/socialspace/ideas" in url
    
    def test_create_profile_url(self):
        """Test creating profile URLs."""
        url = create_profile_url("socialspace")
        assert "pinterest.com/socialspace" in url
    
    def test_is_valid_username(self):
        """Test username validation."""
        assert is_valid_username("socialspace") is True
        assert is_valid_username("user_123") is True
        assert is_valid_username("ab") is False  # Too short
    
    def test_format_save_count(self):
        """Test save count formatting."""
        assert format_save_count(1234) == "1.2K"
        assert format_save_count(1234567) == "1.2M"
        assert format_save_count(42) == "42"


# ============================================
# TEST: PINTEREST MODELS
# ============================================

class TestPinterestModels:
    """Test Pinterest data models."""
    
    def test_create_pinterest_user(self):
        """Test creating Pinterest user."""
        from socialspace_agent.platforms.pinterest.models import PinterestUser
        
        user = PinterestUser(
            id="123",
            username="socialspace",
            first_name="Social",
            last_name="Space",
            pin_count=100,
            board_count=10
        )
        
        assert user.id == "123"
        assert user.get_display_name() == "Social Space"
        assert "pinterest.com/socialspace" in user.get_profile_url()
    
    def test_create_pinterest_board(self):
        """Test creating Pinterest board."""
        board = PinterestBoard(
            id="board_123",
            name="Ideas",
            description="Great ideas",
            privacy="PUBLIC",
            pin_count=50
        )
        
        assert board.id == "board_123"
        assert board.name == "Ideas"
        assert board.is_public() is True
    
    def test_create_pinterest_pin(self):
        """Test creating Pinterest pin."""
        from socialspace_agent.platforms.pinterest.models import PinterestMedia
        
        pin = PinterestPin(
            id="pin_123",
            title="Amazing Pin",
            description="Check this out!",
            media=PinterestMedia(
                media_type="image",
                images={"original": {"url": "https://example.com/image.jpg"}}
            ),
            save_count=42
        )
        
        assert pin.id == "pin_123"
        assert pin.title == "Amazing Pin"
        assert "pinterest.com/pin/pin_123" in pin.get_url()


# ============================================
# TEST: PINTEREST CLIENT
# ============================================

class TestPinterestClient:
    """Test Pinterest API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = PinterestClient(
            access_token="test_token",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.access_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_get_user_info_mock(self):
        """Test getting user info in mock mode."""
        async with PinterestClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            user = await client.get_user_info()
            
            assert user.username == "socialspace_pin"
            assert user.pin_count == 100
    
    @pytest.mark.asyncio
    async def test_get_boards_mock(self):
        """Test getting boards in mock mode."""
        async with PinterestClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            boards = await client.get_boards()
            
            assert isinstance(boards, list)
            assert len(boards) > 0
    
    @pytest.mark.asyncio
    async def test_get_pins_mock(self):
        """Test getting pins in mock mode."""
        async with PinterestClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            pins = await client.get_pins()
            
            assert isinstance(pins, list)
            assert len(pins) > 0
    
    @pytest.mark.asyncio
    async def test_create_pin_mock(self):
        """Test creating pin in mock mode."""
        async with PinterestClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            pin = await client.create_pin(
                board_id="board_123",
                title="Test Pin",
                description="This is a test pin"
            )
            
            assert pin.title == "Amazing Social Media Strategy"
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with PinterestClient(
            access_token="test_token",
            mock_mode=True
        ) as client:
            await client.get_pins()
            
            stats = client.get_stats()
            
            assert stats["pins_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: PINTEREST PLATFORM
# ============================================

class TestPinterestPlatform:
    """Test Pinterest platform adapter."""
    
    def test_create_platform(self):
        """Test creating Pinterest platform instance."""
        config = PlatformConfig(
            platform="pinterest",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = PinterestPlatform(config)
        
        assert platform.platform_type == "pinterest"
        assert platform.access_token == "test_token"
    
    def test_create_platform_missing_token(self):
        """Test that access token is required."""
        config = PlatformConfig(
            platform="pinterest",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            PinterestPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Pinterest authentication."""
        config = PlatformConfig(
            platform="pinterest",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = PinterestPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_pin(self):
        """Test normalizing Pinterest pin to UnifiedMessage."""
        config = PlatformConfig(
            platform="pinterest",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = PinterestPlatform(config)
        
        raw_message = {
            "id": "pin_123",
            "title": "Amazing Pin",
            "description": "Check this out! 📌",
            "media": {
                "media_type": "image",
                "images": {"original": {"url": "https://example.com/image.jpg"}}
            },
            "board_id": "board_123",
            "save_count": 42,
            "comment_count": 5,
            "created_at": datetime.now().isoformat()
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.PINTEREST
        assert unified.type == MessageType.POST
        assert "Amazing Pin" in unified.content
    
    @pytest.mark.asyncio
    async def test_send_pin_requires_media(self):
        """Test that sending pin requires media."""
        config = PlatformConfig(
            platform="pinterest",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = PinterestPlatform(config)
        await platform.authenticate()
        
        # Message without media
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.PINTEREST,
            type=MessageType.POST,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Test pin",
            timestamp=datetime.now(timezone.utc)
        )
        
        with pytest.raises(ValidationError):
            await platform.send_message(msg, recipient_id="board_123")
    
    @pytest.mark.asyncio
    async def test_send_pin_with_media(self):
        """Test sending pin with media."""
        config = PlatformConfig(
            platform="pinterest",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = PinterestPlatform(config)
        await platform.authenticate()
        
        # Message with media
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.PINTEREST,
            type=MessageType.POST,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Amazing inspiration!",
            media=[MediaAttachment(url="https://example.com/image.jpg", type="image")],
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="board_123")
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="pinterest",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = PinterestPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="me")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Pinterest."""
        config = PlatformConfig(
            platform="pinterest",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = PinterestPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])