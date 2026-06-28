# Anchor

Personal AI job-application pipeline (formerly "Atlas") for the 2026 internship search.
Paste a job URL → n8n researches the company, scores the match against a master resume,
drafts a tailored resume + cover letter + LinkedIn message + skill-gap report, and puts
it all in Notion for manual review and send.

**Authoritative spec:** [docs/planning/anchor_planning.md](docs/planning/anchor_planning.md)
(supersedes `anchor_phase_0.md`, which is kept only for history). Consult it before
making architectural decisions — this file is a working summary for day-to-day sessions,
that document is the source of truth. Anything not yet built or explicitly out of scope
belongs in [FUTURE.md](FUTURE.md), not in a workflow.

## Status

**Day 18 of 18 — COMPLETE.** All workflows built and live; dashboard running
with job-URL intake form + `/setup` resume management page; real master resume
seeded (2026-06-16); Material Quality eval complete (20 applications — Anchor
10% grounding pass rate vs 0% baseline); README + ADRs + overview PDF + resume
bullet + LinkedIn post all done. See roadmap in planning doc §12.
n8n owner account set up via REST API (Day 2; login saved in `.env`, gitignored).
Workflow 1 (Job Intake) built, active, exported to
[n8n/workflows/01_job_intake.json](n8n/workflows/01_job_intake.json): webhook
`POST /webhook/intake` → URL validator (Code node — format check, informational
ATS-host detection) → Postgres insert (`application` row, status `intake_received`)
→ responds `{application_id, status: "processing"}`, well under the 500ms target,
→ Execute Workflow → Workflow 2 (fire-and-continue, parallel to the response node).
Invalid URLs get a 400 and no row is inserted.

JD Parser agent done (Day 3): prompt at
[prompts/jd_parser.md](prompts/jd_parser.md), structured-output contract as
`JDParserOutput` in [llm/schemas.py](llm/schemas.py), smoke-tested via
[scripts/test_jd_parser.py](scripts/test_jd_parser.py) (Playwright fetch → LLM
wrapper → Pydantic validation) against 3 live postings — all passed. One prompt
bug found and fixed: `location_type` was sometimes returned as a pipe-joined
list (`"hybrid | onsite"`) instead of a single enum value; prompt's output
example tightened to a single concrete value with an explicit "pick exactly
one" rule.

