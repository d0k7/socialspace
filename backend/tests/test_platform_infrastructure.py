"""
SocialSpace Agent - Platform Infrastructure Tests
==================================================

Tests for Session 2 components:
- Configuration management
- Rate limiting
- Retry logic
- Base platform adapter
- Platform factory

Run:
    pytest tests/test_platform_infrastructure.py -v

Author: Dheeraj Mishra
Created: February 7, 2026
Session: 2
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone

# Import our Session 2 components
from socialspace_agent.utils.config import PlatformConfig, Settings
from socialspace_agent.utils.rate_limiter import RateLimiter, create_rate_limiter
from socialspace_agent.utils.retry import (
    retry_with_backoff,
    async_retry_with_backoff,
    calculate_backoff_delay,
)
from socialspace_agent.platforms.base_platform import BasePlatform
from socialspace_agent.platforms.factory import PlatformFactory
from socialspace_agent.models import UnifiedMessage, PlatformType, MessageType, UserInfo
from socialspace_agent.exceptions import AuthenticationError


# ============================================
# TEST: CONFIGURATION
# ============================================

class TestPlatformConfig:
    """Test PlatformConfig model."""
    
    def test_create_valid_config(self):
        """Test creating valid platform config."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="test_key_12345",
            rate_limit=100,
            timeout=30
        )
        
        assert config.platform == "whatsapp"
        assert config.rate_limit == 100
        assert config.timeout == 30
        assert config.enabled is True
    
    def test_rate_limit_validation(self):
        """Test rate limit must be positive."""
        with pytest.raises(ValueError):
            PlatformConfig(
                platform="whatsapp",
                rate_limit=-10  # Invalid: negative
            )
    
    def test_burst_limit_validation(self):
        """Test burst_limit cannot exceed rate_limit."""
        with pytest.raises(ValueError):
            PlatformConfig(
                platform="whatsapp",
                rate_limit=10,
                burst_limit=20  # Invalid: > rate_limit
            )
    
    def test_mask_secrets(self):
        """Test that secrets are masked in output."""
        config = PlatformConfig(
            platform="whatsapp",
            api_key="secret_key_123",
            api_secret="secret_value_456"
        )
        
        masked = config.mask_secrets()
        
        assert masked['api_key'] == "***"
        assert masked['api_secret'] == "***"
        assert masked['platform'] == "whatsapp"


# ============================================
# TEST: RATE LIMITER
# ============================================

