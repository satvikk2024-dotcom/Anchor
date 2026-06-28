# Anchor — Daily Progress Log

Plain-English log of what got built each day, for catching up at a glance.
Not part of the permanent docs — delete whenever it's no longer useful.
See [docs/planning/anchor_planning.md](docs/planning/anchor_planning.md) for the
authoritative spec and the 18-day roadmap (§12).

---

## Day 1 — Set up the foundation

Building the workshop before making anything.

- **Database (Postgres)**: created all 10 tables Anchor will ever need (applications,
  companies, resume facts, generated documents, etc.) — the permanent "memory" of the
  project.
- **AI wrapper (`llm/`)**: a small local FastAPI service that talks to Ollama
  (`qwen2.5:7b`, free, runs on your machine). Every AI "agent" step goes through this.
  It caches results to disk, so repeating the same request doesn't re-run the model.
- **n8n**: installed the workflow-automation tool that will orchestrate everything,
  running locally — but no workflows built yet.
- **Scaffolding**: created the folder structure (`prompts/`, `pdf/`, `eval/`, etc.) and
  a `docker-compose.yml` for later (everything currently runs natively, not Docker).

**End of Day 1:** plumbing exists, nothing does anything yet.

---

## Day 2 — Build the front door

- **Finished n8n setup**: one-time admin account created, connected to Postgres.
- **Built Workflow 1 — "Job Intake"**, the entry point of the whole pipeline:
  - POST a job URL to `localhost:5678/webhook/intake`
  - n8n checks the URL is well-formed (and flags known ATS hosts like Greenhouse/Lever,
    informationally — doesn't block other domains)
  - Saves a new row in the `application` table, status `intake_received`
  - Replies instantly with `{application_id, status: "processing"}` (~15-35ms,
    well under the 500ms target)
  - Bad URL → 400 error, nothing saved
- **Tested end-to-end** with real job URLs (Greenhouse, Stripe careers page) and a
  garbage URL — both paths work. Cleaned up test rows afterward.
- Left a sticky note on the canvas marking where Workflow 2 will plug in (Day 4) —
  didn't build that hookup early since Workflow 2 doesn't exist yet.

**End of Day 2:** you can paste a job URL and Anchor "catches" and records it. No
intelligence yet — that starts Day 3.

---

## Day 3 — Teach Anchor to read a job posting

Target: JD Parser agent + prompt working on 3 real job postings.

- **Wrote the JD Parser prompt** (`prompts/jd_parser.md`): given the raw text of a
  job posting page, extract a fixed set of facts as JSON — company, role title,
  team, must-have vs nice-to-have requirements, responsibilities, tech stack,
  culture signals, comp range, and location type (remote/hybrid/onsite/unknown).
  Read-only extraction — never invent or infer beyond what's on the page.
- **Added a `JDParserOutput` schema** (`llm/schemas.py`) so every response from
  the model is checked against that exact shape before anything downstream trusts it.
- **Built a test script** (`scripts/test_jd_parser.py`): Playwright opens the job
  page headlessly, grabs the visible text, sends it to the local LLM wrapper with
  the JD Parser prompt, and validates the JSON that comes back.
- **Tested on 3 real, live postings**: two LinkedIn internship listings (Origin,
  Rubrik) and a live IMC "Graduate Software Engineer (2026)" posting from
  Greenhouse. All 3 passed — correct company/role, must-haves vs nice-to-haves
  split correctly, tech stack and culture signals pulled out cleanly.
- **Found and fixed a real prompt bug along the way**: on one posting the model
  returned `"location_type": "hybrid | onsite"` instead of picking one value —
  it was copying the literal `"remote | hybrid | onsite | unknown"` example from
  the prompt instead of treating it as a list of choices. Tightened the prompt's
  example + added an explicit "pick exactly one" rule, and reruns since then have
  returned a single clean value.
- **Noted for later (Day 4/5, not solved now)**: some ATS pages don't hand back
  clean JD text from a simple "grab the visible page text" approach — stale
  Lever links 404, and some Greenhouse "job board" URLs render the company's full
  open-roles list instead of the one posting (likely an iframe/SPA quirk). Workflow
  2's JD fetch step will need to handle this; today's test deliberately used
  postings where plain-text extraction worked so the *agent/prompt* could be
  validated on its own.

**End of Day 3:** given the text of a real job posting, Anchor can reliably turn
it into structured data — the raw material every downstream agent (Match Scorer,
Resume Tailorer, etc.) will work from.

---

## Day 4 — Workflow 2: from URL to researched application

Target: Workflow 2 single-source happy path (news only); Postgres `company` row.

- **Taught the LLM wrapper to load prompts by name**: `/complete` now accepts a
  `system_prompt_name` field — n8n can say `"jd_parser"` instead of pasting the
  whole prompt markdown into a node. The server reads `prompts/<name>.md` from
  disk (with a path-traversal guard) and uses it as the system prompt. Keeps
  `prompts/` "prompt-only" per CLAUDE.md while letting workflows reference
  prompts by short name.
- **Built a small Playwright fetch microservice** (`fetch/`, port 8002): one
  long-lived headless Chrome instance started at app startup, exposing
  `POST /fetch {url} -> {url, text, length}`. This is how Workflow 2 gets
  JS-rendered job pages without n8n needing a native Playwright node.
- **Added a migration** (`db/migrations/001_company_name_unique.sql`): unique
  index on `lower(company.name)` so Workflow 2 can `ON CONFLICT (lower(name))`
  upsert company rows (domain-based dedup is Day 5, once website research lands).
- **Built Workflow 2** (`n8n/workflows/02_job_processor.json`, 10 nodes): Execute
  Workflow Trigger (passthrough) → Load Application → Fetch JD Page (Playwright
  service) → JD Parser Agent (Ollama) → Parse JD → Fetch Company News (Google
  News RSS) → Parse News XML → Extract News Items → Upsert Company → Update
  Application (sets `company_id`, `role_title`, `status = 'researched'`).
- **Wired Workflow 1's deferred handoff**: added the "Execute Workflow - Job
  Processor" node (parallel to "Respond - Accepted", so the webhook still
  responds first) and removed the Day 2 sticky note that flagged this as
  pending. Discovered this n8n version refuses to activate a workflow that
  calls an inactive sub-workflow, so Workflow 2 needed activating too.
- **Found and fixed a real bug**: the two HTTP Request nodes calling the local
  microservices used `http://localhost:8001` / `:8002`, but n8n's Node runtime
  resolves `localhost` to `::1` (IPv6) first while both services only listen on
  `127.0.0.1` (IPv4) — instant `ECONNREFUSED`. Fixed by hardcoding `127.0.0.1`
  in both URLs.
- **End-to-end test**: posted the same live IMC Greenhouse posting from Day 3 to
  `/webhook/intake`. The application row went `intake_received` → `researched`,
  with `role_title = "Graduate Software Engineer (2026)"` and `company_id` set;
  a new `company` row ("IMC") was created with `synthesis.news` holding the top
  5 Google News RSS results. Test rows cleaned up afterward.
- **Noted for later (Day 5)**: "IMC" is a short, generic name — Google News
  returned mostly unrelated stories (softball scores, an unrelated "IMC
  Architecture"). Day 5's Company Synthesizer + additional sources (company
  site, careers page) should give enough context to filter or weight news
  signal quality.
- **Technical note for future Postgres nodes**: n8n's `executeQuery` v2
  `queryReplacement` splits comma-separated values and can mis-bind params for
  free-text strings containing commas. Worked around this by packing all values
  for a query into one `JSON.stringify({...})` resolvable (one `$1` param) and
  extracting fields in SQL via `$1::jsonb->>'key'`. Used for both "Upsert
  Company" and "Update Application".

**End of Day 4:** paste a job URL and, ~30-60s later, Anchor has parsed the
posting, looked up the company's recent news, and marked the application
`researched` — fully automated, no manual steps.

---

## Day 5 — Three more research sources + Company Synthesizer

Target: add 3 more sources to Workflow 2, run them as parallel branches, add
the Company Synthesizer agent.

- **Wrote the Company Synthesizer prompt** (`prompts/company_synthesizer.md`):
  given everything Workflow 2 could gather about a company (news, homepage,
  about page, careers page — any of which may be missing), produce one
  consolidated view: `what_they_do`, `recent_developments`, `tech_signals`,
  `company_type` (startup/enterprise/unknown), `culture_signals`, and
  `likely_role_context`. Rigorous-honesty rule baked in: if the guessed
  domain looks wrong or a source is `(unavailable)`, say so — missing data
  is not evidence the company lacks that quality.
- **Added `CompanySynthesizerOutput`** to `llm/schemas.py` (+ a `CompanyType`
  enum) as the structured-output contract.
- **Built `scripts/test_company_synthesizer.py`** (mirrors the Day 3 JD
  parser test pattern) and validated the prompt standalone against Stripe,
  IMC, and Notion — all passed schema validation with sensible, honestly-
  hedged output before touching the workflow.
