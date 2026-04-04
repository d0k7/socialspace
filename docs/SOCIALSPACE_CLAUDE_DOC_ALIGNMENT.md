# SocialSpace Claude Doc Alignment Notes

Generated: 2026-03-31  
Purpose: Reconcile Claude's planning document with the actual repo snapshot on disk.

## How To Use This File

Claude's generated project document is useful, but it mixes three different kinds of information:

- real current repo state
- intended architecture and roadmap
- assumptions that do not match the current codebase

This file separates those so future work does not drift.

## Short Verdict

Claude's document is strong as:

- a product vision document
- a roadmap document
- a standards and workflow document

Claude's document is not safe to use as the sole source of truth for current implementation status.

The best working model is:

- use Claude's document for vision, standards, and roadmap
- use `SOCIALSPACE_MASTER_CONTEXT.md` and `SOCIALSPACE_CODEX_TO_CLAUDE.md` for repo reality

## What Claude's Document Gets Right

These parts align well with the current project direction and should be kept:

- the user wants a high-quality, multi-platform social management product
- PowerShell should be the default command style
- shared documentation between assistants is important
- demo mode versus real integration should be clearly distinguished
- the project needs a disciplined handoff protocol
- roadmap thinking is useful here because the project has grown across many iterative sessions

Claude's document is especially valuable as a planning artifact for:

- future AI integration
- production architecture aspirations
- engineering standards
- development workflow

## What Needs Correction Against The Actual Repo

### 1. Backend Structure Is Not `backend/app`

Claude's document describes a FastAPI-style tree like:

- `backend/app/main.py`
- `backend/app/routers`
- `backend/app/models`
- `backend/app/services`

That is not the current backend structure on disk.

The actual backend root contains:

- `socialspace_agent`
- `tests`
- `README.md`
- `requirements.txt`
- `setup.py`
- `verify_models.py`

The real backend package is:

- `socialspace/backend/socialspace_agent`

### 2. Backend Has Been Run And Verified

Claude's document says the backend has never been run or tested and that Session 24 should verify it.

That is no longer true for the current audited snapshot.

Direct verification already performed:

From `socialspace/backend`, this PowerShell command was run:

```powershell
..\venv\Scripts\pytest.exe tests -q
```

Observed result:

- `325 passed`
- `3 warnings`

So the backend is not "unknown" in the broad sense described by Claude's doc.

### 3. Messages Page Is Not A Placeholder

Claude's document says:

- `MessagesPage.tsx` is placeholder only

That does not match the current file on disk.

The current `MessagesPage.tsx` includes:

- inbox tab
- compose tab
- archive tab
- trash tab
- local mock message state
- mark-as-read behavior
- archive/restore/delete behavior
- auto-trash cleanup

It is still mock-driven, but it is not a placeholder page.

### 4. Platforms Page Is Not A Placeholder

Claude's document says:

- `PlatformsPage.tsx` is placeholder only

That does not match the current file on disk.

The current `PlatformsPage.tsx` includes:

- platform stats
- connection modal flow
- mock connection state
- refresh/test/connect/disconnect style interactions

It is not fully backend-integrated, but it is more than a placeholder.

### 5. Backend Database / FastAPI / JWT / Celery Claims Are Not Current Verified Facts

Claude's document presents several backend choices as if they are the current implemented stack:

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT auth
- Celery + Redis

Those may be valid roadmap intentions, but they are not the best description of the current backend snapshot that was audited.

The real current backend is centered around:

- normalized multi-platform models
- platform clients and adapters
- config
- rate limiting
- retries
- tests

So those infrastructure claims should be treated as planned architecture unless directly verified in code.

### 6. The Platform Story Is More Complicated Than Claude's Doc Shows

Claude's document names only a subset of likely target platforms in the overview sections.

The current repo reality is:

- 12 concrete platform packages are implemented in the backend
- frontend constants also support 12
- but docs/models/tests still contain a WeChat inconsistency that makes the codebase read like 12 in some places and 13 in others

This mismatch is one of the most important cleanup items.

### 7. Frontend Is Not 90 Percent Complete In A Build-Clean Sense

Claude's document says frontend is 90 percent complete.

That may be a morale or roadmap framing, but it is not a safe statement of current repo readiness.

During audit, this PowerShell command was run from `socialspace/frontend`:

```powershell
npm run build
```

Observed result:

- build failed

So a better statement is:

- the frontend has broad product surface area
- but it is not currently in a clean buildable TypeScript state

### 8. The Repo Already Has Documentation Now

Claude's document treats docs as uncertain.

Current docs now include:

- `SOCIALSPACE_MASTER_CONTEXT.md`
- `SOCIALSPACE_CLAUDE_HANDOFF.md`
- `SOCIALSPACE_CODEX_TO_CLAUDE.md`
- this alignment note

## Best Combined Working Model

To keep both assistants aligned, use the documents this way:

### Use Claude's Document For

- project ambition
- roadmap planning
- standards
- long-term architecture goals
- working style expectations

### Use Codex Audit Documents For

- current repo structure
- current implementation reality
- current verification status
- known inconsistencies
- what was directly checked in the codebase

## Recommended Shared Source Of Truth Rule

When there is a conflict:

1. Current code on disk wins over memory.
2. Fresh command output wins over older assistant claims.
3. Claude's document should be treated as roadmap plus intent unless a detail is verified.
4. Codex audit docs should be treated as current-state documentation for this snapshot.

## Suggested Message Back To Claude

If you want a short direction to give Claude, this is the right framing:

"Use your project document as the roadmap and intent layer, but please align implementation decisions to `SOCIALSPACE_CLAUDE_HANDOFF.md`, `SOCIALSPACE_CODEX_TO_CLAUDE.md`, and `SOCIALSPACE_MASTER_CONTEXT.md` because those were written from the current repo snapshot and direct verification commands."

## Final Alignment Summary

Claude's document is valuable and worth keeping. It just should not be treated as a literal description of the current codebase without reconciliation. The strongest setup is to combine:

- Claude for long-horizon roadmap and project leadership
- Codex audit docs for repo-grounded reality

That gives you the smoothest multi-assistant workflow.
