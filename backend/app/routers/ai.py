"""
SocialSpace — AI Content Generation Router
============================================
Created: Phase 3, Session 3.1
April 27, 2026

WHY this file exists:
Implements AI-powered content generation using Groq as the primary provider.
This is the core intelligence layer of SocialSpace — transforming a user's
topic or idea into polished, platform-appropriate social media content.

Provider cascade:
    1. Groq (primary) — free tier, fast inference, openai/gpt-oss-120b
    2. OpenAI (fallback) — if Groq fails or is unavailable
    3. Claude (ultimate fallback) — if both above fail

WHY this cascade matters:
SocialSpace's promise is autonomous operation. If the primary AI provider
goes down, content generation must still work. The cascade ensures
availability without requiring the user to configure multiple providers.
For Phase 3, only Groq is implemented. OpenAI and Claude fallbacks
are scaffolded for Phase 4.

Content generation strategy:
    - User provides a topic/prompt and target platforms
    - AI generates 3 distinct content variations
    - Each variation is platform-optimized (length, tone, hashtags)
    - User picks one or edits before posting
"""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from groq import AsyncGroq, APIConnectionError, APIStatusError, RateLimitError
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_active_user
from app.database.models import User
from socialspace_agent.utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Content Generation"])

# ============================================================================
# CONSTANTS
# ============================================================================

# WHY openai/gpt-oss-120b: Groq recommended replacement after llama-3.3-70b-versatile was shut down on 2026-08-16.
# Fast enough for real-time UX, smart enough for quality social content.
GROQ_MODEL = "openai/gpt-oss-120b"

# WHY a generous max tokens: 3 short posts need far fewer tokens than this,
# but gpt-oss is a reasoning model and its hidden thinking also draws on
# this limit. Too low a value returns empty or cut-off replies.
MAX_TOKENS = 2000

# Platform-specific guidance injected into the system prompt
PLATFORM_GUIDANCE = {
    "telegram": "casual, conversational tone, up to 4096 characters, emojis welcome",
    "discord": "casual community tone, up to 2000 characters, emojis and formatting welcome",
    "twitter": "punchy and concise, max 280 characters, 1-2 hashtags max",
    "linkedin": "professional tone, 150-300 words, industry insights, 3-5 hashtags",
    "instagram": "visual storytelling, 150-300 words, 10-15 relevant hashtags",
    "facebook": "conversational, 100-250 words, question to drive engagement",
    "tiktok": "trendy, energetic, 150 characters max for caption",
    "youtube": "descriptive, SEO-friendly, 200-300 words, include keywords",
}

# ============================================================================
# REQUEST / RESPONSE MODELS
# ============================================================================


class AIGenerateRequest(BaseModel):
    """
    Request for AI content generation.

    WHY topic not full prompt:
    Users think in topics, not prompts. "My new product launch" is more
    natural than a full prompt. SocialSpace constructs the optimized
    prompt internally so users get great results without prompt engineering.
    """
    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Topic or idea to generate content about"
    )
    platforms: list[str] = Field(
        ...,
        min_length=1,
        description="Target platforms — content will be optimized for these"
    )
    tone: Optional[str] = Field(
        default="professional",
        description="Desired tone: professional, casual, humorous, inspirational"
    )
    variations: Optional[int] = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of content variations to generate (1-5)"
    )


class ContentVariation(BaseModel):
    """Single content variation returned by AI."""
    index: int
    content: str
    platform_notes: Optional[str] = None


class AIGenerateResponse(BaseModel):
    """Response from AI content generation."""
    topic: str
    platforms: list[str]
    variations: list[ContentVariation]
    model_used: str
    provider: str


# ============================================================================
# PROMPT BUILDER
# ============================================================================