Workflow 2 (Job Processor) — Day 4 single-source version superseded by Day 5,
active, exported to
[n8n/workflows/02_job_processor.json](n8n/workflows/02_job_processor.json),
22 nodes: Execute Workflow Trigger → Load Application → Fetch JD Page (new
[fetch/](fetch/) Playwright microservice, port 8002) → JD Parser Agent (LLM
wrapper, supports `system_prompt_name` to load `prompts/<name>.md`) → Parse
JD → Derive Research URLs (guesses homepage/about from company name, derives
the real careers-board URL from the JD's ATS — Greenhouse/Lever/Workday) →
4 parallel branches (news via Google News RSS, homepage, about, careers —
each tolerant of fetch failure via `onError: continueRegularOutput`) → Merge
Research → Prepare Synthesizer Input → Company Synthesizer Agent (LLM
wrapper, `system_prompt_name: "company_synthesizer"`) → Parse Synthesis →
Prepare Company Upsert → Upsert Company (`domain` + full `synthesis` jsonb,
`ON CONFLICT (lower(name))`, see
[db/migrations/001_company_name_unique.sql](db/migrations/001_company_name_unique.sql))
→ Update Application (`company_id`, `role_title`, `status = 'researched'`).
End-to-end tested against a live posting — synthesis correctly populated
(`company_type`, `tech_signals`, `what_they_do`, etc.) plus `raw_news` and
`sources_available`. Postgres `queryReplacement` rule (revised from Day 4):
each `$n` placeholder must be a *simple* `{{ $json.field }}` property access
— build any combined JSON blob (e.g. `synthesis_json: JSON.stringify({...})`)
in a preceding code node, since `{{ }}` wrapping an object literal that
itself contains nested `{ }` breaks n8n's queryReplacement parser
(`"Query Parameters must be a string of comma-separated values or an array
of values"`).

Master resume seeded (Day 6): no real resume exists yet (confirmed with
user), so [db/seed_master_resume.sql](db/seed_master_resume.sql) seeded
`master_resume_entry` (8 rows, all 5 categories) and `user_profile` (1 row)
with clearly "[TEMPLATE]"-marked placeholder content — applied via
`psql -d anchor -f db/seed_master_resume.sql`. (Superseded post-Day-11 — see
the seed-swap paragraph near "Next:" below: the `[TEMPLATE]` rows have since
been replaced with genericized real content as a temporary stand-in.) Every
non-placeholder row must still be real, your-own-voice facts before Workflow
3 runs for real; the Grounding Critic catches invented claims, not
placeholder ones.

Resume Critic agent done (Day 6): prompt at
[prompts/resume_critic.md](prompts/resume_critic.md), structured-output
contract as `ResumeCriticOutput` in [llm/schemas.py](llm/schemas.py),
smoke-tested via [scripts/test_resume_critic.py](scripts/test_resume_critic.py)
(loads seeded resume entries + profile from Postgres via `psql`/`json_agg`,
pairs with a standalone sample JD + company synthesis hardcoded in the
script — deliberately not dependent on a live posting, per Day 5's note
that test postings go stale) — passed schema validation, with specific,
honest strengths/gaps mapped to concrete JD requirements even from
placeholder resume text.

Match Scorer + low-match gate done (Day 7): prompt at
[prompts/match_scorer.md](prompts/match_scorer.md), structured-output
contract as `MatchScorerOutput` (+ `MatchTier`, `GapSeverity`, `MatchGap`) in
[llm/schemas.py](llm/schemas.py). Added a `POST /notify-slack` endpoint to
the LLM wrapper ([llm/server.py](llm/server.py), `SLACK_WEBHOOK_URL` in
`.env.example`/`llm/config.py`) so n8n can post to Slack without the webhook
URL living in committed workflow JSON. Started
[n8n/workflows/03_match_and_generate.json](n8n/workflows/03_match_and_generate.json)
(Execute Workflow Trigger → load application/JD/master resume/profile →
Resume Critic Agent → Persist Resume Critic → Match Scorer Agent → Persist +
Update Match Score → **IF Score >= 60**): `>= 60` continues to Day 8's chain;
`< 60` → Mark Low Match (`status = 'low_match_waiting'`) → Slack message with
score/reasoning/top_gaps/red_flags + Continue/Skip links via
`$execution.resumeUrl` → **Wait for Decision** (webhook resume) → IF
Continue/Skip → continue or Mark Withdrawn (`status = 'withdrawn'`).
Smoke-tested via [scripts/test_match_scorer.py](scripts/test_match_scorer.py)
(chains Resume Critic → Match Scorer against Day 6's standalone fixtures) —
scored 68/100 ("warm"), correctly above 60 with the CI/CD and
distributed-systems gaps reflected in `top_gaps`/`reasoning` rather than
silently absorbed.

Resume Tailorer + Grounding Critic done (Day 8): prompts at
[prompts/resume_tailorer.md](prompts/resume_tailorer.md) and
[prompts/grounding_critic.md](prompts/grounding_critic.md), structured-output
contracts as `ResumeTailorerOutput` (+ `TailoredResumeSection`,
`TailoredResumeLine`, `ResumeEntryCategory`) and `GroundingCriticOutput` in
`llm/schemas.py`. Extended Workflow 3's `>= 60` branch: Prepare Tailorer Input
→ Resume Tailorer Agent → Parse Tailored Resume → Prepare Grounding Check →
Grounding Critic Agent → **IF Grounding Passes** — pass: Persist Tailored
Resume (`generated_material`, type `tailored_resume`) → Insert Grounding Rows
(`material_grounding`, one per cited `master_resume_entry_id`) → Finalize
Material → Mark Awaiting Review (`status = 'awaiting_review'`) → Prepare/Post
Ready Slack; fail: **IF Retry Available** (`retry_count < 1`) loops back to
the Tailorer with the violation list as revision feedback, or — on a second
failure — Prepare/Post Escalation Slack with no `generated_material` row
written. "Prepare Ready Slack" notes "(Notion/Drive export lands in Day 9.)"
— Workflow 3 currently ends at `awaiting_review` + Slack, not yet the full
Drive/Notion handoff in the architecture table below.
Smoke-tested via
[scripts/test_resume_tailorer.py](scripts/test_resume_tailorer.py) (full
Resume Critic → Match Scorer → Resume Tailorer → Grounding Critic chain
against Day 6's fixtures, plus a check that every cited
`master_resume_entry_id` was actually loaded from Postgres) — all 4 outputs
passed schema validation; the Grounding Critic correctly *failed* the
tailored output with 3 specific violations (an added technology + a
stronger verb than the `[TEMPLATE]` source entry supports) — exactly the
kind of subtle overstatement it exists to catch, on real model output.

Cover Letter / LinkedIn Drafter / Skill Gap Analyzer + PDF rendering done
(Day 9 part 1): prompts at [prompts/cover_letter.md](prompts/cover_letter.md),
[prompts/linkedin_drafter.md](prompts/linkedin_drafter.md),
[prompts/skill_gap_analyzer.md](prompts/skill_gap_analyzer.md); structured-output
contracts `CoverLetterOutput`, `LinkedInDrafterOutput`, `SkillGapAnalyzerOutput`
(+ `RequirementCategory`, `SkillGap`, `SkillGapVerdict`) in
[llm/schemas.py](llm/schemas.py). LinkedIn Drafter prompt fix: qwen2.5:7b
couldn't reliably hit a 300-char limit when told "300 characters" (348, then
330 chars); switched to a word-count proxy ("no more than 35 words") → 288
chars. Smoke-tested via
[scripts/test_day9_agents.py](scripts/test_day9_agents.py) (Resume Critic →
Match Scorer → {Cover Letter, LinkedIn, Skill Gap} against Day 6's standalone
fixtures) — all passed schema validation, cover letter cited valid
`master_resume_entry_id`s under the 250-word cap, LinkedIn under 300 chars.
PDF rendering: extended [fetch/server.py](fetch/server.py) (port 8002) with
`POST /render-pdf {template: "resume"|"cover_letter", data}` — Jinja2 template
from [pdf/templates/](pdf/templates/) → HTML → headless-Chrome `page.pdf()`.
Templates use the same "[TEMPLATE]"/bracketed-placeholder convention as
`db/seed_master_resume.sql` for candidate name/contact fields. Smoke-tested via
[scripts/test_pdf_render.py](scripts/test_pdf_render.py) and visually verified
via PNG screenshots — both templates render correctly. Workflow 3 grew from 39
to 53 nodes: between "Finalize Material" and "Mark Awaiting Review", added
Prepare/Persist Cover Letter (+ grounding rows on a side branch) → Prepare/
Persist LinkedIn Message → Prepare/Persist Skill Gap Report, writing
`generated_material` rows of type `cover_letter`, `linkedin_message`, and
`skill_gap_report`. "Mark Awaiting Review" now reads `application_id` from
`$('Finalize Material')` instead of `$json` (decoupled from the new chain's
output shape); "Prepare Ready Slack" now reports the skill-gap verdict too.

Google Drive + Notion export done (Day 9 part 2): credentials configured in
n8n (`Anchor - Google Drive` OAuth2, plus the existing `notionApi`
credential — found by type via the REST API since the credential-rename UI
wasn't where expected), target Notion database id
`3806af3e78ea805fb6b8d1ca4c58188b` and Drive parent folder id
`1b1UHjbDJ1TP03X0dX7p4lybN46FzB5Ug` supplied by the user. Workflow 3 grew from
53 to 67 nodes: between "Persist Skill Gap Report" and "Mark Awaiting Review",
added Load JD URL (small standalone query — `Load Application` doesn't select
`application.url`) → Prepare Drive Folder Name (sanitizes
`{company}_{role}_{ISO date}` per planning doc §5.3) → Create Drive Folder →
Prepare/Render/Upload Resume PDF (`/render-pdf` → `responseFormat: "file"` →
Drive `file`/`upload`) → Prepare/Render/Upload Cover Letter PDF (same
pattern) → Prepare PDF URL Updates → Update Resume/Cover Letter PDF URL (two
`UPDATE generated_material SET pdf_drive_url = $1 WHERE id = $2::uuid`) →
Prepare Notion Page → Create Notion Page (`POST
https://api.notion.com/v1/pages`, `predefinedCredentialType`/`notionApi`,
explicit `Notion-Version: 2022-06-28` header; flat property schema — Name,
Company, Role Title, Application ID, Status, Match Score, Match Tier, Skill
Gap Verdict, JD URL, Resume PDF, Cover Letter PDF, LinkedIn Message, Created;
select-type properties rely on Notion auto-creating new options). "Prepare
Ready Slack" rewritten to include the Drive folder link, Notion page link,
and skill-gap verdict. Binary-response state-carrying rule: any HTTP node with
`responseFormat: "file"` resets `json` to `{}` (PDF bytes go to
`binary.data`), so every downstream node reaches upstream state via
`$('NodeName').item.json...` rather than `$json`/`...prior` spreads — same
pattern as `Finalize Material`'s `material_id`. All new Code nodes passed
`node --check`; the full 67-node workflow passed structural validation
(no dupes, all connections resolve, expected terminal nodes).

Imported into n8n: pushed via `PATCH /rest/workflows/<id>` (n8n's REST API
uses PATCH, not PUT, for workflow updates) — the live workflow was still on
the Day 8 (39-node) version since Day 9 part 1's update was never imported
either, so both jumps landed in this one PATCH. Verified post-import: 67
nodes, still `active: true`, new `versionId`, chain
`Persist Skill Gap Report → Load JD URL → ... → Create Notion Page → Mark
Awaiting Review` intact. Definition-only update, no execution triggered.

Phase B Code nodes smoke-tested (no external side effects): added
[scripts/test_phase_b_codenodes.js](scripts/test_phase_b_codenodes.js) —
extracts the 6 new nodes' `jsCode` live from the workflow JSON, runs them
against mock upstream data shaped like real agent outputs, mocks Drive/Notion
responses, and makes both `/render-pdf` calls for real. All 22 checks pass
(folder-name sanitization, both PDFs render, `pdf_drive_url` bookkeeping,
`notion_body` property shapes/values, `slack_text` content).

Workflow 4 (Follow-up Scheduler) done (Day 11): prompt at
[prompts/follow_up_decision.md](prompts/follow_up_decision.md),
structured-output contract `FollowUpDecisionOutput` (+ `FollowUpDecision`
enum `send_now`/`wait`) in [llm/schemas.py](llm/schemas.py). Single-call
agent per the Token-Saving Playbook — decides whether to nudge *and* drafts
the nudge in one pass, defaulting to patience (no response yet is the normal
case; 2+ nudges already sent forces `wait`). Smoke-tested via
[scripts/test_follow_up_decision.py](scripts/test_follow_up_decision.py) (3
scenarios: window just reached/no nudge, window not reached, already nudged
twice) — all 3 produced the expected decision. One prompt fix found via the
smoke test: qwen2.5:7b got the days-vs-window comparison wrong on its own
(same class of issue as Day 9's LinkedIn char-limit fix), so "Prepare Decision
Input" now precomputes `Follow-up window reached: yes/no` and the prompt has
a hard rule that `no` forces `decision: wait`.
[n8n/workflows/04_follow_up_scheduler.json](n8n/workflows/04_follow_up_scheduler.json)
(14 nodes): Schedule Trigger (daily 8am) → Mark Ghosted (21-day no-response →
`status='ghosted'`) → Find Due Applications → per application: Prepare
Decision Input → Follow-up Decision Agent → Parse Decision Output → IF Should
Follow Up → (true: Persist Follow-up Nudge as `generated_material` type
`follow_up_nudge` + Insert Follow-up Event into `application_event`) → Merge
Decisions → Wait Until 9am (`resume: "specificTime"`) → Build Digest (reads
`$('Parse Decision Output').all()`, sidestepping the Postgres-overwrites-json
problem) → Post Follow-up Digest via `/notify-slack`. All Code nodes pass
`node --check`; workflow passes the same structural checks as Workflow 3; the
data-flow chain (Prepare Decision Input → mocked LLM → Parse Decision Output
→ Prepare Follow-up Event → Build Digest) is smoke-tested via
[scripts/test_followup_codenodes.js](scripts/test_followup_codenodes.js) — all
14 checks pass. Notion's "Drafts to send" view (§5.4) is not yet wired (would
need Workflow 3 to persist `notion_page_id`, or a Notion query-by-property) —
deferred; Postgres + the Slack digest are enough to review drafts for now.
**Not imported into n8n** — no applications are `status='submitted'` yet, so
there's nothing for it to act on, consistent with the deferred-import pattern
used for Workflow 3.

Demo + reliability hardening (post-Day 11): built
[scripts/demo_realistic_resume.py](scripts/demo_realistic_resume.py), a
standalone run of the full Workflow 3 chain against 13 genericized
(non-`[TEMPLATE]`, non-PII) fixture entries based on a friend's resume
("for testing only" — not written to Postgres or
`db/seed_master_resume.sql`). At this larger, more realistic scale it
surfaced and (mostly) fixed 3 bugs Day 6-9's 8-entry fixtures never hit: (1)
Cover Letter prose containing literal `(id=...)` citation markers — fixed via
prompt rules plus a `CoverLetterOutput.paragraphs` regex-strip
`field_validator` in [llm/schemas.py](llm/schemas.py) (and the matching
"Parse Cover Letter Output" node in
[n8n/workflows/03_match_and_generate.json](n8n/workflows/03_match_and_generate.json)),
verified fully stripped; (2) LinkedIn message over the 300-char limit (314) —
fixed by tightening [prompts/linkedin_drafter.md](prompts/linkedin_drafter.md)
from a 35-word to a 25-word guideline with a self-count check, verified at
253/216 chars; (3) Grounding Critic false positives (5 violations, one against
an uncited entry) — fixed by restructuring
[prompts/grounding_critic.md](prompts/grounding_critic.md) (and
`build_grounding_prompt` in `demo_realistic_resume.py`,
`test_resume_tailorer.py`, and the "Prepare Grounding Check" node) from two
cross-referenced lists into a paired "Lines to check" format (`Line N (from
<id>)` / `Tailored:` / `Source:`), which eliminated the reported false
positives (now `passes: true, violations: []` on those 6 lines). A residual,
lower-severity false-positive mode remains on Day 8's `[TEMPLATE]` fixture
(2/4 violations claim a verbatim-present word is missing when the tailored
line *omits* other words from its source) — judged a qwen2.5:7b
near-identical-text-comparison limitation that the fail-safe
retry-then-escalate design absorbs safely (unnecessary escalation, never bad
content shipped); not pursued further. Also found and fixed an unrelated infra
bug along the way: the LLM wrapper's Ollama call had only a 120s timeout,
which intermittently 500'd on slower back-to-back calls — added
`OLLAMA_TIMEOUT_SECONDS` (default 240) to
[llm/config.py](llm/config.py)/[.env.example](.env.example), used in
[llm/client.py](llm/client.py); re-ran Day 9's smoke test and the full demo
afterward with zero 500s. Full writeup in
[PROGRESS.md](PROGRESS.md#demo--reliability-hardening-post-day-11-pre-day-10-resume).

Master resume seed swapped from `[TEMPLATE]` to real (genericized) content:
per the user's explicit instruction ("use it for now, I'll upload mine when
the project is ready"), [db/seed_master_resume.sql](db/seed_master_resume.sql)
now seeds the same 13 entries + profile from `demo_realistic_resume.py`'s
`DEMO_ENTRIES`/`DEMO_PROFILE` (genericized friend's-resume content, no
"[TEMPLATE]" strings, no PII — privacy is still crucial, so no real names,
contact info, or identifying institution/org names anywhere in the file).
Applied via `DELETE FROM master_resume_entry; DELETE FROM user_profile;` +
re-`INSERT` (FK-safe — `material_grounding` had 0 rows); Postgres now has 13
`master_resume_entry` rows across all 5 categories and 1 `user_profile` row.
This is **still a placeholder**, not the user's own resume — when the real
one arrives, replace every row in `db/seed_master_resume.sql` the same way
(nothing downstream is special-cased to this content).

Error workflow + retry logic (Day 12, done — on-disk + live): per planning doc
§5.6, built [n8n/workflows/00_error_handler.json](n8n/workflows/00_error_handler.json)
(6 nodes — `errorTrigger` → Parse Error Context → Prepare Error Event →
Insert Error Event (`application_event` type `error`, `application_id`
always `NULL` — n8n's Error Trigger doesn't expose the failed execution's
node data, so there's no reliable application_id to attach; see PROGRESS.md
for the full reasoning) → Prepare Slack Alert (includes execution URL + a
fill-in `UPDATE application SET status = 'errored'...` template) → Post Slack
Alert). Smoke-tested via
[scripts/test_error_handler_codenodes.js](scripts/test_error_handler_codenodes.js)
(15 checks, transient + permanent error scenarios). Also added
`retryOnFail: true, maxTries: 3, waitBetweenTries: 2000` to all 23
`httpRequest` nodes across `00`/`02`/`03`/`04` (covers §5.6 step 3's "HTTP
5xx/timeout/rate limit → retry, max 2 retries"; Postgres nodes intentionally
excluded — retrying INSERT/UPDATE after an ambiguous failure risks duplicate
writes). Along the way, fixed a real bug: "Fetch Company News" in Workflow 2
was missing `onError: continueRegularOutput`, unlike its 3 sibling research
branches (contrary to this file's existing Day 4/5 claim that all 4 are
fetch-failure-tolerant) — now fixed to match.

**Live part**: logged into n8n's REST API (`POST /rest/login`,
`emailOrLdapLoginId` + password from `.env`) and pushed the retryOnFail +
grounding/cover-letter-fix updates to live workflows 02
(`6c1GWSWFB30upbH2`) and 03 (`x189x3S4YZQTVctl`) via `PATCH
/rest/workflows/<id>`. Imported `00_error_handler.json` as a new workflow
(`POST /rest/workflows` → id `hULM9d6nFUMdite1`) and activated it via `POST
/rest/workflows/<id>/activate` — n8n 2.8.4 requires an error-workflow target
to be *active* (`activeVersion !== null`) or `executeErrorWorkflow` silently
no-ops, and a plain `PATCH {"active": true}` doesn't activate a workflow (the
dedicated `/activate` endpoint with `versionId`+`expectedChecksum` does).
Wired `settings.errorWorkflow: "hULM9d6nFUMdite1"` into 01-04 (on-disk +live
PATCH for the now-live 01/02/03). Imported `04_follow_up_scheduler.json` too
(`POST /rest/workflows` → id `5QC5r8KK8u2hWhj5`), left inactive — nothing is
`status='submitted'` yet for its Schedule Trigger to act on. Failure-path
tested workflow 00 itself end-to-end via n8n's manual-run API (`POST
/rest/workflows/<id>/run` with `pinData`+`triggerToStartFrom` on the Error
Trigger node) — real `application_event` row inserted
(`application_id` NULL, `event_type='error'`) and the Slack-alert HTTP node
executed successfully. Full writeup in
[PROGRESS.md](PROGRESS.md#day-12-part-2-live--error-workflow-import--wiring--failure-path-test).

Workflow 5 (Weekly Reflection + Pattern Detector) done on-disk (Day 13): per
planning doc §5.5, prompt at
[prompts/pattern_detector.md](prompts/pattern_detector.md),
structured-output contract `PatternDetectorOutput` (+ `Pattern`,
`PatternConfidence` enum `low`/`medium`/`high`) in
[llm/schemas.py](llm/schemas.py). Single-call agent: input is one precomputed
text block (window stats), output is `{patterns[], summary}`. Implements
§17's min-N=5 guard the same way Day 11 handled the days-vs-window
comparison — "Prepare Pattern Detector Input" precomputes `N` and a "Minimum
sample size reached (N >= 5): yes/no" line; if `no`, the prompt requires
`patterns: []` and a `summary` that plainly cites N and 5 rather than
speculating. When the guard passes, each pattern needs >= 2 applications per
compared group.
[n8n/workflows/05_weekly_reflection.json](n8n/workflows/05_weekly_reflection.json)
(8 nodes): Schedule Trigger (Sunday 7pm) → Aggregate Last 4 Weeks (Postgres —
applications from the last 28 days joined with company + latest
`match_scorer` tier) → Prepare Pattern Detector Input → Pattern Detector
Agent → Parse Pattern Detector Output → Persist Weekly Insight (`INSERT INTO
weekly_insight`) → Build Digest → Post Weekly Digest
(`/notify-slack`). `settings.errorWorkflow` wired from creation, same as
01-04. Smoke-tested via
[scripts/test_pattern_detector.py](scripts/test_pattern_detector.py) (N=1 —
the real current Postgres state, correctly returns `patterns: []` /
"not enough data" — and a hypothetical N=6 startup-vs-enterprise scenario)
and
[scripts/test_weekly_reflection_codenodes.js](scripts/test_weekly_reflection_codenodes.js)
(21 checks across both scenarios' Code-node chains). One prompt fix found via
the smoke test: qwen2.5:7b initially *recomputed* a response-rate ratio in
`evidence` and got it wrong (claimed "3 out of 3" for what the input's
breakdown said was `2/3 (67%)`) — fixed by requiring `evidence` to copy the
exact `"X/Y (Z%)"` string verbatim from the input rather than re-deriving it;
re-ran and got the correct `2/3 (67%)` / `0/3 (0%)` figures. All 3 Code nodes
pass `node --check`; the 8-node workflow passes the same structural checks as
prior workflows. **Imported into n8n inactive** (same `POST /rest/workflows`
procedure as Workflow 4) → id `Mk8farJ0Ekw2yV7Q` — left inactive since with
only 1 application in
Postgres, a live Sunday run would just reproduce the already-tested N=1 "not
enough data" case; revisit once >= 5 applications exist.

Dashboard skeleton (Day 14, done): built [dashboard/](dashboard/) as a new
Next.js 14.2.35 App Router + TypeScript + Tailwind 3.4.1 + lucide-react app,
per planning doc §6's "Dashboard is just SQL" ADR — direct Postgres queries
from Server Components via a `pg.Pool` singleton
([dashboard/lib/db.ts](dashboard/lib/db.ts)), no separate backend, no SSE
(Meridian's pattern explicitly not reused, only its structural Next.js/
Tailwind/design-token conventions). Cream-background, deep-teal-accent
(`#2F6B66`, the user's choice over LinkedIn blue/terracotta/navy/sage)
design tokens in [dashboard/app/globals.css](dashboard/app/globals.css) +
`tailwind.config.ts`. 4 routes: `/` (animated welcome page — CSS
`fade-in-up` keyframes, hero + 3 feature cards), `/dashboard` (Applications
kanban — all 11 `application_status` values grouped into Active Pipeline /
Outcomes / Errors sections), `/decisions` (agent_run audit log,
`<details>`/`<pre>` JSON viewer per run), `/insights` (weekly_insight cards,
empty-state citing Workflow 5's Sunday-7pm/min-N=5 guard since 0 rows exist
yet). Shared `app/layout.tsx` header with nav + external shortcuts to
Notion/Drive/n8n (lucide-react icons, `target="_blank"`). All 3 DB-backed
pages use `export const dynamic = "force-dynamic"` (App Router static
prerendering would otherwise freeze Postgres data at build time). Verified:
all 4 routes return 200 with real data (the one Airbnb application in
`low_match_waiting`/score 58 renders with a warning-colored
`MatchScoreBadge`; 4 `agent_run` rows render in the audit log), `npm run
build` type-checks cleanly with `/dashboard`/`/decisions`/`/insights` all
`ƒ (Dynamic)`. Run via `cd dashboard && npm run dev` → `http://localhost:3000`.

**Real master resume seeded (2026-06-16):** `db/seed_master_resume.sql` and
`scripts/demo_realistic_resume.py`'s `DEMO_ENTRIES`/`DEMO_PROFILE` were both
replaced with the candidate's actual resume content (14 entries: 2 education,
2 experience/KuKClean, 6 project/Meridian+Anchor+CrowdSense, 3 skill, 1
achievement/certs). Applied via `DELETE + re-INSERT`; Postgres now has 14 real
`master_resume_entry` rows + 1 `user_profile` row. The two paused "Wait for
Decision" executions (24, 26) from the Airbnb Greenhouse posting
(`bfe91458-cd95-429c-8186-54d24bb6c913`) remain in n8n — that application
scored 58/"cold" under both the old and the ML-focused new profile (Airbnb
SWE-intern JD is heavy AI/ML, profile is a good match but the open posting had
closed by Day 5 so the full JD was unavailable). Leave both paused unless you
explicitly revisit the Airbnb application; the existing low-match Slack + Wait
nodes cover it.

