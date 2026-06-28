"""
Day 8 smoke test: Resume Tailorer + Grounding Critic, chained after the
Resume Critic and Match Scorer (Days 6-7).

Usage:
    .venv/bin/python scripts/test_resume_tailorer.py

Runs the full Workflow 3 agent chain against the seeded master resume +
profile and a standalone sample JD + company synthesis (same fixtures as
test_match_scorer.py — see PROGRESS.md Day 5 note on test postings going
stale):

    Resume Critic -> Match Scorer -> Resume Tailorer -> Grounding Critic

Validates each response against its schema in llm.schemas, and additionally
checks that every `master_resume_entry_id` the Tailorer cites is one of the
ids actually loaded from Postgres (a sanity check the Grounding Critic
doesn't do).

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
from llm.schemas import (  # noqa: E402
    GroundingCriticOutput,
    MatchScorerOutput,
    ResumeCriticOutput,
    ResumeTailorerOutput,
)

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
            jd_summary_lines(jd),
            "## Company research synthesis",
            synthesis_lines,
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


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


def build_tailorer_prompt(entries: list[dict], jd: dict, critic: ResumeCriticOutput) -> str:
    entry_lines = "\n".join(
        f"- id={e['id']} [{e['category']}] {e['canonical_text']} (tags: {', '.join(e['tags'] or [])})"
        for e in entries
    )

    prompt = "\n\n".join(
        [
            "## Candidate's master resume entries (each has an id you must reference)",
            entry_lines,
            "## Job description",
            jd_summary_lines(jd),
            f"## Suggested angle\n{critic.suggested_angle}",
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def build_grounding_prompt(entries: list[dict], tailored: ResumeTailorerOutput) -> str:
    entries_by_id = {e["id"]: e for e in entries}
    blocks = []
    n = 0
    for section in tailored.sections:
        for line in section.lines:
            n += 1
            entry = entries_by_id.get(line.master_resume_entry_id)
            source_text = entry["canonical_text"] if entry else "(no entry with this id was provided)"
            blocks.append(
                "\n".join(
                    [
                        f"Line {n} [{section.category.value}] (from {line.master_resume_entry_id})",
                        f'Tailored: "{line.text}"',
                        f'Source ({line.master_resume_entry_id}): "{source_text}"',
                    ]
                )
            )

    prompt = "\n\n".join(
        [
            "## Lines to check\nEach numbered item pairs one tailored-resume line with the exact "
            "source entry it claims to be drawn from. Check each line only against its own paired source.",
            *blocks,
            f'## Summary to check\nTailored summary: "{tailored.summary}"\nCheck the summary against '
            "the union of all source entries above — it should not introduce facts beyond what they support.",
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
        "select id, category, canonical_text, tags from master_resume_entry order by priority desc, category"
    )
    profiles = psql_json("select long_term_goals, target_role_types from user_profile limit 1")
    profile = profiles[0] if profiles else None

    if not entries:
        print("No master_resume_entry rows found — run `psql -d anchor -f db/seed_master_resume.sql` first.")
        sys.exit(1)

    print(f"Loaded {len(entries)} resume entries, profile={'yes' if profile else 'no'}")
    entry_ids = {e["id"] for e in entries}

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

    # Step 2: Match Scorer
    scorer_prompt = build_scorer_prompt(critic, profile, SAMPLE_JD)
    try:
        scorer_data = call_llm(scorer_prompt, "match_scorer")
        scorer = MatchScorerOutput.model_validate(scorer_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"MATCH SCORER FAILED: {e}")
        return

    print("\n=== Match Scorer output ===")
    print(f"score: {scorer.score}, tier: {scorer.tier.value}")
    print(json.dumps(scorer.model_dump(), indent=2))

    # Step 3: Resume Tailorer
    tailorer_prompt = build_tailorer_prompt(entries, SAMPLE_JD, critic)
    try:
        tailored_data = call_llm(tailorer_prompt, "resume_tailorer")
        tailored = ResumeTailorerOutput.model_validate(tailored_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"RESUME TAILORER FAILED: {e}")
        return

    print("\n=== Resume Tailorer output ===")
    print(json.dumps(tailored.model_dump(), indent=2))

    # Sanity check: every cited id must be one we actually loaded.
    cited_ids = {
        line.master_resume_entry_id for section in tailored.sections for line in section.lines
    }
    unknown_ids = cited_ids - entry_ids
    if unknown_ids:
        print(f"\n-> WARNING: tailorer cited {len(unknown_ids)} id(s) not in master_resume_entry: {unknown_ids}")
    else:
        print(f"\n-> all {len(cited_ids)} cited master_resume_entry_id(s) are valid.")

    # Step 4: Grounding Critic
    grounding_prompt = build_grounding_prompt(entries, tailored)
    try:
        grounding_data = call_llm(grounding_prompt, "grounding_critic")
        grounding = GroundingCriticOutput.model_validate(grounding_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"GROUNDING CRITIC FAILED: {e}")
        return

    print("\n=== Grounding Critic output ===")
    print(json.dumps(grounding.model_dump(), indent=2))

    if grounding.passes:
        print("\n-> grounding check PASSED: tailored resume would be persisted to generated_material.")
    else:
        print(f"\n-> grounding check FAILED with {len(grounding.violations)} violation(s): would retry once.")


if __name__ == "__main__":
    main()