def _build_system_prompt(platforms: list[str], tone: str) -> str:
    """
    Build the system prompt for content generation.

    WHY separate function: Prompt construction is complex enough to warrant
    its own function. Makes testing and iteration easier — change the prompt
    without touching the endpoint logic.

    Args:
        platforms: List of target platform names
        tone: Desired content tone

    Returns:
        System prompt string for the AI model
    """
    platform_specs = []
    for p in platforms:
        if p in PLATFORM_GUIDANCE:
            platform_specs.append(f"- {p.capitalize()}: {PLATFORM_GUIDANCE[p]}")

    platform_section = "\n".join(platform_specs) if platform_specs else "- General social media post"

    # WHY ask for dividers and plain text: live replies carried divider lines
    # between posts and platform labels in bold markers at the start of a post.
    # The composer inserts variation.content unchanged, so a label or asterisks
    # would land in the user's post. The parser tolerates dividers, but asking
    # for them keeps the reply shape predictable.
    # WHY forbid invented details: a live reply for a product launch topic carried
    # a made up link (example.com) and three different invented product descriptions.
    # The user could publish them unchecked, so the model must leave missing details out.
    return f"""You are SocialSpace AI, an expert social media content creator.
Your job is to generate engaging, platform-optimized social media content.

Target platforms and their requirements:
{platform_section}

Tone: {tone}

Instructions:
- Generate exactly the number of variations requested
- Each variation must be complete and ready to post — no placeholders
- Optimize content length and style for the specified platforms
- Include relevant emojis where appropriate for the platform
- Format your response as a numbered list: 1. [content] 2. [content] etc.
- Put a line containing only --- between one post and the next
- Write plain text only: no markdown, no asterisks, no bold
- Do NOT start a post with a platform name or any other label, begin directly with the post text
- Never invent links, URLs, product names, features, prices or statistics that the topic does not state. If a detail is missing, leave it out and keep the post general
- Do NOT include labels like "Variation 1:" — just the content itself
- Each variation must be meaningfully different in approach or angle
- Never truncate content — every variation must be complete"""


def _build_user_prompt(topic: str, variations: int) -> str:
    """
    Build the user prompt for content generation.

    Args:
        topic: User's topic or idea
        variations: Number of variations to generate

    Returns:
        User prompt string
    """
    return f"Generate {variations} different social media post{'s' if variations > 1 else ''} about: {topic}"


# ============================================================================
# RESPONSE PARSER
# ============================================================================

# WHY a divider pattern: models often put a line of ---, *** or === between
# posts. The old parser glued those lines onto the end of the previous post.
_DIVIDER_RE = re.compile(r"^([-*_=])\1{2,}$")

# WHY a numbered-item pattern: captures the list number and the text after it,
# for "1. text", "1) text" and a bare "1." alone on its line. The (?!\d) guard
# keeps decimals such as "1.5 million" from being read as list items.
_NUMBERED_RE = re.compile(r"^(\d{1,2})[.)](?!\d)\s*(.*)$")


