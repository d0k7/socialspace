"""
WhatsApp Platform Tests
========================

Comprehensive tests for WhatsApp integration.

Run:
    pytest tests/test_whatsapp.py -v

Author: Dheeraj Mishra
Created: February 19, 2026
Session: 3
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.whatsapp import (
    WhatsAppPlatform,
    WhatsAppClient,
    WhatsAppMessage,
)
from socialspace_agent.platforms.whatsapp.utils import (
    format_phone_number,
    validate_phone_number,
    is_valid_whatsapp_id,
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
# TEST: PHONE NUMBER UTILITIES
# ============================================

class TestPhoneNumberUtils:
    """Test phone number utility functions."""
    
    def test_format_phone_number_with_plus(self):
        """Test formatting phone number with + prefix."""
        assert format_phone_number("+91 98765 43210") == "919876543210"
    
    def test_format_phone_number_with_dashes(self):
        """Test formatting phone number with dashes."""
        assert format_phone_number("91-9876-543210") == "919876543210"
    
    def test_format_phone_number_with_parentheses(self):
        """Test formatting US phone number with parentheses."""
        assert format_phone_number("+1 (555) 123-4567") == "15551234567"
    
    def test_validate_phone_number_valid(self):
        """Test validating correct phone numbers."""
        assert validate_phone_number("919876543210") is True
        assert validate_phone_number("+1 555 123 4567") is True
    
    def test_validate_phone_number_too_short(self):
        """Test rejecting too short phone numbers."""
        assert validate_phone_number("12345") is False
    
    def test_validate_phone_number_too_long(self):
        """Test rejecting too long phone numbers."""
        assert validate_phone_number("1234567890123456") is False
    
    def test_is_valid_whatsapp_id(self):
        """Test WhatsApp message ID validation."""
        assert is_valid_whatsapp_id("wamid.ABC123") is True
        assert is_valid_whatsapp_id("invalid_id") is False
        assert is_valid_whatsapp_id("") is False


# ============================================
# TEST: WHATSAPP MESSAGE MODEL
# ============================================

class TestWhatsAppMessage:
    """Test WhatsApp message model."""
    
    def test_create_text_message(self):
        """Test creating text message."""
        msg = WhatsAppMessage(
            id="wamid.123",
            **{"from": "919876543210"},
            timestamp="1708300000",
            type="text",
            text={"body": "Hello!"}
        )
        
        assert msg.id == "wamid.123"
        assert msg.from_number == "919876543210"
        assert msg.type == "text"
        assert msg.get_content() == "Hello!"
    
    def test_create_image_message(self):
        """Test creating image message."""
        msg = WhatsAppMessage(
            id="wamid.456",
            **{"from": "919876543210"},
            timestamp="1708300000",
            type="image",
            image={
                "id": "media_123",
                "caption": "Check this out!"
            }
        )
        
        assert msg.type == "image"
        assert msg.get_content() == "Check this out!"
        assert msg.get_media_url() == "media_123"


# ============================================
# TEST: WHATSAPP CLIENT
# ============================================

class TestWhatsAppClient:
    """Test WhatsApp API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = WhatsAppClient(
            access_token="test_token",
            phone_number_id="123456789",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.phone_number_id == "123456789"
    
    @pytest.mark.asyncio
    async def test_send_text_message_mock(self):
        """Test sending text message in mock mode."""
        async with WhatsAppClient(
            access_token="test_token",
            phone_number_id="123456789",
            mock_mode=True
        ) as client:
            response = await client.send_text_message(
                to="919876543210",
                text="Test message"
            )
            
            assert response.messaging_product == "whatsapp"
            assert response.get_message_id() is not None
            assert response.get_message_id().startswith("wamid.mock_")
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics tracking."""
        async with WhatsAppClient(
            access_token="test_token",
            phone_number_id="123456789",
            mock_mode=True
        ) as client:
            # Send a message
            await client.send_text_message(to="919876543210", text="Test")
            
            stats = client.get_stats()
            
            assert stats["messages_sent"] == 1
            assert stats["mock_mode"] is True


# ============================================
# TEST: WHATSAPP PLATFORM ADAPTER
# ============================================

class TestWhatsAppPlatform:
    """Test WhatsApp platform adapter."""
    
    def test_create_platform(self):
        """Test creating WhatsApp platform instance."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_token",
            metadata={"phone_number_id": "123456789"},
            mock_mode=True
        )
        
        platform = WhatsAppPlatform(config)
        
        assert platform.platform_type == "whatsapp"
        assert platform.phone_number_id == "123456789"
    
    def test_create_platform_missing_phone_id(self):
        """Test that phone_number_id is required."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_token",
            metadata={},  # Missing phone_number_id
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            WhatsAppPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test WhatsApp authentication."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_token",
            metadata={"phone_number_id": "123456789"},
            mock_mode=True
        )
        
        platform = WhatsAppPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_message(self):
        """Test normalizing WhatsApp message to UnifiedMessage."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_token",
            metadata={"phone_number_id": "123456789"},
            mock_mode=True
        )
        
        platform = WhatsAppPlatform(config)
        
        raw_message = {
            "id": "wamid.123",
            "from": "919876543210",
            "timestamp": "1708300000",
            "type": "text",
            "text": {"body": "Hello from WhatsApp!"}
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.WHATSAPP
        assert unified.type == MessageType.TEXT
        assert unified.content == "Hello from WhatsApp!"
        assert unified.sender.id == "919876543210"
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message via WhatsApp."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_token",
            metadata={"phone_number_id": "123456789"},
            mock_mode=True
        )
        
        platform = WhatsAppPlatform(config)
        await platform.authenticate()
        
        # Create message to send
        msg = UnifiedMessage(
            platform_message_id="temp_123",
            platform=PlatformType.WHATSAPP,
            type=MessageType.TEXT,
            sender=UserInfo(id="me", display_name="Me"),
            content="Test message from SocialSpace",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="919876543210")
        
        assert result["success"] is True
        assert "message_id" in result
        assert result["message_id"].startswith("wamid.")
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_token",
            metadata={"phone_number_id": "123456789"},
            mock_mode=True
        )
        
        platform = WhatsAppPlatform(config)
        
        # Try to fetch without authenticating
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="919876543210")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from WhatsApp."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_token",
            metadata={"phone_number_id": "123456789"},
            mock_mode=True
        )
        
        platform = WhatsAppPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])