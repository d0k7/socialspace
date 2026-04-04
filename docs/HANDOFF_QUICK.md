# SOCIALSPACE — QUICK HANDOFF
# Paste this at the start of every new chat. Full detail in HANDOFF_CURRENT.md.
# Last updated: April 3, 2026

## WHAT IT IS
Multi-platform social media management agent. Backend + React frontend. Currently disconnected — zero real API integration. AI agent not started.

## SYSTEM STATUS
- Frontend build: BROKEN (TypeScript errors across multiple files)
- Frontend dev server: UNVERIFIED
- Backend tests: WORKING (325 passed, 3 warnings)
- Backend as live API: NOT STARTED
- Database: NOT STARTED
- Auth: DEMO MODE ONLY (fake login)
- Real OAuth: NOT STARTED (any platform)
- Real posting: NOT STARTED (any platform)
- AI (Groq/OpenAI): NOT STARTED
- Frontend→Backend calls: NONE (all data is hardcoded mock)

## NEXT TASK
Run create_gitignore.ps1, make first git commit, then fix frontend TypeScript build errors one file at a time starting with AnalyticsPage.tsx.

## TOP WARNINGS
- DO NOT assume frontend build passes — it FAILS
- DO NOT run git add -A without .gitignore committed first (node_modules will be included)
- DO NOT add a 3rd auth/theme/api/composer pattern — consolidate existing duplicates
- DO NOT assume backend is backend/app/routers structure — actual package is socialspace_agent
- BE AWARE platform count is 12 (WeChat is ghost code — remove it)

## 3 MOST DANGEROUS OPEN ISSUES
1. No git commits exist — any crash loses everything
2. Frontend build fails — product cannot be deployed or demoed
3. Auth/API client/composer duplicates — cannot safely add real backend without resolving first

## KEY FILES
- Repo root: C:\Users\dheer\Downloads\socialspace-workspace\socialspace
- Backend: socialspace\backend\socialspace_agent
- Frontend: socialspace\frontend\src
- Run tests (from backend\): ..\venv\Scripts\pytest.exe tests -q
- Run build (from frontend\): npm run build
- Full handoff: socialspace\docs\HANDOFF_CURRENT.md

## SHELL CONVENTION
PowerShell for ALL commands. Always specify which directory to run from.