- **Grew Workflow 2 from 10 → 22 nodes**:
  - New **"Derive Research URLs"** code node: from the company name, guesses
    a homepage (`https://www.{slug}.com`) and `/about` page, same heuristic
    as Day 4's domain guess. For the careers page, it's smarter — it inspects
    the *original JD URL* and recognizes Greenhouse (`boards.greenhouse.io` /
    `job-boards.greenhouse.io`), Lever (`jobs.lever.co`), and Workday
    (`*.myworkdayjobs.com`) patterns to point at the company's real careers
    board instead of guessing `/careers`.
  - Three new parallel branches (homepage, about, careers), each an HTTP
    request to the Day 4 fetch service with `onError: continueRegularOutput`
    — a dead guess just means that source is unavailable, not a workflow
    failure — followed by a small "Label" code node that truncates to 3000
    chars and sets an `_ok` flag.
  - **"Merge Research"** (Merge node, `combineByPosition`, 4 inputs): joins
    the existing news branch with the three new ones into a single item.
  - **"Prepare Synthesizer Input"**: assembles all four sources (or their
    "(unavailable)" placeholders) plus the role title into the prompt text
    for the synthesizer agent, capped at 12k chars.
  - **"Company Synthesizer Agent"** (LLM wrapper call, `system_prompt_name:
    "company_synthesizer"`, `json_mode: true`) → **"Parse Synthesis"**.
  - **"Upsert Company"** now writes `domain` and the *full* synthesis object
    (including `raw_news` and `sources_available`) into `company.synthesis`,
    keyed on the same `lower(name)` upsert from Day 4's migration.
- **Found and fixed a real bug** in the queryReplacement pattern documented
  at the end of Day 4: that pattern (`JSON.stringify({...})` → one `$1`
  param → `$1::jsonb->>'key'` in SQL) breaks once the object literal has a
  **nested** object inside it (here, `synthesis: { ...$json, raw_news, ... }`
  nested inside the outer `{ name, domain, synthesis }`). n8n's
  `queryReplacement` expression parser can't cleanly extract a single
  resolvable when `{{ }}` wraps an object literal containing its own `{ }`,
  and throws `"Query Parameters must be a string of comma-separated values
  or an array of values"`. Fixed by adding a **"Prepare Company Upsert"**
  code node that flattens everything into simple top-level fields
  (`company_name`, `domain`, `synthesis_json` — the last one already
  JSON-stringified), then using three trivial `{{ $json.field }}`
  placeholders for `$1, $2, $3::jsonb`. Applied the same flattening to
  "Update Application". Rule of thumb going forward: `queryReplacement`
  expressions must be simple property accesses, one per `$n` — build any
  combined JSON blob in a preceding code node, never inline.
- **End-to-end test**: posted the same IMC Greenhouse URL from Day 4 to
  `/webhook/intake`. Application went `intake_received` → `researched`. The
  `company` row for "IMC" now has `domain = "imc.com"` (the slug guess was
  correct this time) and a full `synthesis`: `company_type: "startup"`,
  `tech_signals: ["machine learning", "AI-powered engineering"]`,
  `what_they_do` correctly describes IMC's trading/quant focus (pulled from
  the about/careers pages, both fetched successfully), plus `raw_news` and
  `sources_available: ["news", "about", "careers"]`.
- **Noted for later**: that specific Greenhouse posting (job 4388436101) has
  since closed — "the job you are looking for is no longer open" — so the
  JD Parser correctly returned `role_title: null` and empty
  must-haves/responsibilities for *this* run (honest behavior given a closed-
  posting page, not a bug). `company_id` and the full company synthesis were
  still populated correctly since those don't depend on JD content. Day 6's
  Resume Critic test will use a standalone sample JD rather than depend on
  this posting staying live.

**End of Day 5:** Workflow 2 now researches a company from four angles (news,
homepage, about, careers) in parallel and hands an LLM-synthesized summary —
not just raw scraped text — to `company.synthesis` for every application.

---

## Day 6 — Master resume seed + Resume Critic

Target: master resume table seeded with real resume facts; Resume Critic
working.

- **No real resume exists yet** (confirmed with the user), so
  `db/seed_master_resume.sql` seeds `master_resume_entry` (8 rows — one
  education, one experience, two projects, three skills, one achievement,
  covering all 5 categories) and `user_profile` (1 row — Summer 2026 SWE
  internship goals, backend/AI-infra/dev-tooling interests) with clearly
  "[TEMPLATE]"-marked placeholder content using bracketed fields
  (`[Company]`, `[Project Name]`, etc.). The seed file's header is explicit:
  every "[TEMPLATE]" row must be replaced with real, your-own-voice facts
  before Workflow 3 runs on real applications — the Grounding Critic checks
  for *invented* claims, not placeholder ones, so it won't catch this. Seed
  applied via `psql -d anchor -f db/seed_master_resume.sql` (8 + 1 rows).
- **Wrote the Resume Critic prompt** (`prompts/resume_critic.md`): given the
  master resume entries, user profile, parsed JD, and company synthesis,
  produce `strengths_for_this_role`, `weaknesses_to_address`,
  `gaps_unfixable_in_this_application`, and a `suggested_angle` — the
  narrative thread the Resume Tailorer (Day 7+) will pull through. Same
  rigorous-honesty framing as the other critic/scorer agents: an empty
  `gaps_unfixable_in_this_application` list for a brand-new intern candidate
  would be a red flag, not a clean bill of health.
- **Added `ResumeCriticOutput`** to `llm/schemas.py` as the structured-output
  contract.
- **Built `scripts/test_resume_critic.py`**: loads the seeded
  `master_resume_entry` + `user_profile` rows from Postgres (via `psql -tAc`
  + `json_agg`, no new Python DB dependency), pairs them with a **standalone
  sample JD + company synthesis** (Backend SWE Intern at a fictional
  company, hand-written in the script — deliberately not dependent on a live
  posting, per Day 5's note that test postings go stale), builds the prompt,
  and validates the response against `ResumeCriticOutput`.
- **Ran it successfully**: schema validation passed. Even working from
  bracketed template text, the critic correctly mapped specific resume
  entries to specific JD requirements (Python/FastAPI → tech stack, Postgres
  entry → "crucial for the role", CS degree → education requirement), and
  flagged two honest, specific gaps (no Django experience; no mention of
  improving test coverage/observability) rather than glossing over them.

**End of Day 6:** the resume side of the pipeline has real (if placeholder)
data to work from, and the first resume-facing agent — the Resume Critic —
is prompted, schema-validated, and producing the kind of specific, honest
critique the Match Scorer and Resume Tailorer will build on next.

---

## Day 7 — Match Scorer + low-match decision gate

Target: Match Scorer + decision branch + Slack prompt for low-match (Wait +
Resume).

- **Wrote the Match Scorer prompt** (`prompts/match_scorer.md`): takes the
  Resume Critic's critique + parsed JD + user profile and turns it into a
  single `score` (0-100), `tier` (`hot`/`warm`/`cold`, derived from the score
  — must be consistent with it), `reasoning` (2-4 sentences naming the single
  biggest factor), `top_strengths`, `top_gaps` (every
  `gaps_unfixable_in_this_application` item, each labeled
  `minor`/`significant`/`dealbreaker`), and `red_flags`. Same rigorous-honesty
  framing as the other critic agents: missing must-haves with no substitute
  should land well below 60, unfixable gaps must pull the score down even
  when strengths look strong, and a borderline 58 stays 58 — never rounded up
  to clear the threshold.
- **Added `MatchScorerOutput`** (+ `MatchTier`, `GapSeverity`, `MatchGap`) to
  `llm/schemas.py` as the structured-output contract.
- **Added a Slack bridge to the LLM wrapper**: new `POST /notify-slack`
  endpoint (`llm/server.py`) forwards `{text}` to a Slack Incoming Webhook
  configured via `SLACK_WEBHOOK_URL` (new setting in `llm/config.py` +
  `.env.example`). Keeps the webhook URL out of the committed n8n workflow
  JSON — n8n calls this local endpoint instead of Slack directly.
- **Started Workflow 3** (`n8n/workflows/03_match_and_generate.json`) with
  the Match & Generate skeleton + Day 7's slice: Execute Workflow Trigger →
  parallel Postgres loads (application, JD parse, master resume entries, user
  profile) → Merge Inputs → Prepare Critic Input → Resume Critic Agent →
  Parse Critic Output → Persist Resume Critic → Prepare Scorer Input → Match
  Scorer Agent → Parse Scorer Output → Persist Match Scorer → Update Match
  Score (writes `match_score` onto `application`) → **IF Score >= 60**:
  - **>= 60**: continues into Day 8's tailoring chain.
  - **< 60**: Mark Low Match (`status = 'low_match_waiting'`) → Prepare Slack
    Message (formats score/tier/reasoning/top_gaps/red_flags plus
    Continue/Skip links built from `$execution.resumeUrl?action=...`) → Post
    Low-Match Slack (via `/notify-slack`) → **Wait for Decision** (`resume:
    webhook`, `responseMode: onReceived`) → IF Continue or Skip on the
    `?action=` query param → continues to tailoring on `"continue"`, or Mark
    Withdrawn (`status = 'withdrawn'`) on `"skip"`.
- **Built `scripts/test_match_scorer.py`**: chains Resume Critic → Match
  Scorer against the same standalone sample JD + company synthesis fixtures
  from Day 6/8, and validates both responses against their schemas.
- **Ran it**: Resume Critic reproduced Day 6's honest strengths/gaps; Match
  Scorer scored **68/100 ("warm")** — correctly above 60 given the candidate
  covers all 3 must-haves, with the CI/CD and distributed-systems gaps
  reflected explicitly in `top_gaps`/`reasoning` rather than silently
  absorbed into a higher number. Tier (`warm`) was consistent with the score.

**End of Day 7:** Workflow 3 can now turn a critique into a calibrated match
score, gate on the 60 threshold, and — on a low score — pause for a real
human decision via Slack + n8n's Wait/Resume webhook pattern, exactly as the
non-negotiable constraints require.

---

## Day 8 — Resume Tailorer + Grounding Critic

Target: Resume Tailorer + Grounding Critic; first end-to-end tailored output.

- **Wrote the Resume Tailorer prompt** (`prompts/resume_tailorer.md`): given
  master resume entries (each prefixed with its id), the parsed JD, and the
  Resume Critic's `suggested_angle`, select and rephrase entries into a
  tailored `summary` + per-category `sections`. Hard rule spelled out
  explicitly: tailoring is selection + rephrasing, never invention — every
  line must cite a `master_resume_entry_id`, and rephrasing can't add facts
  (tech, numbers, scope, stronger verbs) beyond what's in the cited entry's
  `canonical_text`. Also documents the retry contract: on a retry, fix
  exactly the violations listed without introducing new ones.
- **Wrote the Grounding Critic prompt** (`prompts/grounding_critic.md`): for
  every tailored line, check it against its cited master entry's
  `canonical_text` and flag any added technology, number/metric, stronger
  verb, broader scope, or cross-entry combination. `passes: true` only if
  *every* line (including the summary) is fully supported; `violations` must
  be specific (quote the phrase, name the entry id, say what's
  missing/overstated) and exhaustive — the tailorer gets one retry, so
  incomplete feedback wastes it.
- **Added `ResumeTailorerOutput`** (+ `TailoredResumeSection`,
  `TailoredResumeLine`, `ResumeEntryCategory`) and **`GroundingCriticOutput`**
  to `llm/schemas.py`.
- **Extended Workflow 3's `>= 60` branch**: Prepare Tailorer Input → Resume
  Tailorer Agent → Parse Tailored Resume → Prepare Grounding Check →
  Grounding Critic Agent → Parse Grounding Output → **IF Grounding Passes**:
  - **pass**: Persist Tailored Resume (`INSERT generated_material`, type
    `tailored_resume`) → Prepare Grounding Rows → Insert Grounding Rows (one
    `material_grounding` row per cited `master_resume_entry_id`) → Finalize
    Material → Mark Awaiting Review (`status = 'awaiting_review'`) → Prepare
    Ready Slack → Post Ready Slack.
  - **fail**: IF Retry Available (`retry_count < 1`) loops back to the Resume
    Tailorer Agent with the violation list as revision feedback; if the retry
    also fails, Prepare Escalation Slack → Post Escalation Slack and **no**
    `generated_material` row is written — review master resume entries and
    the tailorer prompt manually.
  - "Prepare Ready Slack" explicitly notes "(Notion/Drive export lands in Day
    9.)" — Workflow 3 currently ends at `awaiting_review` + a Slack
    notification, not yet the full Cover Letter/PDF/Drive/Notion handoff
    described in the architecture table.