**To get a live Phase B run** (Drive + Notion + Slack, the last unexercised
path): POST any Python/ML/backend internship URL to `/webhook/intake` —
the real ML-focused profile should score ≥60 on well-aligned roles. The
workflow chain is fully wired and import-verified; this is the only step that
needs a real execution.

**To activate Workflows 4 and 5** once you have submitted applications:
- Workflow 4 (`5QC5r8KK8u2hWhj5`): activate when ≥1 application reaches
  `status='submitted'` — daily 8am cron will then start acting on them.
- Workflow 5 (`Mk8farJ0Ekw2yV7Q`): activate when ≥5 applications exist —
  min-N=5 guard needs the sample before pattern detection fires.

**Material Quality eval** (Days 15-16, complete): ran 20 tailored + 20
baseline fixtures against the real candidate profile.
Results: **Anchor 10% grounding pass rate (2/20) vs Baseline 0% (0/20)**.
Mean match score: 74.2, tier distribution: 8 hot, 11 warm, 1 cold.
Full detail in [eval/results_summary.md](eval/results_summary.md).
README eval table updated with real numbers.

Dashboard UI features added (post-Day-14): job-URL intake form on
`/dashboard` page (proxies to n8n webhook, no curl needed), `/setup` page
for master resume management (profile editor + CRUD for
`master_resume_entry` rows — category, canonical_text, tags, priority,
facts). Server Actions for all mutations; `npm run build` passes.

