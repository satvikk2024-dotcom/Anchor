"""
Day 7 smoke test: Match Scorer agent, chained after the Resume Critic.

Usage:
    .venv/bin/python scripts/test_match_scorer.py

Loads `master_resume_entry` and `user_profile` from Postgres (same as Day 6's
test_resume_critic.py), pairs them with the same standalone sample JD +
company synthesis (no live posting required — see PROGRESS.md Day 5 note on
test postings going stale). Runs the Resume Critic first, then feeds its
output + the JD + user profile into the Match Scorer, and validates both
responses against their schemas in llm.schemas.

Requires:
  - Postgres running, `anchor` db seeded (psql on PATH, see CLAUDE.md "Local dev")
  - LLM wrapper running: .venv/bin/uvicorn llm.server:app --port 8001
  - Ollama running with qwen2.5:7b pulled
"""

import json
import subprocess
import sys
from pathlib import Path

import httpx
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.schemas import MatchScorerOutput, ResumeCriticOutput  # noqa: E402

LLM_WRAPPER_URL = "http://localhost:8001/complete"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
MAX_PROMPT_CHARS = 12000

# Standalone sample JD (shape of llm.schemas.JDParserOutput) — a Backend
# Software Engineering Intern posting. Avoids depending on a live posting.
SAMPLE_JD = {
    "company_name": "Fictional Co",
    "role_title": "Software Engineering Intern - Backend",
    "team_or_org": "Platform Infrastructure",
    "must_haves": [
        "Proficiency in Python or Java",
        "Understanding of relational databases (SQL)",
        "Currently pursuing a B.S. in Computer Science or related field",
    ],
    "nice_to_haves": [
        "Experience with FastAPI, Django, or similar web frameworks",
        "Familiarity with Docker and CI/CD pipelines",
        "Exposure to distributed systems or message queues",
    ],
    "responsibilities": [
        "Build and maintain backend services that power internal tooling",
        "Write and review pull requests with senior engineers",
        "Improve test coverage and observability for existing services",
    ],
    "tech_stack": ["Python", "PostgreSQL", "Docker", "AWS"],
    "culture_signals": ["collaborative", "fast-paced", "mentorship-focused"],
    "comp_range": "$35-45/hr",
    "location_type": "hybrid",
}

# Standalone sample company synthesis (shape of CompanySynthesizerOutput).
SAMPLE_SYNTHESIS = {
    "what_they_do": "Fictional Co builds backend infrastructure tooling for mid-size engineering teams.",
    "recent_developments": ["Raised a Series B to expand the platform team"],
    "tech_signals": ["Python", "PostgreSQL", "Docker", "AWS"],
    "company_type": "startup",
    "culture_signals": ["collaborative", "mentorship-focused"],
    "likely_role_context": "The intern would join the Platform Infrastructure team working on internal developer tooling.",
}


