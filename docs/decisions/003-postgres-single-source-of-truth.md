# ADR-003: Postgres as single source of truth, not n8n static data

**Status:** Accepted

## Context

n8n can persist small amounts of state between executions via its built-in static
data / data store. Anchor needs to track application status across 5 workflows,
generated materials, grounding citations, agent run history, and weekly insights —
all of which need to be queried, joined, and displayed outside of n8n (the
dashboard).

## Decision

Postgres (`db/schema.sql`, 10 tables) is the single source of truth for all
application/company/material/agent-run state. n8n's own data store is used only for
workflow-internal bookkeeping, never as the record of truth.

## Consequences

- Cross-workflow queries are trivial SQL (e.g. Workflow 4's "find applications past
  their follow-up window", Workflow 5's "aggregate last 4 weeks").
- The `agent_run` table is a queryable audit log of every LLM call — surfaced
  directly in the dashboard's `/decisions` page.
- The dashboard (Day 14) is *just SQL*: Next.js Server Components query Postgres
  directly via a `pg.Pool` singleton (`dashboard/lib/db.ts`), no separate backend API,
  no SSE. This is the most consequential downstream effect of this ADR — an entire
  layer of the stack (backend-for-frontend) doesn't need to exist.
- Trade-off: more upfront setup (schema design, migrations) than relying on n8n's
  built-in storage, and every workflow needs Postgres credentials configured.

## Alternatives Considered

- **n8n static data**: too limited for relational queries and joins across entities
  (company ↔ application ↔ generated_material ↔ agent_run).
- **SQLite**: simpler to set up, but poor concurrent-write behavior under a
  dockerized n8n + dashboard + scheduled workflows all writing at once.
