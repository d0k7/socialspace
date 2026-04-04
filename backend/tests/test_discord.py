"""
Discord Platform Tests
=======================

Comprehensive tests for Discord integration.

Run:
    pytest tests/test_discord.py -v

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 6
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.discord import (
    DiscordPlatform,
    DiscordClient,
    DiscordMessage,
    DiscordUser,
    DiscordEmbed,
)
from socialspace_agent.platforms.discord.utils import (
    validate_discord_id,
    parse_mention,
    parse_channel_mention,
    create_user_tag,
    hex_to_decimal_color,
    truncate_content,
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
# TEST: DISCORD UTILITIES
# ============================================

class TestDiscordUtils:
    """Test Discord utility functions."""
    
    def test_validate_discord_id(self):
        """Test Discord ID validation."""
        assert validate_discord_id("123456789012345678") is True
        assert validate_discord_id("12345") is False  # Too short
        assert validate_discord_id("abc") is False
    
    def test_parse_mention(self):
        """Test parsing user mentions."""
        assert parse_mention("Hello <@123456789>!") == ["123456789"]
        assert parse_mention("Hi <@!111> and <@222>") == ["111", "222"]
        assert parse_mention("No mentions here") == []
    
    def test_parse_channel_mention(self):
        """Test parsing channel mentions."""
        assert parse_channel_mention("Check <#123456789>") == ["123456789"]
        assert parse_channel_mention("No channels") == []
    
    def test_create_user_tag(self):
        """Test creating user tag."""
        assert create_user_tag("john", "0001") == "john#0001"
    
    def test_hex_to_decimal_color(self):
        """Test color conversion."""
        assert hex_to_decimal_color("#00ff00") == 65280
        assert hex_to_decimal_color("ff0000") == 16711680
    
    def test_truncate_content(self):
        """Test message truncation."""
        long_text = "a" * 2500
        truncated = truncate_content(long_text)
        assert len(truncated) == 2000
        assert truncated.endswith("...")


# ============================================
# TEST: DISCORD MODELS
# ============================================

class TestDiscordModels:
    """Test Discord data models."""
    
    def test_create_discord_user(self):
        """Test creating Discord user."""
        user = DiscordUser(
            id="123456789",
            username="john",
            discriminator="0001",
            bot=False
        )
        
        assert user.id == "123456789"
        assert user.get_tag() == "john#0001"
        assert user.get_mention() == "<@123456789>"
    
    def test_create_discord_message(self):
        """Test creating Discord message."""
        user = DiscordUser(
            id="123",
            username="test",
            discriminator="0001"
        )
        
        msg = DiscordMessage(
            id="987654321",
            channel_id="111111111",
            author=user,
            content="Hello Discord!",
            timestamp="2026-02-21T01:30:00+00:00"
        )
        
        assert msg.id == "987654321"
        assert msg.content == "Hello Discord!"
        assert msg.get_content() == "Hello Discord!"
    
    def test_discord_embed(self):
        """Test creating Discord embed."""
        embed = DiscordEmbed(
            title="Test Embed",
            description="This is a test",
            color=0x00ff00
        )
        
        assert embed.title == "Test Embed"
        assert embed.color == 0x00ff00


# ============================================
# TEST: DISCORD CLIENT
# ============================================

class TestDiscordClient:
    """Test Discord API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = DiscordClient(
            bot_token="test_token",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.bot_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_get_current_user_mock(self):
        """Test getting bot user in mock mode."""
        async with DiscordClient(
            bot_token="test_token",
            mock_mode=True
        ) as client:
            bot_user = await client.get_current_user()
            
            assert bot_user.bot is True
            assert bot_user.username == "SocialSpace Bot"
    
    @pytest.mark.asyncio
    async def test_send_message_mock(self):
        """Test sending message in mock mode."""
        async with DiscordClient(
            bot_token="test_token",
            mock_mode=True
        ) as client:
            message = await client.send_message(
                channel_id="123456789",
                content="Test message"
            )
            
            assert message.content == "Test message"
    
    @pytest.mark.asyncio
    async def test_send_message_with_embed_mock(self):
        """Test sending message with embed."""
        async with DiscordClient(
            bot_token="test_token",
            mock_mode=True
        ) as client:
            embed = DiscordEmbed(
                title="Test",
                description="Test embed",
                color=0xff0000
            )
            
            message = await client.send_message(
                channel_id="123456789",
                embed=embed
            )
            
            assert message is not None
    
    @pytest.mark.asyncio
    async def test_get_messages_mock(self):
        """Test getting messages in mock mode."""
        async with DiscordClient(
            bot_token="test_token",
            mock_mode=True
        ) as client:
            messages = await client.get_messages(
                channel_id="123456789",
                limit=10
            )
            
            assert isinstance(messages, list)
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with DiscordClient(
            bot_token="test_token",
            mock_mode=True
        ) as client:
            await client.send_message(channel_id="123", content="Test")
            
            stats = client.get_stats()
            
            assert stats["messages_sent"] == 1
            assert stats["mock_mode"] is True


# ============================================
# TEST: DISCORD PLATFORM
# ============================================

class TestDiscordPlatform:
    """Test Discord platform adapter."""
    
    def test_create_platform(self):
        """Test creating Discord platform instance."""
        config = PlatformConfig(
            platform="discord",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = DiscordPlatform(config)
        
        assert platform.platform_type == "discord"
        assert platform.bot_token == "test_token"
    
    def test_create_platform_missing_token(self):
        """Test that bot token is required."""
        config = PlatformConfig(
            platform="discord",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            DiscordPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Discord authentication."""
        config = PlatformConfig(
            platform="discord",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = DiscordPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
        assert platform._bot_user is not None
    
    @pytest.mark.asyncio
    async def test_normalize_message(self):
        """Test normalizing Discord message to UnifiedMessage."""
        config = PlatformConfig(
            platform="discord",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = DiscordPlatform(config)
        
        raw_message = {
            "id": "987654321",
            "channel_id": "123456789",
            "author": {
                "id": "111111111",
                "username": "john",
                "discriminator": "0001",
                "bot": False
            },
            "content": "Hello from Discord!",
            "timestamp": "2026-02-21T01:30:00+00:00"
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.DISCORD
        assert unified.type == MessageType.TEXT
        assert unified.content == "Hello from Discord!"
        assert unified.sender.username == "john"
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message via Discord."""
        config = PlatformConfig(
            platform="discord",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = DiscordPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.DISCORD,
            type=MessageType.TEXT,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Test message from SocialSpace",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="123456789")
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="discord",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = DiscordPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="123456789")
    
    @pytest.mark.asyncio
    async def test_send_embed_message(self):
        """Test sending embed message."""
        config = PlatformConfig(
            platform="discord",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = DiscordPlatform(config)
        await platform.authenticate()
        
        result = await platform.send_embed_message(
            channel_id="123456789",
            title="Test Embed",
            description="This is a test",
            color=0x00ff00
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Discord."""
        config = PlatformConfig(
            platform="discord",
            api_key="test_token",
            mock_mode=True
        )
        
        platform = DiscordPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])