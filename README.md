# OI Pulse — Fleet & Logistics

Multi-tenant transport management SaaS: React + TypeScript + Vite frontend, FastAPI + MongoDB backend.

## Prerequisites

- Node 20+
- Python 3.12+
- MongoDB 7+ (or Docker)

## Setup

```bash
cp .env.example .env
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' ../.env | xargs)
RUN_SEED=true uvicorn app.main:app --reload --app-dir .
# frontend
cd ../frontend
npm install
npm run dev
```

Demo users (seed only, development):

- Platform: `platform@oi-pulse.local` / `Platform@123`
- Owner: `owner@demo.local` / `Owner@123`
- Deewanji: `deewanji@demo.local` / `Deewanji@123`

## Commands

Backend tests: `cd backend && pytest`  
Frontend build: `cd frontend && npm run build`  
Frontend tests: `cd frontend && npm test`

## Production

`docker compose up --build`

See `docs/` for architecture, database, API, security, and deployment.
