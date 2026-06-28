# ADR-004: Manual URL paste, not job-board scraping

**Status:** Accepted

## Context

A pipeline that automatically discovers and scrapes new job postings (LinkedIn,
Greenhouse/Lever boards, aggregators) would demo as more "autonomous" and arguably
more useful day-to-day.

## Decision

Anchor only accepts a manually-pasted job posting URL via `POST /webhook/intake`
(Workflow 1). No scrapers, no aggregators, no scheduled discovery of new postings.

## Consequences

- Scope stays bounded — intake is a URL-format check plus an informational
  ATS-host detection (Greenhouse/Lever/Workday), not a scraping system that needs to
  keep up with site changes, logins, or anti-bot measures.
- The orchestration story — multi-source company research, critique, grounded
  generation, follow-up, reflection — is the actual project, and isn't drowned out by
  scraper fragility/maintenance.
- Workflow 2's "Derive Research URLs" step still does lightweight, targeted fetches
  (homepage, about page, careers board, news RSS) *for the one company in the pasted
  posting* — this is research support for an already-identified job, not discovery.
- A bookmarklet/extension for one-click paste-from-browser is recorded in
  [FUTURE.md](../../FUTURE.md), not built in this version.

## Alternatives Considered

- **LinkedIn scraping**: hostile to LinkedIn's terms of service and legally grey;
  rejected outright.
- **Aggregator APIs** (e.g. paid job-board APIs): real cost, and reintroduces the
  "search the internet for jobs" scope explicitly excluded in the planning doc's
  Non-Goals (§17) — Anchor processes jobs the user has already found, it doesn't find
  them.