class TestRateLimiter:
    """Test RateLimiter functionality."""
    
    def test_create_rate_limiter(self):
        """Test creating rate limiter."""
        limiter = RateLimiter(rate=10.0, burst=20)
        
        assert limiter.rate == 10.0
        assert limiter.burst == 20
        assert limiter.tokens == 20.0  # Starts full
    
    def test_acquire_tokens(self):
        """Test acquiring tokens."""
        limiter = RateLimiter(rate=100.0, burst=10)
        
        # Should succeed immediately
        result = limiter.acquire(tokens=1, block=False)
        assert result is True
        
        # Tokens should be consumed
        assert limiter.tokens < 10.0
    
    def test_rate_limiting_blocks(self):
        """Test that rate limiting blocks when no tokens."""
        limiter = RateLimiter(rate=10.0, burst=1)
        
        # First acquire succeeds
        assert limiter.acquire(block=False) is True
        
        # Second acquire fails (no tokens)
        assert limiter.acquire(block=False) is False
    
    def test_tokens_refill(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(rate=100.0, burst=10)
        
        # Consume all tokens
        for _ in range(10):
            limiter.acquire(block=False)
        
        # Wait for refill
        time.sleep(0.2)  # 0.2s * 100 tokens/s = 20 tokens
        
        # Should have tokens again
        assert limiter.tokens > 0
    
    @pytest.mark.asyncio
    async def test_async_acquire(self):
        """Test async token acquisition."""
        limiter = RateLimiter(rate=100.0, burst=10)
        
        result = await limiter.acquire_async(tokens=1, block=False)
        assert result is True
    
    def test_rate_limiter_stats(self):
        """Test getting rate limiter statistics."""
        limiter = RateLimiter(rate=10.0, burst=20)
        
        stats = limiter.get_stats()
        
        assert stats['rate'] == 10.0
        assert stats['burst'] == 20
        assert 'tokens_available' in stats
        assert 'utilization' in stats
    
    def test_create_from_requests_per_minute(self):
        """Test creating limiter from requests/minute."""
        limiter = create_rate_limiter(requests_per_minute=60, burst_factor=2.0)
        
        # 60/min = 1/sec
        assert limiter.rate == 1.0
        assert limiter.burst == 2


# ============================================
# TEST: RETRY LOGIC
# ============================================

class TestRetryLogic:
    """Test retry decorators and logic."""
    
    def test_calculate_backoff_delay(self):
        """Test exponential backoff calculation."""
        # Attempt 0: 1 * (2^0) = 1.0
        delay = calculate_backoff_delay(
            attempt=0,
            base_delay=1.0,
            max_delay=60.0,
            jitter=False
        )
        assert delay == 1.0
        
        # Attempt 1: 1 * (2^1) = 2.0
        delay = calculate_backoff_delay(
            attempt=1,
            base_delay=1.0,
            max_delay=60.0,
            jitter=False
        )
        assert delay == 2.0
        
        # Attempt 5: 1 * (2^5) = 32.0
        delay = calculate_backoff_delay(
            attempt=5,
            base_delay=1.0,
            max_delay=60.0,
            jitter=False
        )
        assert delay == 32.0
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        delay = calculate_backoff_delay(
            attempt=10,  # Would be 1024s without cap
            base_delay=1.0,
            max_delay=60.0,
            jitter=False
        )
        
        assert delay == 60.0  # Capped
    
    def test_retry_decorator_success(self):
        """Test retry decorator with successful call."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def successful_function():
            call_count[0] += 1
            return "success"
        
        result = successful_function()
        
        assert result == "success"
        assert call_count[0] == 1  # Called only once
    
    def test_retry_decorator_eventual_success(self):
        """Test retry decorator retries until success."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def eventually_successful():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = eventually_successful()
        
        assert result == "success"
        assert call_count[0] == 3  # Retried twice
    
    def test_retry_decorator_max_retries(self):
        """Test retry decorator respects max_retries."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def always_fails():
            call_count[0] += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_fails()
        
        assert call_count[0] == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_async_retry_decorator(self):
        """Test async retry decorator."""
        call_count = [0]
        
        @async_retry_with_backoff(max_retries=3, base_delay=0.1)
        async def async_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Not yet")
            return "success"
        
        result = await async_function()
        
        assert result == "success"
        assert call_count[0] == 2


# ============================================
# TEST: BASE PLATFORM (MOCK IMPLEMENTATION)
# ============================================

class MockPlatform(BasePlatform):
    """Mock platform implementation for testing."""
    
    async def authenticate(self) -> bool:
        """Mock authentication."""
        self._is_authenticated = True
        return True
    
    async def fetch_messages(self, user_id, since=None, limit=100, filters=None):
        """Mock message fetching."""
        self._ensure_authenticated()
        
        # Return mock messages
        user = UserInfo(id=user_id, display_name="Test User")
        
        messages = []
        for i in range(min(limit, 3)):
            msg = UnifiedMessage(
                platform_message_id=f"mock_{i}",
                platform=PlatformType.WHATSAPP,
                type=MessageType.TEXT,
                sender=user,
                content=f"Mock message {i}",
                timestamp=datetime.now(timezone.utc)
            )
            messages.append(msg)
        
        self._stats["messages_fetched"] += len(messages)
        return messages
    
    async def send_message(self, message, recipient_id):
        """Mock message sending."""
        self._ensure_authenticated()
        
        self._stats["messages_sent"] += 1
        
        return {
            "success": True,
            "message_id": "mock_sent_123",
            "timestamp": datetime.now(),
            "metadata": {}
        }
    
    def normalize_message(self, raw_message):
        """Mock message normalization."""
        return UnifiedMessage(
            platform_message_id=raw_message.get('id', 'mock_id'),
            platform=PlatformType.WHATSAPP,
            type=MessageType.TEXT,
            sender=UserInfo(id="test_user", display_name="Test"),
            content=raw_message.get('text', ''),
            timestamp=datetime.now(timezone.utc)
        )


class TestBasePlatform:
    """Test BasePlatform functionality."""
    
    def test_create_platform(self):
        """Test creating platform instance."""
        config = PlatformConfig(
            platform="whatsapp",
            rate_limit=60,
            timeout=30
        )
        
        platform = MockPlatform(config)
        
        assert platform.platform_type == "whatsapp"
        assert platform._is_authenticated is False
    
    @pytest.mark.asyncio
    async def test_authentication(self):
        """Test platform authentication."""
        config = PlatformConfig(platform="whatsapp")
        platform = MockPlatform(config)
        
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test fetch_messages requires authentication."""
        config = PlatformConfig(platform="whatsapp")
        platform = MockPlatform(config)
        
        # Should fail without authentication
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="test")
    
    @pytest.mark.asyncio
    async def test_fetch_messages_success(self):
        """Test successful message fetching."""
        config = PlatformConfig(platform="whatsapp")
        platform = MockPlatform(config)
        
        await platform.authenticate()
        messages = await platform.fetch_messages(user_id="test", limit=5)
        
        assert len(messages) == 3  # Mock returns 3
        assert all(isinstance(m, UnifiedMessage) for m in messages)
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending messages."""
        config = PlatformConfig(platform="whatsapp")
        platform = MockPlatform(config)
        
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="test",
            platform=PlatformType.WHATSAPP,
            type=MessageType.TEXT,
            sender=UserInfo(id="me", display_name="Me"),
            content="Hello!",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="recipient")
        
        assert result["success"] is True
        assert "message_id" in result
    
    def test_platform_stats(self):
        """Test getting platform statistics."""
        config = PlatformConfig(platform="whatsapp")
        platform = MockPlatform(config)
        
        stats = platform.get_stats()
        
        assert stats['platform'] == "whatsapp"
        assert stats['authenticated'] is False
        assert 'api_calls' in stats


# ============================================
# TEST: PLATFORM FACTORY
# ============================================

class TestPlatformFactory:
    """Test PlatformFactory functionality."""
    
    def test_create_factory(self):
        """Test creating factory instance."""
        factory = PlatformFactory()
        
        assert isinstance(factory, PlatformFactory)
        assert factory.list_platforms() == []
    
    def test_register_platform(self):
        """Test registering platform."""
        factory = PlatformFactory()
        factory.register("mock", MockPlatform)
        
        assert factory.is_registered("mock")
        assert "mock" in factory.list_platforms()
    
    def test_create_platform_from_factory(self):
        """Test creating platform via factory."""
        factory = PlatformFactory()
        factory.register("mock", MockPlatform)
        
        config = PlatformConfig(platform="mock")
        platform = factory.create_platform("mock", config)
        
        assert isinstance(platform, MockPlatform)
    
    def test_create_unregistered_platform_fails(self):
        """Test creating unregistered platform fails."""
        factory = PlatformFactory()
        
        config = PlatformConfig(platform="nonexistent")
        
        with pytest.raises(Exception):  # ConfigurationError
            factory.create_platform("nonexistent", config)


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])