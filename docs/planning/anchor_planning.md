# Anchor — Master Planning Document

**Personal AI Application Pipeline · n8n-Orchestrated**
**Phase 0 — Project Planning & Architecture**
**Last updated: June 2026**

---

## Table of Contents

1. Executive Summary
2. Problem Statement & Scope
3. The Three-Layer Pitch
4. System Architecture
5. The Five Workflows
6. Folder Structure
7. Data Flow Walkthrough
8. Database Schema
9. AI Role Matrix
10. Evaluation Framework
11. Tech Stack & Tooling
12. 18-Day Build Roadmap
13. Risk Register
14. Token-Saving Playbook
15. Architecture Decision Records (ADRs)
16. Success Criteria
17. Non-Goals (read this twice)
18. Resume & Interview Strategy
19. Comprehension Check

---

## 1. Executive Summary

Anchor is a personal AI application pipeline orchestrated in n8n that takes a job posting URL and produces a researched, tailored, tracked application — replacing ~90 minutes of manual work per application with ~8 minutes of review.

**Single user:** Me. Anchor is a tool I build for myself and use across my 2026 internship search. It is not a product, not a SaaS, not a platform.

**Built to demonstrate:**

- Advanced n8n orchestration (5 workflows, sub-workflow composition, Wait/Resume patterns, error workflows, mixed sync/async, real OAuth, stateful logic across runs)
- AI as multiple distinct components, not as one node
- Factual grounding by construction (same pattern as Meridian, applied to generation rather than research)
- Real-world utility validated by daily personal use
- Eval methodology applied to a generation problem (harder than research)

**Target audiences for the resume bullet:**

- AI startup recruiters who recognize n8n at depth
- Technical PM interviewers who care about scoping and product instinct
- AI-forward enterprise SaaS companies who need engineers who can build inside existing stacks

**Build constraints:**

- 2.5 weeks (~40 hours total), running in parallel with active internship applications
- Zero monetary spend (Ollama local + free tiers everywhere)
- Solo developer
- Local-first dev; minimal public deploy (read-only dashboard with anonymized data)

---

## 2. Problem Statement & Scope

### 2.1 The Core Problem

Applying to internships well is mechanical research dressed up as judgment. Each application requires:

1. Reading the JD carefully
2. Researching the company (Crunchbase, recent news, public team signals, tech stack indicators)
3. Identifying which parts of my master resume most match what they care about
4. Rewriting resume bullets to emphasize the right things — without inventing experience I don't have
5. Writing a cover letter that's specific to the company, not generic
6. Submitting through whatever ATS they use
7. Tracking what was sent, when, to whom
8. Following up after appropriate delays

This is roughly 90 minutes per application done well, 15 minutes done badly. Across 30 applications, that's 45 hours of work or 7.5 hours of regret-quality submissions. Both are bad outcomes.

### 2.2 What Anchor Does

> Anchor takes a job-posting or company URL, produces a rigorously honest match assessment + four materials per role (tailored resume, cover letter, LinkedIn connection message, skill gap report) in Notion, and discovers other relevant roles at the same company I may have overlooked — all while enforcing that no material claims experience I don't have.

Every word is load-bearing:

| Phrase | Why It Matters |
|---|---|
| job-posting URL | Single, well-defined trigger. Not "search the internet for jobs." |
| under 8 minutes of my review time | Sets latency budget and forces the pipeline to make decisions, not punt them to me |
| factually-grounded | Tailored resume cannot invent experience — same constraint as Meridian's citations |
| multi-source company research | Forces orchestration: parallel sub-workflows, error handling, deduplication |
| critique against the JD | The resume-critic adds value beyond tailoring — flags real gaps |
| stateful tracking | Anchor remembers; this is what makes it a *system* rather than a *script* |

### 2.3 Why n8n Is Right for This

This is the project where n8n is unambiguously the right tool. Most projects don't need workflow orchestration — Anchor does:

- **Multi-trigger**: webhook intake + cron for follow-ups + cron for weekly reflection
- **Stateful across runs**: application progresses through `intake → researched → ready → submitted → responded → closed` over days/weeks
- **Wait + Resume patterns**: Anchor pauses on low-match scores for human decision, resumes via Slack action
- **Real OAuth flows**: Google Drive, Notion, Slack — credential management that custom Python would just reinvent
- **Multi-channel I/O**: webhook in, Slack/Notion/Drive out — n8n handles this natively
- **Visual orchestration**: the canvas itself is the documentation; recruiters who know n8n see the architecture at a glance

A custom Python service would do the same logic, but the orchestration choices would be invisible. n8n makes them visible. That visibility is the portfolio asset.

---

## 3. The Three-Layer Pitch

### 3.1 Ten-Second Pitch

> "Anchor is an n8n-orchestrated AI pipeline I built for my own internship search — paste a job URL, get a tailored, tracked application in 8 minutes."

### 3.2 Sixty-Second Pitch

> "Applying to internships is mechanical research that doesn't deserve 90 minutes per application. Anchor compresses it. I paste a job URL into a webhook. n8n spawns five workflows: one researches the company across multiple public sources in parallel, one critiques my master resume against the JD to find real gaps, one generates tailored materials with a critic agent that enforces I can't claim experience I don't have, one handles follow-up scheduling with Wait nodes, and one does weekly reflection on what's actually working. Everything is stateful in Postgres so the system improves my targeting over time. I'm using it across my own 2026 internship search — about 30 applications planned — which means I get a real eval: response rates with Anchor vs control."

