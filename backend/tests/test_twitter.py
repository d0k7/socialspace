"""
Twitter Platform Tests
=======================

Comprehensive tests for Twitter integration.

Run:
    pytest tests/test_twitter.py -v

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 8
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.twitter import (
    TwitterPlatform,
    TwitterClient,
    TwitterTweet,
    TwitterUser,
)
from socialspace_agent.platforms.twitter.utils import (
    validate_tweet_length,
    truncate_tweet,
    extract_hashtags,
    extract_mentions,
    parse_twitter_username,
    is_valid_twitter_username,
    format_engagement_count,
    split_long_text,
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
# TEST: TWITTER UTILITIES
# ============================================

class TestTwitterUtils:
    """Test Twitter utility functions."""
    
    def test_validate_tweet_length(self):
        """Test tweet length validation."""
        assert validate_tweet_length("Short tweet") is True
        assert validate_tweet_length("a" * 280) is True
        assert validate_tweet_length("a" * 281) is False
    
    def test_truncate_tweet(self):
        """Test tweet truncation."""
        long_text = "a" * 300
        truncated = truncate_tweet(long_text)
        assert len(truncated) == 280
        assert truncated.endswith("...")
    
    def test_extract_hashtags(self):
        """Test extracting hashtags."""
        text = "Great post! #python #coding #ai"
        hashtags = extract_hashtags(text)
        assert hashtags == ["python", "coding", "ai"]
    
    def test_extract_mentions(self):
        """Test extracting mentions."""
        text = "Hey @john and @jane, check this out!"
        mentions = extract_mentions(text)
        assert mentions == ["john", "jane"]
    
    def test_parse_twitter_username(self):
        """Test parsing usernames."""
        assert parse_twitter_username("@elonmusk") == "elonmusk"
        assert parse_twitter_username("elonmusk") == "elonmusk"
    
    def test_is_valid_twitter_username(self):
        """Test username validation."""
        assert is_valid_twitter_username("elonmusk") is True
        assert is_valid_twitter_username("user_123") is True
        assert is_valid_twitter_username("123456") is False  # All numbers
        assert is_valid_twitter_username("a" * 16) is False  # Too long
    
    def test_format_engagement_count(self):
        """Test engagement count formatting."""
        assert format_engagement_count(1234) == "1.2K"
        assert format_engagement_count(1234567) == "1.2M"
        assert format_engagement_count(42) == "42"
    
    def test_split_long_text(self):
        """Test splitting long text."""
        long_text = "This is a long text. " * 20
        tweets = split_long_text(long_text, max_length=280)
        assert len(tweets) > 1
        assert all(len(t) <= 280 for t in tweets)


# ============================================
# TEST: TWITTER MODELS
# ============================================

class TestTwitterModels:
    """Test Twitter data models."""
    
    def test_create_twitter_user(self):
        """Test creating Twitter user."""
        user = TwitterUser(
            id="123456789",
            username="johndoe",
            name="John Doe",
            verified=True,
            followers_count=1000,
            following_count=500,
            tweet_count=250
        )
        
        assert user.id == "123456789"
        assert user.get_handle() == "@johndoe"
        assert "twitter.com/johndoe" in user.get_profile_url()
    
    def test_create_twitter_tweet(self):
        """Test creating Twitter tweet."""
        tweet = TwitterTweet(
            id="987654321",
            text="Hello Twitter! #python",
            author_id="123456789",
            created_at="2026-02-21T18:45:00.000Z",
            public_metrics={
                "like_count": 42,
                "retweet_count": 10,
                "reply_count": 5,
                "quote_count": 2
            }
        )
        
        assert tweet.id == "987654321"
        assert tweet.text == "Hello Twitter! #python"
        assert tweet.get_like_count() == 42
        assert tweet.get_retweet_count() == 10


# ============================================
# TEST: TWITTER CLIENT
# ============================================

class TestTwitterClient:
    """Test Twitter API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = TwitterClient(
            bearer_token="test_bearer_token",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.bearer_token == "test_bearer_token"
    
    @pytest.mark.asyncio
    async def test_get_user_mock(self):
        """Test getting user in mock mode."""
        async with TwitterClient(
            bearer_token="test_bearer_token",
            mock_mode=True
        ) as client:
            user = await client.get_user_by_username("test_user")
            
            assert user.username == "test_user"
            assert user.name == "SocialSpace Bot"
    
    @pytest.mark.asyncio
    async def test_post_tweet_mock(self):
        """Test posting tweet in mock mode."""
        async with TwitterClient(
            bearer_token="test_bearer_token",
            mock_mode=True
        ) as client:
            tweet = await client.post_tweet(
                text="Test tweet from SocialSpace!"
            )
            
            assert "SocialSpace" in tweet.text
    
    @pytest.mark.asyncio
    async def test_get_user_tweets_mock(self):
        """Test getting user tweets in mock mode."""
        async with TwitterClient(
            bearer_token="test_bearer_token",
            mock_mode=True
        ) as client:
            tweets = await client.get_user_tweets(
                user_id="123456789",
                max_results=10
            )
            
            assert isinstance(tweets, list)
            assert len(tweets) > 0
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with TwitterClient(
            bearer_token="test_bearer_token",
            mock_mode=True
        ) as client:
            await client.post_tweet(text="Test")
            
            stats = client.get_stats()
            
            assert stats["tweets_posted"] == 1
            assert stats["mock_mode"] is True


# ============================================
# TEST: TWITTER PLATFORM
# ============================================

class TestTwitterPlatform:
    """Test Twitter platform adapter."""
    
    def test_create_platform(self):
        """Test creating Twitter platform instance."""
        config = PlatformConfig(
            platform="twitter",
            api_key="test_bearer_token",
            mock_mode=True
        )
        
        platform = TwitterPlatform(config)
        
        assert platform.platform_type == "twitter"
        assert platform.bearer_token == "test_bearer_token"
    
    def test_create_platform_missing_token(self):
        """Test that bearer token is required."""
        config = PlatformConfig(
            platform="twitter",
            api_key=None,
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            TwitterPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Twitter authentication."""
        config = PlatformConfig(
            platform="twitter",
            api_key="test_bearer_token",
            mock_mode=True
        )
        
        platform = TwitterPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_message(self):
        """Test normalizing Twitter tweet to UnifiedMessage."""
        config = PlatformConfig(
            platform="twitter",
            api_key="test_bearer_token",
            mock_mode=True
        )
        
        platform = TwitterPlatform(config)
        
        raw_message = {
            "id": "987654321",
            "text": "Hello Twitter! #python @johndoe",
            "author_id": "123456789",
            "created_at": "2026-02-21T18:45:00.000Z",
            "public_metrics": {
                "like_count": 42,
                "retweet_count": 10,
                "reply_count": 5,
                "quote_count": 2
            }
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.TWITTER
        assert unified.type == MessageType.POST
        assert "Hello Twitter!" in unified.content
        assert unified.likes == 42
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message (posting tweet) via Twitter."""
        config = PlatformConfig(
            platform="twitter",
            api_key="test_bearer_token",
            mock_mode=True
        )
        
        platform = TwitterPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.TWITTER,
            type=MessageType.POST,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Hello Twitter from SocialSpace! 🚀",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id=None)
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_send_message_too_long(self):
        """Test that long messages are rejected."""
        config = PlatformConfig(
            platform="twitter",
            api_key="test_bearer_token",
            mock_mode=True
        )
        
        platform = TwitterPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.TWITTER,
            type=MessageType.POST,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="a" * 300,  # Too long!
            timestamp=datetime.now(timezone.utc)
        )
        
        with pytest.raises(ValidationError):
            await platform.send_message(msg, recipient_id=None)
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="twitter",
            api_key="test_bearer_token",
            mock_mode=True
        )
        
        platform = TwitterPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="123456789")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Twitter."""
        config = PlatformConfig(
            platform="twitter",
            api_key="test_bearer_token",
            mock_mode=True
        )
        
        platform = TwitterPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])