def _parse_variations(raw_text: str, count: int) -> list[ContentVariation]:
    """
    Parse AI response into structured ContentVariation objects.

    WHY custom parser not structured output:
    Groq's free tier does not guarantee JSON mode on all models.
    A numbered list is more reliable and the parser handles edge cases.

    WHY two strategies, because replies differ from run to run:
    A. Exactly `count` blocks separated by divider lines (---): each block
       is one variation, and numbers inside a block cannot split it. If the
       later blocks are numbered, intro text before "1." in block 1 is dropped.
    B. Otherwise, sequential numbered items: only the NEXT expected number
       starts a new variation, so a list inside the last post stays in it.

    Args:
        raw_text: Raw AI response text
        count: Expected number of variations

    Returns:
        List of ContentVariation objects
    """
    # Split at divider lines and drop blank lines. Each block is a list of
    # stripped, non-empty lines.
    blocks: list[list[str]] = [[]]
    for raw_line in raw_text.strip().split("\n"):
        stripped = raw_line.strip()
        if _DIVIDER_RE.match(stripped):
            blocks.append([])
        elif stripped:
            blocks[-1].append(stripped)
    blocks = [block for block in blocks if block]

    # ---- Strategy A: one variation per divider-separated block ----
    if len(blocks) == count:
        first_numbers: list[Optional[int]] = []
        for block in blocks:
            match = _NUMBERED_RE.match(block[0])
            first_numbers.append(int(match.group(1)) if match else None)

        # WHY numbered_reply: when every later block starts with its own number,
        # the reply numbers its posts, so a line before "1." in the first block
        # is intro text. Without that evidence, a "1." inside the first block may
        # be an inner list, and the lines before it belong to the post.
        numbered_reply = count > 1 and all(
            number == position
            for position, number in enumerate(first_numbers, start=1)
            if position > 1
        )

        # WHY this check: a block that starts with the wrong number is probably
        # intro text or a split list, so strategy B is safer for that reply.
        if all(
            number is None or number == position
            for position, number in enumerate(first_numbers, start=1)
        ):
            parsed: list[ContentVariation] = []
            for position, block in enumerate(blocks, start=1):
                lines = list(block)
                if position == 1 and numbered_reply:
                    # WHY: drop intro lines such as "Here are your posts:" that
                    # come before the first "1." marker.
                    for offset, candidate in enumerate(lines):
                        item = _NUMBERED_RE.match(candidate)
                        if item and int(item.group(1)) == 1:
                            lines = lines[offset:]
                            break
                match = _NUMBERED_RE.match(lines[0])
                if match and int(match.group(1)) == position:
                    lines[0] = match.group(2).strip()
                content = "\n".join(line for line in lines if line).strip()
                if content:
                    parsed.append(ContentVariation(index=position, content=content))
            if len(parsed) == count:
                return parsed

    # ---- Strategy B: sequential numbered items ----
    variations: list[ContentVariation] = []
    current_lines: list[str] = []
    expected = 1
    for block in blocks:
        for line in block:
            match = _NUMBERED_RE.match(line)
            if match and expected <= count and int(match.group(1)) == expected:
                if expected > 1 and current_lines:
                    variations.append(ContentVariation(
                        index=expected - 1,
                        content="\n".join(current_lines).strip(),
                    ))
                first = match.group(2).strip()
                current_lines = [first] if first else []
                expected += 1
            elif expected > 1:
                current_lines.append(line)

    # Save the last variation
    if expected > 1 and current_lines:
        variations.append(ContentVariation(
            index=expected - 1,
            content="\n".join(current_lines).strip(),
        ))

    # WHY fallback: If parsing fails completely, return the raw text as one
    # variation rather than returning empty. User gets something useful.
    if not variations:
        logger.warning("AI response parsing produced no variations, using raw text as fallback")
        variations.append(ContentVariation(
            index=1,
            content=raw_text.strip(),
        ))

    return variations[:count]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_content(
    request: AIGenerateRequest,
    current_user: User = Depends(get_current_active_user),
) -> AIGenerateResponse:
    """
    Generate AI-powered social media content using Groq.

    WHY no db dependency:
    Content generation is stateless — we generate and return.
    Saving to posts table happens in the composer when user clicks Post,
    not during generation. Keeping generation stateless makes it fast
    and retryable without side effects.

    Args:
        request: AIGenerateRequest with topic, platforms, tone, variations
        current_user: Authenticated SocialSpace user

    Returns:
        AIGenerateResponse with list of content variations

    Raises:
        HTTPException 500: Groq API key not configured
        HTTPException 429: Groq rate limit exceeded
        HTTPException 502: Groq API connection error
        HTTPException 500: Unexpected generation failure
    """
    settings = get_settings()

    if not settings.groq_api_key:
        logger.error("AI generation attempted but GROQ_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI content generation is not configured. Add GROQ_API_KEY to .env",
        )

    system_prompt = _build_system_prompt(request.platforms, request.tone or "professional")
    user_prompt = _build_user_prompt(request.topic, request.variations or 3)

    logger.info(
        "AI generation request from user %s — topic: '%s' platforms: %s variations: %d",
        current_user.id,
        request.topic[:50],
        request.platforms,
        request.variations or 3,
    )

    # -------------------------------------------------------------------------
    # Call Groq API
    # WHY AsyncGroq: the groq SDK has a native async client (checked on 1.2.0),
    # so the request is awaited and never blocks the event loop. A sync client
    # here would stall every other request while Groq responds.
    # -------------------------------------------------------------------------
    try:
        # WHY async context manager: the client closes its HTTP pool when the
        # block exits, even if the request raises.
        async with AsyncGroq(api_key=settings.groq_api_key) as client:
            completion = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=MAX_TOKENS,
                # WHY reasoning_effort low: gpt-oss is a reasoning model. Its thinking
                # tokens count against max_tokens, and social posts need little
                # deliberation, so low keeps latency down and leaves room for the answer.
                reasoning_effort="low",
                temperature=0.8,
                # WHY temperature 0.8: High enough for creative variation between
                # outputs, low enough to stay on-topic and coherent. 1.0 produces
                # too much randomness for professional content.
            )

        raw_text = completion.choices[0].message.content or ""

        if not raw_text.strip():
            logger.error("Groq returned empty content for user %s", current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI generated empty content. Please try again.",
            )

        variations = _parse_variations(raw_text, request.variations or 3)

        logger.info(
            "AI generation complete for user %s — %d variations generated",
            current_user.id,
            len(variations),
        )

        return AIGenerateResponse(
            topic=request.topic,
            platforms=request.platforms,
            variations=variations,
            model_used=GROQ_MODEL,
            provider="groq",
        )

    except RateLimitError:
        logger.warning("Groq rate limit exceeded for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI rate limit reached. Please wait a moment before generating again.",
        )

    except APIConnectionError as exc:
        logger.error("Groq connection error for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not connect to AI service. Please try again.",
        )

    except APIStatusError as exc:
        logger.error(
            "Groq API status error for user %s: %d %s",
            current_user.id,
            exc.status_code,
            exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {exc.message}",
        )

    except Exception as exc:
        logger.error(
            "Unexpected AI generation error for user %s: %s",
            current_user.id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during content generation. Please try again.",
        )