"""
Day 6 smoke test: Resume Critic agent against the seeded master resume.

Usage:
    .venv/bin/python scripts/test_resume_critic.py

Loads `master_resume_entry` and `user_profile` from Postgres (seeded via
`psql -d anchor -f db/seed_master_resume.sql`), pairs them with a standalone
sample JD + company synthesis (no live posting required — see PROGRESS.md
Day 5 note on test postings going stale), builds the prompt, sends it to the
LLM wrapper with prompts/resume_critic.md as the system prompt,
json_mode=True, and validates the response against
llm.schemas.ResumeCriticOutput.

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
from llm.schemas import ResumeCriticOutput  # noqa: E402

LLM_WRAPPER_URL = "http://localhost:8001/complete"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "resume_critic.md"
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


def build_prompt(entries: list[dict], profile: dict | None, jd: dict, synthesis: dict) -> str:
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

    jd_lines = "\n".join(
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

    prompt = build_prompt(entries, profile, SAMPLE_JD, SAMPLE_SYNTHESIS)
    system_prompt = PROMPT_PATH.read_text()

    resp = httpx.post(
        LLM_WRAPPER_URL,
        json={"prompt": prompt, "system": system_prompt, "json_mode": True},
        timeout=180.0,
    )
    resp.raise_for_status()
    raw_text = resp.json()["text"]

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"PARSE FAILED: {e}\nraw: {raw_text[:2000]}")
        return

    try:
        validated = ResumeCriticOutput.model_validate(data)
    except ValidationError as e:
        print(f"SCHEMA VALIDATION FAILED: {e}\nraw: {json.dumps(data, indent=2)[:2000]}")
        return

    print("PASSED schema validation")
    print(json.dumps(validated.model_dump(), indent=2))


if __name__ == "__main__":
    main()
