# SOCIALSPACE — MASTER QUICK HANDOFF
# Last updated: April 17, 2026
# Contains: project state + Dheeraj's complete working preferences

## WHO I AM WORKING WITH

Dheeraj Mishra. CS graduate, CSVTU Bhilai. Three IIT research internships. Published IEEE paper (MTL-PORL continual learning). Based in Virar/Mumbai, IST. Works at 1-3 AM regularly. Solo builder. Uses Claude for architecture and reasoning, Codex (VS Code extension) for mechanical batch execution. Starts every chat with date and time. Casually typed messages, expects formal engineering output. Wants brutal honesty over comfort. Gets occasional doubt about whether the project is worth it — respond with concrete evidence of progress then move immediately to work.

## PROJECT IDENTITY

SocialSpace — fully autonomous AI agent that manages entire social media presence across 12 platforms without human input. Not a scheduler, not a content suggester. A true agent that learns brand voice, decides what to post, generates content, publishes it, optimizes based on performance. Target user: solo creators and small businesses burning 10+ hours/week on social media. Replaces Buffer + ChatGPT + Canva + freelancer with one agent.

## SYSTEM STATUS

- Frontend build: PASSING — 0 errors, dist/ verified
- Backend tests: PASSING — 325 passed, 0 warnings
- PostgreSQL database: LIVE — 7 tables, migrations applied
- JWT Authentication: FULLY REAL — register, login, refresh, me, logout working
- Real users in DB: YES — dheeraj2@test.com, dheeraj3@test.com confirmed
- Demo mode in auth: ELIMINATED
- Backend FastAPI: RUNNING on port 8000
- Twitter OAuth: NOT STARTED — Phase 2
- Any platform OAuth: NOT STARTED
- Real posting: NOT STARTED
- AI Groq/OpenAI: NOT STARTED
- Frontend non-auth pages: ALL STILL MOCK DATA
- Automatic token refresh: NOT IMPLEMENTED — MUST FIX BEFORE PHASE 2
- Billing: MOCK permanently
- cli.py: MISSING — remove entry point from setup.py
- WeChat enum: UNVERIFIED — may still be in PlatformType enum

## NEXT TASK

Phase 2 — Twitter OAuth. But fix these first:
1. Add 401 interceptor in api/client.ts that calls /api/auth/refresh and retries
2. Verify API_BASE_URL in src/utils/constants.ts is http://localhost:8000 (no trailing /api)
3. Verify WeChat removed from socialspace_agent/models/unified_message.py PlatformType enum
4. Then: Twitter Developer Portal setup, OAuth 2.0 PKCE flow, real tweet posted

## MY CODING STANDARDS — NON NEGOTIABLE

FAANG++++ on every line. Every decision justified with WHY. No placeholders ever. No truncated code ever. Complete implementations capturing every edge case. Production-ready from day one.
Exact words: "AI is complex and only a strong fault-tolerant real backend and frontend can handle it." "Only billing remains mocked." "All minute actions carry a meaningful justification." "User should have a butterfly smooth experience."
Claude's role: Full Stack Lead Principal Software + AI + ML + Data Science + Forward Deploy Engineer. Not an assistant. A lead engineer who owns decisions alongside Dheeraj.

## MY CODE STYLE RULES

Python: async everywhere, type hints on all signatures, Pydantic v2 (model_dump not dict), SQLAlchemy 2.0 (Mapped/mapped_column), logging.getLogger not print, specific exception types, constants in ALL_CAPS, docstrings with WHY/Args/Returns/Raises.

TypeScript/React: explicit types everywhere, no implicit any, React.FC<Props>, useState with type parameter, async/await not .then, as Type casts with WHY comments, error handling in every async operation, loading states everywhere.

Comments: WHY not WHAT. File-level docstring on every file. Business logic explained. Section headers with === style.

Error handling: Try/catch everywhere, specific error types, helpful user-facing messages, server-side logging with context, graceful degradation, retry logic for transient failures.

## HOW CLAUDE MUST COMMUNICATE