- **Built `scripts/test_resume_tailorer.py`**: runs the full Resume Critic →
  Match Scorer → Resume Tailorer → Grounding Critic chain against the same
  standalone fixtures, validates every response against its schema, and
  additionally checks that every `master_resume_entry_id` the Tailorer cites
  is one of the ids actually loaded from Postgres.
- **Ran it**: full chain passed schema validation end-to-end (Resume Critic →
  Match Scorer 68/"warm" → Resume Tailorer). The Tailorer cited 3 valid entry
  ids across an `experience` and a `skill` section with a plausible tailored
  summary. The Grounding Critic then correctly **failed** the result with 3
  specific violations — e.g. tightening "familiar with SQL" into "Experience
  with SQL and relational database design (Postgres)" added a technology
  (PostgreSQL) and a stronger verb ("proficient") than the `[TEMPLATE]`
  source entry supports. This is the *expected* outcome given Day 6's
  placeholder resume content, and a good sign: the critic is catching exactly
  the kind of subtle overstatement it exists to catch, on real model output —
  not a contrived example. The workflow's retry/escalation path (not
  exercised by this script, which runs each agent once) is what would handle
  this in practice.

**End of Day 8:** the full Resume Critic → Match Scorer → Resume Tailorer →
Grounding Critic chain runs end-to-end with schema-validated outputs at every
step, persists `tailored_resume` + `material_grounding` rows on success, and
marks an application `awaiting_review` with a Slack notification. The core
"Match & Generate" loop — minus cover letter, PDF rendering, and Drive/Notion
export, which are Day 9 — is wired and working.

---

## Day 9 (part 1) — Cover Letter, LinkedIn Drafter, Skill Gap Analyzer + PDF rendering

Target: Cover Letter Generator; PDF rendering; Drive + Notion integration.

- **Wrote the Cover Letter Generator prompt** (`prompts/cover_letter.md`):
  given master resume entries (with ids), the JD, company synthesis, the
  Resume Critic's `suggested_angle`, and the user profile, produce exactly 3
  paragraphs (opening referencing a specific company detail + the role, body
  connecting 1-2 cited master entries to JD requirements, close — no
  clichés), a `master_resume_entry_ids` list, and `company_detail_referenced`.
  Same grounding rule as the Resume Tailorer (selection + rephrasing, no
  invented facts about candidate or company); 250 words is a hard ceiling.
  **Added `CoverLetterOutput`** to `llm/schemas.py` — went through one schema
  revision during testing, from a single `body: str` to `paragraphs: list[str]`
  so the PDF template can render each paragraph as its own `<p>` without
  re-splitting a blob of text.
- **Wrote the LinkedIn Drafter prompt** (`prompts/linkedin_drafter.md`, per
  ADR-004 — no LinkedIn scraping, no named recipients): a generic-audience
  connection note naming the role, one specific company detail, and a brief
  reason for reaching out — no fabricated connections, no "would love to
  connect!" energy. **Added `LinkedInDrafterOutput`** to `llm/schemas.py`.
  - **Found and fixed a real prompt bug**: the model (qwen2.5:7b) blew past
    the 300-character LinkedIn connection-note limit twice in a row (348,
    then 330 chars) even with explicit character-count instructions — it's
    just not reliable at counting characters. Switched the instruction from
    "300 characters" to a word-count proxy ("write no more than 35 words —
    two short sentences, not three"), which the model hit reliably: 288
    chars on the next test.
- **Wrote the Skill Gap Analyzer prompt** (`prompts/skill_gap_analyzer.md`):
  takes the JD's must-haves/nice-to-haves and the Resume Critic's
  `weaknesses_to_address` + `gaps_unfixable_in_this_application`, and turns
  each into a `{requirement, category: must_have|nice_to_have, severity:
  minor|significant|dealbreaker, how_to_close}` entry, plus an overall
  `verdict` (`apply_now` / `address_gap_first` / `not_recommended`) — one
  dealbreaker forces `not_recommended` regardless of strengths.
  `how_to_close` must be realistic for *this application's* timeframe (no
  "get 2 years of experience"). **Added `SkillGapAnalyzerOutput`** (+
  `RequirementCategory`, `SkillGap`, `SkillGapVerdict`) to `llm/schemas.py`.
- **Built `scripts/test_day9_agents.py`**: chains Resume Critic → Match Scorer
  → {Cover Letter, LinkedIn, Skill Gap} against the same standalone
  fictional-company fixtures as Days 6-8. All three passed schema validation;
  cover letter cited valid `master_resume_entry_id`s and stayed under the
  250-word cap, LinkedIn message stayed under 300 chars after the prompt fix,
  and Skill Gap produced a sensible verdict from placeholder resume data.
- **Built PDF rendering** — extended the Day 4/5 `fetch/` Playwright
  microservice with `POST /render-pdf {template: "resume"|"cover_letter",
  data: {...}}`: looks up a Jinja2 template in `pdf/templates/`, renders it
  to HTML, loads that HTML in a headless Chrome page, and returns a PDF via
  `page.pdf()`. Added `pdf_templates_dir` to `fetch/config.py` and `jinja2` to
  `fetch/requirements.txt`.
  - **`pdf/templates/resume.html`**: renders `ResumeTailorerOutput`'s shape
    (`summary` + categorized `sections[].lines[]`), with header fields
    (`candidate_name`, `candidate_email`, `candidate_phone`,
    `candidate_location`) defaulting to bracketed `[Your Name]`-style
    placeholders — same "[TEMPLATE]" convention as the seed data, so a PDF
    rendered before the real resume facts are filled in is honest about that.
  - **`pdf/templates/cover_letter.html`**: renders `CoverLetterOutput`'s
    `paragraphs` list with a sender block, date, "{{ company_name }} Hiring
    Team" recipient, and signoff — same placeholder convention.
  - **`scripts/test_pdf_render.py`**: posts hand-written sample data (shapes
    of `ResumeTailorerOutput`/`CoverLetterOutput`) to `/render-pdf` for both
    templates, writes the resulting PDFs to `data/tmp/`, and checks that an
    invalid `template` value is rejected with 422 (Pydantic's
    `Literal["resume","cover_letter"]` catches it before the handler runs —
    the `TemplateNotFound`/404 branch in the handler is unreachable defensive
    code, kept for if the literal type is ever loosened).
  - **Verified visually**: rendered both templates to PNG via a one-off
    Playwright screenshot script and confirmed layout — resume header,
    summary, and categorized bullet sections render correctly; cover letter's
    sender block, date, recipient, salutation, three paragraphs, and signoff
    all render correctly. Both sample PDFs are valid single-page documents
    (63KB resume, 31KB cover letter).