### 3.3 Five-Minute Architecture Pitch

Built progressively across the workflows below. By Day 18 you can whiteboard the full system from memory.

---

## 4. System Architecture

### 4.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  ME (browser, manually paste URL or click bookmarklet)      │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP POST /webhook/intake
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  n8n Workflow 1 — JOB INTAKE                                │
│  • Validates URL                                            │
│  • Creates application row (status: intake_received)        │
│  • Responds immediately with application_id                 │
│  • Calls Workflow 2 via Execute Workflow (async)            │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  n8n Workflow 2 — JOB PROCESSOR                             │
│  • Scrapes JD (with AI fallback if structured fails)        │
│  • JD Parser Agent (Ollama, structured output)              │
│  • Parallel company research (4 sources)                    │
│  • Company Synthesizer Agent                                │
│  • Writes to Postgres (status: researched)                  │
│  • Calls Workflow 3                                         │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  n8n Workflow 3 — MATCH & GENERATE                          │
│  • Resume Critic Agent (master resume vs JD)                │
│  • Match Scorer Agent                                       │
│  • IF score < threshold → Wait + Slack human decision       │
│  • Resume Tailorer Agent                                    │
│  • Grounding Critic (enforces no invented facts)            │
│  • Cover Letter Generator                                   │
│  • Renders to PDF, saves to Drive                           │
│  • Creates Notion row                                       │
│  • Slack: "Ready for review" (status: awaiting_review)      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  n8n Workflow 4 — FOLLOW-UP SCHEDULER (cron, daily 8am)     │
│  • Loads submitted applications past their nudge window     │
│  • Follow-up Decision Agent                                 │
│  • Drafts polite nudge referencing original application     │
│  • Queues for my morning review (not auto-send)             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  n8n Workflow 5 — WEEKLY REFLECTION (cron, Sun 7pm)         │
│  • Aggregates last 4 weeks of applications + outcomes       │
│  • Pattern Detector Agent                                   │
│  • Slack: weekly insights digest                            │
└─────────────────────────────────────────────────────────────┘

         ┌───────────────────────────────────────────┐
         │  ERROR WORKFLOW (n8n)                     │
         │  • Catches failures from all 5 workflows  │
         │  • Retries with backoff (max 2)           │
         │  • Slack alert on permanent failure       │
         │  • Application moves to status: errored   │
         └───────────────────────────────────────────┘

         ┌───────────────────────────────────────────┐
         │  POSTGRES (single source of truth)        │
         │  applications, companies, master_resume,  │
         │  agent_runs, generated_materials,         │
         │  application_events, weekly_insights      │
         └───────────────────────────────────────────┘

         ┌───────────────────────────────────────────┐
         │  OLLAMA (local) — qwen2.5:7b              │
         │  All AI calls go through one HTTP wrapper │
         │  Disk cache identical to Meridian's       │
         └───────────────────────────────────────────┘
