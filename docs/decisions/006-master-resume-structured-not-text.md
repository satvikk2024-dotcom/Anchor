# ADR-006: Master resume as structured data, not a text blob

**Status:** Accepted

## Context

The simplest way to give the Resume Tailorer agent "everything about the candidate"
is a single text blob (the literal resume PDF/Markdown), passed in full as context on
every tailoring call.

## Decision

Decompose the master resume into typed `master_resume_entry` rows (one of
`experience | project | skill | education | achievement`, each with a
`canonical_text` and a stable UUID), plus a single `user_profile` row for
goals/preferences. The Resume Tailorer must cite a `master_resume_entry_id` for every
line it produces; the Grounding Critic checks each cited line against *that specific
entry's* `canonical_text`.

## Consequences

- Tailoring becomes a **selection + rephrasing** operation over addressable facts,
  not free-form rewriting — the same architectural move that made Meridian's citation
  grounding work, applied here to generation instead of research.
- The Grounding Critic can verify structurally: "does tailored line N's claim follow
  from entry `<uuid>`'s text?" — a per-line, per-entry check — rather than "does this
  resume sound plausible given the candidate's general background?"
- Every accepted tailored resume line has a `material_grounding` row (FK to both the
  generated material and the source `master_resume_entry`), making "where did this
  line come from?" a one-hop join — visible in the dashboard's `/decisions` audit log
  and reusable by the eval framework (`eval/benchmark.py`) for an apples-to-apples
  grounding check against the baseline.
- Trade-off: seeding the master resume is more work than pasting a resume file —
  each fact has to be decomposed into its own row up front (`db/seed_master_resume.sql`).

## Alternatives Considered

- **Single text blob**: rejected — gives the Grounding Critic no structural handle to
  check against; "is this true?" degrades into "does this sound consistent with the
  rest of the document?", which is exactly the check that lets hallucinated resume
  lines slip through (the failure mode the eval's baseline,
  `prompts/baseline_tailor.md`, is designed to measure).
