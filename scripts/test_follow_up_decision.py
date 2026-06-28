"""
Day 11 smoke test: Follow-up Decision agent (prompts/follow_up_decision.md).

Usage:
    .venv/bin/python scripts/test_follow_up_decision.py

Unlike the Day 6-9 agents, the Follow-up Decision agent doesn't depend on the
master resume, a JD, or a company synthesis chain — its input is just an
application's follow-up history plus the company research already gathered
for it. So this script uses three standalone scenarios (shape of the
"Find Due Applications" query output in
n8n/workflows/04_follow_up_scheduler.json) chosen to exercise the prompt's
decision boundaries:

  1. Window just reached, no nudge sent yet -> expect "send_now".
  2. Window not yet reached -> expect "wait".
  3. Two nudges already sent -> expect "wait" (avoid pestering).

Validates each response against FollowUpDecisionOutput and checks that
nudge_paragraphs is empty iff decision == "wait".

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
from llm.schemas import FollowUpDecisionOutput  # noqa: E402

LLM_WRAPPER_URL = "http://localhost:8001/complete"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

SAMPLE_SYNTHESIS = {
    "what_they_do": "Fictional Co builds backend infrastructure tooling for mid-size engineering teams.",
    "recent_developments": ["Raised a Series B to expand the platform team"],
    "company_type": "startup",
    "likely_role_context": "The intern would join the Platform Infrastructure team working on internal developer tooling.",
}

SCENARIOS = [
    {
        "name": "window just reached, no nudge yet",
        "expected_decision": "send_now",
        "application": {
            "role_title": "Software Engineering Intern - Backend",
            "company_name": "Fictional Co",
            "match_score": 68,
            "days_since_submitted": 10,
            "follow_up_window_days": 10,
            "follow_up_count": 0,
            "last_follow_up_at": None,
        },
        "synthesis": SAMPLE_SYNTHESIS,
    },
    {
        "name": "window not yet reached",
        "expected_decision": "wait",
        "application": {
            "role_title": "Data Engineering Intern",
            "company_name": "Other Co",
            "match_score": 72,
            "days_since_submitted": 4,
            "follow_up_window_days": 10,
            "follow_up_count": 0,
            "last_follow_up_at": None,
        },
        "synthesis": {
            "what_they_do": "Other Co provides data pipeline tooling for analytics teams.",
            "recent_developments": [],
            "company_type": "startup",
            "likely_role_context": "(unavailable)",
        },
    },
    {
        "name": "already nudged twice",
        "expected_decision": "wait",
        "application": {
            "role_title": "Software Engineering Intern - Backend",
            "company_name": "Fictional Co",
            "match_score": 68,
            "days_since_submitted": 35,
            "follow_up_window_days": 10,
            "follow_up_count": 2,
            "last_follow_up_at": "2026-06-05",
        },
        "synthesis": SAMPLE_SYNTHESIS,
    },
]


def synthesis_lines(synthesis: dict) -> str:
    return "\n".join(
        [
            f"What they do: {synthesis['what_they_do']}",
            f"Company type: {synthesis['company_type']}",
            f"Recent developments: {', '.join(synthesis['recent_developments']) or '(none)'}",
            f"Likely role context: {synthesis['likely_role_context']}",
        ]
    )


def build_prompt(application: dict, synthesis: dict) -> str:
    if application["follow_up_count"] == 0:
        history = "No follow-up nudges have been drafted for this application yet."
    else:
        history = (
            f"{application['follow_up_count']} follow-up nudge(s) already drafted for this "
            f"application. Most recent: {application['last_follow_up_at']}."
        )

    window_reached = application["days_since_submitted"] >= application["follow_up_window_days"]

    return "\n\n".join(
        [
            "## Application",
            f"Role: {application['role_title']}",
            f"Company: {application['company_name']}",
            f"Match score: {application['match_score']}",
            f"Days since submitted: {application['days_since_submitted']}",
            f"Follow-up window for this application: {application['follow_up_window_days']} days",
            f"Follow-up window reached: {'yes' if window_reached else 'no'}",
            "## Follow-up history",
            history,
            "## Company research",
            synthesis_lines(synthesis),
        ]
    )


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
        prompt = build_prompt(scenario["application"], scenario["synthesis"])
        try:
            data = call_llm(prompt, "follow_up_decision")
            output = FollowUpDecisionOutput.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"FAILED: {e}")
            failures.append(scenario["name"])
            continue

        print(json.dumps(output.model_dump(), indent=2))

        if output.decision.value != scenario["expected_decision"]:
            print(
                f"-> WARNING: expected decision '{scenario['expected_decision']}', "
                f"got '{output.decision.value}'"
            )

        if output.decision.value == "wait" and output.nudge_paragraphs:
            print("-> WARNING: decision is 'wait' but nudge_paragraphs is non-empty")
        if output.decision.value == "send_now" and not output.nudge_paragraphs:
            print("-> WARNING: decision is 'send_now' but nudge_paragraphs is empty")
            failures.append(scenario["name"])

    if failures:
        print(f"\n{len(failures)} scenario(s) failed schema/consistency checks: {failures}")
        sys.exit(1)
    else:
        print("\nAll scenarios produced valid, internally-consistent output.")


if __name__ == "__main__":
    main()
