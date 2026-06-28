"""
Day 13 smoke test: Pattern Detector agent (prompts/pattern_detector.md).

Usage:
    .venv/bin/python scripts/test_pattern_detector.py

The Pattern Detector's input is a precomputed aggregation of the last 4
weeks of applications (built by "Prepare Pattern Detector Input" in
n8n/workflows/05_weekly_reflection.json) - this script reimplements that
aggregation in Python for two scenarios chosen to exercise the planning
doc Sec 17 min-N=5 guard:

  1. N=1 - mirrors the real current Postgres state (one application, the
     Airbnb posting from Day 10). Expect patterns == [] and a summary that
     plainly states there isn't enough data yet.
  2. N=6 - a hypothetical week with a clear startup-vs-enterprise
     response-rate gap (2/3 vs 0/3), matching the kind of example given in
     planning doc Sec 5.5. Expect at least one pattern whose evidence cites
     those exact counts.

Validates each response against PatternDetectorOutput.

Requires:
  - LLM wrapper running: .venv/bin/uvicorn llm.server:app --port 8001
  - Ollama running with qwen2.5:7b pulled
"""

import json
import sys
from pathlib import Path

import httpx
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.schemas import PatternDetectorOutput  # noqa: E402

LLM_WRAPPER_URL = "http://localhost:8001/complete"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

MIN_N = 5

RESPONDED_STATUSES = {"responded", "interview"}


def pct(num: int, den: int) -> str:
    if den == 0:
        return "n/a"
    return f"{num}/{den} ({round(num / den * 100)}%)"


def build_prompt(apps: list[dict], week_start: str, today: str) -> tuple[str, bool]:
    n = len(apps)
    min_n_reached = n >= MIN_N

    status_counts: dict[str, int] = {}
    for a in apps:
        status_counts[a["status"]] = status_counts.get(a["status"], 0) + 1
    status_lines = "\n".join(f"  {status}: {count}" for status, count in status_counts.items()) or "  (none)"

    scored = [a for a in apps if a.get("match_score") is not None]
    avg_score = round(sum(a["match_score"] for a in scored) / len(scored)) if scored else None

    by_tier: dict[str, dict[str, int]] = {}
    for a in apps:
        tier = a.get("match_tier") or "unknown"
        d = by_tier.setdefault(tier, {"total": 0, "responded": 0})
        d["total"] += 1
        if a["status"] in RESPONDED_STATUSES:
            d["responded"] += 1
    tier_lines = "\n".join(
        f"  {tier}: {d['total']} application(s), response rate {pct(d['responded'], d['total'])}"
        for tier, d in by_tier.items()
    ) or "  (none)"

    by_company_type: dict[str, dict[str, int]] = {}
    for a in apps:
        ct = a.get("company_type") or "unknown"
        d = by_company_type.setdefault(ct, {"total": 0, "responded": 0})
        d["total"] += 1
        if a["status"] in RESPONDED_STATUSES:
            d["responded"] += 1
    company_type_lines = "\n".join(
        f"  {ct}: {d['total']} application(s), response rate {pct(d['responded'], d['total'])}"
        for ct, d in by_company_type.items()
    ) or "  (none)"

    app_lines = "\n".join(
        f"  - {a['role_title']} @ {a['company_name']} "
        f"| company_type: {a.get('company_type') or 'unknown'} "
        f"| match tier: {a.get('match_tier') or 'unknown'} "
        f"| match score: {a.get('match_score', 'unknown')} "
        f"| status: {a['status']} "
        f"| {a['days_ago']} day(s) ago"
        for a in apps
    ) or "  (none)"

    prompt = "\n".join(
        [
            "## Window",
            f"Date range: {week_start} to {today} (last 4 weeks)",
            f"Total applications in window: {n}",
            f"Minimum sample size reached (N >= {MIN_N}): {'yes' if min_n_reached else 'no'}",
            "",
            "## Status breakdown",
            status_lines,
            "",
            "## Match score stats",
            f"Average match score: {avg_score if avg_score is not None else 'unknown'}",
            "By match tier:",
            tier_lines,
            "",
            "## Company type breakdown",
            company_type_lines,
            "",
            "## Applications in window",
            app_lines,
        ]
    )
    return prompt, min_n_reached