- **Extended Workflow 3 by 14 nodes** (39 → 53), inserted between "Finalize
  Material" and "Mark Awaiting Review":
  - Prepare Cover Letter Input → Cover Letter Agent → Parse Cover Letter
    Output → Persist Cover Letter (`INSERT generated_material`, type
    `cover_letter`) → fans out to (a) Prepare/Insert Cover Letter Grounding
    Rows (one `material_grounding` row per cited `master_resume_entry_id`,
    side branch — terminates even if the list is empty) and (b) the main
    chain continues to:
  - Prepare LinkedIn Input → LinkedIn Drafter Agent → Parse LinkedIn Output →
    Persist LinkedIn Message (type `linkedin_message`) →
  - Prepare Skill Gap Input → Skill Gap Analyzer Agent → Parse Skill Gap
    Output → Persist Skill Gap Report (type `skill_gap_report`) → **Mark
    Awaiting Review**.
  - "Mark Awaiting Review"'s `queryReplacement` now reads
    `$('Finalize Material').item.json.application_id` instead of `$json`, so
    it no longer depends on the shape of whatever node happens to run just
    before it — same defensive pattern already used by "Prepare Ready Slack".
  - "Prepare Ready Slack" now also reports the skill-gap verdict and notes
    that the cover letter + LinkedIn message were generated; the "(Notion/
    Drive export lands in Day 9)" note became "(Drive/Notion export lands
    next)".
  - All new Code-node JS passed `node --check` syntax validation; prompt-
    building logic mirrors `scripts/test_day9_agents.py`'s
    `build_cover_letter_prompt` / `build_linkedin_prompt` /
    `build_skill_gap_prompt` functions field-for-field.

**Remaining for Day 9**: render the tailored resume + cover letter to PDF via
the new `/render-pdf` endpoint, upload both to Google Drive, create the Notion
row with all materials + match score + skill-gap verdict, and update "Prepare
Ready Slack" with the Drive/Notion links — blocked on the user setting up
Google Drive OAuth2 and Notion API credentials in n8n (guide given, in
progress).

**End of Day 9 (part 1):** Workflow 3 now generates and persists all four
`generated_material` types (`tailored_resume`, `cover_letter`,
`linkedin_message`, `skill_gap_report`) for every application that passes the
match-score gate and grounding check, and the PDF rendering path is built and
visually verified end-to-end — independent of, and ready for, the Drive/Notion
export that completes the workflow.

---

## Day 9 (part 2) — Google Drive + Notion export

Target: wire `/render-pdf`, Drive upload, and Notion page creation into
Workflow 3; finish the "awaiting_review" handoff.

- **Set up credentials in n8n**: walked through Google Cloud Console (enable
  Drive API, OAuth consent screen under the new "Google Auth Platform" UI —
  Audience tab → add self as a test user to clear the "Access blocked: Error
  403: access_denied" screen, Web-application OAuth client with n8n's
  `/rest/oauth2-credential/callback` redirect URI) and Notion
  (internal integration at notion.so/my-integrations → Internal Integration
  Secret → shared the target database with the integration via
  "Connections"). Resulting n8n credentials: `Anchor - Google Drive`
  (`googleDriveOAuth2Api`) and a Notion API credential (`notionApi`, found by
  type via the REST API rather than by name — n8n's credential-rename UI
  wasn't where expected, but the name doesn't matter since only one
  `notionApi` credential exists). User supplied the target Notion database id
  (`3806af3e78ea805fb6b8d1ca4c58188b`) and Drive parent folder id
  (`1b1UHjbDJ1TP03X0dX7p4lybN46FzB5Ug`).
- **Extended Workflow 3 by 14 nodes** (53 → 67), inserted between "Persist
  Skill Gap Report" and "Mark Awaiting Review":
  - **Load JD URL**: small standalone Postgres lookup
    (`SELECT url FROM application WHERE id = $1::uuid`) — `Load
    Application`'s existing query doesn't select the JD url, and the
    9-node `...prior` spread chain was left alone rather than risk breaking
    it.
  - **Prepare Drive Folder Name**: sanitizes company name + role title into
    `{company}_{role}_{ISO date}`, per the planning doc's
    `anchor/applications/{company}_{role}_{date}/` convention.
  - **Create Drive Folder** (Google Drive node, `folder`/`create`) under the
    user's parent folder id.
  - **Prepare Resume PDF Data** → **Render Resume PDF** (HTTP POST to
    `/render-pdf`, `responseFormat: "file"` so the PDF bytes land in
    `binary.data`) → **Upload Resume PDF** (Drive `file`/`upload` into the
    new folder, `name: "Resume.pdf"`).
  - **Prepare Cover Letter PDF Data** → **Render Cover Letter PDF** → **Upload
    Cover Letter PDF** (same pattern, `name: "Cover Letter.pdf"`).
  - **Prepare PDF URL Updates** → **Update Resume PDF URL** / **Update Cover
    Letter PDF URL**: two `UPDATE generated_material SET pdf_drive_url = $1
    WHERE id = $2::uuid` Postgres nodes, populating the previously-unused
    `pdf_drive_url` column for both the tailored-resume and cover-letter
    `generated_material` rows.
  - **Prepare Notion Page** → **Create Notion Page**: `POST
    https://api.notion.com/v1/pages` into the shared database with a flat
    property schema — Name (title: "{Company} — {Role}"), Company, Role
    Title, Application ID, Status, Match Score, Match Tier, Skill Gap
    Verdict, JD URL, Resume PDF, Cover Letter PDF, LinkedIn Message, Created.
    Uses `authentication: "predefinedCredentialType"` /
    `nodeCredentialType: "notionApi"` so the integration secret never appears
    in the workflow JSON, with an explicit `Notion-Version: 2022-06-28`
    header (the credential's default of `2022-02-22` is older than the API
    shape used here). Select-type properties (`Status`, `Match Tier`, `Skill
    Gap Verdict`) rely on Notion auto-creating new select options on page
    creation, so the database doesn't need to be pre-populated with exact
    option lists.
  - **Rewired** `Persist Skill Gap Report → Load JD URL → ... → Create Notion
    Page → Mark Awaiting Review → Prepare Ready Slack → Post Ready Slack` into
    one linear chain, and rewrote **Prepare Ready Slack** to include the Drive
    folder link, the Notion page link, and the skill-gap verdict.
  - **Binary-response state-carrying pattern**: `responseFormat: "file"` HTTP
    nodes reset `json` to `{}` (the PDF bytes go to `binary.data`), which
    breaks the established `...prior`-spread pattern for carrying state.
    Every node downstream of a PDF render therefore reaches back to named
    upstream nodes directly (`$('Finalize Material').item.json...`,
    `$('Persist Cover Letter').item.json.id`, etc.) — the same pattern
    Day 8/9 already used for `Finalize Material`'s `material_id`.
  - Drive folder links aren't returned by `folder`/`create` with
    `simplifyOutput: true` (the default), so the shareable folder URL is
    built manually as `https://drive.google.com/drive/folders/{folderId}`;
    `file`/`upload` *does* return `webViewLink` by default, so the two PDF
    links use that directly.
  - All 6 new/modified Code nodes passed `node --check` syntax validation;
    the full 67-node workflow passed structural checks (no duplicate
    node ids/names, every connection resolves, expected terminal nodes).