Keep this line current as days land — it's how a new session knows where the build stands.

## Non-negotiable design constraints

These are load-bearing decisions from the planning doc (§4.2, §17, ADRs in §15).
Don't relax them for convenience:

- **No auto-submit, ever.** Anchor drafts; the user reviews in Notion and sends manually.
- **Grounding.** Every line of a tailored resume must trace to a `master_resume_entry`
  row via `material_grounding`. Tailoring is selection + rephrasing, never invention.
  The Grounding Critic agent enforces this with one retry max before escalating.
- **Rigorous honesty.** Critic/scorer agents do not inflate. Accuracy over encouragement,
  even when the news is bad (low match score, real skill gaps).
- **Match threshold: 60.** Below it → Slack prompt + Wait node, human decides whether
  to continue. Don't auto-skip or auto-continue.
- **Postgres is the single source of truth** for all application/company/material state.
  n8n's own data store is only for workflow-internal bookkeeping.
- **Ollama (qwen2.5:7b) local only** during the build — no paid LLM APIs. All calls go
  through the `llm/` wrapper, which caches to disk by `(model, prompt, system, json_mode)`.
- **FUTURE.md discipline.** "But what if it also..." ideas get parked in FUTURE.md, not
  built mid-flow. Re-read the Non-Goals section (planning doc §17) when scope creep tempts.

