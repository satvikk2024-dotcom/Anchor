# ADR-002: Use Ollama (qwen2.5:7b) local, not a paid LLM API

**Status:** Accepted

## Context

Every agent in Anchor (JD Parser, Company Synthesizer, Resume Critic, Match Scorer,
Resume Tailorer, Grounding Critic, Cover Letter, LinkedIn Drafter, Skill Gap Analyzer,
Follow-up Decision, Pattern Detector) needs an LLM call. Claude/GPT-4-class models
would produce noticeably higher-quality structured output with less prompt
engineering.

## Decision

All agent calls go through the `llm/` wrapper to a local Ollama instance running
`qwen2.5:7b`, adapted from Meridian's wrapper (same disk-cache-by-`(model, prompt,
system, json_mode)` pattern, trimmed config). No paid LLM API calls anywhere in the
build.

## Consequences

- Zero marginal cost per application generated — important for a tool used daily
  across an entire internship search.
- "Cost-engineering under a weak model" becomes its own interview signal: every
  prompt-reliability bug found during smoke testing (char limits, enum drift,
  days-vs-window numeric reasoning, JSON-citation leakage into prose) was fixed by
  *tightening the prompt's field rules*, not by upgrading the model — a discipline
  that transfers directly to cost-constrained production systems.
- Trade-off: prompt design has to be considerably more rigorous and defensive than it
  would be against a frontier model. Pydantic schema validation
  (`llm/schemas.py`) plus the project's standing rule — fix unreliable structured
  output via prompt tightening and re-test, never by relaxing the schema — absorbs
  this cost. The Material Quality eval (Day 15/16,
  [eval/results_summary.md](../../eval/results_summary.md)) measures how well that
  discipline holds up at scale.

## Alternatives Considered

- **Gemini Flash free tier**: free, but rate-limited and requires API key management
  — adds an external dependency and a credential to track for a tool meant to run
  unattended.
- **Paid APIs (Claude/GPT-4)**: best quality, but real per-call cost across hundreds
  of agent calls during development and daily personal use; rejected for this build.
