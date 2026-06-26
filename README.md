# SocialSpace

An autonomous AI social media management agent that manages your entire 
social media presence across multiple platforms without constant human input.

## What it does

- Connects to Telegram, Discord, Twitter, and Reddit
- Generates AI content variations via Groq (llama-3.3-70b-versatile)
- Posts to multiple platforms simultaneously from a single composer UI
- Learns brand voice and schedules posts autonomously (in progress)

## Tech Stack

**Backend:** Python, FastAPI, PostgreSQL, SQLAlchemy 2.0 async, Alembic, JWT auth  
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Query  
**AI:** Groq API (primary), OpenAI (fallback), Anthropic Claude (fallback)  
**Platforms:** Telegram Bot API, Discord Bot API, Twitter OAuth 2.0 PKCE, Reddit OAuth 2.0

## Architecture
socialspace/

├── backend/

│   ├── app/                  # FastAPI web server

│   │   ├── routers/          # Platform endpoints (twitter, telegram, discord, reddit, ai)

│   │   ├── auth/             # JWT authentication

│   │   └── database/         # SQLAlchemy models + Alembic migrations

│   └── socialspace_agent/    # Platform adapter library (importable, independently testable)

└── frontend/

└── src/

├── pages/            # Composer, Platforms, Dashboard, Analytics

├── api/              # Typed API client with automatic token refresh

└── contexts/         # Auth, Theme


## Current Status

| Feature | Status |
|---|---|
| JWT Authentication | Live |
| Telegram posting | Live |
| Discord posting | Live |
| Twitter OAuth 2.0 PKCE | Live (posting requires paid API tier) |
| Reddit OAuth 2.0 | Built, pending API approval |
| AI content generation | Live (Groq) |
| Scheduling engine | In progress |
| Brand voice learning | Planned |

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Copy `backend/.env.example` to `backend/.env` and fill in your credentials.

## Author

Dheeraj Mishra — https://github.com/d0k7
