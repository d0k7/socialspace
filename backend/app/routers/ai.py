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
    1. Groq (primary) — free tier, 500+ tokens/sec, llama-3.3-70b-versatile
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
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from groq import Groq, APIConnectionError, APIStatusError, RateLimitError
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_active_user
from app.database.models import User
from socialspace_agent.utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Content Generation"])

# ============================================================================
# CONSTANTS
# ============================================================================

# WHY llama-3.3-70b-versatile: Best quality/speed ratio on Groq free tier.
# Fast enough for real-time UX, smart enough for quality social content.
GROQ_MODEL = "llama-3.3-70b-versatile"

# WHY 500 max tokens: Social media content is short. 500 tokens covers
# even the longest LinkedIn post with room for 3 variations.
MAX_TOKENS = 500

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

def _parse_variations(raw_text: str, count: int) -> list[ContentVariation]:
    """
    Parse AI response into structured ContentVariation objects.

    WHY custom parser not structured output:
    Groq's free tier does not guarantee JSON mode on all models.
    Numbered list format is more reliable and the parser handles
    edge cases gracefully.

    Args:
        raw_text: Raw AI response text
        count: Expected number of variations

    Returns:
        List of ContentVariation objects
    """
    variations = []
    lines = raw_text.strip().split('\n')
    current_variation = []
    current_index = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect numbered list items: "1.", "2.", "1)", "2)" etc.
        is_new_item = False
        for i in range(1, count + 2):
            if stripped.startswith(f"{i}.") or stripped.startswith(f"{i})"):
                # Save previous variation if exists
                if current_variation and current_index > 0:
                    variations.append(ContentVariation(
                        index=current_index,
                        content='\n'.join(current_variation).strip(),
                    ))
                # Start new variation
                current_index = i
                content_start = stripped[len(str(i)) + 1:].strip()
                current_variation = [content_start] if content_start else []
                is_new_item = True
                break

        if not is_new_item and current_index > 0:
            current_variation.append(stripped)

    # Save the last variation
    if current_variation and current_index > 0:
        variations.append(ContentVariation(
            index=current_index,
            content='\n'.join(current_variation).strip(),
        ))

    # WHY fallback: If parsing fails completely, return the raw text as one
    # variation rather than returning empty. User gets something useful.
    if not variations:
        logger.warning("AI response parsing produced no variations — using raw text as fallback")
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
    # WHY synchronous Groq client in async endpoint:
    # Groq's Python SDK does not have a native async client in v1.x.
    # The synchronous call blocks the event loop briefly — acceptable for
    # content generation which is a user-initiated action, not a background
    # task. Phase 4 will wrap in asyncio.run_in_executor if needed.
    # -------------------------------------------------------------------------
    try:
        client = Groq(api_key=settings.groq_api_key)

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
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