SCENARIOS = [
    {
        "name": "N=1, below min-N=5 (real current state)",
        "week_start": "2026-06-09",
        "today": "2026-06-15",
        "apps": [
            {
                "role_title": "Software Engineer Intern",
                "company_name": "Airbnb",
                "status": "low_match_waiting",
                "match_score": 58,
                "match_tier": "cold",
                "company_type": "enterprise",
                "days_ago": 5,
            },
        ],
    },
    {
        "name": "N=6, clear startup-vs-enterprise response-rate gap",
        "week_start": "2026-06-09",
        "today": "2026-06-15",
        "apps": [
            {
                "role_title": "Backend Engineering Intern",
                "company_name": "Startup Co A",
                "status": "responded",
                "match_score": 78,
                "match_tier": "hot",
                "company_type": "startup",
                "days_ago": 14,
            },
            {
                "role_title": "Platform Engineering Intern",
                "company_name": "Startup Co B",
                "status": "interview",
                "match_score": 81,
                "match_tier": "hot",
                "company_type": "startup",
                "days_ago": 13,
            },
            {
                "role_title": "Infrastructure Intern",
                "company_name": "Startup Co C",
                "status": "rejected",
                "match_score": 64,
                "match_tier": "warm",
                "company_type": "startup",
                "days_ago": 12,
            },
            {
                "role_title": "Software Engineer Intern",
                "company_name": "Enterprise Co A",
                "status": "submitted",
                "match_score": 62,
                "match_tier": "warm",
                "company_type": "enterprise",
                "days_ago": 11,
            },
            {
                "role_title": "Cloud Engineering Intern",
                "company_name": "Enterprise Co B",
                "status": "ghosted",
                "match_score": 60,
                "match_tier": "warm",
                "company_type": "enterprise",
                "days_ago": 26,
            },
            {
                "role_title": "Systems Engineering Intern",
                "company_name": "Enterprise Co C",
                "status": "rejected",
                "match_score": 58,
                "match_tier": "cold",
                "company_type": "enterprise",
                "days_ago": 24,
            },
        ],
    },
]


def call_llm(prompt: str, system_prompt_name: str) -> dict:
    system_prompt = (PROMPTS_DIR / f"{system_prompt_name}.md").read_text()
    resp = httpx.post(
        LLM_WRAPPER_URL,
        json={"prompt": prompt, "system": system_prompt, "json_mode": True},
        timeout=180.0,
    )
    resp.raise_for_status()
    raw_text = resp.json()["text"]
    return json.loads(raw_text)


def main() -> None:
    failures = []

    for scenario in SCENARIOS:
        print(f"\n=== Scenario: {scenario['name']} ===")
        prompt, min_n_reached = build_prompt(scenario["apps"], scenario["week_start"], scenario["today"])
        print(prompt)

        try:
            data = call_llm(prompt, "pattern_detector")
            output = PatternDetectorOutput.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"FAILED: {e}")
            failures.append(scenario["name"])
            continue

        print("\n--- output ---")
        print(json.dumps(output.model_dump(), indent=2))

        if not min_n_reached and output.patterns:
            print("-> FAIL: min-N=5 guard not reached but patterns is non-empty")
            failures.append(scenario["name"])
        elif not min_n_reached:
            n = len(scenario["apps"])
            if str(n) not in output.summary or str(MIN_N) not in output.summary:
                print(f"-> WARNING: summary doesn't cite N={n} or MIN_N={MIN_N}: {output.summary!r}")
        elif min_n_reached and not output.patterns:
            print("-> WARNING: min-N=5 guard reached but no patterns were surfaced (allowed, but check summary)")

    if failures:
        print(f"\n{len(failures)} scenario(s) failed: {failures}")
        sys.exit(1)
    else:
        print("\nAll scenarios produced valid, guard-respecting output.")


if __name__ == "__main__":
    main()
