# Future / Out of Scope

Every "but what if it also..." idea goes here. Not implemented. Not discussed during the
18-day build. See `docs/planning/anchor_planning.md` §17 (Non-Goals) before adding anything.

## Multi-user support
- Sign-up page (not just login)
- `user_id` column on `application`, `master_resume_entry`, `user_profile`, `generated_material`, `agent_run`
- Per-user data isolation — each user sees only their own applications and resume
- Session-based user context passed through to n8n webhook
- Postgres Row-Level Security or query-level filtering

## Multi-profile resumes
- `resume_profile` table (e.g. "AI/ML", "PM", "Backend") linking to subsets of `master_resume_entry` rows
- Profile selector on intake form — choose which resume profile to use for this application
- Pipeline filters entries by selected profile before passing to Resume Critic/Tailorer

## Stronger LLM integration
- Config switch to use Claude/GPT-4 via API for higher-quality resume tailoring and grounding checks
- qwen2.5:7b can't reliably do semantic text comparison (grounding critic) or produce full-page structured resumes
- One-line change: `OLLAMA_MODEL` in `.env` or add `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`

---

## Infra TODO (not scope creep — deferred setup tasks)

### Docker Day (target: before Day 12 freeze point)

**Status:** Deferred from Day 1. Postgres + n8n run natively for dev speed;
`docker-compose.yml` was written on Day 1 but not yet run (Docker Desktop not installed).

**Done looks like:**
- [ ] Docker Desktop installed and running (`brew install --cask docker`, then launch once)
- [ ] `docker compose up` starts `postgres`, `n8n`, `llm-wrapper` with no manual steps
- [ ] `db/schema.sql` auto-applies via `/docker-entrypoint-initdb.d` — verify all 10 tables exist:
      `docker compose exec postgres psql -U anchor -d anchor -c "\dt"`
- [ ] n8n UI reachable at `localhost:5678`, can recreate the Postgres credential
      against the dockerized db
- [ ] `llm-wrapper` reachable at `localhost:8001/health` and `/complete` works
      (talks to host Ollama via `host.docker.internal`)
- [ ] Native Postgres/n8n stopped (`brew services stop postgresql@16`, kill any
      running `npx n8n`) to avoid port conflicts during the docker test
- [ ] Document any divergence between native and docker-compose configs found
      during this exercise (update `docker-compose.yml` / `.env.example` accordingly)