def psql_json(query: str) -> list | None:
    result = subprocess.run(
        ["psql", "-d", "anchor", "-tAc", f"select coalesce(json_agg(t), '[]') from ({query}) t"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip())


def build_critic_prompt(entries: list[dict], profile: dict | None, jd: dict, synthesis: dict) -> str:
    entry_lines = "\n".join(
        f"- [{e['category']}] {e['canonical_text']} (tags: {', '.join(e['tags'] or [])})"
        for e in entries
    )

    if profile:
        profile_lines = (
            f"Long-term goals: {profile['long_term_goals']}\n"
            f"Target role types: {', '.join(profile['target_role_types'] or [])}"
        )
    else:
        profile_lines = "(no user profile on file)"

    jd_lines = jd_summary_lines(jd)

    synthesis_lines = "\n".join(
        [
            f"What they do: {synthesis['what_they_do']}",
            f"Recent developments: {', '.join(synthesis['recent_developments'])}",
            f"Tech signals: {', '.join(synthesis['tech_signals'])}",
            f"Company type: {synthesis['company_type']}",
            f"Culture signals: {', '.join(synthesis['culture_signals'])}",
            f"Likely role context: {synthesis['likely_role_context']}",
        ]
    )

    prompt = "\n\n".join(
        [
            "## Candidate's master resume entries",
            entry_lines,
            "## Candidate's profile",
            profile_lines,
            "## Job description",
            jd_lines,
            "## Company research synthesis",
            synthesis_lines,
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def jd_summary_lines(jd: dict) -> str:
    return "\n".join(
        [
            f"Role: {jd['role_title']} (team: {jd.get('team_or_org') or 'unspecified'})",
            f"Company: {jd['company_name']}",
            f"Must-haves: {', '.join(jd['must_haves'])}",
            f"Nice-to-haves: {', '.join(jd['nice_to_haves'])}",
            f"Responsibilities: {', '.join(jd['responsibilities'])}",
            f"Tech stack: {', '.join(jd['tech_stack'])}",
            f"Culture signals: {', '.join(jd['culture_signals'])}",
            f"Location type: {jd['location_type']}",
        ]
    )


def bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["(none)"]


def build_scorer_prompt(critic: ResumeCriticOutput, profile: dict | None, jd: dict) -> str:
    if profile:
        profile_lines = (
            f"Long-term goals: {profile['long_term_goals']}\n"
            f"Target role types: {', '.join(profile['target_role_types'] or [])}"
        )
    else:
        profile_lines = "(no user profile on file)"

    critic_lines = "\n".join(
        [
            "Strengths for this role:",
            *bullet_list(critic.strengths_for_this_role),
            "Weaknesses to address:",
            *bullet_list(critic.weaknesses_to_address),
            "Gaps unfixable in this application:",
            *bullet_list(critic.gaps_unfixable_in_this_application),
            f"Suggested angle: {critic.suggested_angle}",
        ]
    )

    prompt = "\n\n".join(
        [
            "## Resume Critic output",
            critic_lines,
            "## Job description",
            jd_summary_lines(jd),
            "## Candidate's profile",
            profile_lines,
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


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
    entries = psql_json(
        "select category, canonical_text, tags from master_resume_entry order by priority desc, category"
    )
    profiles = psql_json("select long_term_goals, target_role_types from user_profile limit 1")
    profile = profiles[0] if profiles else None

    if not entries:
        print("No master_resume_entry rows found — run `psql -d anchor -f db/seed_master_resume.sql` first.")
        sys.exit(1)

    print(f"Loaded {len(entries)} resume entries, profile={'yes' if profile else 'no'}")

    # Step 1: Resume Critic
    critic_prompt = build_critic_prompt(entries, profile, SAMPLE_JD, SAMPLE_SYNTHESIS)
    try:
        critic_data = call_llm(critic_prompt, "resume_critic")
        critic = ResumeCriticOutput.model_validate(critic_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"RESUME CRITIC FAILED: {e}")
        return

    print("\n=== Resume Critic output ===")
    print(json.dumps(critic.model_dump(), indent=2))

    # Step 2: Match Scorer, fed the critic's output
    scorer_prompt = build_scorer_prompt(critic, profile, SAMPLE_JD)
    try:
        scorer_data = call_llm(scorer_prompt, "match_scorer")
    except json.JSONDecodeError as e:
        print(f"MATCH SCORER PARSE FAILED: {e}")
        return

    try:
        scorer = MatchScorerOutput.model_validate(scorer_data)
    except ValidationError as e:
        print(f"MATCH SCORER SCHEMA VALIDATION FAILED: {e}\nraw: {json.dumps(scorer_data, indent=2)}")
        return

    print("\n=== Match Scorer output ===")
    print("PASSED schema validation")
    print(json.dumps(scorer.model_dump(), indent=2))

    if scorer.score < 60:
        print(f"\n-> score {scorer.score} < 60: would trigger Slack low-match prompt + Wait node.")
    else:
        print(f"\n-> score {scorer.score} >= 60: would continue to Resume Tailorer.")


if __name__ == "__main__":
    main()