- **Imported into n8n**: pushed the updated definition (`PATCH
  /rest/workflows/<id>` — n8n's REST API uses PATCH, not PUT, for workflow
  updates) to the live, active workflow. The on-disk JSON had been two
  updates ahead of n8n (which was still on the Day 8, 39-node version — Day 9
  part 1's 53-node update was never imported either); both jumps landed in
  this one PATCH. Verified post-import: 67 nodes present, still `active:
  true`, new `versionId`, spot-checked node names and the
  `Persist Skill Gap Report → Load JD URL → ... → Create Notion Page → Mark
  Awaiting Review` chain. Definition-only update — no execution triggered, so
  no Drive/Notion/Slack/Postgres side effects yet.

- **Smoke-tested the 6 new Code nodes** without touching Drive/Notion/Slack/
  Postgres: [scripts/test_phase_b_codenodes.js](scripts/test_phase_b_codenodes.js)
  extracts each node's `jsCode` live from the workflow JSON (so it can't drift
  from what's deployed), runs it against hand-built mock upstream data shaped
  like real agent outputs (per `llm/schemas.py`), with Drive/Notion API
  responses mocked but both `/render-pdf` calls real. All 22 checks passed:
  folder-name sanitization, both PDFs rendered (63KB resume, 31KB cover
  letter), `pdf_drive_url` bookkeeping fields line up, the full `notion_body`
  has correct property types (title/rich_text/select/number/url/date) and
  values, and `slack_text` includes the Drive folder link, Notion page link,
  match score, and skill-gap verdict.

**Not yet done**: a live end-to-end test against the real Drive/Notion/Slack
APIs. The only existing application row
(`bfe91458-cd95-429c-8186-54d24bb6c913`, score 58, `low_match_waiting`) hits
the `<60` branch and never reaches Phase B, so testing the new nodes for real
needs either a fresh application that scores >=60 through the full chain, or
manual "pin data + execute" testing of the new nodes in the n8n UI. A true run
would create a real Drive folder + 2 files, a real Notion page, and a real
Slack post — deliberately deferred pending the user's go-ahead.

**End of Day 9 (part 2):** Workflow 3's full chain — Resume Critic → Match
Scorer → Resume Tailorer/Grounding Critic → Cover Letter/LinkedIn/Skill Gap →
PDF render → Drive upload → Notion page → `awaiting_review` + Slack — is fully
designed, wired, and imported into the live n8n instance (67 nodes, active),
pending a live end-to-end test.

## Day 10 — status

Day 10's milestone ("first real application generated via Anchor; review and
submit manually") remains **not started**, blocked on two things that are the
user's call, not engineering work:

1. **Real master resume content.** `db/seed_master_resume.sql` /
   `master_resume_entry` still hold Day 6's `[TEMPLATE]`-marked placeholder
   rows. Two attempts this session to extract real content from uploaded
   resume images both turned out to be generic resume-template-service
   samples (unrelated names/companies/dates), not the user's actual
   background — neither was used. The Grounding Critic only catches
   *invented* claims, not placeholder ones, so this must be real before a
   live run means anything.
2. **A live end-to-end Phase B test.** Workflow 3's Drive/Notion/Slack nodes
   (Day 9 part 2) are imported but never executed for real — doing so creates
   a real Drive folder + files, a real Notion page, and a real Slack post.

Given both blockers are unresolved, Day 11 (independently buildable on disk)
was picked up instead.

## Day 11 — Workflow 4 (Follow-up Scheduler)

Built per planning doc §5.4: daily 8am cron → ghost stale applications →
find applications past their follow-up window → Follow-up Decision Agent
(single call, decides *and* drafts) → persist nudge + event → wait until 9am
→ Slack digest.

- **Follow-up Decision Agent**: prompt at
  [prompts/follow_up_decision.md](prompts/follow_up_decision.md),
  structured-output contract `FollowUpDecisionOutput` (+ `FollowUpDecision`
  enum: `send_now`/`wait`) in [llm/schemas.py](llm/schemas.py). One call per
  application, mirroring the Token-Saving Playbook (§14) — the agent both
  decides whether to nudge *and* drafts the nudge paragraphs in the same
  pass, like the Cover Letter / LinkedIn / Skill Gap agents.
  - **Default to patience**: the prompt frames "no response yet" as the
    normal case, not a problem. `send_now` requires the follow-up window to
    have been reached *and* (no nudge sent yet, or the last one was sent long
    enough ago); 2+ nudges already sent forces `wait` regardless ("further
    nudging reads as pestering").
  - Nudges must reference the real role/company and one concrete detail from
    the company research (same grounding spirit as the cover letter/LinkedIn
    agents) — never an invented referral, connection, or signal.
  - **Prompt fix found via smoke test**: qwen2.5:7b initially got the
    days-vs-window comparison wrong (e.g. called 4/10 days "reached" on one
    run) — the same class of arithmetic-reliability issue as Day 9's LinkedIn
    char-limit fix. Fixed the same way: moved the comparison into code.
    "Prepare Decision Input" now computes `Follow-up window reached: yes/no`
    and the prompt has a hard rule — if `no`, `decision` MUST be `wait`, no
    exceptions. Also tightened tone: "avoid generic openers ('Hi there! I
    hope this message finds you well...') and exclamation points," mirroring
    `linkedin_drafter.md`'s anti-cliché rules.
  - Smoke-tested via
    [scripts/test_follow_up_decision.py](scripts/test_follow_up_decision.py)
    (3 standalone scenarios — window just reached/no nudge yet, window not
    reached, already nudged twice) — all 3 produced the expected
    `send_now`/`wait` decision and schema-valid output.

- **n8n/workflows/04_follow_up_scheduler.json** (14 nodes, not yet imported —
  see below):
  - **Schedule Trigger - Daily 8am** (`scheduleTrigger`,
    `rule.interval: [{field: 'days', daysInterval: 1, triggerAtHour: 8}]`).
  - **Mark Ghosted**: `UPDATE application SET status = 'ghosted' WHERE
    status = 'submitted' AND responded_at IS NULL AND submitted_at <= now() -
    interval '21 days'` — handles the "21-day-old → ghosted, flagged for
    weekly reflection" part of §5.4. No dedicated notification; Workflow 5
    (Weekly Reflection, not yet built) is where ghosted applications get
    surfaced.
  - **Find Due Applications**: one query joining `application` + `company`,
    computing `days_since_submitted`, `follow_up_count`, and
    `last_follow_up_at` (from `generated_material` where
    `type = 'follow_up_nudge'`) per application where
    `status = 'submitted' AND responded_at IS NULL AND submitted_at <= now() -
    (follow_up_window_days || ' days')::interval`. Zero rows → nothing
    downstream executes, no Slack noise on quiet days.
  - Per application: **Prepare Decision Input** (builds the prompt + the
    `Follow-up window reached` flag) → **Follow-up Decision Agent**
    (httpRequest → LLM wrapper, `system_prompt_name: "follow_up_decision"`) →
    **Parse Decision Output** → **IF Should Follow Up**
    (`decision.decision === 'send_now'`).
  - True branch: **Persist Follow-up Nudge** (`generated_material`, type
    `follow_up_nudge`, `content_json` = the full decision object) → **Prepare
    Follow-up Event** → **Insert Follow-up Event** (`application_event`,
    `event_type = 'follow_up_drafted'`, payload = `{material_id, decision,
    reasoning}`).
  - **Merge Decisions** (`merge`, `mode: "append"`, 2 inputs) recombines the
    true branch (after `Insert Follow-up Event`) and the false branch (IF's
    second output) into one stream — purely for sequencing, since both
    branches' Postgres nodes overwrite `json`.
  - **Wait Until 9am** (`wait`, `resume: "specificTime"`, `dateTime:
    "={{ $now.set({ hour: 9, minute: 0, second: 0, millisecond: 0 }) }}"`) —
    the "draft at 8am, deliver at 9am" pattern from §5.4. Since the cron fires
    at 8am, "today at 9am" is always ~1 hour in the future.
  - **Build Digest** (Code, `runOnceForAllItems`) reads
    `$('Parse Decision Output').all()` directly — sidesteps the
    Postgres-overwrites-`json` problem entirely, since it doesn't need
    `Merge Decisions`'s output data, only its *timing* (run after all
    persists finish). Produces one summary: counts of nudges drafted vs.
    applications held off, each with its `reasoning`.
  - **Post Follow-up Digest** (httpRequest → `/notify-slack`, same pattern as
    Workflow 3's "Post Ready Slack").
  - Notion's "Drafts to send" view from §5.4 is **not yet wired** — Workflow 3
    doesn't persist the Notion page id anywhere, so finding "the page for this
    application" would need either a new `application.notion_page_id` column
    (written by Workflow 3) or a Notion database query by the `Application
    ID` property. Deferred rather than bolted on here; the Slack digest +
    `generated_material`/`application_event` rows are enough to review drafts
    via Postgres in the meantime.

- **Validated, not imported**: all 4 Code nodes pass `node --check`; the
  14-node workflow passes the same structural checks as Workflow 3 (no dupes,
  every connection resolves, one root, one terminal node). Additionally,
  [scripts/test_followup_codenodes.js](scripts/test_followup_codenodes.js)
  runs the real `Prepare Decision Input` → (mocked LLM) → `Parse Decision
  Output` → `Prepare Follow-up Event` → `Build Digest` chain against two mock
  "Find Due Applications" rows (one 10/10-day window-reached row, one
  4/10-day not-reached row) — all 14 checks pass, including the digest text
  for both the "drafted" and "held off" cases. Following the pattern set for
  Workflow 3, import into the live n8n instance is deferred — this workflow
  has no applications to act on yet anyway (none are `status = 'submitted'`).

**End of Day 11:** Workflow 4 is fully designed and validated on disk (prompt,
schema, agent smoke test, 14-node workflow, Code-node data-flow test). Not
imported into n8n (nothing for it to do yet — no `submitted` applications
exist). Day 10's two blockers (real resume content, live Phase B test) are
unchanged and still the user's call.

---

## Demo + reliability hardening (post-Day 11, pre-Day-10-resume)

Target: stress-test the full Workflow 3 chain on a realistic (non-template)
resume without touching the user's permanent seed data, since the real resume
(Day 10 blocker #1) hasn't arrived yet.

- Built `scripts/demo_realistic_resume.py`: a standalone run of the full
  Resume Critic → Match Scorer → Resume Tailorer → Grounding Critic → Cover
  Letter → LinkedIn → Skill Gap chain, using 13 genericized fixture entries
  based on a friend's resume (offered "for testing only" — no names, emails,
  or identifying org names included; nothing written to Postgres or
  `db/seed_master_resume.sql`, which remain `[TEMPLATE]`-marked per Day 6).
  Renders both PDFs to `/tmp/anchor_demo/` (not in the repo).
- The first run surfaced 3 real bugs at this larger, more realistic scale that
  hadn't shown up on Day 6-9's 8-entry placeholder fixtures:
  1. Cover Letter paragraphs contained literal `(id=<uuid>)` citation markers
     in the prose, visible in the rendered PDF.
  2. LinkedIn message hit 314 chars, over the 300-char hard limit.
  3. Grounding Critic flagged 5 violations, including a reference to an entry
     that was never cited by the tailored resume at all, and 2 that claimed
     facts (CGPA, "full project lifecycle", "500 beneficiaries") were missing
     when they were verbatim present in the cited source.
- **Fix 1 (LinkedIn length) — prompt only, verified**: tightened
  `prompts/linkedin_drafter.md`'s guidance from "35 words" to "25 words" with
  an explicit self-check ("count the words before you finish"). Re-tested:
  253 and 216 chars on two separate runs, both comfortably under 300.
- **Fix 2 (Cover Letter inline ids) — prompt fix insufficient, added
  code-level backstop**: added explicit "never write `(id=...)`/`(from ...)`
  in prose" rules to `prompts/cover_letter.md`, but a standalone repro showed
  qwen2.5:7b ignored them and still emitted `(id=demo-proj-1)`,
  `(id=demo-skill-2)`, `(id=demo-edu-1, id=demo-exp-1)`. Added a
  `field_validator` on `CoverLetterOutput.paragraphs` in `llm/schemas.py`
  (`_INLINE_CITATION_RE`) that strips any `(id=...)`/`(ids=...)`/`(from
  <id-like-token>)` parenthetical and cleans up the resulting
  whitespace/punctuation — applies automatically on every `model_validate`
  call. Mirrored the same regex in n8n's "Parse Cover Letter Output" code node
  (`03_match_and_generate.json`). Verified on real (non-cached) model output:
  all three citation markers removed, prose reads naturally.
- **Fix 3 (Grounding Critic false positives) — prompt restructure,
  substantially improved**: the original prompt gave the critic two separate
  lists ("Master resume entries" and "Tailored resume") and asked it to
  cross-reference by id — qwen2.5:7b cross-referenced unreliably even when the
  master-entries list was filtered down to only cited entries (5→2 violations,
  but both remaining were still false positives on 100%-verbatim lines).
  Rewrote `prompts/grounding_critic.md`'s Input/Output format entirely: each
  tailored line is now paired *directly* with its cited source's full
  `canonical_text` in a numbered "Lines to check" block (`Line N (from <id>)`
  / `Tailored: "..."` / `Source (<id>): "..."`), eliminating the cross-list
  lookup. Applied the matching `build_grounding_prompt` rewrite to
  `scripts/demo_realistic_resume.py`, `scripts/test_resume_tailorer.py`, and
  the "Prepare Grounding Check" node in `03_match_and_generate.json`.
  - Re-ran the demo: Grounding Critic now returns `passes: true, violations:
    []` on the same 6 cited lines that previously produced 2 false positives —
    the restructuring fixed the originally-reported case.
  - **Residual limitation found on a different fixture**: re-running Day 8's
    smoke test (`scripts/test_resume_tailorer.py`, `[TEMPLATE]`-based entries)
    still produces 2/4 false positives where the tailored line *omits* a few
    words from its source (an explicitly-allowed pattern) and the critic
    incorrectly claims a word that's still present verbatim is "not in the
    Source." The other 2 violations (an invented "internal tooling" detail
    filling a `[bracket]` placeholder, and a summary claiming unsupported
    "robust services"/"observability" capability) are legitimate catches. This
    appears to be a genuine qwen2.5:7b limitation on near-identical-text
    comparison that the restructuring reduced but didn't eliminate. Given the
    workflow's fail-safe design (failed grounding → one retry → escalate to
    Slack with no `generated_material` written, never auto-submit), a false
    positive here means an unnecessary retry/escalation, not bad content
    shipped — left as a known limitation rather than over-tuning a 7B model
    further.
