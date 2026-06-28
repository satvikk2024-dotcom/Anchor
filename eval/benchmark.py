"""
Material Quality Eval benchmark (planning doc §10.1, roadmap Days 15-16).

Runs the full Anchor Phase-B agent chain (Resume Critic -> Match Scorer ->
Resume Tailorer -> Grounding Critic [with one retry] -> Cover Letter ->
LinkedIn Drafter -> Skill Gap Analyzer) against the 20 standalone JD fixtures
in jd_fixtures.py, using the same seeded master-resume fixture
(scripts/demo_realistic_resume.py's DEMO_ENTRIES/DEMO_PROFILE) that's loaded
into Postgres via db/seed_master_resume.sql.

Also runs a single-prompt "baseline" (prompts/baseline_tailor.md, no critic,
no grounding instructions) against the same fixtures, then runs the existing
Grounding Critic post-hoc against the baseline's output (checked against the
candidate's full resume, since the baseline doesn't cite entry ids) — giving
an apples-to-apples grounding-violation comparison, which is the eval's
headline metric per §10.1.

Usage:
    .venv/bin/python eval/benchmark.py tailored --start 0 --end 10
    .venv/bin/python eval/benchmark.py baseline --start 0 --end 20
    .venv/bin/python eval/benchmark.py summary

Requires the LLM wrapper running: .venv/bin/uvicorn llm.server:app --port 8001
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from demo_realistic_resume import (  # noqa: E402
    DEMO_ENTRIES,
    DEMO_PROFILE,
    MAX_PROMPT_CHARS,
    build_cover_letter_prompt,
    build_critic_prompt,
    build_grounding_prompt,
    build_linkedin_prompt,
    build_scorer_prompt,
    build_skill_gap_prompt,
    build_tailorer_prompt,
    call_llm,
    profile_lines,
)
from jd_fixtures import FIXTURES  # noqa: E402
from llm.schemas import (  # noqa: E402
    BaselineTailorOutput,
    CoverLetterOutput,
    GroundingCriticOutput,
    LinkedInDrafterOutput,
    MatchScorerOutput,
    ResumeCriticOutput,
    ResumeTailorerOutput,
    SkillGapAnalyzerOutput,
)

TAILORED_DIR = ROOT / "eval" / "tailored_outputs"
BASELINE_DIR = ROOT / "eval" / "baseline_outputs"
ENTRY_IDS = {e["id"] for e in DEMO_ENTRIES}


def build_tailorer_retry_prompt(entries: list[dict], jd: dict, critic: ResumeCriticOutput, violations: list[str]) -> str:
    base = build_tailorer_prompt(entries, jd, critic)
    feedback = "\n".join(f"- {v}" for v in violations)
    return (base + "\n\n## Revision feedback (from a previous attempt — fix exactly these lines)\n" + feedback)[
        :MAX_PROMPT_CHARS
    ]


def build_baseline_prompt(entries: list[dict], profile: dict | None, jd: dict) -> str:
    entry_lines = "\n".join(f"- [{e['category']}] {e['canonical_text']}" for e in entries)
    jd_lines = "\n".join(
        [
            f"Role: {jd['role_title']} (team: {jd.get('team_or_org') or 'unspecified'})",
            f"Company: {jd['company_name']}",
            f"Must-haves: {', '.join(jd['must_haves'])}",
            f"Nice-to-haves: {', '.join(jd['nice_to_haves'])}",
            f"Responsibilities: {', '.join(jd['responsibilities'])}",
            f"Tech stack: {', '.join(jd['tech_stack'])}",
            f"Culture signals: {', '.join(jd['culture_signals'])}",
        ]
    )
    prompt = "\n\n".join(
        [
            "## Candidate's resume background",
            entry_lines,
            "## Candidate's career goals",
            profile_lines(profile),
            "## Job description",
            jd_lines,
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def build_baseline_grounding_prompt(entries: list[dict], baseline: BaselineTailorOutput) -> str:
    """Pair each baseline line against the candidate's *full* resume (the
    baseline doesn't cite entry ids, so there's no single source to pair
    against)."""
    full_resume = "\n".join(f"- [{e['category']}] {e['canonical_text']}" for e in entries)
    blocks = []
    n = 0
    for section in baseline.sections:
        for line in section.lines:
            n += 1
            blocks.append(
                "\n".join(
                    [
                        f"Line {n} [{section.category.value}] (from full-resume)",
                        f'Tailored: "{line.text}"',
                        f'Source (full-resume): "{full_resume}"',
                    ]
                )
            )

    prompt = "\n\n".join(
        [
            "## Lines to check\nEach numbered item pairs one tailored-resume line with the "
            "candidate's full resume as its source. Check whether the line's claims are "
            "supported anywhere in the full resume.",
            *blocks,
            f'## Summary to check\nTailored summary: "{baseline.summary}"\nCheck the summary '
            "against the full resume above — it should not introduce facts beyond what it supports.",
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def run_tailored(fixture: dict) -> dict:
    jd = fixture["jd"]
    synthesis = fixture["synthesis"]
    entries = DEMO_ENTRIES
    profile = DEMO_PROFILE
    result: dict = {"id": fixture["id"], "company_name": jd["company_name"], "role_title": jd["role_title"]}

    # 1. Resume Critic
    critic_data = call_llm(build_critic_prompt(entries, profile, jd, synthesis), "resume_critic")
    critic = ResumeCriticOutput.model_validate(critic_data)
    result["critic"] = critic.model_dump()

    # 2. Match Scorer
    scorer_data = call_llm(build_scorer_prompt(critic, profile, jd), "match_scorer")
    scorer = MatchScorerOutput.model_validate(scorer_data)
    result["scorer"] = scorer.model_dump()

    # 3. Resume Tailorer
    tailored_data = call_llm(build_tailorer_prompt(entries, jd, critic), "resume_tailorer")
    tailored = ResumeTailorerOutput.model_validate(tailored_data)

    cited_ids = {line.master_resume_entry_id for section in tailored.sections for line in section.lines}
    result["cited_ids_valid"] = cited_ids.issubset(ENTRY_IDS)

    # 4. Grounding Critic (with one retry, matching Workflow 3)
    grounding_data = call_llm(build_grounding_prompt(entries, tailored), "grounding_critic")
    grounding = GroundingCriticOutput.model_validate(grounding_data)
    retried = False
    if not grounding.passes:
        retried = True
        retry_data = call_llm(build_tailorer_retry_prompt(entries, jd, critic, grounding.violations), "resume_tailorer")
        tailored = ResumeTailorerOutput.model_validate(retry_data)
        cited_ids = {line.master_resume_entry_id for section in tailored.sections for line in section.lines}
        result["cited_ids_valid"] = cited_ids.issubset(ENTRY_IDS)
        grounding_data = call_llm(build_grounding_prompt(entries, tailored), "grounding_critic")
        grounding = GroundingCriticOutput.model_validate(grounding_data)

    result["tailored"] = tailored.model_dump()
    result["grounding"] = grounding.model_dump()
    result["grounding_retried"] = retried
    result["escalated"] = retried and not grounding.passes

    # 5. Cover Letter
    cover_letter_data = call_llm(build_cover_letter_prompt(entries, jd, synthesis, critic, profile), "cover_letter")
    cover_letter = CoverLetterOutput.model_validate(cover_letter_data)
    result["cover_letter"] = cover_letter.model_dump()
    result["cover_letter_word_count"] = sum(len(p.split()) for p in cover_letter.paragraphs)

    # 6. LinkedIn Drafter
    linkedin_data = call_llm(build_linkedin_prompt(jd, synthesis, critic), "linkedin_drafter")
    linkedin = LinkedInDrafterOutput.model_validate(linkedin_data)
    result["linkedin"] = linkedin.model_dump()
    result["linkedin_char_count"] = len(linkedin.message)

    # 7. Skill Gap Analyzer
    skill_gap_data = call_llm(build_skill_gap_prompt(jd, critic, profile), "skill_gap_analyzer")
    skill_gap = SkillGapAnalyzerOutput.model_validate(skill_gap_data)
    result["skill_gap"] = skill_gap.model_dump()

    return result


def run_baseline(fixture: dict) -> dict:
    jd = fixture["jd"]
    entries = DEMO_ENTRIES
    profile = DEMO_PROFILE
    result: dict = {"id": fixture["id"], "company_name": jd["company_name"], "role_title": jd["role_title"]}

    # 1. Single-prompt baseline tailor + cover letter
    baseline_data = call_llm(build_baseline_prompt(entries, profile, jd), "baseline_tailor")
    baseline = BaselineTailorOutput.model_validate(baseline_data)
    result["baseline"] = baseline.model_dump()
    result["cover_letter_word_count"] = sum(len(p.split()) for p in baseline.cover_letter_paragraphs)

    # 2. Post-hoc Grounding Critic, checked against the full resume
    grounding_data = call_llm(build_baseline_grounding_prompt(entries, baseline), "grounding_critic")
    grounding = GroundingCriticOutput.model_validate(grounding_data)
    result["grounding"] = grounding.model_dump()

    return result


def run_batch(mode: str, start: int, end: int) -> None:
    out_dir = TAILORED_DIR if mode == "tailored" else BASELINE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    runner = run_tailored if mode == "tailored" else run_baseline

    for fixture in FIXTURES[start:end]:
        fid = fixture["id"]
        out_path = out_dir / f"{fid}.json"
        print(f"[{mode}] {fid} ({fixture['jd']['company_name']} - {fixture['jd']['role_title']}) ...", flush=True)
        t0 = time.time()
        try:
            result = runner(fixture)
        except (ValidationError, Exception) as e:  # noqa: BLE001
            print(f"  FAILED: {type(e).__name__}: {e}", flush=True)
            out_path.write_text(json.dumps({"id": fid, "error": f"{type(e).__name__}: {e}"}, indent=2))
            continue
        elapsed = time.time() - t0
        result["elapsed_seconds"] = round(elapsed, 1)
        out_path.write_text(json.dumps(result, indent=2))
        if mode == "tailored":
            print(
                f"  done in {elapsed:.1f}s -> score={result['scorer']['score']} "
                f"tier={result['scorer']['tier']} grounding_passes={result['grounding']['passes']} "
                f"retried={result['grounding_retried']}",
                flush=True,
            )
        else:
            print(
                f"  done in {elapsed:.1f}s -> grounding_passes={result['grounding']['passes']} "
                f"violations={len(result['grounding']['violations'])}",
                flush=True,
            )


def summarize() -> None:
    tailored_files = sorted(TAILORED_DIR.glob("*.json"))
    baseline_files = sorted(BASELINE_DIR.glob("*.json"))

    def load(files):
        out = []
        for f in files:
            data = json.loads(f.read_text())
            if "error" not in data:
                out.append(data)
        return out

    tailored = load(tailored_files)
    baseline = load(baseline_files)

    lines = ["# Material Quality Eval — Results Summary", ""]
    lines.append(f"Generated from {len(tailored)} tailored outputs and {len(baseline)} baseline outputs.")
    lines.append("")

    lines.append("## Headline metric: factual grounding")
    lines.append("")
    if tailored:
        anchor_pass = sum(1 for r in tailored if r["grounding"]["passes"])
        anchor_violations = sum(len(r["grounding"]["violations"]) for r in tailored)
        escalated = sum(1 for r in tailored if r.get("escalated"))
        lines.append(
            f"- **Anchor (Resume Tailorer + Grounding Critic, 1 retry max)**: "
            f"{anchor_pass}/{len(tailored)} ({anchor_pass / len(tailored):.0%}) passed grounding, "
            f"{anchor_violations} total violation(s) across all attempts, "
            f"{escalated} escalated (failed even after retry)."
        )
    if baseline:
        baseline_pass = sum(1 for r in baseline if r["grounding"]["passes"])
        baseline_violations = sum(len(r["grounding"]["violations"]) for r in baseline)
        lines.append(
            f"- **Baseline (single-prompt, no critic, no grounding instructions)**: "
            f"{baseline_pass}/{len(baseline)} ({baseline_pass / len(baseline):.0%}) passed grounding, "
            f"{baseline_violations} total violation(s)."
        )
    lines.append("")

    if tailored:
        lines.append("## Match score distribution (Anchor)")
        lines.append("")
        for r in tailored:
            lines.append(
                f"- `{r['id']}` — {r['company_name']} / {r['role_title']}: "
                f"score={r['scorer']['score']} tier={r['scorer']['tier']}"
            )
        lines.append("")

    lines.append("## Per-application detail")
    lines.append("")
    lines.append("| id | company | role | match score | tier | grounding (Anchor) | grounding (baseline) |")
    lines.append("|---|---|---|---|---|---|---|")
    baseline_by_id = {r["id"]: r for r in baseline}
    for r in tailored:
        b = baseline_by_id.get(r["id"])
        b_grounding = (
            f"{'pass' if b['grounding']['passes'] else 'fail'} ({len(b['grounding']['violations'])})"
            if b
            else "n/a"
        )
        lines.append(
            f"| {r['id']} | {r['company_name']} | {r['role_title']} | {r['scorer']['score']} | "
            f"{r['scorer']['tier']} | "
            f"{'pass' if r['grounding']['passes'] else 'fail'} ({len(r['grounding']['violations'])}) | "
            f"{b_grounding} |"
        )
    lines.append("")

    out_path = ROOT / "eval" / "results_summary.md"
    out_path.write_text("\n".join(lines))
    print(f"Wrote {out_path}")
    print("\n".join(lines))

    # Scoring template for hand-graded dimensions (eval/grading_rubric.md §2-4).
    csv_path = ROOT / "eval" / "scores_template.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "company",
                "role",
                "match_score",
                "match_tier",
                "grounding_anchor_pass",
                "grounding_anchor_violations",
                "grounding_baseline_pass",
                "grounding_baseline_violations",
                "jd_relevance_anchor_1to5",
                "jd_relevance_baseline_1to5",
                "cover_letter_specificity_anchor_1to5",
                "cover_letter_specificity_baseline_1to5",
                "tone_match_anchor_1to5",
                "notes",
            ]
        )
        for r in tailored:
            b = baseline_by_id.get(r["id"])
            writer.writerow(
                [
                    r["id"],
                    r["company_name"],
                    r["role_title"],
                    r["scorer"]["score"],
                    r["scorer"]["tier"],
                    r["grounding"]["passes"],
                    len(r["grounding"]["violations"]),
                    b["grounding"]["passes"] if b else "",
                    len(b["grounding"]["violations"]) if b else "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
    print(f"Wrote {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["tailored", "baseline", "summary"])
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=len(FIXTURES))
    args = parser.parse_args()

    if args.mode == "summary":
        summarize()
    else:
        run_batch(args.mode, args.start, args.end)


if __name__ == "__main__":
    main()