## Relationship to Meridian

`llm/` (config, cache, client, server) is adapted from the equivalent files in
`/Users/satvik/Downloads/PROJECTS/meridian/backend/app/llm/` — same disk-cache pattern,
trimmed config. **Meridian is a separate, independently-running project.** Never edit,
move, or run anything under `PROJECTS/meridian/` from this repo; if the wrapper pattern
needs to change, change Anchor's copy only.

## Local dev (native — Docker deferred)

Postgres and n8n run natively via Homebrew/npx for dev speed. `docker-compose.yml` is
written but not activated; see [FUTURE.md](FUTURE.md) → "Docker Day" for the checklist
and target date.

```bash
# Postgres (one-time setup, then brew services keeps it running)
brew services start postgresql@16
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

# LLM wrapper (requires local Ollama with qwen2.5:7b pulled)
.venv/bin/uvicorn llm.server:app --reload --port 8001
curl localhost:8001/health

# n8n
npx n8n start   # editor at http://localhost:5678
```

Copy `.env.example` → `.env` for local config (gitignored).

## Architecture

Five n8n workflows + one error workflow, Postgres-backed, all AI calls via the local
LLM wrapper. Full detail in planning doc §5.

| Workflow | Trigger | Does |
|---|---|---|
| 1. Job Intake | Webhook `/webhook/intake` | Validate URL, insert `application` row (`intake_received`), respond <500ms, hand off to Workflow 2 |
| 2. Job Processor | Execute Workflow (from 1) | Playwright JD fetch + parse, parallel company research (news + site), careers-page scrape → `role_recommendation`, Company Synthesizer, status → `researched` |
| 3. Match & Generate | Execute Workflow (from 2) | Resume Critic → Match Scorer (gate at 60) → Resume Tailorer → Grounding Critic → Cover Letter / LinkedIn / Skill Gap agents → PDF render → Drive + Notion, status → `awaiting_review` |
| 4. Follow-up Scheduler | Cron, daily 8am | Find `submitted` applications past their nudge window, draft follow-ups for review, mark 21-day-old ones `ghosted` |
| 5. Weekly Reflection | Cron, Sun 7pm | Aggregate last 4 weeks, Pattern Detector agent, Slack digest, write `weekly_insight` |
| Error workflow | n8n error trigger (all 5) | Retry transient errors (max 2, backoff), Slack alert on permanent failure, status → `errored` |

