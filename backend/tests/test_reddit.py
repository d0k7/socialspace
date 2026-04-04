"""
Reddit Platform Tests
======================

Comprehensive tests for Reddit integration.

Run:
    pytest tests/test_reddit.py -v

Author: Dheeraj Mishra
Created: February 21, 2026
Session: 7
"""

import pytest
from datetime import datetime, timezone

from socialspace_agent.platforms.reddit import (
    RedditPlatform,
    RedditClient,
    RedditSubmission,
    RedditComment,
)
from socialspace_agent.platforms.reddit.utils import (
    format_reddit_id,
    add_thing_prefix,
    parse_subreddit_name,
    parse_username,
    extract_reddit_mentions,
    is_valid_subreddit_name,
    format_karma,
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
# TEST: REDDIT UTILITIES
# ============================================

class TestRedditUtils:
    """Test Reddit utility functions."""
    
    def test_format_reddit_id(self):
        """Test formatting Reddit IDs."""
        assert format_reddit_id("t3_abc123") == "abc123"
        assert format_reddit_id("abc123") == "abc123"
    
    def test_add_thing_prefix(self):
        """Test adding thing prefix."""
        assert add_thing_prefix("abc123", "submission") == "t3_abc123"
        assert add_thing_prefix("abc123", "comment") == "t1_abc123"
    
    def test_parse_subreddit_name(self):
        """Test parsing subreddit names."""
        assert parse_subreddit_name("r/python") == "python"
        assert parse_subreddit_name("python") == "python"
    
    def test_parse_username(self):
        """Test parsing usernames."""
        assert parse_username("u/john_doe") == "john_doe"
        assert parse_username("john_doe") == "john_doe"
    
    def test_extract_reddit_mentions(self):
        """Test extracting mentions."""
        text = "Check u/john and r/python!"
        mentions = extract_reddit_mentions(text)
        assert mentions["users"] == ["john"]
        assert mentions["subreddits"] == ["python"]
    
    def test_is_valid_subreddit_name(self):
        """Test subreddit name validation."""
        assert is_valid_subreddit_name("python") is True
        assert is_valid_subreddit_name("r/python") is True
        assert is_valid_subreddit_name("ab") is False  # Too short
    
    def test_format_karma(self):
        """Test karma formatting."""
        assert format_karma(1234) == "1.2k"
        assert format_karma(1234567) == "1.2M"
        assert format_karma(42) == "42"


# ============================================
# TEST: REDDIT MODELS
# ============================================

class TestRedditModels:
    """Test Reddit data models."""
    
    def test_create_reddit_submission(self):
        """Test creating Reddit submission."""
        submission = RedditSubmission(
            id="abc123",
            name="t3_abc123",
            subreddit="python",
            subreddit_id="t5_mock",
            author="john_doe",
            title="My Python Project",
            selftext="Check it out!",
            is_self=True,
            created_utc=datetime.now().timestamp(),
            score=42,
            num_comments=5,
            permalink="/r/python/comments/abc123/my_python_project/"
        )
        
        assert submission.id == "abc123"
        assert submission.title == "My Python Project"
        assert submission.get_full_url().startswith("https://reddit.com")
    
    def test_create_reddit_comment(self):
        """Test creating Reddit comment."""
        comment = RedditComment(
            id="xyz789",
            name="t1_xyz789",
            parent_id="t3_abc123",
            link_id="t3_abc123",
            subreddit="python",
            subreddit_id="t5_mock",
            author="jane_doe",
            body="Great project!",
            created_utc=datetime.now().timestamp(),
            score=10
        )
        
        assert comment.id == "xyz789"
        assert comment.body == "Great project!"
        assert comment.is_top_level() is True


# ============================================
# TEST: REDDIT CLIENT
# ============================================

class TestRedditClient:
    """Test Reddit API client."""
    
    @pytest.mark.asyncio
    async def test_create_client_mock_mode(self):
        """Test creating client in mock mode."""
        client = RedditClient(
            client_id="test_client_id",
            client_secret="test_secret",
            user_agent="SocialSpace/1.0",
            mock_mode=True
        )
        
        assert client.mock_mode is True
        assert client.client_id == "test_client_id"
    
    @pytest.mark.asyncio
    async def test_authenticate_mock(self):
        """Test authentication in mock mode."""
        async with RedditClient(
            client_id="test_client_id",
            client_secret="test_secret",
            user_agent="SocialSpace/1.0",
            mock_mode=True
        ) as client:
            result = await client.authenticate()
            
            assert result is True
            assert client._access_token == "mock_access_token"
    
    @pytest.mark.asyncio
    async def test_get_subreddit_submissions_mock(self):
        """Test getting submissions in mock mode."""
        async with RedditClient(
            client_id="test_client_id",
            client_secret="test_secret",
            user_agent="SocialSpace/1.0",
            mock_mode=True
        ) as client:
            await client.authenticate()
            
            submissions = await client.get_subreddit_submissions(
                subreddit="python",
                limit=10
            )
            
            assert isinstance(submissions, list)
            assert len(submissions) > 0
    
    @pytest.mark.asyncio
    async def test_post_comment_mock(self):
        """Test posting comment in mock mode."""
        async with RedditClient(
            client_id="test_client_id",
            client_secret="test_secret",
            user_agent="SocialSpace/1.0",
            mock_mode=True
        ) as client:
            await client.authenticate()
            
            comment = await client.post_comment(
                parent_id="t3_abc123",
                text="Test comment"
            )
            
            assert comment.body == "Great post! Thanks for sharing!"
    
    @pytest.mark.asyncio
    async def test_client_stats(self):
        """Test client statistics."""
        async with RedditClient(
            client_id="test_client_id",
            client_secret="test_secret",
            user_agent="SocialSpace/1.0",
            mock_mode=True
        ) as client:
            await client.authenticate()
            await client.get_subreddit_submissions("python", limit=5)
            
            stats = client.get_stats()
            
            assert stats["submissions_fetched"] > 0
            assert stats["mock_mode"] is True


# ============================================
# TEST: REDDIT PLATFORM
# ============================================

class TestRedditPlatform:
    """Test Reddit platform adapter."""
    
    def test_create_platform(self):
        """Test creating Reddit platform instance."""
        config = PlatformConfig(
            platform="reddit",
            api_key="test_client_id",
            metadata={
                "client_secret": "test_secret",
                "user_agent": "SocialSpace/1.0"
            },
            mock_mode=True
        )
        
        platform = RedditPlatform(config)
        
        assert platform.platform_type == "reddit"
        assert platform.client_id == "test_client_id"
    
    def test_create_platform_missing_client_id(self):
        """Test that client_id is required."""
        config = PlatformConfig(
            platform="reddit",
            api_key=None,
            metadata={"client_secret": "test_secret"},
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            RedditPlatform(config)
    
    def test_create_platform_missing_client_secret(self):
        """Test that client_secret is required."""
        config = PlatformConfig(
            platform="reddit",
            api_key="test_client_id",
            metadata={},
            mock_mode=True
        )
        
        with pytest.raises(ValidationError):
            RedditPlatform(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self):
        """Test Reddit authentication."""
        config = PlatformConfig(
            platform="reddit",
            api_key="test_client_id",
            metadata={
                "client_secret": "test_secret",
                "user_agent": "SocialSpace/1.0"
            },
            mock_mode=True
        )
        
        platform = RedditPlatform(config)
        result = await platform.authenticate()
        
        assert result is True
        assert platform._is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_normalize_submission(self):
        """Test normalizing Reddit submission to UnifiedMessage."""
        config = PlatformConfig(
            platform="reddit",
            api_key="test_client_id",
            metadata={
                "client_secret": "test_secret",
                "user_agent": "SocialSpace/1.0"
            },
            mock_mode=True
        )
        
        platform = RedditPlatform(config)
        
        raw_message = {
            "id": "abc123",
            "name": "t3_abc123",
            "subreddit": "python",
            "subreddit_id": "t5_mock",
            "author": "john_doe",
            "title": "My Python Project",
            "selftext": "Check it out!",
            "is_self": True,
            "created_utc": datetime.now().timestamp(),
            "score": 42,
            "num_comments": 5,
            "permalink": "/r/python/comments/abc123/my_python_project/"
        }
        
        unified = platform.normalize_message(raw_message)
        
        assert isinstance(unified, UnifiedMessage)
        assert unified.platform == PlatformType.REDDIT
        assert unified.type == MessageType.POST
        assert "My Python Project" in unified.content
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message (posting comment) via Reddit."""
        config = PlatformConfig(
            platform="reddit",
            api_key="test_client_id",
            metadata={
                "client_secret": "test_secret",
                "user_agent": "SocialSpace/1.0"
            },
            mock_mode=True
        )
        
        platform = RedditPlatform(config)
        await platform.authenticate()
        
        msg = UnifiedMessage(
            platform_message_id="temp",
            platform=PlatformType.REDDIT,
            type=MessageType.COMMENT,
            sender=UserInfo(id="bot", display_name="Bot"),
            content="Great post! Thanks for sharing!",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = await platform.send_message(msg, recipient_id="t3_abc123")
        
        assert result["success"] is True
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_fetch_messages_requires_auth(self):
        """Test that fetch_messages requires authentication."""
        config = PlatformConfig(
            platform="reddit",
            api_key="test_client_id",
            metadata={
                "client_secret": "test_secret",
                "user_agent": "SocialSpace/1.0"
            },
            mock_mode=True
        )
        
        platform = RedditPlatform(config)
        
        with pytest.raises(AuthenticationError):
            await platform.fetch_messages(user_id="python")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Reddit."""
        config = PlatformConfig(
            platform="reddit",
            api_key="test_client_id",
            metadata={
                "client_secret": "test_secret",
                "user_agent": "SocialSpace/1.0"
            },
            mock_mode=True
        )
        
        platform = RedditPlatform(config)
        await platform.authenticate()
        
        assert platform._is_authenticated is True
        
        await platform.disconnect()
        
        assert platform._is_authenticated is False


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])