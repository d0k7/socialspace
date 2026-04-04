"""
Simple Verification Script for SocialSpace Models
==================================================

Tests core functionality without requiring pytest.
Run this to verify everything is working!

Author: Dheeraj Mishra
Created: February 6, 2026
"""

from datetime import datetime, timezone

from socialspace_agent.models.unified_message import (
    UnifiedMessage,
    PlatformType,
    MessageType,
    UrgencyLevel,
    SentimentType,
    UserInfo,
    MediaAttachment,
)
from socialspace_agent.exceptions import (
    SocialSpaceError,
    ValidationError,
    WhatsAppError,
    RateLimitError,
)


def test_result(name, passed):
    """Print test result."""
    label = "PASS" if passed else "FAIL"
    print(f"[{label}] {name}")
    return passed


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("SOCIALSPACE AGENT - MODEL VERIFICATION")
    print("=" * 60)
    print()

    total_tests = 0
    passed_tests = 0

    # Test 1: Create a simple WhatsApp message
    try:
        user = UserInfo(
            id="+1234567890",
            display_name="John Doe",
        )

        msg = UnifiedMessage(
            platform_message_id="wa_123",
            platform=PlatformType.WHATSAPP,
            type=MessageType.TEXT,
            sender=user,
            content="Hello World!",
            timestamp=datetime.now(timezone.utc),
        )

        total_tests += 1
        passed_tests += test_result("Create WhatsApp text message", True)
    except Exception as e:
        total_tests += 1
        test_result(f"Create WhatsApp message (ERROR: {e})", False)

    # Test 2: All 12 platforms
    platforms_tested = 0
    for platform in PlatformType:
        try:
            msg = UnifiedMessage(
                platform_message_id=f"{platform.value}_123",
                platform=platform,
                type=MessageType.TEXT,
                sender=user,
                content=f"Test message from {platform.value}",
                timestamp=datetime.now(timezone.utc),
            )
            platforms_tested += 1
        except Exception:
            pass

    total_tests += 1
    passed_tests += test_result(
        f"All 12 platforms supported ({platforms_tested}/13)",
        platforms_tested == 13,
    )

    # Test 3: Media attachment
    try:
        media = MediaAttachment(
            url="https://example.com/image.jpg",
            type="image",
            width=1920,
            height=1080,
        )

        msg = UnifiedMessage(
            platform_message_id="ig_123",
            platform=PlatformType.INSTAGRAM,
            type=MessageType.IMAGE,
            sender=user,
            media=[media],
            timestamp=datetime.now(timezone.utc),
        )

        total_tests += 1
        passed_tests += test_result("Create message with media", True)
    except Exception as e:
        total_tests += 1
        test_result(f"Create media message (ERROR: {e})", False)

    # Test 4: AI Classification
    try:
        msg.urgency = UrgencyLevel.HIGH
        msg.sentiment = SentimentType.POSITIVE
        msg.suggested_reply = "Thank you!"

        total_tests += 1
        passed_tests += test_result("AI classification fields", True)
    except Exception as e:
        total_tests += 1
        test_result(f"AI classification (ERROR: {e})", False)

    # Test 5: Validation (should fail)
    try:
        invalid_msg = UnifiedMessage(
            platform_message_id="test",
            platform=PlatformType.WHATSAPP,
            type=MessageType.TEXT,
            sender=user,
            content=None,  # This should fail
            timestamp=datetime.now(timezone.utc),
        )
        total_tests += 1
        test_result("Validation catches empty content", False)
    except ValueError:
        total_tests += 1
        passed_tests += test_result("Validation catches empty content", True)

    # Test 6: Exception hierarchy
    try:
        error = WhatsAppError("Test error", context={"code": "AUTH_FAILED"})

        assert error.code == 502
        assert error.context["platform"] == "whatsapp"
        assert "error_type" in error.to_dict()

        total_tests += 1
        passed_tests += test_result("Exception hierarchy works", True)
    except Exception as e:
        total_tests += 1
        test_result(f"Exception hierarchy (ERROR: {e})", False)

    # Test 7: Message methods
    try:
        msg = UnifiedMessage(
            platform_message_id="test",
            platform=PlatformType.TELEGRAM,
            type=MessageType.DM,
            sender=user,
            content="Test",
            timestamp=datetime.now(timezone.utc),
            urgency=UrgencyLevel.NORMAL,
        )

        age = msg.age_in_seconds()
        needs_reply = msg.needs_reply()

        total_tests += 1
        passed_tests += test_result(
            f"Helper methods (age={age:.1f}s, needs_reply={needs_reply})",
            age >= 0 and isinstance(needs_reply, bool),
        )
    except Exception as e:
        total_tests += 1
        test_result(f"Helper methods (ERROR: {e})", False)

    # Test 8: Serialization
    try:
        msg_dict = msg.model_dump()
        json_str = msg.model_dump_json()

        total_tests += 1
        passed_tests += test_result(
            "Serialization to dict/JSON",
            isinstance(msg_dict, dict) and isinstance(json_str, str),
        )
    except Exception as e:
        total_tests += 1
        test_result(f"Serialization (ERROR: {e})", False)

    # Summary
    print()
    print("=" * 60)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    if passed_tests == total_tests:
        print("ALL TESTS PASSED! Foundation is solid!")
    else:
        print(f"{total_tests - passed_tests} tests failed. Review errors above.")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    raise SystemExit(0 if success else 1)