- **Found and fixed an unrelated infra bug along the way**: the LLM wrapper's
  Ollama call used a 120s `httpx` timeout, which intermittently raised
  `ReadTimeout` → 500 on slower back-to-back calls during this session's
  longer demo runs (`/tmp/llm_wrapper.log` confirmed the root cause). Added
  `OLLAMA_TIMEOUT_SECONDS` (default 240) to `llm/config.py`/`.env.example`,
  used in `llm/client.py`. Re-ran both `scripts/test_day9_agents.py` and the
  full demo afterward with zero 500s.

**Status**: 2 of 3 originally-reported bugs fully fixed and verified (LinkedIn
length, Cover Letter inline ids); the 3rd (Grounding Critic false positives)
is substantially improved for the reported case, with one residual
lower-severity limitation documented above. Day 10's two blockers (real resume
content, live Phase B test) are unchanged.

---

## Master resume seed swap (post-Day 11, real-resume blocker)

Per the user's explicit instruction ("use it for now, I'll upload mine when
the project is ready"), promoted the demo's 13 genericized fixture entries
(`DEMO_ENTRIES`/`DEMO_PROFILE` from `scripts/demo_realistic_resume.py`, based
on a friend's resume with no names/contact info/identifying org names) from
"demo-only" to actual seed data:

- Rewrote `db/seed_master_resume.sql`: replaced all 8 `[TEMPLATE]`
  `master_resume_entry` rows and the 1 `[TEMPLATE]` `user_profile` row with
  the 13 entries (education x2, project x4, skill x3, experience x3,
  achievement x1) and the profile's `long_term_goals`/`target_role_types`,
  each with a `facts` jsonb object matching the established pattern. Added
  `DELETE FROM master_resume_entry; DELETE FROM user_profile;` at the top so
  the file is safely re-runnable, and rewrote the header comment to document
  this as temporary genericized content pending the user's own resume — the
  "privacy is crucial" framing from the original instruction still applies
  (no real names, emails, phone numbers, or identifying institution/org
  names anywhere in the file).
- Applied via `psql -d anchor -f db/seed_master_resume.sql`: `DELETE 8`,
  `DELETE 1`, `INSERT 0 13`, `INSERT 0 1`. FK-safe — `material_grounding` had
  0 rows referencing the old entries. Verified row counts and content via
  `psql` (13 `master_resume_entry` rows across all 5 categories, 1
  `user_profile` row matching `DEMO_PROFILE`).

**Status**: Day 10 blocker #1 (real resume content) is resolved *for now* —
Postgres no longer has any `[TEMPLATE]` rows, so Workflow 3 has real material
to tailor against. This is still a stand-in for the user's own resume, which
will replace these rows the same way once ready. Day 10 blocker #2 (live
Phase B end-to-end test) is unchanged, and this session's edits to
`03_match_and_generate.json` (Grounding Critic restructure, Cover Letter
citation strip) still need to be pushed to the live n8n instance before that
test can run.

---

## Day 12 (part 1, on-disk) — Error workflow + retry logic

Per planning doc §5.6, scoped to what's buildable purely on-disk first (live
import + failure-path testing by killing services is part 2, see "Status"
below).

