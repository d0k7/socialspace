"""
Unit tests for the AI reply parser in app/routers/ai.py.

WHY this file exists: the parser turns free-form model text into posts, and
model replies change from run to run. Two real failures were found on
2026-10-24: divider lines (---) were glued onto the end of a post, and a
numbered list inside the last post cut that post short. These tests pin the
reply shapes seen so far, so a later edit cannot bring those failures back.

These tests call no API and need no network.
"""

import pytest

from app.routers.ai import _parse_variations

# ============================================================================
# CONSTANTS
# ============================================================================

# WHY 3: the composer asks for 3 variations by default.
EXPECTED_COUNT = 3

# WHY a case table: each entry is (case id, raw model reply, expected post
# texts in order). The shapes come from real Groq replies or were traced by
# hand against the parser.
PARSER_CASES: list[tuple[str, str, list[str]]] = [
    (
        "inner_list_stays_in_post_3",
        "1. **Telegram**\nPost one text\n"
        "2. **Discord**\nPost two text\n"
        "3. **Telegram**\nHow AI is fueling abundance:\n"
        "1. Energy is cheap\n2. Food is plentiful\n3. Travel is fast\n"
        "Closing line of post three",
        [
            "**Telegram**\nPost one text",
            "**Discord**\nPost two text",
            "**Telegram**\nHow AI is fueling abundance:\n"
            "1. Energy is cheap\n2. Food is plentiful\n3. Travel is fast\n"
            "Closing line of post three",
        ],
    ),
    (
        "dividers_are_removed",
        "1. **Telegram**\nFirst post text\n---\n\n"
        "2. **Discord**\nSecond post text\n---\n\n"
        "3. **Universal**\nThird post text #Tag",
        [
            "**Telegram**\nFirst post text",
            "**Discord**\nSecond post text",
            "**Universal**\nThird post text #Tag",
        ],
    ),
    ("plain_numbered_list", "1. Alpha\n2. Beta\n3. Gamma", ["Alpha", "Beta", "Gamma"]),
    (
        "decimal_is_not_a_list_item",
        "1. First line\n1.5 million is big\n2. Beta\n3. Gamma",
        ["First line\n1.5 million is big", "Beta", "Gamma"],
    ),
    ("intro_text_is_ignored", "Here are your posts:\n1. A\n2. B\n3. C", ["A", "B", "C"]),
    (
        "numbers_inside_a_divided_block",
        "1. A\n1. x\n2. y\n---\n2. B\n---\n3. C",
        ["A\n1. x\n2. y", "B", "C"],
    ),
    ("no_list_returns_raw_text", "Just one blob of text", ["Just one blob of text"]),
    ("fewer_posts_than_asked", "1. A\n2. B", ["A", "B"]),
    ("star_dividers", "1. A\n***\n2. B\n***\n3. C", ["A", "B", "C"]),
    (
        "intro_in_its_own_divided_block",
        "Here are your posts:\n---\n1. A\n---\n2. B\n---\n3. C",
        ["A", "B", "C"],
    ),
    (
        "intro_in_first_divided_block",
        "Here are your posts:\n1. A\n---\n2. B\n---\n3. C",
        ["A", "B", "C"],
    ),
    (
        "intro_plus_inner_list_in_first_block",
        "Here are your posts:\n1. A\n1. x\n2. y\n---\n2. B\n---\n3. C",
        ["A\n1. x\n2. y", "B", "C"],
    ),
    (
        "unnumbered_divided_reply_keeps_lead_line",
        "Lead line:\n1. x\n2. y\n---\nPost two\n---\nPost three",
        ["Lead line:\n1. x\n2. y", "Post two", "Post three"],
    ),
]

# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.parametrize(
    "raw_text, expected_contents",
    [(raw_text, expected) for _, raw_text, expected in PARSER_CASES],
    ids=[case_id for case_id, _, _ in PARSER_CASES],
)
def test_parse_variations_known_shapes(raw_text: str, expected_contents: list[str]) -> None:
    """
    Check that each known reply shape parses into the exact expected posts.

    WHY exact comparison: a looser check such as "contains" would let a
    divider line or a stray list number slip into a post unnoticed.

    Args:
        raw_text: Model reply text for one known shape
        expected_contents: The post texts the parser must return, in order

    Returns:
        None

    Raises:
        AssertionError: If the parsed posts or their indexes differ from expected
    """
    parsed = _parse_variations(raw_text, EXPECTED_COUNT)

    assert [variation.content for variation in parsed] == expected_contents
    assert [variation.index for variation in parsed] == list(range(1, len(expected_contents) + 1))


def test_extra_posts_are_folded_into_the_last_post() -> None:
    """
    Document what happens when the model returns more posts than requested.

    WHY a normal test, not xfail: posts beyond the requested count are folded
    into the last post (post 3 here). Dropping them instead would mean accepting
    list numbers above the count as new posts, and then a numbered list of 4 or
    more items inside the last post would start fake posts and lose its tail.
    Neither shape was seen in real replies, and the fold keeps all the text.
    This test pins the chosen behavior, so changing it is a deliberate act.

    Returns:
        None

    Raises:
        AssertionError: If the parser's handling of extra posts changes
    """
    parsed = _parse_variations("1. A\n2. B\n3. C\n4. D\n5. E", EXPECTED_COUNT)

    assert [variation.content for variation in parsed] == ["A", "B", "C\n4. D\n5. E"]
