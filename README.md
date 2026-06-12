# Anchor

A personal, n8n-orchestrated AI pipeline that takes a job-posting URL and produces a
researched, factually-grounded application (tailored resume, cover letter, LinkedIn
message, skill gap report) for review in Notion — plus role discovery, follow-up
scheduling, and weekly reflection.

Full design: [`docs/planning/anchor_planning.md`](docs/planning/anchor_planning.md)
(authoritative — supersedes `anchor_phase_0.md`).

## Status

Day 1 of the 18-day build: infra bootstrap. Postgres schema applied, LLM wrapper
(Ollama + disk cache) running, n8n running locally. No workflows yet.

## Local Setup (current — native, no Docker)

### 1. Postgres
```bash
brew install postgresql@16
brew services start postgresql@16
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
createdb anchor
psql -d anchor -f db/schema.sql
```

### 2. LLM wrapper (Ollama + FastAPI + disk cache)
Requires Ollama running locally with `qwen2.5:7b` pulled (`ollama pull qwen2.5:7b`).

```bash
~/.pyenv/versions/3.11.9/bin/python3 -m venv .venv
.venv/bin/pip install -r llm/requirements.txt
.venv/bin/uvicorn llm.server:app --reload --port 8001
```

Verify:
```bash
curl localhost:8001/health
curl -X POST localhost:8001/complete -H "Content-Type: application/json" \
  -d '{"prompt": "Say hello in exactly 3 words."}'
```

### 3. n8n
```bash
npx n8n start
```
Editor at http://localhost:5678.

## Docker (future)

`docker-compose.yml` bundles `postgres` + `n8n` + `llm-wrapper`, with `db/schema.sql`
auto-applied on first Postgres init. Not yet activated — see `FUTURE.md` → "Docker Day".

## Environment

Copy `.env.example` to `.env` and adjust as needed.