- **Built [n8n/workflows/00_error_handler.json](n8n/workflows/00_error_handler.json)**
  (6 nodes): `n8n-nodes-base.errorTrigger` → Parse Error Context → Prepare
  Error Event → Insert Error Event (Postgres, `application_event` type
  `error`) → Prepare Slack Alert → Post Slack Alert (`/notify-slack`).
  - **Design decision — why this is simpler than planning §5.6's literal
    steps 3/5**: n8n's Error Trigger payload only contains execution/workflow
    metadata (`execution.id`, `.url`, `.error.message`, `.error.stack`,
    `.lastNodeExecuted`, `workflow.id`, `.name`) — it does **not** expose the
    failed execution's node data, so there's no reliable `application_id` to
    act on at this level. Two options considered: (a) call n8n's own REST API
    from this workflow to fetch the full failed execution and grep its node
    outputs for `application_id` (needs a new n8n API key credential — new
    infra surface, and the extracted id could be a false-positive UUID match,
    risking an `application_event.application_id` FK violation on insert), or
    (b) keep the handler infra-free and put the burden on the human via the
    Slack alert's execution URL. Chose (b): `application_id` is always `NULL`
    in the `application_event` row this workflow inserts, and the Slack alert
    includes the execution URL plus a copy-pasteable
    `UPDATE application SET status = 'errored' WHERE id = '<application_id>'`
    template for the human to fill in after opening the execution. Step 3's
    "retry with exponential backoff (max 2 retries)" is likewise handled
    *before* this workflow ever fires — see retryOnFail below — so
    `error_class` (transient-looking vs permanent, via regex on the error
    message: timeout/ECONNRESET/ECONNREFUSED/429/502/503/504 → "transient
    (retries exhausted)", else "permanent") is informational only, shown in
    the Slack message for triage.
  - Smoke-tested via
    [scripts/test_error_handler_codenodes.js](scripts/test_error_handler_codenodes.js)
    (extracts the 3 Code nodes' `jsCode` live from the workflow JSON, runs a
    transient-classified scenario — HTTP 503 from "Fetch News" — and a
    permanent-classified scenario — a Pydantic validation error with no
    execution URL) — all 15 checks pass, including that the "Execution: ..."
    line is omitted when `execution_url` is null.
- **Retry logic**: added `retryOnFail: true, maxTries: 3, waitBetweenTries:
  2000` (3 tries total = 1 + 2 retries, 2s between, per planning §5.6 step 3)
  to every `n8n-nodes-base.httpRequest` node across
  `00_error_handler.json`/`02_job_processor.json`/`03_match_and_generate.json`/`04_follow_up_scheduler.json`
  (23 nodes total: LLM wrapper `/complete` calls, the fetch microservice's
  `/fetch`/`/render-pdf`, Google News RSS, Notion's `/v1/pages`, and all
  `/notify-slack` calls). Workflow 01 has no `httpRequest` nodes, so nothing
  to change there. Scoped to HTTP nodes only — Postgres `executeQuery` nodes
  were deliberately left alone, since retrying an `INSERT`/`UPDATE` after an
  ambiguous (e.g. connection-dropped-after-commit) failure risks a duplicate
  write; n8n's fixed `waitBetweenTries` is also a documented simplification
  of "exponential backoff" (n8n doesn't support per-try backoff growth
  natively).
  - **Found and fixed a real pre-existing bug along the way**: CLAUDE.md's
    Day 4/5 notes claim all 4 of Workflow 2's research branches (news,
    homepage, about, careers) are "tolerant of fetch failure via `onError:
    continueRegularOutput`" — but "Fetch Company News" was missing that
    setting entirely, so a failed/blocked Google News RSS request would have
    failed the whole Job Processor execution for that application (contrary
    to the documented design). Added `onError: continueRegularOutput` to
    match its 3 siblings.
- Re-validated all 4 touched workflow files: node counts unchanged (6/25/67/14),
  no duplicate ids/names, all connections resolve, `active` flags unchanged
  (02 stays `true`; 00/03/04 stay `false`), and `node --check` passes on every
  Code node's `jsCode`. Re-ran
  [scripts/test_phase_b_codenodes.js](scripts/test_phase_b_codenodes.js) and
  [scripts/test_followup_codenodes.js](scripts/test_followup_codenodes.js) as
  a regression check — both still pass (22 + 5 checks).

**Status**: on-disk artifacts for Day 12's "error workflow" and "retry logic"
items are done and tested. Part 2 (live import/wiring) is now also done — see
"Day 12 (part 2, live) — error workflow import + wiring + failure-path test"
below.

---

## Second test fixture (technical/backend-heavy resume)

Added [scripts/fixtures_technical_resume.py](scripts/fixtures_technical_resume.py):
a second `DEMO_ENTRIES`/`DEMO_PROFILE` pair, same shape as
`demo_realistic_resume.py`'s, genericized from a second friend's resume
offered "for testing" (no name/email/phone/LinkedIn/GitHub/institution/company
names included). 13 entries (education x2, experience x2, project x6, skill
x3) covering a .NET/C# backend internship, an NLP/knowledge-graph/GNN patent
platform, an ML cloud-intrusion-detection project, and a CV pothole-detection
project — a more technical/backend/ML-heavy profile than the first fixture's
generalist/leadership one. Not wired into any script or seed data — just an
alternative fixture set for future demo/test runs against a different
applicant profile (e.g. more technical JDs).

---

## Day 12 (part 2, live) — error workflow import + wiring + failure-path test

Per the user's go-ahead ("proceed with whatever is pending"), completed the
live-touching parts of Day 12 deferred in part 1.

- **n8n REST auth**: `POST /rest/login` with `{emailOrLdapLoginId, password}`
  (not `email` — n8n 2.8.4 renamed the field) using the owner credentials in
  `.env`, returns an `n8n-auth` session cookie used for all subsequent REST
  calls.
- **Pushed updated 02/03 definitions** via `PATCH /rest/workflows/<id>`
  (`02 - Job Processor` = `6c1GWSWFB30upbH2`, `03 - Match and Generate` =
  `x189x3S4YZQTVctl`), sending `{name, nodes, connections, settings}` from the
  on-disk JSON. Diffed on-disk vs. live first: 02 had exactly the 7
  `retryOnFail`/`onError` node diffs from part 1; 03 had the 13
  `retryOnFail` httpRequest nodes plus the 2 Code-node fixes (`Prepare
  Grounding Check` restructure, `Parse Cover Letter Output` citation-strip)
  from the post-Day-11 hardening session. Post-push diff against on-disk is
  empty for both. `active` untouched (02 stayed `true`; 03 stayed `true` live
  — note live 03 has been `active: true` since at least Day 9 despite the
  on-disk export saying `false`, a pre-existing discrepancy not touched here).
- **Imported `00_error_handler.json`** via `POST /rest/workflows` → assigned
  id `hULM9d6nFUMdite1`, created `active: false` (new workflows can't be
  created active).
- **Activating an error-only workflow**: `PATCH /rest/workflows/<id>` with
  `{"active": true}` silently no-ops (n8n's PATCH ignores `active`). The real
  endpoint is `POST /rest/workflows/<id>/activate` with
  `{versionId, name, expectedChecksum}` (optimistic-concurrency fields read
  from a fresh GET) — this returned `active: true,
  activeVersionId: <versionId>`. **This step is not optional**: read n8n
  2.8.4's `workflow-execution.service.js` (`executeErrorWorkflow`) — if
  `workflowData.activeVersion === null`, it logs an error and returns without
  running the error workflow at all. An inactive `settings.errorWorkflow`
  target is silently never invoked.
- **Wired `settings.errorWorkflow: "hULM9d6nFUMdite1"`** into all 4 workflows'
  `settings` (on-disk JSON for 01-04, plus live PATCH for the now-live 01/02/03
  using the same diff-then-push pattern as above — 01 had zero other diffs
  from live, confirmed before pushing).
- **Imported `04_follow_up_scheduler.json`** via `POST /rest/workflows` →
  assigned id `5QC5r8KK8u2hWhj5`, `active: false`. Left inactive deliberately
  — activating it would start the daily 8am Schedule Trigger, and per the
  original Day 11 deferral there's still nothing for it to act on
  (`status='submitted'` has 0 rows). Revisit once an application reaches
  `submitted`.
- **Failure-path test (real side effects)**: discovered n8n 2.8.4's manual-run
  API, `POST /rest/workflows/<id>/run`, body
  `{workflowData: <full def with id + pinData>, triggerToStartFrom: {name:
  "<trigger node>"}}` — `pinData[<trigger node name>]` supplies the mock
  trigger output as `[{json: {...}}]`. Used this to run `00 - Error Handler`
  end-to-end from a hand-built Error Trigger payload (workflow
  `x189x3S4YZQTVctl` / "03 - Match and Generate", failed node "Resume Critic
  Agent", a descriptive message, no transient keywords -> classified
  `permanent`). Execution 25 finished `status: success`. Verified real side
  effects: `application_event` row `f0d07e90-c958-451d-b7c8-a6b10271fb7a`
  (`application_id` NULL, `event_type='error'`, full payload incl.
  `execution_url`) inserted into Postgres, and "Post Slack Alert" (terminal
  node) executed without error — i.e. the `/notify-slack` POST went through.
  This validates the workflow-00 internals for real (Postgres credential,
  query syntax, Slack webhook) on top of part 1's pure-jsCode unit test.
  (Did not separately re-test "kill a live service mid-run" — that exercises
  the *retryOnFail* config already validated structurally in part 1, whereas
  this test exercises the *error-workflow* config, which was the part with no
  prior live validation.)

**Status**: all 4 of part 1's deferred items are done — 00 imported and
active, `errorWorkflow` wired on 01-04 (04 still inactive pending a
`submitted` application), 02/03 retryOnFail+fixes live, and workflow 00
validated end-to-end with a real Postgres insert + Slack post.

---

## Day 10 milestone attempt — re-score existing application against new seed

Used the same manual-run API to re-run `03 - Match and Generate` for the one
existing application (`bfe91458-cd95-429c-8186-54d24bb6c913`, the Airbnb
Greenhouse posting, previously scored 58/`low_match_waiting` against
`[TEMPLATE]` resume data) — trigger node "When Executed by Another Workflow",
`pinData: [{json: {id: "bfe91458-..."}}]`. Goal: with the seed swapped to the
13 real(ish) genericized entries (see "Master resume seed swap" above), see
whether the score now clears 60 and reaches Phase B for a live Drive/Notion/
Slack test (Day 10's milestone).

**Result: still 58/"cold"** (execution 26). New `agent_run` rows for
`resume_critic` and `match_scorer` were written (re-run against the new
resume + profile), `application.match_score` was re-set to 58 (same number,
recomputed), and the Match Scorer's reasoning now reflects the *real* new
resume content rather than `[TEMPLATE]` placeholders: *"While the candidate
has strong project management and leadership experience, there is a lack of
clear tech stack alignment with Airbnb's requirements, particularly in
AI/ML."* This is the rigorous-honesty outcome working as designed — richer
resume content didn't manufacture a higher score where the actual skill
overlap (an AI/ML-heavy Airbnb SWE internship vs. a generalist CS/leadership
profile) isn't there.

Score `< 60` → "Mark Low Match" (status already `low_match_waiting`, no
change) → "Post Low-Match Slack" (a **second** low-match Slack message for
this same application, with a new Continue/Skip link bound to *this*
execution's resume URL) → "Wait for Decision". **Execution 26 is now parked
in `waiting` status** on a real webhook-resume Wait node — per the
no-auto-skip/no-auto-continue rule, this was left unresolved; it's a genuine
pending human decision (now duplicated: 2026-06-14's original low-match
decision for this application, plus this re-run's, both ultimately about the
same "continue with this 58/cold Airbnb application or skip it" choice).

**Net status**: Day 10 blocker #2 (a live Phase B run producing a real Drive
folder, Notion page, and "Ready" Slack message) is still open. The richer
seed data didn't change the verdict for *this specific* posting. Getting a
live ≥60 Phase B run needs either (a) a different/new job posting that's a
better fit for this resume's generalist/leadership profile, or (b) a
deliberate gate-bypass test (e.g. manual execution starting from "Resume
Tailorer" with hand-built input, skipping the Match Scorer entirely) — both
require a decision the user should make, so this was not pursued further
without checking in.

**User decision**: asked what to do with the two paused "Wait for Decision"
executions (24, 26) for this application — answer was to leave both paused
indefinitely and start Day 13. Neither execution was touched.

---

## Day 13 — Workflow 5 (Weekly Reflection + Pattern Detector)

Built per planning doc §5.5: Sunday-7pm cron → aggregate the last 4 weeks of
`application` data → Pattern Detector Agent (with the §17 min-N=5 guard) →
write `weekly_insight` row → Slack digest.

- **Pattern Detector Agent**: prompt at
  [prompts/pattern_detector.md](prompts/pattern_detector.md),
  structured-output contract `PatternDetectorOutput` (+ `Pattern`,
  `PatternConfidence` enum `low`/`medium`/`high`) in
  [llm/schemas.py](llm/schemas.py). Single call per run — input is one
  precomputed text block (window stats), output is `{patterns[], summary}`.
  - **Min-N=5 guard, precomputed**: same pattern as Day 11's "Follow-up
    window reached: yes/no" — qwen2.5:7b can't reliably do this kind of
    threshold reasoning unprompted, so "Prepare Pattern Detector Input"
    computes `N` and a `Minimum sample size reached (N >= 5): yes/no` line
    up front. The prompt has a hard rule: if `no`, `patterns` MUST be `[]`
    and `summary` must plainly state there's not enough data yet (citing N
    and 5) rather than speculating about future patterns.
  - When the guard passes, each pattern requires >= 2 applications in *each*
    group being compared (so a 1-vs-8 split can't masquerade as a pattern),
    and `confidence` (`low`/`medium`/`high`) is meant to reflect how much of
    N the pattern is based on and how large the gap is.
  - **Prompt fix found via smoke test**: the first run of the N=6
    startup-vs-enterprise scenario (real startup response rate 2/3 = 67%)
    came back with `evidence: "3 out of 3 startup applications got a
    response vs. 0 out of 3 enterprise applications"` — qwen2.5:7b re-derived
    the ratio from the "3 application(s)" count and got it wrong, the same
    class of numeric-reliability issue as Day 9's char-limit fix and Day 11's
    days-vs-window fix. Fixed by tightening the `evidence` rule to require
    **copying the exact `"X/Y (Z%)"` string verbatim** from the input's
    breakdown lines rather than recomputing or rephrasing it. Re-ran the same
    scenario afterward: `evidence: "2/3 (67%) for startups vs. 0/3 (0%) for
    enterprise"` — correct, copied character-for-character.
  - Smoke-tested via
    [scripts/test_pattern_detector.py](scripts/test_pattern_detector.py),
    two scenarios: (1) N=1 — the real current Postgres state (one
    `low_match_waiting` application) — returned `patterns: []` and a summary
    citing "1" and the minimum of "5"; (2) N=6 hypothetical with a clear
    startup (2/3 responded) vs. enterprise (0/3 responded) gap — returned one
    `high`-confidence pattern with the verbatim `2/3 (67%)` / `0/3 (0%)`
    evidence above. Both schema-valid.

