"""
Discord Platform - Usage Example
=================================

Demonstrates the Discord integration.

Run:
    python example_discord.py
"""

import asyncio
from datetime import datetime, timezone

from socialspace_agent.platforms import create_platform
from socialspace_agent.utils.config import PlatformConfig
from socialspace_agent.models import UnifiedMessage, PlatformType, MessageType, UserInfo


async def main():
    """Demo Discord integration."""
    
    print("=" * 60)
    print("SOCIALSPACE AGENT - DISCORD DEMO")
    print("=" * 60)
    print()
    
    # 1. Create configuration
    print("1️⃣  Creating Discord configuration...")
    config = PlatformConfig(
        platform="discord",
        api_key="test_bot_token_12345",  # Replace with real bot token
        mock_mode=True,  # Set to False for production
        rate_limit=50,
        timeout=30
    )
    print(f"✅ Config created (mock_mode={config.mock_mode})")
    print()
    
    # 2. Create platform instance using factory
    print("2️⃣  Creating Discord platform instance...")
    discord = create_platform("discord", config)
    print(f"✅ Platform created: {discord}")
    print()
    
    # 3. Authenticate
    print("3️⃣  Authenticating with Discord Bot API...")
    await discord.authenticate()
    bot_info = discord.get_bot_info()
    print(f"✅ Authentication successful!")
    print(f"   Bot: {bot_info.get('username')}#{bot_info.get('discriminator')}")
    print(f"   Bot ID: {bot_info.get('id')}")
    print()
    
    # 4. Send a text message
    print("4️⃣  Sending text message to channel...")
    message = UnifiedMessage(
        platform_message_id="demo_001",
        platform=PlatformType.DISCORD,
        type=MessageType.TEXT,
        sender=UserInfo(id="bot", display_name="SocialSpace Bot"),
        content="Hello Discord! 🎮\nSocialSpace Agent is now online!",
        timestamp=datetime.now(timezone.utc)
    )
    
    result = await discord.send_message(
        message=message,
        recipient_id="123456789"  # Channel ID
    )
    
    print(f"✅ Message sent!")
    print(f"   Message ID: {result['message_id']}")
    print(f"   Timestamp: {result['timestamp']}")
    print()
    
    # 5. Send a rich embed message
    print("5️⃣  Sending rich embed message...")
    embed_result = await discord.send_embed_message(
        channel_id="123456789",
        title="🚀 SocialSpace Agent Status",
        description="All systems operational!",
        color=0x00ff00,  # Green
        fields=[
            {"name": "Platforms", "value": "4/12", "inline": True},
            {"name": "Tests", "value": "111 ✅", "inline": True},
            {"name": "Status", "value": "Production Ready", "inline": False}
        ]
    )
    print(f"✅ Embed sent!")
    print(f"   Message ID: {embed_result['message_id']}")
    print()
    
    # 6. Normalize a received message
    print("6️⃣  Normalizing received Discord message...")
    raw_discord_message = {
        "id": "999888777",
        "channel_id": "123456789",
        "author": {
            "id": "111222333",
            "username": "gamer_pro",
            "discriminator": "4321",
            "bot": False
        },
        "content": "This is awesome! <@987654321> check this out!",
        "timestamp": "2026-02-21T03:30:00+00:00"
    }
    
    unified = discord.normalize_message(raw_discord_message)
    print(f"✅ Message normalized!")
    print(f"   Platform: {unified.platform}")
    print(f"   Type: {unified.type}")
    print(f"   Content: {unified.content}")
    print(f"   Sender: {unified.sender.display_name}")
    print()
    
    # 7. Get statistics
    print("7️⃣  Platform statistics...")
    stats = discord.get_stats()
    print(f"✅ Stats retrieved:")
    print(f"   Messages sent: {stats['messages_sent']}")
    print(f"   Messages fetched: {stats['messages_fetched']}")
    print(f"   API calls: {stats['api_calls']}")
    print(f"   Authenticated: {stats['authenticated']}")
    print()
    
    # 8. Multi-platform comparison
    print("8️⃣  Multi-platform ecosystem status...")
    print(f"✅ Platform integrations:")
    print(f"   WhatsApp:  ✅ Business API (Mock mode - future ready)")
    print(f"   Telegram:  ✅ Bot API (FREE - production ready!) 🆓")
    print(f"   Instagram: ✅ Graph API (Mock mode - future ready)")
    print(f"   Discord:   ✅ Bot API (FREE - production ready!) 🆓")
    print(f"")
    print(f"   Progress:  4/12 platforms = 33.33% ✅")
    print(f"   FREE platforms ready: 2 (Telegram + Discord)")
    print(f"   Total cost: ₹0! 💰")
    print()
    
    # 9. Disconnect
    print("9️⃣  Disconnecting...")
    await discord.disconnect()
    print("✅ Disconnected successfully!")
    print()
    
    print("=" * 60)
    print("✅ DEMO COMPLETE! Discord integration rocks! 🎮🚀")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())