## Database conventions (`db/schema.sql`)

10 tables, FK-ordered: `company`, `application`, `master_resume_entry`,
`generated_material`, `material_grounding`, `agent_run`, `application_event`,
`weekly_insight`, `user_profile`, `role_recommendation`.

- UUID PKs via `pgcrypto`'s `gen_random_uuid()`.
- Native `ENUM` types for closed sets: `application_status` (11 values, e.g.
  `intake_received` → `researched` → `awaiting_review` → `submitted` → ... →
  `responded`/`ghosted`/`errored`/`withdrawn`), `resume_entry_category`
  (`experience|project|skill|education|achievement`), `generated_material_type`
  (`tailored_resume|cover_letter|linkedin_message|skill_gap_report|follow_up_nudge`).
- `jsonb` for agent outputs and flexible structured data (`synthesis`, `facts`,
  `content_json`, `output_json`, `insights`, `payload`).
- `timestamptz` everywhere, `DEFAULT now()`.
- `schema.sql` is the cumulative baseline (auto-applied via
  `/docker-entrypoint-initdb.d` once Docker Day lands); incremental changes after
  that go in `db/migrations/`.

## Prompts (`prompts/`)

Versioned prompt files, one per agent (e.g. `jd_parser.md`, `resume_critic.md`,
`match_scorer.md`, `grounding_critic.md`). Loaded by HTTP from n8n — keep them
prompt-only (no code), and keep each agent's structured-output contract documented
inline since `agent_run.output_json` and downstream nodes depend on the shape.

## Folder structure

```
anchor/
├── n8n/workflows/        ← exported workflow JSON, numbered 00-05
├── n8n/credentials/       ← .env-driven, not committed
├── db/                    ← schema.sql, migrations/, seed data
├── prompts/               ← one .md per agent
├── llm/                   ← Ollama wrapper (FastAPI), see "Relationship to Meridian"
├── pdf/templates/         ← resume.html, cover_letter.html for Playwright render
├── dashboard/             ← Next.js: kanban, decisions audit log, insights
├── eval/                  ← hand-graded tailored vs. baseline outputs
└── docs/
    ├── planning/          ← anchor_planning.md (authoritative)
    ├── decisions/         ← ADRs (extract from planning §15 as they stabilize)
    └── canvas-screenshots/
```