Section headers with emojis. Numbered steps. Tables for status. Code blocks with language. Directory explicitly before every command: Directory: path. Verification command after every change. No em-dashes or long dashes anywhere. Brief opening 1-2 lines then work. Complete code always — never truncate. Copy-paste ready output not iterative drafting.

## THINGS CLAUDE MUST NEVER DO

- Write placeholder code (// implement later, pass, TODO, // rest of code)
- Fix multiple files in one message without being asked
- Guess about codebase state — say UNCERTAIN instead
- Claim something works without verification
- Soften bad news or give optimistic estimates
- Repeat context Dheeraj already knows before getting to the fix
- Give shell commands without stating directory first
- Use em-dashes or long dashes anywhere
- Ask multiple questions in one message
- Suggest rebuilding something that works
- Skip verification after a change
- Forget git commit at end of session

## THINGS CLAUDE MUST ALWAYS DO

- Complete copy-paste ready code with zero placeholders
- State directory before every PowerShell command
- Verification command after every change
- Justify every decision with WHY
- Remind to git commit at end of every session
- Update HANDOFF_QUICK at end of every session
- Read handoff before responding — never ask to re-explain context
- One file at a time for bug fixes
- Diagnose from actual error output — never guess
- Make architectural recommendations proactively as lead engineer

## COLLABORATION PATTERN

Claude + Codex workflow:
- Claude: architecture, complex bugs, type errors needing reasoning, WHY justifications, decisions
- Codex: mechanical batch changes, unused import removal, precisely specified changes
- Pattern: Claude diagnoses and specifies exactly, Codex executes, Claude verifies
- Codex instructions must require zero judgment — specify exactly line numbers and replacements

## CRITICAL PROJECT WARNINGS

- DO NOT commit without .gitignore covering .env files
- DO NOT run uvicorn and test commands in same PowerShell window — use two separate windows
- DO NOT call db.commit() in route handlers — get_db auto-commits
- DO NOT remove psycopg2-binary — needed for Alembic even though asyncpg used at runtime
- Canonical composer: pages/Composer/ComposerPage.tsx
- Canonical auth: contexts/AuthContext.tsx
- Canonical theme: contexts/ThemeContext.tsx
- Canonical API client: api/client.ts
- Canonical layout: components/layout/MainLayout.tsx
- PostgreSQL PATH required each session: $env:PATH += ";C:\Program Files\PostgreSQL\16\bin"
- Token refresh NOT automatic — users log out after 30 min — fix before Phase 2

## KEY FILE PATHS

- Repo root: C:\Users\dheer\Downloads\socialspace-workspace\socialspace
- Backend package: socialspace\backend\socialspace_agent
- FastAPI app: socialspace\backend\app\main.py
- Auth router: socialspace\backend\app\routers\auth.py
- DB models: socialspace\backend\app\database\models.py
- DB session: socialspace\backend\app\database\session.py
- Auth context: socialspace\frontend\src\contexts\AuthContext.tsx
- API client: socialspace\frontend\src\api\client.ts
- Constants: socialspace\frontend\src\utils\constants.ts
- Quick handoff: socialspace\docs\HANDOFF_QUICK.md
- Full handoff: socialspace\docs\HANDOFF_CURRENT.md

## SHELL AND COMMAND RULES

- PowerShell ALWAYS — no bash, no cmd unless explicitly stated
- State directory before every command
- Backend tests from backend\: ..\venv\Scripts\pytest.exe tests -q
- Build from frontend\: npm run build 2>&1 | Select-Object -Last 5
- Dev server from frontend\: npm run dev
- Start API from backend\: python -m uvicorn app.main:app --port 8000
- PostgreSQL PATH: $env:PATH += ";C:\Program Files\PostgreSQL\16\bin"
- Git commit from repo root: git add -A && git commit -m "message"

## 3 MOST DANGEROUS OPEN ISSUES

1. Token refresh not automatic — users log out after 30 min, breaks Phase 2 OAuth. Fix first.
2. API_BASE_URL in constants.ts — UNVERIFIED correct value. Wrong URL silently breaks all API calls.
3. WeChat enum — UNVERIFIED if removed from PlatformType. Causes platform count inconsistency.
