# Material Quality Eval — Grading Rubric

Per planning doc §10.1. 20 applications generated via `eval/benchmark.py`
against the standalone JD fixtures in `eval/jd_fixtures.py` (same seeded
master resume as Postgres — `scripts/demo_realistic_resume.py`'s
`DEMO_ENTRIES`/`DEMO_PROFILE`). Each application has an **Anchor** output
(`eval/tailored_outputs/<id>.json` — full Resume Critic → Match Scorer →
Resume Tailorer → Grounding Critic [1 retry] → Cover Letter → LinkedIn →
Skill Gap chain) and a **baseline** output
(`eval/baseline_outputs/<id>.json` — single-prompt `prompts/baseline_tailor.md`,
no critic, no grounding instructions).

## Dimensions

### 1. Factual grounding (binary, automated — the headline metric)

Does every line of the tailored resume trace back to something the master
resume actually says? This is computed automatically by the **same**
Grounding Critic agent for both Anchor and baseline:

- **Anchor**: `tailored_outputs/<id>.json` → `grounding.passes` /
  `grounding.violations` — checked against the *single cited entry* each
  line claims to be drawn from (`material_grounding`'s real check).
  `escalated: true` means even the one allowed retry didn't produce a fully
  grounded resume (Workflow 3 would not ship this material — a safety
  property, not a failure to record as "ungrounded content shipped").
- **Baseline**: `baseline_outputs/<id>.json` → `grounding.passes` /
  `grounding.violations` — checked against the candidate's *full* resume
  (the baseline doesn't cite entry ids, so there's no single source to pair
  against; "is this claim supported anywhere in the resume?" is the fairest
  equivalent check).

No hand-grading needed for this dimension — `eval/benchmark.py summary`
aggregates both pass rates into `eval/results_summary.md`.

**Expected outcome (§10.1)**: Anchor's grounding pass rate should
substantially exceed the baseline's — prior testing suggested baseline
hallucination rates around 20-30%.

### 2. JD relevance (1-5, hand-graded)

For both the Anchor and baseline tailored resume + summary, how well do the
selected/emphasized bullets match *this specific JD's* must-haves,
nice-to-haves, and responsibilities (in `eval/jd_fixtures.py`)?

- **5** — Every must-have that the candidate has *any* relevant background
  for is reflected; bullets are ordered/framed around this JD's priorities.
- **3** — Generally on-topic, but misses an obvious opportunity to connect a
  relevant entry to a JD requirement, or includes a couple of low-relevance
  bullets ahead of more relevant ones.
- **1** — Reads like a generic resume; little evidence the JD was used to
  select or order content.

**Expected outcome (§10.1)**: Anchor should roughly match baseline here —
this is not where Anchor's value proposition lies.

### 3. Cover letter specificity (1-5, hand-graded)

How company-specific vs. generic is the cover letter
(`cover_letter.paragraphs` / `baseline.cover_letter_paragraphs`)? Check
against `eval/jd_fixtures.py`'s `synthesis` block (what the company does,
recent developments, culture signals).

- **5** — References specific, fixture-accurate details about the company
  (what they build, a recent development, a culture signal) woven into the
  argument for why the candidate fits.
- **3** — Mentions the company/role by name and tech stack, but the
  reasoning could apply to most companies in the same space.
- **1** — Could be sent to any company with a find-and-replace on the name.

### 4. Tone match (1-5, hand-graded, Anchor only)

Does the tailored resume/cover letter sound like *the candidate's own
voice* rather than generic LLM-speak (buzzwords, inflated verbs, "passionate
about leveraging synergies")?

- **5** — Plain, concrete, matches the register of the source
  `canonical_text` entries.
- **3** — Mostly fine, with a few stock phrases that read as LLM-generated.
- **1** — Saturated with corporate-LLM phrasing, disconnected from how the
  source entries are actually written.

Baseline is not scored on tone — without grounding constraints its tone is
expected to be generically "confident LLM," which isn't a meaningful
comparison.

## How to grade

1. Run the benchmark (already done for the 20 fixtures, see
   `eval/tailored_outputs/` and `eval/baseline_outputs/`).
2. Run `.venv/bin/python eval/benchmark.py summary` — writes
   `eval/results_summary.md` (grounding headline numbers, automated) and
   `eval/scores_template.csv` (one row per application, grounding columns
   pre-filled, dimensions 2-4 blank for hand-grading).
3. Open each `tailored_outputs/<id>.json` / `baseline_outputs/<id>.json`
   alongside the matching `eval/jd_fixtures.py` entry, fill in
   `eval/scores_template.csv` columns 2-4 (1-5 each).
4. Average each column across the 20 rows for the final eval numbers to cite
   in the README (per roadmap Day 17).