```

### 4.2 Key Design Choices

| Choice | Rationale |
|---|---|
| n8n self-hosted via Docker | Visual workflow showcase; full control over canvas screenshots; works locally without paid tier |
| Five workflows, not one | Composition over monoliths. Each is testable in isolation. The "5 workflows talking to each other" pattern *is* the n8n showcase. |
| Postgres for state | Real persistence, queryable, auditable. n8n's static data is too limited for cross-application learning. |
| Ollama local, not API | Free; already installed from Meridian; reuses the Meridian LLM wrapper verbatim; demonstrates cost engineering. |
| Manual URL paste (v1) | LinkedIn/ATS scraping is hostile and unreliable. Manual paste removes an entire category of failure. Chrome extension goes in FUTURE.md. |
| No auto-submit | Hard safety boundary. Anchor drafts; I send. Removes liability, errors, and ethical issues in one decision. |
| Master resume as structured data | Same instinct as Meridian's Evidence/Finding split. Facts live in one place; tailoring is *selection and rephrasing*, not invention. |

---

## 5. The Five Workflows

### 5.1 Workflow 1 — Job Intake

**Trigger:** Webhook (POST `/webhook/intake`)

**Input:** `{ "url": "https://..." }`

**Nodes:**
1. Webhook (in)
2. URL validator (Code node, regex sanity check + domain whitelist for known ATS hosts)
3. Postgres: insert `application` row with status `intake_received`
4. Respond to Webhook with `{ "application_id": "uuid", "status": "processing" }` — *sync response, async processing*
5. Execute Workflow → calls Workflow 2 with `application_id`

**Latency target:** Webhook response in under 500ms. The user (me) shouldn't wait for processing.

**Why this matters:** Mixed sync/async pattern. The Respond to Webhook node firing *before* Workflow 2 starts is the kind of n8n usage that signals real understanding.

### 5.2 Workflow 2 — Job Processor

**Trigger:** Execute Workflow (called from Workflow 1)

**Steps:**
1. Load application row from Postgres
2. **Job description fetch (Playwright — always):**
   - Playwright headless Chrome renders the page (handles JS-heavy ATS like Greenhouse/Lever/Workday)
   - `JD Parser Agent` (Ollama, structured output): extracts `{role_title, team_or_org, must_haves[], nice_to_haves[], responsibilities[], tech_stack[], culture_signals[], comp_range, location_type, company_name}`
3. **Parallel company research (2 branches):**
   - News fetch (Google News RSS) — recent funding, launches, layoffs, press
   - Company website fetch (homepage + /about + /careers) — what they do, culture, team signals
   - Each branch caches to Postgres `companies` table — dedup by domain, 7-day TTL
4. **Careers page sub-scrape:** Playwright also scrapes `/careers` or `/jobs` to extract ALL currently open roles (title + URL + brief description) → stored in `role_recommendation` table
5. **Company Synthesizer Agent** consumes both branch outputs:
   - Structured output: `{what_they_do, recent_developments[], tech_signals[], company_type: startup|enterprise|unknown, culture_signals[], likely_role_context}`
6. **Role Evaluator Agent** (NEW):
   - Input: all open roles from careers scrape + user profile (master resume + long-term goals + target role types)
   - Output: ranked list with scores, rationale, and top gap for each role
   - Rules: conservative scoring; must-have gaps are disqualifying; surfaces to Notion company page as recommendation list
   - User manually triggers generation for chosen roles; no auto-generation
7. Update application row: status `researched`
8. Execute Workflow → Workflow 3

**Error handling:** Failed branches don't kill the workflow. Synthesizer is told which sources were available and weights accordingly.

### 5.3 Workflow 3 — Match & Generate

**Trigger:** Execute Workflow (called from Workflow 2)

**Steps:**
1. Load: application row, parsed JD, company synthesis, user profile (master resume + long-term goals + target role types)
2. **Resume Critic Agent** (runs *before* tailoring):
   - Input: master resume + JD + company synthesis
   - Output: `{strengths_for_this_role[], weaknesses_to_address[], gaps_unfixable_in_this_application[], suggested_angle}`
   - Rigorous honesty: identifies real gaps, does not inflate strengths
3. **Match Scorer Agent**:
   - Input: critique output + JD + user profile
   - Output: `{score: 0-100, tier: hot/warm/cold, reasoning, top_strengths[], top_gaps[{gap, severity: minor|significant|dealbreaker}], red_flags[]}`
   - Does not inflate scores. Accuracy over encouragement.
4. **Decision branch:**
   - IF score < 60 → Wait node + Slack message: "Match score [N] for [Role] @ [Company]. Reason: [reasoning]. Continue or skip?" Two action buttons
   - IF score >= 60 → continue
5. **Resume Tailorer Agent:**
   - Input: master resume entries (structured) + JD + critique's suggested angle
   - Output: tailored resume as structured JSON — each line tagged with `master_resume_entry_id`
   - *Hard constraint*: every output line must reference a master entry. Schema enforces this.
6. **Grounding Critic Agent:**
   - Input: tailored resume + master resume
   - Output: `{passes: bool, violations[]}` — checks every claim traces to master
   - IF violations → retry tailoring with violation feedback, max 1 retry
   - IF still failing → Slack escalation with violation detail; you decide
7. **Cover Letter Generator Agent:**
   - Input: company synthesis + JD + critique's suggested angle + story bank (5 narratives)
   - Output: cover letter draft, max 250 words, first-person prose, must reference specific company detail
8. **LinkedIn Drafter Agent** (NEW):
   - Input: company synthesis + role + recruiter/HM signal from research
   - Output: 300-char max connection message, specific to this company and role, not sycophantic
   - If no recruiter identifiable: omit, note in Notion
9. **Skill Gap Analyzer Agent** (NEW):
   - Input: JD must-haves/nice-to-haves + user profile + critique output
   - Output: structured report with gaps categorized as minor / significant / dealbreaker, each with "how hard to close" and a final verdict (Apply now / Address gap first / Not recommended)
10. **Render to PDF** (Playwright headless Chrome — same service as JD fetching)
11. Save PDFs to Google Drive (`anchor/applications/{company}_{role}_{date}/`)
12. Create Notion page (company-centric: under company page → Applications → this role) with all 4 materials + match score + gap report
13. Update application row: status `awaiting_review`
14. Slack message: structured card with company, role, match score, Notion link, Drive link

### 5.4 Workflow 4 — Follow-up Scheduler

**Trigger:** Cron, daily at 8:00 AM

**Steps:**
1. Postgres query: applications where `status = submitted` AND `days_since_submitted >= follow_up_window`
2. For each:
   - **Follow-up Decision Agent**: should I nudge today? Considers company's typical response window (heuristic table), how the application went (was the role hot or warm?), whether I've already followed up
   - IF nudge → draft polite, specific nudge referencing one specific thing from original application
   - Output queued in Notion "Drafts to send" view for my morning review
3. Applications past 21 days with no response → status `ghosted`, flagged for weekly reflection

**Why Wait node patterns matter here:** the follow-up draft is scheduled to land at 9 AM (just after my morning review window) rather than at 8 AM when the cron fires. n8n's Wait until specific time pattern.

### 5.5 Workflow 5 — Weekly Reflection

**Trigger:** Cron, Sunday at 7:00 PM

**Steps:**
1. Aggregate last 4 weeks: applications submitted, responses, interviews, rejections, ghosted
2. **Pattern Detector Agent**:
   - Input: aggregated data + match scores + role tiers + outcomes
   - Output: `{patterns[]: each has {observation, evidence, suggested_action, confidence}}`
3. Format as Slack digest with charts (sparklines via Markdown emoji or links to dashboard)
4. Write findings to `weekly_insights` table — drift loop equivalent

**Example outputs:**
- "Your response rate at AI-infra startups is 40% (4/10), at general SaaS is 8% (1/12). Consider focusing applications."
- "Match scores above 75 had 60% response rate; below 60 had 5%. Suggest raising threshold to 65."
- "Three applications ghosted at companies that publicly use Workday ATS. Possible application black hole."

### 5.6 Error Workflow

**Trigger:** n8n error trigger (set on all 5 workflows)

**Steps:**
1. Capture error context (which workflow, which node, error message, application_id if available)
2. Write to Postgres `application_events` table with type `error`
3. Decide: transient or permanent?
   - HTTP 5xx, timeout, rate limit → retry with exponential backoff (max 2 retries)
   - JSON parse, schema violation, 4xx → permanent, log and surface
4. IF permanent OR retries exhausted → Slack alert with full context and application_id
5. Update application status to `errored` (does not block other applications)

---

## 6. Folder Structure

```
anchor/
├── README.md
├── FUTURE.md                       ← park every "but what if it also..." here
├── .gitignore
├── docker-compose.yml              ← n8n + Postgres + (optional) pgadmin
│
├── n8n/
│   ├── workflows/
│   │   ├── 01_job_intake.json
│   │   ├── 02_job_processor.json
│   │   ├── 03_match_and_generate.json
│   │   ├── 04_follow_up_scheduler.json
│   │   ├── 05_weekly_reflection.json
│   │   └── 00_error_handler.json
│   ├── credentials/                ← .env-driven, not committed
│   └── README.md                   ← how to import workflows
│
├── db/
│   ├── schema.sql                  ← Postgres DDL
│   ├── seed_master_resume.sql      ← my master resume facts (gitignored or templated)
│   └── migrations/
│
├── prompts/                        ← versioned prompt files; loaded by HTTP from n8n
│   ├── jd_parser.md
│   ├── company_synthesizer.md
│   ├── resume_critic.md
│   ├── match_scorer.md
│   ├── resume_tailorer.md
│   ├── grounding_critic.md
│   ├── cover_letter.md
│   ├── follow_up_decision.md
│   └── pattern_detector.md
│
├── llm/                            ← reused from Meridian
│   ├── server.py                   ← lightweight FastAPI wrapper around Ollama
│   ├── cache.py                    ← disk cache identical to Meridian's
│   └── schemas.py                  ← Pydantic models for every agent output
│
├── pdf/                            ← PDF rendering service
│   ├── render.py                   ← headless Chrome via Playwright
│   └── templates/
│       ├── resume.html
│       └── cover_letter.html
│
├── dashboard/                      ← Next.js, reuses Meridian design tokens
│   ├── app/
│   │   ├── page.tsx                ← Applications kanban
│   │   ├── decisions/page.tsx      ← Audit log of every AI call
│   │   └── insights/page.tsx       ← Weekly reflections + trends
│   └── lib/
│
├── eval/
│   ├── benchmark.py
│   ├── grading_rubric.md
│   ├── tailored_outputs/           ← 20 hand-graded outputs
│   └── baseline_outputs/           ← single-prompt comparison
│
└── docs/
    ├── architecture.md
    ├── decisions/                  ← ADRs
    │   ├── 001-n8n-not-custom-python.md
    │   ├── 002-ollama-not-api.md
    │   ├── 003-postgres-not-n8n-state.md
    │   ├── 004-manual-paste-not-scraper.md
    │   ├── 005-no-auto-submit.md
    │   └── 006-master-resume-as-structured-data.md
    └── canvas-screenshots/         ← high-res workflow screenshots for README
