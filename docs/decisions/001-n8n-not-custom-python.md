# ADR-001: Use n8n, not custom Python, for orchestration

**Status:** Accepted

## Context

The orchestration logic (5 workflows: intake, job processing, match & generate,
follow-up scheduling, weekly reflection) could be written as a FastAPI service with
Celery for async/scheduled work.

## Decision

Use n8n as the orchestration layer. AI logic (prompt construction, structured-output
validation, disk caching) lives in a small Python/FastAPI wrapper (`llm/`); n8n calls
that wrapper over HTTP and handles state transitions, scheduling, Wait/Resume,
integrations (Drive, Notion, Slack), and error paths.

## Consequences

- The visual workflow canvas is itself a portfolio asset — exported JSON in
  `n8n/workflows/` and canvas screenshots in `docs/canvas-screenshots/` tell the
  architecture story to anyone who knows n8n at a glance.
- AI logic stays cleanly separated from orchestration logic, so prompt/schema changes
  (`prompts/`, `llm/schemas.py`) don't require touching workflow JSON unless the
  contract shape changes.
- Trade-off: workflow logic is split across JSON (n8n) and Code nodes (JavaScript),
  which is less ergonomic to test than pure Python — addressed by extracting Code
  node `jsCode` and unit-testing it directly (see `scripts/test_*_codenodes.js`).

## Alternatives Considered

- **Custom FastAPI + Celery**: more familiar tooling, but loses the visual showcase
  and requires building scheduling/retry/Wait-for-human primitives from scratch.
- **Temporal**: powerful workflow engine, but overkill for a solo personal project
  and adds significant operational complexity.
