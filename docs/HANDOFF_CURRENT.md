# SOCIALSPACE MASTER HANDOFF
**Generated:** April 3, 2026 — from uploaded project docs + brutal reality check audit
**Source:** Claude analysis of SOCIALSPACE_CLAUDE_HANDOFF.md, SOCIALSPACE_CODEX_TO_CLAUDE.md, SOCIALSPACE_CLAUDE_DOC_ALIGNMENT.md, SOCIALSPACE_PASTE_TO_CLAUDE.md
**IMPORTANT:** All sections marked UNVERIFIED must be confirmed by running `.\docs\run_verify.ps1`
**Run that script now and paste VERIFICATION_OUTPUT.txt back into a fresh Claude chat to fill gaps.**

---

### SECTION 1 — PROJECT IDENTITY
- Product name: SocialSpace (no confirmed codename; "Neuroplume" mentioned informally)
- What it does RIGHT NOW: A Python backend with 12 platform adapters and a React frontend UI — both currently disconnected from each other, running entirely on mock data
- Vision: A fully autonomous AI agent that manages your entire social media presence across 12 platforms — learns your brand voice, decides what to post, generates content, publishes it, and optimises based on performance without human input
- Target user: Solo content creators burning 10+ hours/week on social media, small businesses that cannot afford a social media manager
- Current phase: Foundation — backend tests pass, frontend build fails, zero real API integration, AI agent not started
- Default shell: PowerShell for ALL commands unless explicitly stated otherwise

---

### SECTION 2 — ENVIRONMENT
- OS: Windows (exact version UNVERIFIED)
- Workspace root: `C:\Users\dheer\Downloads\socialspace-workspace`
- Repo root: `C:\Users\dheer\Downloads\socialspace-workspace\socialspace`
- Backend directory: `C:\Users\dheer\Downloads\socialspace-workspace\socialspace\backend`
- Frontend directory: `C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend`
- Venv directory: `C:\Users\dheer\Downloads\socialspace-workspace\socialspace\venv` (one level above backend)
- Python version: UNVERIFIED — run `python --version`
- Node version: UNVERIFIED — run `node --version`
- Run backend tests: `..\venv\Scripts\pytest.exe tests -q` (run from `socialspace\backend`)
- Start frontend dev: `npm run dev` (run from `socialspace\frontend`)
- Build frontend: `npm run build` (run from `socialspace\frontend`)
- .env files needed: UNVERIFIED — no .env confirmed to exist yet

---

