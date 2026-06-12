# Future / Out of Scope

Every "but what if it also..." idea goes here. Not implemented. Not discussed during the
18-day build. See `docs/planning/anchor_planning.md` §17 (Non-Goals) before adding anything.

(Nothing parked here yet.)

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