```

---

## 7. Data Flow Walkthrough

What happens when I paste a job URL.

1. **Intake (Workflow 1, ~400ms):** Webhook fires, application row created, webhook responds with application_id. I see "Processing" in Notion within a second.

2. **Research (Workflow 2, ~30-90s):** JD scraped/parsed. Four parallel branches fetch company info. Synthesizer consolidates.

3. **Critique + Match (Workflow 3, first half, ~20s):** Resume Critic identifies real strengths/weaknesses for this role. Match Scorer outputs a number with reasoning.

4. **Decision gate:** Below 50 → Slack prompt to me, workflow pauses. Above 50 → continue.

5. **Generation (Workflow 3, second half, ~40-90s):** Tailorer produces structured resume tied to master entries. Grounding Critic validates. Cover letter generated. PDFs rendered. Drive + Notion updated.

6. **Notification:** Slack card lands. I open Notion, review the materials, edit if needed (usually small tweaks), submit through the company's site. Update Notion to `submitted`.

7. **Follow-up (Workflow 4, days later):** Daily 8 AM cron checks if any application has aged past the follow-up window. Drafts a nudge for my review.

8. **Reflection (Workflow 5, weekly):** Sunday digest tells me what's working and what isn't.

Total wall-clock from URL to ready-to-review: typically 2-4 minutes. Total *my* time: under 8 minutes if I trust the output, up to 15 if I edit heavily.

---

## 8. Database Schema

Postgres, single database. The schema is the system's spine — get it right and everything else falls in line.

### 8.1 Tables

**application**

| Field | Type |
|---|---|
| id | uuid PK |
| url | text |
| company_id | fk → company (nullable until research completes) |
| role_title | text |
| status | enum: intake_received, researched, low_match_waiting, awaiting_review, submitted, responded, interview, rejected, ghosted, errored, withdrawn |
| match_score | int 0-100 (nullable) |
| created_at | timestamp |
| submitted_at | timestamp (nullable) |
| responded_at | timestamp (nullable) |
| follow_up_window_days | int default 10 |

**company**

| Field | Type |
|---|---|
| id | uuid PK |
| name | text |
| domain | text unique |
| synthesis | jsonb (structured output of synthesizer agent) |
| last_researched_at | timestamp |

**master_resume_entry** — *the canonical facts about me*

| Field | Type |
|---|---|
| id | uuid PK |
| category | enum: experience, project, skill, education, achievement |
| canonical_text | text (the full version, written in my voice) |
| facts | jsonb (structured: dates, technologies, metrics, etc.) |
| tags | text[] (e.g., `["python", "fastapi", "ai-systems", "evaluation"]`) |
| priority | int 1-5 |

**generated_material**

| Field | Type |
|---|---|
| id | uuid PK |
| application_id | fk |
| type | enum: tailored_resume, cover_letter, linkedin_message, skill_gap_report, follow_up_nudge |
| content_json | jsonb (structured) |
| content_rendered | text (markdown or HTML) |
| pdf_drive_url | text (nullable) |
| generated_at | timestamp |
| model_used | text |

**material_grounding** — the citation-table equivalent

| Field | Type |
|---|---|
| id | uuid PK |
| material_id | fk → generated_material |
| master_entry_id | fk → master_resume_entry |
| usage_note | text (how this entry was used) |

*This table enforces grounding by construction — if a tailored resume line has no row here, the grounding critic rejects it.*

**agent_run** — *the audit log*

| Field | Type |
|---|---|
| id | uuid PK |
| application_id | fk |
| workflow_name | text |
| agent_name | text |
| input_hash | text (sha256 of inputs) |
| output_json | jsonb |
| latency_ms | int |
| critic_passed | bool (nullable) |
| created_at | timestamp |

**application_event** — *human-readable lifecycle log*

| Field | Type |
|---|---|
| id | uuid PK |
| application_id | fk |
| event_type | text |
| payload | jsonb |
| occurred_at | timestamp |

**weekly_insight**

| Field | Type |
|---|---|
| id | uuid PK |
| week_start | date |
| insights | jsonb |
| generated_at | timestamp |

**user_profile** — *the three-part profile all analysis agents load*

| Field | Type |
|---|---|
| id | uuid PK |
| long_term_goals | text (2-3 sentence statement) |
| target_role_types | text[] (e.g. ["ML engineering", "AI infra", "early-stage startups"]) |
| updated_at | timestamp |

*Note: master_resume_entry rows are the third profile component. All three load together into Match Scorer, Role Evaluator, and Resume Critic.*

**role_recommendation** — *all open roles found at a company, ranked by fit*

| Field | Type |
|---|---|
| id | uuid PK |
| company_id | fk → company |
| role_title | text |
| role_url | text |
| match_score | int 0-100 |
| rationale | text |
| top_gap | text (top disqualifying gap, even for recommended roles) |
| recommended | bool |
| created_at | timestamp |

### 8.2 Why This Schema Is Good

1. **Grounding by construction.** No `generated_material` line of type `tailored_resume` can exist without rows in `material_grounding` linking it to master entries. This is *the* schema-level constraint that makes the system trustworthy.
2. **Audit log is structural.** `agent_run` records every AI decision — input hash, output, latency, critic verdict. This becomes the Trace-tab equivalent on the dashboard.
3. **Master resume as data, not text.** Tailoring becomes *selection and rephrasing* of structured facts, not free-form generation. This is the same instinct that made Meridian's citation grounding work.
4. **Cache as first-class.** `input_hash` in `agent_run` enables replay and dedup.

---

## 9. AI Role Matrix

Twelve distinct AI roles. Each does one well-defined job. None are general-purpose "summarize this" calls.

**Design constraint on all agents:** Rigorous honesty. Every agent operates as if reviewed by a senior recruiter + hiring manager + career strategist. Outputs must distinguish facts, estimates, and recommendations. Do not inflate scores or soften gaps.

| Agent | Primary Input | Output Schema | Key Risk |
|---|---|---|---|
| JD Parser | Playwright-rendered HTML | Structured JD fields (title, must-haves, nice-to-haves, responsibilities, tech stack, culture signals) | JS-heavy pages → Playwright handles this |
| Company Synthesizer | 2 source branches (news + website) | Structured company profile incl. `company_type` | Empty branches → synthesizer must tolerate partial inputs |
| Role Evaluator *(NEW)* | All open roles at company + user profile | Ranked list with scores, rationale, top disqualifying gap per role | Over-recommending → conservative scoring, must-have gaps disqualify |
| Resume Critic | Master resume + JD + user profile | Strengths/weaknesses/gaps | Generic critiques → prompt forces specificity and evidence |
| Match Scorer | Critique + JD + user profile | Score 0-100 + reasoning + gaps labeled minor/significant/dealbreaker + red flags | Score inflation → accuracy over encouragement |
| Resume Tailorer | Master + JD + angle | Structured resume w/ `master_resume_entry_id` per line | Hallucinated experience → grounding critic |
| Grounding Critic | Tailored resume + master resume | Pass/fail + violations | False positives → violation reasons must be specific |
| Cover Letter Gen | Company synthesis + JD + story bank | Letter draft, ≤250 words, first-person, must reference specific company detail | Generic letters → hard constraint on company-specific reference |
| LinkedIn Drafter *(NEW)* | Company synthesis + role + recruiter signal | 300-char connection message, specific, not sycophantic | Template outputs → prompt enforces specificity |
| Skill Gap Analyzer *(NEW)* | JD must-haves + user profile + critique | Gaps categorized minor/significant/dealbreaker + verdict | Softening gaps → prompt enforces honest severity labels |
| Follow-up Decision | Application history + company_type | Nudge or wait + draft (tiered: 7/10/14 days) | Annoying nudges → conservative timing defaults |
| Pattern Detector | 4+ weeks aggregate data | Insights with evidence, min N=5 before surfacing any pattern | Spurious patterns → require minimum N and cite evidence |

**Model:** All agents use `qwen2.5:7b` via Ollama, with structured output via JSON mode + Pydantic validation. Same wrapper as Meridian — *literally reuse `llm/server.py` and `llm/cache.py` from Meridian*.

---

## 10. Evaluation Framework

Three evals, increasing in real-world validity over time.

### 10.1 Material Quality Eval (immediate, hand-graded)

- **Sample:** 20 tailored applications generated in week 2-3
- **Rubric** (per application):
  - Factual grounding: does every line trace to master resume? (binary, must be 100%)
  - JD relevance: 1-5 scale on how well bullets emphasize JD priorities
  - Cover letter specificity: 1-5 scale on company-specific vs generic
  - Tone match: 1-5 scale on my voice vs LLM voice
- **Baseline:** single-prompt GPT-style "tailor this resume to this JD" with same inputs, no critic, no grounding
- **Expected outcome:** Anchor matches baseline on JD relevance, *substantially* beats baseline on grounding (baseline will hallucinate ~20-30% of the time based on prior testing). Grounding metric is the headline number.

### 10.2 Response Rate Eval (3-4 weeks in)

- **Sample:** all applications submitted via Anchor in June + July
- **Comparison:** if possible, a small control batch (10 applications) submitted with master resume + generic cover letter, no Anchor
- **Caveats stated openly in README:** small N, no causal control, confounded by timing/role-fit/luck
- **Honest framing:** "preliminary signal, not proof"
- **Resume bullet uses the cleaner Material Quality eval as the headline number, mentions response rate as secondary**

### 10.3 Pattern Validity Eval (4+ weeks in)

- For each weekly insight generated, retroactively grade: was the pattern real?
- Catches the "spurious correlations" failure mode of the Pattern Detector

---

## 11. Tech Stack & Tooling

| Layer | Choice | Reason |
|---|---|---|
| Orchestration | n8n self-hosted (Docker) | Visual workflow showcase; full canvas control |
| Database | Postgres 16 | Real persistence, JSON support, free |
| LLM | Ollama + qwen2.5:7b | Already installed from Meridian; free; reused wrapper |
| LLM client | FastAPI wrapper from Meridian | Disk cache, retry, Pydantic validation — proven |
| PDF rendering | Playwright (headless Chromium) | Real HTML → PDF, supports custom fonts |
| Notion API | Official SDK | Free, generous limits, structured pages |
| Drive API | OAuth2 | Free, n8n native node |
| Slack | Incoming Webhook + Bot Token | Free, n8n native nodes |
| Frontend | Next.js 14 + Tailwind | Reuse Meridian's design tokens |
| Dev hosting | Local Docker Compose | Zero cost during build |
| Demo hosting | Railway free tier | Public dashboard for portfolio |

---

## 12. 18-Day Build Roadmap

Realistic, exam-aware, parallel with active applications. ~3 hours/day average, more on weekends.

| Day | Phase | Deliverable |
|---|---|---|
| 1 | 1 | Docker compose up: n8n + Postgres running; schema applied; Ollama wrapper port from Meridian working |
| 2 | 1 | Workflow 1 (intake) end-to-end; can POST a URL and see row in Postgres |
| 3 | 2 | JD Parser agent + prompt working on 3 real job postings |
| 4 | 2 | Workflow 2 single-source happy path (news only); Postgres companies row |
| 5 | 2 | Add 3 more sources to Workflow 2; parallel branches; Company Synthesizer |
| 6 | 3 | Master resume table seeded with my actual resume facts; Resume Critic working |
| 7 | 3 | Match Scorer + decision branch + Slack prompt for low-match (Wait + Resume) |
| 8 | 3 | Resume Tailorer + Grounding Critic; first end-to-end tailored output |
| 9 | 3 | Cover Letter Generator; PDF rendering; Drive + Notion integration |
| 10 | 4 | First real application generated via Anchor; review and submit manually |
| 11 | 4 | Workflow 4 (follow-ups); Wait until 9am pattern; nudge drafting |
| 12 | 4 | Error workflow; retry logic; failure paths tested by killing services |
| 13 | 5 | Workflow 5 (weekly reflection); Pattern Detector with min-N guard |
| 14 | 5 | Dashboard skeleton: Applications kanban + Decisions audit log |
| 15 | 6 | Eval framework: 10 applications generated, hand-graded against rubric |
| 16 | 6 | 10 more applications + single-prompt baseline comparison |
| 17 | 7 | README with screenshots, ADR cleanup, demo video |
| 18 | 7 | Public deploy (anonymized read-only dashboard); LinkedIn post; resume bullet |

**Realistic expectation:** 85-90% completion. Plan for 100%, descope from bottom up. The Dashboard and Workflow 5 are the most cuttable. The eval is non-negotiable.

---

## 13. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Job URL scrape fails on Workday/Greenhouse | High | Med | AI fallback from raw HTML; manual paste of JD text as backup input |
| Ollama JSON malformation | Med | High | Pydantic validation + 1 retry with explicit format note; proven from Meridian |
| Scope creep adds "search jobs" feature mid-build | High | Very High | This document. FUTURE.md. Re-read non-goals section every week |
| Grounding Critic too strict, rejects valid tailorings | Med | Med | Allow critic to suggest *revisions* not just reject; max 1 retry then surface |
| n8n workflow corruption when iterating | Med | Med | Export workflows to JSON daily; git commit `.json` files |
| Wait + Resume pattern flakes in n8n self-hosted | Low | High | Test on day 7; have polling fallback ready |
| Eval data is too small for credible numbers | High | Med | Lead resume bullet with the deterministic Grounding metric; frame response rate honestly |
| Build runs over 18 days into application crunch | Med | High | Workflows 1-3 are the MVP. If day 12 still on workflows 1-3, freeze and ship that |

---

## 14. Token-Saving Playbook

Same instincts as Meridian:

1. **Cache-first dev.** Disk cache on every Ollama call. Re-running the same JD/company hits cache.
2. **Local Ollama for everything.** No paid APIs. Total cost: zero.
3. **Small structured outputs.** Each agent returns under 500 tokens of structured JSON. Synthesizer is the longest at ~800.
4. **One call per agent role.** No agent chains, no recursive reflection loops. Critic is a separate pass, not nested.
5. **Pre-warm the demo.** Before recording the demo video, run 5 real applications and let everything cache.

---

## 15. Architecture Decision Records (ADRs)

### ADR-001: Use n8n, not custom Python
**Status:** Accepted
**Context:** The orchestration logic could be written as a FastAPI service.
**Decision:** Use n8n as the orchestration layer.
**Consequences:** Visual workflow is the project's portfolio asset — the canvas screenshots tell the architecture story instantly to anyone who knows n8n. AI logic still lives in Python (the Ollama wrapper); n8n handles state, scheduling, integrations, error paths.
**Alternatives:** Custom FastAPI + Celery (loses the visual showcase), Temporal (overkill for solo project).

### ADR-002: Use Ollama local, not paid API
**Status:** Accepted
**Context:** Quality of `qwen2.5:7b` is lower than Claude/GPT-4.
**Decision:** Ollama for all agents.
**Consequences:** Free; reuses Meridian's wrapper; "cost engineering" is an interview signal. Trade-off: prompt design has to be more rigorous because the model is weaker.
**Alternatives:** Gemini Flash free tier (rate-limited, requires API key management), paid APIs ($).

### ADR-003: Use Postgres for state, not n8n static data
**Status:** Accepted
**Context:** n8n can hold workflow state in static data.
**Decision:** Postgres as single source of truth for all entities.
**Consequences:** Cross-workflow queries are easy. Audit log is queryable. Dashboard is just SQL. Trade-off: more setup.
**Alternatives:** n8n static data (too limited), SQLite (poor concurrent writes in dockerized n8n).

### ADR-004: Manual URL paste, not job scraping
**Status:** Accepted
**Context:** "Find jobs automatically" would be more impressive.
**Decision:** Manual URL paste only. No scrapers, no aggregators.
**Consequences:** Scope stays bounded. The intake works reliably. The orchestration story (which is the actual project) doesn't get drowned by scraping fragility.
**Alternatives:** LinkedIn scraping (hostile + legal grey), aggregator APIs (paid).
**Note:** Bookmarklet/extension goes to FUTURE.md.

### ADR-005: Anchor drafts; I send
**Status:** Accepted
**Context:** Could automate submission via headless browser.
**Decision:** No auto-submit. Anchor produces materials; I review and send.
**Consequences:** Hard safety boundary. Removes entire categories of failure (wrong company, broken PDF, ATS form errors). Keeps me in the loop.
**Alternatives:** Auto-submit (rejected on safety + scope grounds).

### ADR-006: Master resume as structured data, not text
**Status:** Accepted
**Context:** Could store master resume as a single text blob and pass it to the tailorer.
**Decision:** Decompose into typed `master_resume_entry` rows.
**Consequences:** Tailoring becomes selection + rephrasing of facts. Grounding Critic can verify by structural reference. Same architectural instinct that made Meridian's citation grounding work — facts are addressable, not parseable.
**Alternatives:** Text blob (rejected — no grounding handle).

---

## 16. Success Criteria

Anchor succeeds if, by Day 18:

- 5 workflows are deployed and triggerable end-to-end on real job URLs
- 20 real applications have been generated by Anchor (and submitted manually)
- Material Quality eval has run with at least 15 hand-graded outputs; grounding metric reported
- README has: hero canvas screenshot, architecture diagram, ADR links, eval table, demo video link
- 60-second demo video plays cleanly: paste URL → watch processing → show ready materials
- Resume bullet drafted with real numbers
- LinkedIn post drafted

If anything is missing, fix that before adding new features. Especially Workflow 5 and dashboard — those are nice-to-haves.

---

## 17. Non-Goals (read this section twice)

Anchor does NOT, and will not in this build:

- ❌ Search the internet for jobs / scrape job boards / scrape LinkedIn
- ❌ Help anyone other than me
- ❌ Have user accounts, auth, or multi-tenancy
- ❌ Have a recruiter side, an ATS, or screening features
- ❌ Auto-submit applications
- ❌ Analyze GitHub repos
- ❌ Detect AI-generated content
- ❌ Be a Chrome extension (manual paste only in v1)
- ❌ Be a mobile app
- ❌ Be a SaaS or have payments
- ❌ Be "for the community"

Every "but what if it also..." idea goes in `FUTURE.md`. Not implemented. Not discussed. Not considered.

If at Day 10 I find myself wanting to add any of the above, the correct action is to re-read this section and keep building Workflow 4.

---

## 18. Resume & Interview Strategy

### 18.1 Resume Bullet Template

> **Anchor — Personal AI Application Pipeline (n8n orchestration)** · github · demo
> · Built and shipped a 5-workflow n8n orchestration system that compresses internship-application workflow from ~90 min to ~8 min per application — orchestrating multi-source company research, master-resume critique, factually-grounded material generation, follow-up scheduling, and weekly reflection
> · Used personally across [N] applications in 2026 internship search; designed factual-grounding constraint that links every tailored resume line to a structured master-resume entry by database FK — eliminated hallucinated experience by construction
> · Implemented adversarial Grounding Critic agent over tailoring outputs; achieved 100% factual grounding vs ~75% for single-prompt baseline on 20-output hand-graded benchmark
> · Showcases advanced n8n patterns: sub-workflow composition, Wait + Resume for human-in-loop decisions, error workflow with retry/backoff, mixed sync/async webhook handling, OAuth integrations (Drive/Notion/Slack)

### 18.2 Three Interview Stories To Prepare

1. **The grounding decision.** "The temptation with a resume tailorer is to let the LLM rewrite freely. But generated resumes hallucinate experience — that's the headline failure mode. I decomposed my master resume into structured entries, made tailoring a selection-and-rephrasing operation, and added a critic that enforces every output line traces to a master entry. The grounding metric went from ~75% to 100% — and more importantly, the failure mode disappeared structurally, not statistically."

2. **The async decision.** "Workflow 1 responds to the webhook in 400ms with an application_id, then kicks off Workflow 2 asynchronously. I considered keeping it sync, but the processing takes 1-3 minutes — the user (me) shouldn't wait. The split also means the intake never times out, even if the LLM is slow. Cost: more state to track. Benefit: reliable UX and clean separation of concerns."

3. **The non-goals discipline.** "Halfway through, I had the urge to add job scraping, recruiter features, GitHub analysis — the project could've ballooned into a platform. I had explicit non-goals in the planning doc and a FUTURE.md for scope-creep ideas. The discipline to *not* build those is what made Anchor ship in 2.5 weeks. Knowing what to leave out is a senior engineering skill I'm trying to develop."

### 18.3 The Architectural Choices To Foreground

- "n8n is the right tool for this specific problem because the work *is* orchestration — Wait-Resume patterns, OAuth credential management, multi-channel I/O, cron + webhook triggers, state across runs."
- "The audit log table records every AI call with input hash and output. That's the dashboard's Trace tab, and it's also how I built confidence in the system."
- "Grounding is structural, not statistical. The schema constraint makes it impossible to ship a hallucinated bullet."

---

## 19. Comprehension Check

Before Day 1, you should be able to answer:

1. Why is the master resume stored as structured rows instead of as a text blob?
2. What's the difference between the Resume Critic and the Grounding Critic? Why are both needed?
3. Why does Workflow 1 respond to the webhook *before* Workflow 2 finishes?
4. Why does Workflow 3 pause on low match scores instead of auto-rejecting them?
5. If you had to cut one workflow on Day 12, which would it be — and which would you absolutely refuse to cut?
6. What goes in FUTURE.md and what goes in this build?

If any feel shaky, revisit the relevant section before continuing.

---

## Document Status

- **Phase 0:** ✅ Complete (this document)
- **Phase 1:** ⏳ Up next — Docker + Postgres + Ollama wrapper port
- **Phases 2-7:** ⏸ Pending

This is a living artifact. Update it as decisions evolve. Each significant change pairs with a new ADR in `docs/decisions/`. Read Section 17 (Non-Goals) at the start of every build day.

---

*Author: Satvik · so