- **n8n/workflows/05_weekly_reflection.json** (8 nodes, imported inactive —
  see below):
  - **Schedule Trigger - Sunday 7pm** (`scheduleTrigger`,
    `rule.interval: [{field: 'weeks', weeksInterval: 1, triggerAtDay: [0],
    triggerAtHour: 19}]` — `0` = Sunday per n8n's weekday encoding).
  - **Aggregate Last 4 Weeks** (Postgres): one query joining `application` +
    `company`, with a correlated subquery pulling each application's latest
    `match_scorer` `agent_run.output_json->>'tier'`, filtered to
    `created_at >= now() - interval '28 days'`. Returns one row per
    application (role, company, `company_type` from `company.synthesis`,
    `match_score`, `match_tier`, `status`, timestamps). Zero rows is a normal
    case (handled below, not an error).
  - **Prepare Pattern Detector Input** (Code, `runOnceForAllItems`): computes
    `N`, `min_n_reached` (`N >= 5`), `week_start` (Monday of the
    Sunday-ending week), and builds the prompt text — status breakdown,
    average match score, match-tier breakdown with response rates, company-
    type breakdown with response rates, and a per-application list. "Response"
    = status in `responded` or `interview`.
  - **Pattern Detector Agent** (httpRequest → LLM wrapper,
    `system_prompt_name: "pattern_detector"`, `json_mode: true`,
    `retryOnFail`).
  - **Parse Pattern Detector Output** (Code): parses the JSON, carries
    `n`/`min_n_reached`/`week_start` through alongside `pattern_output` and
    `pattern_output_json` (for the INSERT) and `pattern_model_used`.
  - **Persist Weekly Insight** (Postgres): `INSERT INTO weekly_insight
    (week_start, insights) VALUES ($1::date, $2::jsonb)`.
  - **Build Digest** (Code) reads `$('Parse Pattern Detector Output').item.json`
    directly — same Postgres-overwrites-`json` workaround as Day 9/11's
    `Finalize Material`/`Build Digest`. Renders the week's application count
    and `summary` always; renders a `Patterns:` section (one bullet per
    pattern with observation/confidence/evidence/suggested action) only when
    `min_n_reached` is true *and* `patterns` is non-empty — so a guard-respecting
    "not enough data" response never shows an empty or misleading "Patterns:"
    header.
  - **Post Weekly Digest** (httpRequest → `/notify-slack`, `retryOnFail`).
  - `settings.errorWorkflow: "hULM9d6nFUMdite1"` wired from creation (same as
    01-04).

- **Validated**: 8 nodes, no dupes, single linear chain from the trigger to
  `Post Weekly Digest` (1 root, 1 terminal). All 3 Code nodes pass `node
  --check`.
  [scripts/test_weekly_reflection_codenodes.js](scripts/test_weekly_reflection_codenodes.js)
  runs `Prepare Pattern Detector Input` -> (mocked LLM) -> `Parse Pattern
  Detector Output` -> `Build Digest` for both the N=1 and N=6 scenarios above
  (21 checks) — including that the N=1 digest has no `Patterns:` section at
  all, and the N=6 digest's evidence text matches the exact `2/3 (67%)` /
  `0/3 (0%)` figures.

- **Imported, inactive**: same procedure as Workflow 4 — `POST
  /rest/workflows` with `{name, nodes, connections, settings}` (no `active`
  field, so n8n creates it `active: false`) → id `Mk8farJ0Ekw2yV7Q`. Left
  inactive deliberately: with
  only 1 application in Postgres, a live Sunday-7pm run would just reproduce
  the N=1 "not enough data" case already covered by the smoke test, and
  activating would also start a real weekly Schedule Trigger. Revisit once
  there are >= 5 applications for the min-N guard to have something to say.

**End of Day 13:** Workflow 5 is fully designed, validated on disk, and
registered in n8n inactive (prompt, schema, agent smoke test covering both
sides of the min-N=5 guard, 8-node workflow, Code-node data-flow test). Day
10's two blockers (resume content — resolved with placeholder data; live
Phase B test) are unchanged, and executions 24/26 remain paused per the
user's explicit instruction.

---

## Day 18 — Real resume seed + eval re-run (2026-06-16)

**Real resume arrived.** The user uploaded their actual resume; the genericized
friend's-resume placeholder content was replaced everywhere it appeared:

- **`db/seed_master_resume.sql`** rewritten with 14 real entries (2 education
  at RVCE + NPS; 2 experience at KuKClean as Product & Design Intern with 30+
  design files and 20+ product listings; 6 project entries covering Meridian
  — 4-agent system with 135-claim eval, 15% avg hallucination rate, financial
  agent 0% — and Anchor and CrowdSense; 3 skill entries; 1 achievement/certs).
  Applied via `DELETE + re-INSERT`; `material_grounding` cleared first (FK
  safety). Postgres now has 14 `master_resume_entry` rows + 1 `user_profile`
  row with a goals/target-roles statement aligned to ML engineering and AI
  systems internships.

- **`scripts/demo_realistic_resume.py`** `DEMO_ENTRIES`/`DEMO_PROFILE` updated
  to match the seed exactly (same IDs used by the benchmark, e.g.
  `sk-proj-meridian-sys`, `sk-skill-ai-ml`). The old eval outputs in
  `eval/tailored_outputs/` (17 files, based on the friend's resume) are stale
  and should be cleared with `rm eval/tailored_outputs/*.json` before re-running.

- **Eval re-running:** `eval/benchmark.py tailored --start 0 --end 20` started
  against the real candidate profile and the 20 standalone JD fixtures in
  `eval/jd_fixtures.py`. The fixtures were written for the old generalist
  profile, but the ML/AI-heavy entries (08_ai_tools_eng, 09_backend_fastapi,
  01_fullstack_startup) should score well for the real profile; PM/QA/ops JDs
  will score low as expected. `eval/benchmark.py baseline --start 0 --end 20`
  to follow once tailored completes. `eval/benchmark.py summary` generates
  `eval/results_summary.md` and the headline grounding comparison table for
  the README.

- **CLAUDE.md** status updated to "Day 18 of 18."
