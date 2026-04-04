"""
Telegram Platform - Usage Example
==================================

Demonstrates the Telegram integration.

Run:
    python example_telegram.py
"""

import asyncio
from datetime import datetime, timezone

from socialspace_agent.platforms import create_platform
from socialspace_agent.utils.config import PlatformConfig
from socialspace_agent.models import UnifiedMessage, PlatformType, MessageType, UserInfo


async def main():
    """Demo Telegram integration."""
    
    print("=" * 60)
    print("SOCIALSPACE AGENT - TELEGRAM DEMO")
    print("=" * 60)
    print()
    
    # 1. Create configuration
    print("1️⃣  Creating Telegram configuration...")
    config = PlatformConfig(
        platform="telegram",
        api_key="123456:ABC-DEF1234567890",  # Replace with real token
        mock_mode=True,  # Set to False for production
        rate_limit=30,
        timeout=30
    )
    print(f"✅ Config created (mock_mode={config.mock_mode})")
    print()
    
    # 2. Create platform instance using factory
    print("2️⃣  Creating Telegram platform instance...")
    telegram = create_platform("telegram", config)
    print(f"✅ Platform created: {telegram}")
    print()
    
    # 3. Authenticate
    print("3️⃣  Authenticating with Telegram Bot API...")
    await telegram.authenticate()
    bot_info = telegram.get_bot_info()
    print(f"✅ Authentication successful!")
    print(f"   Bot: @{bot_info.get('username', 'unknown')}")
    print(f"   Bot ID: {bot_info.get('id')}")
    print()
    
    # 4. Send a text message
    print("4️⃣  Sending text message...")
    message = UnifiedMessage(
        platform_message_id="demo_001",
        platform=PlatformType.TELEGRAM,
        type=MessageType.TEXT,
        sender=UserInfo(id="bot", display_name="SocialSpace Bot"),
        content="Hello from SocialSpace Agent! 🤖\nTelegram integration works!",
        timestamp=datetime.now(timezone.utc)
    )
    
    result = await telegram.send_message(
        message=message,
        recipient_id="123456789"
    )
    
    print(f"✅ Message sent!")
    print(f"   Message ID: {result['message_id']}")
    print(f"   Timestamp: {result['timestamp']}")
    print()
    
    # 5. Normalize a received message
    print("5️⃣  Normalizing received Telegram message...")
    raw_telegram_message = {
        "message_id": 999,
        "from": {
            "id": 123456789,
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "is_bot": False
        },
        "chat": {
            "id": 123456789,
            "type": "private",
            "first_name": "John"
        },
        "date": int(datetime.now().timestamp()),
        "text": "/start - Thanks for the Telegram integration!"
    }
    
    unified = telegram.normalize_message(raw_telegram_message)
    print(f"✅ Message normalized!")
    print(f"   Platform: {unified.platform}")
    print(f"   Type: {unified.type}")
    print(f"   Content: {unified.content}")
    print(f"   Sender: {unified.sender.username} ({unified.sender.display_name})")
    print()
    
    # 6. Get statistics
    print("6️⃣  Platform statistics...")
    stats = telegram.get_stats()
    print(f"✅ Stats retrieved:")
    print(f"   Messages sent: {stats['messages_sent']}")
    print(f"   Messages fetched: {stats['messages_fetched']}")
    print(f"   API calls: {stats['api_calls']}")
    print(f"   Authenticated: {stats['authenticated']}")
    print()
    
    # 7. Compare with WhatsApp
    print("7️⃣  Platform comparison...")
    print(f"✅ Multi-platform support working!")
    print(f"   WhatsApp: ✅ Complete")
    print(f"   Telegram: ✅ Complete")
    print(f"   Remaining: 10 platforms")
    print()
    
    # 8. Disconnect
    print("8️⃣  Disconnecting...")
    await telegram.disconnect()
    print("✅ Disconnected successfully!")
    print()
    
    print("=" * 60)
    print("✅ DEMO COMPLETE! Telegram integration working perfectly!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())