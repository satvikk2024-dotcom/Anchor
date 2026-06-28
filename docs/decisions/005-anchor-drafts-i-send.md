# ADR-005: Anchor drafts; I send — no auto-submit, ever

**Status:** Accepted

## Context

A headless browser could fill out and submit ATS application forms (Greenhouse,
Lever, Workday) automatically, completing the "URL in → application sent" loop with
zero manual steps.

## Decision

Anchor never submits applications. Workflow 3 ends at `status = 'awaiting_review'`
with all materials (tailored resume PDF, cover letter PDF, LinkedIn message, skill
gap report) exported to Drive + a Notion page for manual review. The user reviews and
sends manually; only then is the application's status moved to `submitted` (which
then feeds Workflow 4's follow-up scheduler).

## Consequences

- This is a hard safety boundary that removes entire categories of failure outright:
  wrong company, a broken/garbled PDF, an ATS form filled with stale or mismatched
  data, a tailored resume that slipped past the Grounding Critic with an overstated
  claim — none of these can become a *sent* application, because nothing is sent
  without a human looking at it first.
- Keeps the user in the loop at exactly the point where judgment matters most
  (deciding whether *this specific* tailored material represents them well), while
  automating everything that's pure research/drafting/formatting toil.
- Composes with the match-score gate (score < 60 → Slack + Wait for Decision) and the
  Grounding Critic's retry-then-escalate behavior — every "are we sure about this?"
  moment in the pipeline resolves to "ask the human," never "proceed anyway."
- Trade-off: the ~8-minute review step (per the planning doc's headline ~90min →
  ~8min compression) is irreducible by design — it is not a v2 feature to automate
  away.

## Alternatives Considered

- **Auto-submit via headless browser**: rejected on both safety grounds (above) and
  scope grounds — it's explicitly listed in the planning doc's Non-Goals (§17) as
  something Anchor will not do in this build, full stop.
