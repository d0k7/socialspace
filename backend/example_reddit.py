"""
Reddit Platform - Usage Example
================================

Demonstrates the Reddit integration.

Run:
    python example_reddit.py
"""

import asyncio
from datetime import datetime, timezone

from socialspace_agent.platforms import create_platform
from socialspace_agent.utils.config import PlatformConfig
from socialspace_agent.models import UnifiedMessage, PlatformType, MessageType, UserInfo


async def main():
    """Demo Reddit integration."""
    
    print("=" * 60)
    print("SOCIALSPACE AGENT - REDDIT DEMO")
    print("=" * 60)
    print()
    
    # 1. Create configuration
    print("1️⃣  Creating Reddit configuration...")
    config = PlatformConfig(
        platform="reddit",
        api_key="test_client_id",  # Replace with real client_id
        metadata={
            "client_secret": "test_client_secret",
            "user_agent": "SocialSpace/1.0 by u/yourname",
            "username": "your_username",  # Optional
            "password": "your_password"   # Optional
        },
        mock_mode=True,  # Set to False for production
        rate_limit=60,
        timeout=30
    )
    print(f"✅ Config created (mock_mode={config.mock_mode})")
    print()
    
    # 2. Create platform instance using factory
    print("2️⃣  Creating Reddit platform instance...")
    reddit = create_platform("reddit", config)
    print(f"✅ Platform created: {reddit}")
    print()
    
    # 3. Authenticate
    print("3️⃣  Authenticating with Reddit OAuth API...")
    await reddit.authenticate()
    print(f"✅ Authentication successful!")
    print(f"   OAuth 2.0 token obtained!")
    print()
    
    # 4. Fetch posts from r/python
    print("4️⃣  Fetching posts from r/python...")
    messages = await reddit.fetch_messages(
        user_id="python",  # Subreddit name
        limit=5,
        filters={"sort": "hot", "include_comments": False}
    )
    print(f"✅ Fetched {len(messages)} posts!")
    if messages:
        print(f"   First post: {messages[0].content[:60]}...")
    print()
    
    # 5. Post a comment
    print("5️⃣  Posting a comment on a submission...")
    message = UnifiedMessage(
        platform_message_id="demo_001",
        platform=PlatformType.REDDIT,
        type=MessageType.COMMENT,
        sender=UserInfo(id="bot", display_name="SocialSpace Bot"),
        content="Great post! Thanks for sharing this with the community! 🚀",
        timestamp=datetime.now(timezone.utc)
    )
    
    result = await reddit.send_message(
        message=message,
        recipient_id="t3_abc123"  # Submission ID
    )
    
    print(f"✅ Comment posted!")
    print(f"   Comment ID: {result['message_id']}")
    print(f"   Timestamp: {result['timestamp']}")
    print()
    
    # 6. Normalize a received submission
    print("6️⃣  Normalizing received Reddit submission...")
    raw_reddit_submission = {
        "id": "abc123",
        "name": "t3_abc123",
        "subreddit": "python",
        "subreddit_id": "t5_mock",
        "author": "python_dev",
        "title": "New Python 3.13 features!",
        "selftext": "Check out these amazing new features...",
        "is_self": True,
        "created_utc": datetime.now().timestamp(),
        "score": 150,
        "num_comments": 25,
        "permalink": "/r/python/comments/abc123/new_python_features/"
    }
    
    unified = reddit.normalize_message(raw_reddit_submission)
    print(f"✅ Submission normalized!")
    print(f"   Platform: {unified.platform}")
    print(f"   Type: {unified.type}")
    print(f"   Content: {unified.content[:60]}...")
    print(f"   Sender: {unified.sender.display_name}")
    print(f"   Score: {unified.likes}")
    print()
    
    # 7. Get statistics
    print("7️⃣  Platform statistics...")
    stats = reddit.get_stats()
    print(f"✅ Stats retrieved:")
    print(f"   Messages fetched: {stats['messages_fetched']}")
    print(f"   Messages sent: {stats['messages_sent']}")
    print(f"   API calls: {stats['api_calls']}")
    print(f"   Authenticated: {stats['authenticated']}")
    print()
    
    # 8. Multi-platform ecosystem
    print("8️⃣  Multi-platform ecosystem status...")
    print(f"✅ Platform integrations complete:")
    print(f"   WhatsApp:  ✅ Business API (Mock - future ready) 💰")
    print(f"   Telegram:  ✅ Bot API (FREE - production!) 🆓")
    print(f"   Instagram: ✅ Graph API (Mock - future ready) 💰")
    print(f"   Discord:   ✅ Bot API (FREE - production!) 🆓")
    print(f"   Reddit:    ✅ OAuth API (FREE - production!) 🆓")
    print(f"")
    print(f"   Progress:  5/12 platforms = 41.67% ✅")
    print(f"   FREE platforms: 3 (Telegram + Discord + Reddit)")
    print(f"   Total cost: ₹0! 💰")
    print()
    
    # 9. Disconnect
    print("9️⃣  Disconnecting...")
    await reddit.disconnect()
    print("✅ Disconnected successfully!")
    print()
    
    print("=" * 60)
    print("✅ DEMO COMPLETE! Reddit integration is awesome! 🎯🚀")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())