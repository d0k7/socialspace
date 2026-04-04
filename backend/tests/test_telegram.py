"""
Telegram Platform Tests
========================

Comprehensive tests for Telegram integration.

Run:
    pytest tests/test_telegram.py -v

Author: Dheeraj Mishra
Created: February 20, 2026
Session: 4
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.telegram import (
    TelegramPlatform,
    TelegramClient,
    TelegramMessage,
    TelegramUser,
    TelegramChat,
)
from socialspace_agent.platforms.telegram.utils import (
    format_telegram_id,
    validate_telegram_id,
    is_valid_bot_token,
    extract_command,
    get_command_args,
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
# TEST: TELEGRAM UTILITIES
# ============================================

class TestTelegramUtils:
    """Test Telegram utility functions."""
    
    def test_format_telegram_id(self):
        """Test formatting Telegram IDs."""
        assert format_telegram_id("123456789") == "123456789"
        assert format_telegram_id("user_123") == "123"
    
    def test_validate_telegram_id_valid(self):
        """Test validating correct Telegram IDs."""
        assert validate_telegram_id("123456789") is True
        assert validate_telegram_id("1") is True
    
    def test_validate_telegram_id_invalid(self):
        """Test rejecting invalid Telegram IDs."""
        assert validate_telegram_id("0") is False
        assert validate_telegram_id("-123") is False
        assert validate_telegram_id("abc") is False
    
    def test_is_valid_bot_token(self):
        """Test bot token validation."""
        assert is_valid_bot_token("123456:ABC-DEF123") is True
        assert is_valid_bot_token("invalid") is False
        assert is_valid_bot_token("123:") is False
    
    def test_extract_command(self):
        """Test extracting commands from text."""
        assert extract_command("/start") == "start"
        assert extract_command("/help@mybot") == "help"
        assert extract_command("Hello") is None
    
    def test_get_command_args(self):
        """Test extracting command arguments."""
        assert get_command_args("/start arg1 arg2") == ["arg1", "arg2"]
        assert get_command_args("/help") == []
        assert get_command_args("Hello") == []


# ============================================
# TEST: TELEGRAM MODELS
# ============================================

class TestTelegramModels:
    """Test Telegram data models."""
    
    def test_create_telegram_user(self):
        """Test creating Telegram user."""
        user = TelegramUser(
            id=123456789,
            first_name="John",
            last_name="Doe",
            username="johndoe"
        )
        
        assert user.id == 123456789
        assert user.get_full_name() == "John Doe"
        assert user.get_mention() == "@johndoe"
    
    def test_create_telegram_message(self):
        """Test creating Telegram message."""
        msg = TelegramMessage(
            message_id=1,
            date=1708300000,
            **{"from": {
                "id": 123,
                "first_name": "John",
                "is_bot": False
            }},
            chat={"id": 123, "type": "private", "first_name": "John"},
            text="Hello from Telegram!"
        )
        
        assert msg.message_id == 1
        assert msg.text == "Hello from Telegram!"
        assert msg.get_content() == "Hello from Telegram!"


# ============================================
# TEST: TELEGRAM CLIENT
# ============================================

class TestTelegramClient:
    """Test Telegram API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = TelegramClient(
            bot_token="123456:ABC-DEF",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.bot_token == "123456:ABC-DEF"
    
    @pytest.mark.asyncio
    async def test_get_me_mock(self):
        """Test getMe in mock mode."""
        async with TelegramClient(
            bot_token="123456:ABC-DEF",
            mock_mode=True
        ) as client:
            bot_info = await client.get_me()
            
            assert bot_info["is_bot"] is True
            assert "username" in bot_info
    
    @pytest.mark.asyncio
    async def test_send_message_mock(self):
        """Test sending message in mock mode."""
        async with TelegramClient(
            bot_token="123456:ABC-DEF",
            mock_mode=True
        ) as client:
            response = await client.send_message(
                chat_id=123456789,
                text="Test message"
            )
            
            assert response.message_id > 0
            assert response.text == "Test message"
    
    @pytest.mark.asyncio
    async def test_get_updates_mock(self):
        """Test getting updates in mock mode."""
        async with TelegramClient(
            bot_token="123456:ABC-DEF",
            mock_mode=True
        ) as client:
            updates = await client.get_updates()
            
            assert isinstance(updates, list)
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with TelegramClient(
            bot_token="123456:ABC-DEF",
            mock_mode=True
        ) as client:
            await client.send_message(chat_id=123, text="Test")
            
            stats = client.get_stats()
            
            assert stats["messages_sent"] == 1
            assert stats["mock_mode"] is True


# ============================================
# TEST: TELEGRAM PLATFORM
# ============================================

class TestTelegramPlatform:
    """Test Telegram platform adapter."""
    
    def test_create_platform(self):
        """Test creating Telegram platform instance."""
        config = PlatformConfig(
            platform="telegram",
            api_key="123456:ABC-DEF",
            mock_mode=True
        )
        
        platform = TelegramPlatform(config)
        
        assert platform.platform_type == "telegram"
        assert platform.bot_token == "123456:ABC-DEF"
    
    def test_create_platform_missing_token(self):
        """Test that bot token is required."""
        config = PlatformConfig(
            platform="telegram",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            TelegramPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Telegram authentication."""
        config = PlatformConfig(
            platform="telegram",
            api_key="123456:ABC-DEF",
            mock_mode=True
        )
        
        platform = TelegramPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
        assert platform._bot_info is not None
    
    @pytest.mark.asyncio
    async def test_normalize_message(self):
        """Test normalizing Telegram message to UnifiedMessage."""
        config = PlatformConfig(
            platform="telegram",
            api_key="123456:ABC-DEF",
            mock_mode=True
        )
        
        platform = TelegramPlatform(config)
        
        raw_message = {
            "message_id": 123,
            "from": {
                "id": 456,
                "first_name": "John",
                "username": "johndoe",
                "is_bot": False
            },
            "chat": {
                "id": 456,
                "type": "private",
                "first_name": "John"
            },
            "date": 1708300000,
            "text": "Hello from Telegram!"
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.TELEGRAM
        assert unified.type == MessageType.TEXT
        assert unified.content == "Hello from Telegram!"
        assert unified.sender.id == "456"
        assert unified.sender.username == "johndoe"
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message via Telegram."""
        config = PlatformConfig(
            platform="telegram",
            api_key="123456:ABC-DEF",
            mock_mode=True
        )
        
        platform = TelegramPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.TELEGRAM,
            type=MessageType.TEXT,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Test message from SocialSpace",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="123456789")
        
        assert result["success"] is True
        assert "message_id" in result
        assert result["message_id"] > 0
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="telegram",
            api_key="123456:ABC-DEF",
            mock_mode=True
        )
        
        platform = TelegramPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="123456789")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Telegram."""
        config = PlatformConfig(
            platform="telegram",
            api_key="123456:ABC-DEF",
            mock_mode=True
        )
        
        platform = TelegramPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False
    
    @pytest.mark.asyncio
    async def test_get_bot_info(self):
        """Test getting bot information."""
        config = PlatformConfig(
            platform="telegram",
            api_key="123456:ABC-DEF",
            mock_mode=True
        )
        
        platform = TelegramPlatform(config)
        await platform.authenticate()
        
        bot_info = platform.get_bot_info()
        
        assert bot_info is not None
        assert "username" in bot_info


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])