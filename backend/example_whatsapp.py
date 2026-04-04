"""
WhatsApp Platform - Usage Example
==================================

Demonstrates how to use the WhatsApp integration.

Run:
    python example_whatsapp.py
"""

import asyncio
from datetime import datetime, timezone

from socialspace_agent.platforms import create_platform
from socialspace_agent.utils.config import PlatformConfig
from socialspace_agent.models import UnifiedMessage, PlatformType, MessageType, UserInfo


async def main():
    """Demo WhatsApp integration."""
    
    print("=" * 60)
    print("SOCIALSPACE AGENT - WHATSAPP DEMO")
    print("=" * 60)
    print()
    
    # 1. Create configuration
    print("1️⃣  Creating WhatsApp configuration...")
    config = PlatformConfig(
        platform="whatsapp",
        api_key="test_token_12345",  # Replace with real token
        metadata={"phone_number_id": "123456789"},
        mock_mode=True,  # Set to False for production
        rate_limit=100,
        timeout=30
    )
    print(f"✅ Config created (mock_mode={config.mock_mode})")
    print()
    
    # 2. Create platform instance using factory
    print("2️⃣  Creating WhatsApp platform instance...")
    whatsapp = create_platform("whatsapp", config)
    print(f"✅ Platform created: {whatsapp}")
    print()
    
    # 3. Authenticate
    print("3️⃣  Authenticating with WhatsApp...")
    await whatsapp.authenticate()
    print("✅ Authentication successful!")
    print()
    
    # 4. Send a text message
    print("4️⃣  Sending text message...")
    message = UnifiedMessage(
        platform_message_id="demo_001",
        platform=PlatformType.WHATSAPP,
        type=MessageType.TEXT,
        sender=UserInfo(id="me", display_name="SocialSpace Bot"),
        content="Hello from SocialSpace Agent! 🚀",
        timestamp=datetime.now(timezone.utc)
    )
    
    result = await whatsapp.send_message(
        message=message,
        recipient_id="919876543210"
    )
    
    print(f"✅ Message sent!")
    print(f"   Message ID: {result['message_id']}")
    print(f"   Timestamp: {result['timestamp']}")
    print()
    
    # 5. Normalize a received message
    print("5️⃣  Normalizing received WhatsApp message...")
    raw_whatsapp_message = {
        "id": "wamid.ABC123XYZ",
        "from": "919876543210",
        "timestamp": str(int(datetime.now().timestamp())),
        "type": "text",
        "text": {"body": "Thanks for the demo!"}
    }
    
    unified = whatsapp.normalize_message(raw_whatsapp_message)
    print(f"✅ Message normalized!")
    print(f"   Platform: {unified.platform}")
    print(f"   Type: {unified.type}")
    print(f"   Content: {unified.content}")
    print(f"   Sender: {unified.sender.id}")
    print()
    
    # 6. Get statistics
    print("6️⃣  Platform statistics...")
    stats = whatsapp.get_stats()
    print(f"✅ Stats retrieved:")
    print(f"   Messages sent: {stats['messages_sent']}")
    print(f"   Messages fetched: {stats['messages_fetched']}")
    print(f"   API calls: {stats['api_calls']}")
    print(f"   Authenticated: {stats['authenticated']}")
    print()
    
    # 7. Disconnect
    print("7️⃣  Disconnecting...")
    await whatsapp.disconnect()
    print("✅ Disconnected successfully!")
    print()
    
    print("=" * 60)
    print("✅ DEMO COMPLETE! WhatsApp integration working perfectly!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())