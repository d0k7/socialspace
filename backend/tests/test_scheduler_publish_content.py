"""
Unit tests for how publish_post in app/tasks/scheduler_task.py prepares post
text for each platform before sending.

WHY this file exists: scheduled Telegram sends use HTML parse mode, and post
text is plain text, not markup. A bare < > or & in a commit message or a post
can make Telegram reject the send. publish_post therefore escapes the text for
Telegram only. These tests pin that: the escaped text reaches the Telegram
sender, the stored post text stays as the user typed it, and Discord (which
has no HTML mode) still receives the raw text.

These tests call no API and need no network, no Redis and no database. The
database session, the settings and both senders are replaced with fakes.
"""

import uuid
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from app.database.models import PlatformConnection, Post, PostResult, ScheduledPost
from app.tasks import scheduler_task

# ============================================================================
# CONSTANTS
# ============================================================================

# WHY obviously fake values: no real credential is needed or used here.
FAKE_BOT_TOKEN = "test-token-not-real"
TELEGRAM_CHAT_ID = "12345"
DISCORD_CHANNEL_ID = "67890"

# WHY a case table: each entry is (case id, text as the user typed it, text
# Telegram must receive). The first two cases hold the characters that
# Telegram HTML mode treats as markup. The rest pin what must NOT change:
# quotes need no escaping, and a typed entity such as &amp; is literal text,
# so its ampersand is escaped once.
TELEGRAM_CASES = [
    ("angle_and_ampersand", "if a < b & c > d", "if a &lt; b &amp; c &gt; d"),
    (
        "commit_message_style",
        "fix: handle <None> & empty list",
        "fix: handle &lt;None&gt; &amp; empty list",
    ),
    ("plain_text_unchanged", "Shipped the scheduler today", "Shipped the scheduler today"),
    ("double_quotes_untouched", 'say "hi"', 'say "hi"'),
    ("apostrophe_untouched", "it's fine", "it's fine"),
    ("typed_entity_stays_literal", "Tom &amp; Jerry", "Tom &amp;amp; Jerry"),
]

# ============================================================================
# FAKES
# ============================================================================


class _FakeResult:
    """Stands in for the object db.execute returns: one-row and many-row reads."""

    def __init__(self, items: List[Any]) -> None:
        self._items = items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None

    def scalars(self) -> "_FakeResult":
        return self

    def all(self) -> List[Any]:
        return list(self._items)


class _FakeDb:
    """
    A session stand-in that answers each select by the model it selects.

    WHY dispatch by model, not by call order: publish_post reads four kinds
    of rows, and an order based fake would break the moment a read is added
    or moved. An unknown model fails the test loudly instead of returning
    nothing.
    """

    def __init__(self, post: Any, scheduled: Any, connection: Any) -> None:
        self.added: List[Any] = []
        self._rows = {
            Post: [post],
            ScheduledPost: [scheduled],
            PostResult: [],
            PlatformConnection: [connection],
        }

    def execute(self, statement: Any) -> _FakeResult:
        entity = statement.column_descriptions[0]["entity"]
        if entity not in self._rows:
            raise AssertionError("unexpected select on {0}".format(entity))
        return _FakeResult(self._rows[entity])

    def add(self, row: Any) -> None:
        self.added.append(row)


def _run_publish(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
    content: str,
    tokens: Dict[str, str],
) -> Dict[str, Any]:
    """
    Run publish_post for one post on one platform with every outside call faked.

    Returns the fake post, the fake session and the keyword arguments that
    each sender received.
    """
    post = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        content=content,
        platforms=[platform],
        status="publishing",
    )
    scheduled = SimpleNamespace(retry_count=0, max_retries=3, next_retry_at=None)
    connection = SimpleNamespace(tokens=tokens)
    db = _FakeDb(post, scheduled, connection)
    sent: Dict[str, List[Dict[str, Any]]] = {"telegram": [], "discord": []}

    @contextmanager
    def fake_get_sync_db():
        yield db

    def fake_sender(name: str):
        def _send(**kwargs: Any) -> Dict[str, Any]:
            sent[name].append(kwargs)
            return {
                "success": True,
                "platform_post_id": "1",
                "platform_post_url": None,
                "error_message": None,
                "error_code": None,
            }

        return _send

    monkeypatch.setattr(scheduler_task, "get_sync_db", fake_get_sync_db)
    monkeypatch.setattr(
        scheduler_task,
        "get_settings",
        lambda: SimpleNamespace(
            telegram_bot_token=FAKE_BOT_TOKEN, discord_bot_token=FAKE_BOT_TOKEN
        ),
    )
    monkeypatch.setattr(scheduler_task, "send_telegram_sync", fake_sender("telegram"))
    monkeypatch.setattr(scheduler_task, "send_discord_sync", fake_sender("discord"))

    scheduler_task.publish_post(str(post.id))

    return {"post": post, "db": db, "sent": sent}


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.parametrize(
    "typed, expected",
    [(typed, expected) for _, typed, expected in TELEGRAM_CASES],
    ids=[case_id for case_id, _, _ in TELEGRAM_CASES],
)
def test_telegram_receives_escaped_text(monkeypatch, typed, expected):
    """Telegram gets text that is safe for HTML mode, and the stored text is untouched."""
    run = _run_publish(monkeypatch, "telegram", typed, {"chat_id": TELEGRAM_CHAT_ID})

    assert len(run["sent"]["telegram"]) == 1
    call = run["sent"]["telegram"][0]
    assert call["content"] == expected
    assert call["chat_id"] == TELEGRAM_CHAT_ID
    assert call["bot_token"] == FAKE_BOT_TOKEN
    # WHY: the database keeps what the user typed. Only the copy sent to
    # Telegram is escaped.
    assert run["post"].content == typed
    assert run["post"].status == "published"
    assert len(run["db"].added) == 1
    assert run["db"].added[0].success is True


def test_discord_still_receives_raw_text(monkeypatch):
    """Discord has no HTML mode, so escaping its text would show &lt; literally."""
    typed = "if a < b & c > d"
    run = _run_publish(monkeypatch, "discord", typed, {"channel_id": DISCORD_CHANNEL_ID})

    assert run["sent"]["telegram"] == []
    assert len(run["sent"]["discord"]) == 1
    assert run["sent"]["discord"][0]["content"] == typed
    assert run["post"].status == "published"