### SECTION 3 — GIT STATUS
- Has commit history: NO — repo has no commits on master. `backend\`, `frontend\`, `venv\` are untracked.
- "NO COMMITS — catastrophic data loss risk on any crash"
- Current branch: master (UNVERIFIED)
- Untracked files: YES — backend, frontend, venv all untracked
- IMMEDIATE ACTION: Run `create_gitignore.ps1` first, then `git add .gitignore && git commit -m "add gitignore"`, then `git add -A && git commit -m "initial snapshot"`

---

### SECTION 4 — SYSTEM STATUS
- Frontend build (npm run build): BROKEN — build fails with TypeScript errors across multiple files
- Frontend dev server (npm run dev): UNVERIFIED — likely starts but may have runtime errors
- Backend test suite (pytest): WORKING — 325 passed, 3 warnings (verified by Codex audit)
- Backend running as live API: NOT STARTED — no FastAPI server has been verified running
- Database (type, exists, tables): NOT STARTED — no database created, no tables, no migrations
- Auth (real JWT or demo mode): BROKEN — frontend AuthContext is demo mode only, no real JWT
- Real OAuth for any platform: NOT STARTED — zero platforms have real OAuth connected
- Real posting to any platform: NOT STARTED — no real API posting verified
- Groq API wired in: NOT STARTED
- OpenAI API wired in: NOT STARTED
- Frontend making real backend calls: NOT STARTED — all data is hardcoded mock
- cli.py exists: MISSING — packaging references `socialspace_agent.cli:main` but file does not exist

---

### SECTION 5 — ACTUAL FILE STRUCTURE
(Run run_verify.ps1 to get the real file list — use that output to replace UNVERIFIED entries below)

socialspace/
  backend/
    socialspace_agent/
      whatsapp/ — EXISTS
      telegram/ — EXISTS
      instagram/ — EXISTS
      discord/ — EXISTS
      reddit/ — EXISTS
      twitter/ — EXISTS
      youtube/ — EXISTS
      facebook/ — EXISTS
      linkedin/ — EXISTS
      tiktok/ — EXISTS
      snapchat/ — EXISTS
      pinterest/ — EXISTS
      (each platform folder contains: adapter, client, models, utils — UNVERIFIED exact files)
      base platform abstraction — EXISTS (exact filename UNVERIFIED)
      platform factory — EXISTS (exact filename UNVERIFIED)
      config system — EXISTS (exact filename UNVERIFIED)
      rate limiting — EXISTS (exact filename UNVERIFIED)
      retry utilities — EXISTS (exact filename UNVERIFIED)
      UnifiedMessage model — EXISTS (exact filename UNVERIFIED)
      exception hierarchy — EXISTS (exact filename UNVERIFIED)
      cli.py — MISSING (confirmed missing by Codex audit)
    tests/ — EXISTS (325 test files confirmed passing)
    requirements.txt — EXISTS (UNVERIFIED exact contents)
    setup.py — EXISTS (UNVERIFIED)
    verify_models.py — EXISTS (UNVERIFIED)
  frontend/
    src/
      pages/
        Auth/LoginPage.tsx — EXISTS
        Auth/RegisterPage.tsx — EXISTS
        Dashboard/DashboardPage.tsx — EXISTS (500+ lines, rebuilt in Session 23)
        Analytics/AnalyticsPage.tsx — EXISTS (has broken components from Session 21)
        Messages/MessagesPage.tsx — EXISTS (real mock UI — inbox, compose, archive, trash)
        Platforms/PlatformsPage.tsx — EXISTS (real mock UI — stats, connection modal)
        Settings/SettingsPage.tsx — EXISTS
        Composer/ComposerPage.tsx — EXISTS (470+ lines)
      components/
        common/ErrorBoundary.tsx — EXISTS
        common/Toast.tsx — EXISTS
        common/LoadingSkeleton.tsx — EXISTS
        common/EmptyState.tsx — EXISTS
        layout/MainLayout.tsx — EXISTS
        settings/AccountSettings.tsx — EXISTS
        settings/NotificationSettings.tsx — EXISTS
        settings/AIPreferences.tsx — EXISTS
        settings/BillingSettings.tsx — EXISTS (explicitly MOCK/DEMO)
        settings/DangerZone.tsx — EXISTS
        (other components — UNVERIFIED)
      contexts/
        ThemeContext.tsx — EXISTS (UNVERIFIED which is canonical)
        AuthContext.tsx — EXISTS (DEMO MODE — no real auth)
      hooks/ — EXISTS (UNVERIFIED exact files)
      routes/lazyRoutes.tsx — EXISTS
      lib/api.ts — EXISTS (needs update for real backend)
      App.tsx — EXISTS
      main.tsx — EXISTS
    package.json — EXISTS
    vite.config.ts — EXISTS
    tsconfig.json — EXISTS
    tailwind.config.js — EXISTS (UNVERIFIED)
  docs/
    CONTINUITY_SYSTEM.md — EXISTS (you are reading it)
    HANDOFF_CURRENT.md — EXISTS (this file)
    HANDOFF_QUICK.md — DOES NOT EXIST YET (created after first session end)
    SOCIALSPACE_BRUTAL_REALITY_CHECK.md — EXISTS
    SOCIALSPACE_MASTER_CONTEXT.md — EXISTS
    run_verify.ps1 — EXISTS
    update_handoff.ps1 — EXISTS
    create_gitignore.ps1 — EXISTS (delete after running once)
  venv/ — EXISTS
  .gitignore — DOES NOT EXIST YET (create by running create_gitignore.ps1)

---

### SECTION 6 — EVERY KNOWN BUG
- frontend/src/pages/Analytics/AnalyticsPage.tsx — some components broken since Session 21. Exact error UNVERIFIED. Fix attempted: NO. Status: OPEN
- frontend build (npm run build) — fails with multiple TypeScript errors across: analytics, charts, composer, dashboard, settings, hooks, routes, auth areas. Exact errors UNVERIFIED — run `npx tsc --noEmit` to see full list. Fix attempted: NO. Status: OPEN
- frontend/src/lib/api.ts — not updated for real backend. Exact issue: unknown token storage assumptions, may conflict with canonical auth. Status: OPEN
- backend/socialspace_agent/cli.py — MISSING. Packaging references it but file does not exist. Fix: create the file or remove the entry point from setup.py. Status: OPEN
- UnifiedMessage.PlatformType includes `wechat` — creates 12 vs 13 platform count inconsistency across codebase. Fix: remove wechat from enum if final decision is 12 platforms. Status: OPEN
- Settings.get_platform_config() — does not cover all 12 platform adapter packages. Which platforms are missing: UNVERIFIED. Status: OPEN
- Pydantic v1-style serialization calls in several backend files — causing 3 deprecation warnings in test run. Files: UNVERIFIED. Fix: update to Pydantic v2 style. Status: OPEN (low risk, tests still pass)

---

### SECTION 7 — UNRESOLVED ARCHITECTURAL CONFLICTS

- **Auth duplication** — context-based AuthContext.tsx powers the routed shell. A store/API-oriented auth system also exists. Canonical: AuthContext.tsx (context-based). Other files: UNVERIFIED exact names. Risk: HIGH — cannot add real JWT until resolved.

- **Theme duplication** — ThemeContext.tsx exists. Hook/store-based theme logic also exists. A separate layout with its own theme handling also exists. Canonical: ThemeContext.tsx. Other files: UNVERIFIED. Risk: MEDIUM — theme drift across pages.

- **API client duplication** — at least two frontend API clients with different token storage assumptions. Canonical: UNVERIFIED — must check which one App.tsx imports. Risk: HIGH — logout behavior and auth persistence are broken until this is resolved.

- **Composer duplication** — multiple ComposerPage implementations exist from parallel development tracks. Canonical: whichever is imported in lazyRoutes.tsx. Others: UNVERIFIED. Risk: MEDIUM — working on wrong file wastes time.

- **Layout overlap** — multiple shell/layout generations coexist from different architectural phases. Canonical: MainLayout.tsx. Others: UNVERIFIED. Risk: LOW — mostly cosmetic but adds confusion.

- **Platform count 12 vs 13** — 12 adapter folders exist. UnifiedMessage.PlatformType includes wechat making it 13 in some places. Decision needed: WeChat stays or goes. Risk: HIGH — causes silent bugs in platform factory and config.

- **Config coverage gap** — Settings.get_platform_config() missing some platforms. Which ones: UNVERIFIED. Risk: MEDIUM — those platforms will silently fail at runtime.

---

### SECTION 8 — LOCKED DECISIONS
- **Frontend framework: React + TypeScript** — FINAL. Rejected: Vue (smaller ecosystem), Angular (too heavy)
- **Backend package structure: socialspace_agent** — FINAL. The FastAPI/app/routers layout described in early sessions does NOT match disk. Actual structure is socialspace_agent with platform subpackages.
- **State management: React Query + context** — FINAL for current phase. Zustand exists in some areas but not canonical.
- **Canonical auth: AuthContext.tsx (context-based)** — FINAL. Other auth patterns to be deleted.
- **Theme: ThemeContext.tsx** — FINAL. Other theme implementations to be deleted.
- **API client: UNVERIFIED which is canonical** — must check App.tsx imports. REVISABLE.
- **Composer: whichever lazyRoutes.tsx imports** — UNVERIFIED exact file. REVISABLE.
- **Database: NOT DECIDED** — PostgreSQL planned, SQLite for dev. Neither implemented.
- **AI provider order: Groq (primary) → OpenAI (fallback) → Claude (ultimate fallback)** — FINAL for roadmap. None implemented yet.
- **Final platform list: 12 platforms** — Pinterest IN, WeChat OUT. FINAL pending cleanup of wechat references in code.
- **Shell convention: PowerShell** — FINAL. All commands use PowerShell syntax.
- **Mock billing only** — FINAL. Stripe not implemented. BillingSettings.tsx is explicitly marked DEMO.

---

### SECTION 9 — PLATFORM STATUS TABLE

| Platform | Adapter Exists | In Config | Real API Tested | Frontend Wired | Notes |
|---|---|---|---|---|---|
| WhatsApp | YES | UNVERIFIED | NO | NO | |
| Telegram | YES | UNVERIFIED | NO | NO | |
| Instagram | YES | UNVERIFIED | NO | NO | |
| Discord | YES | UNVERIFIED | NO | NO | |
| Reddit | YES | UNVERIFIED | NO | NO | |
| Twitter/X | YES | UNVERIFIED | NO | NO | |
| YouTube | YES | UNVERIFIED | NO | NO | |
| Facebook | YES | UNVERIFIED | NO | NO | |
| LinkedIn | YES | UNVERIFIED | NO | NO | |
| TikTok | YES | UNVERIFIED | NO | NO | |
| Snapchat | YES | UNVERIFIED | NO | NO | |
| Pinterest | YES | UNVERIFIED | NO | NO | |
| WeChat | GHOST CODE ONLY | NO | NO | NO | REMOVE — final decision is 12 platforms |

---

### SECTION 10 — LAST SESSION RECORD
- Goal: Set up continuity system so project survives across new chats on free plan
- Files CREATED: docs/CONTINUITY_SYSTEM.md, docs/HANDOFF_CURRENT.md, docs/SOCIALSPACE_BRUTAL_REALITY_CHECK.md, docs/run_verify.ps1, docs/update_handoff.ps1, docs/create_gitignore.ps1
- Files MODIFIED: None (no product code touched)
- Files DELETED: None
- Completed: Full continuity system designed and documented
- Failed: Nothing — this was a planning/documentation session
- Left half-done: Nothing
- Files in broken state: frontend build (pre-existing, not touched this session)

---

### SECTION 11 — NEXT TASK
- Task: Run create_gitignore.ps1, make first git commit, then fix frontend build errors
- First action: Run `.\docs\create_gitignore.ps1` from `socialspace\` root
- First command sequence:
  ```powershell
  cd C:\Users\dheer\Downloads\socialspace-workspace\socialspace
  .\docs\create_gitignore.ps1
  git add .gitignore
  git commit -m "add gitignore"
  git add -A
  git commit -m "initial project snapshot"
  ```
- Then run `run_verify.ps1` and paste output into a fresh Claude chat
- Then in that chat: "Fix ONLY the TypeScript errors in AnalyticsPage.tsx first. One file only."
- Success: `npm run build` completes with zero errors
- Verify: Run `npm run build` — it should exit with code 0 and output a dist/ folder

---

### SECTION 12 — NEVER DO THESE THINGS
- DO NOT run `git add -A` without `.gitignore` in place — will try to commit node_modules (100k+ files) and hang
- DO NOT paste full 300+ line files into Claude — paste only the broken section
- DO NOT ask Claude to fix multiple files in one message — one file at a time
- DO NOT trust old Claude chat claims about file structure without verifying with run_verify.ps1
- DO NOT add a third auth implementation — consolidate the two that exist first
- DO NOT build new features while the frontend build is failing — fix the build first
- DO NOT reuse a slow lagging chat — open a new one, paste the quick handoff, continue

---

### SECTION 13 — FRONTEND PAGE STATUS

| Page | File Path | Build Error | Works in Dev | Data Source | Notes |
|---|---|---|---|---|---|
| Login | pages/Auth/LoginPage.tsx | UNVERIFIED | UNVERIFIED | Mock/Demo | Demo auth only |
| Register | pages/Auth/RegisterPage.tsx | UNVERIFIED | UNVERIFIED | Mock/Demo | Demo auth only |
| Dashboard | pages/Dashboard/DashboardPage.tsx | UNVERIFIED | LIKELY YES | Mock | 500+ lines, rebuilt S23 |
| Analytics | pages/Analytics/AnalyticsPage.tsx | LIKELY YES | UNVERIFIED | Mock | Broken components since S21 |
| Messages | pages/Messages/MessagesPage.tsx | UNVERIFIED | LIKELY YES | Mock | Real mock UI, not placeholder |
| Platforms | pages/Platforms/PlatformsPage.tsx | UNVERIFIED | LIKELY YES | Mock | Real mock UI, not placeholder |
| Settings | pages/Settings/SettingsPage.tsx | UNVERIFIED | LIKELY YES | Mock | 6 components, billing is demo |
| Composer | pages/Composer/ComposerPage.tsx | UNVERIFIED | LIKELY YES | Mock | Duplicate exists — check lazyRoutes |

---

### SECTION 14 — DEMO MODE TRACKER

| File/Component | What it fakes | Real implementation needed | Priority |
|---|---|---|---|
| AuthContext.tsx | Entire auth system — login always succeeds | Real JWT auth against backend | HIGH |
| DashboardPage.tsx | All stats (followers, posts, engagement) hardcoded | Real API calls to backend analytics | HIGH |
| ComposerPage.tsx | Post creation — does not actually post | Real OAuth + platform API posting | HIGH |
| BillingSettings.tsx | Payment/subscription — all fake | Real Stripe integration (out of scope for MVP) | LOW |
| PlatformsPage.tsx | Connection state — mock toggle only | Real OAuth flow per platform | HIGH |
| MessagesPage.tsx | All messages hardcoded | Real message fetch from platform adapters | MEDIUM |
| AnalyticsPage.tsx | All charts use hardcoded data | Real analytics from backend | MEDIUM |
| lib/api.ts | API base URL pointing to nothing useful | Point to real running backend | HIGH |

---

### SECTION 15 — DEPENDENCY WARNINGS
- Pydantic: v1-style serialization calls causing 3 deprecation warnings in backend test run. Tests still pass. Fix before v2 becomes strict.
- Frontend packages: UNVERIFIED — run `npm audit` from frontend dir to check
- Backend packages: UNVERIFIED — check requirements.txt against actual imports
- Missing from packaging: cli.py referenced in setup.py entry points but file does not exist

---

### SECTION 16 — SESSION HISTORY
- Sessions 1-14 — Backend development: platform adapters, models, config, rate limiting, retry utils
- Sessions 15-20 — Frontend foundation: React/TypeScript setup, routing, component structure
- Session 21 — Analytics dashboard: 7 components built, some broken
- Session 22 — Settings system: 6 components, 2000+ lines
- Session 23 — UI polish + foundation: auth demo, dashboard rebuilt, composer built, routing fixed
- Session 24 — Backend audit planned (Codex ran it instead, found 325 passing tests)
- April 3 2026 — Continuity system built, brutal reality check written, no product code changed

---

### SECTION 17 — WARNINGS FOR NEXT CLAUDE
- DO NOT assume the frontend build passes — it currently FAILS
- DO NOT assume MessagesPage or PlatformsPage are placeholders — they have real mock UIs
- DO NOT assume backend structure is backend/app/routers — actual package is socialspace_agent
- DO NOT assume backend has PostgreSQL, JWT, or Celery implemented — none are verified
- DO NOT add a third auth/theme/api/composer implementation — consolidate the two that exist
- DO NOT run git add -A without .gitignore being committed first
- BE AWARE platform count is inconsistent — 12 adapter folders but wechat ghost in enum
- BE AWARE the CLI entry point (cli.py) is missing — do not reference it
- BE AWARE all frontend data is mock — no real API calls anywhere
- BE AWARE HANDOFF_QUICK.md does not exist yet — create it after first session end or ask Claude to generate it from this document

---

### SECTION 18 — CONFIDENCE RATINGS
- Section 1 (identity): HIGH
- Section 2 (environment): MEDIUM — paths from docs, versions UNVERIFIED
- Section 3 (git): HIGH — confirmed no commits by Codex audit
- Section 4 (system status): HIGH — test results and build failure verified by Codex
- Section 5 (file structure): MEDIUM — platform folders confirmed, exact filenames UNVERIFIED
- Section 6 (bugs): MEDIUM — known bugs from audit, exact line numbers UNVERIFIED
- Section 7 (conflicts): HIGH — confirmed by Codex audit
- Section 8 (decisions): HIGH — confirmed from project docs
- Section 9 (platforms): HIGH for existence, LOW for config coverage
- Section 10 (last session): HIGH — this session
- Section 11 (next task): HIGH
- Section 12 (never do): HIGH
- Section 13 (page status): MEDIUM — existence confirmed, build errors UNVERIFIED
- Section 14 (demo tracker): HIGH
- Section 15 (dependencies): LOW — UNVERIFIED, needs npm audit and pip check
- Section 16 (history): HIGH — from project docs
- Section 17 (warnings): HIGH
- Section 18 (this): HIGH

**Single most dangerous unresolved issue right now:** No git commits exist — any system crash, accidental deletion, or bad file overwrite has no recovery point.
