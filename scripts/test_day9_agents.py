"""
Day 9 smoke test: Cover Letter Generator, LinkedIn Drafter, and Skill Gap
Analyzer agents, chained after the Resume Critic and Match Scorer
(Days 6-7).

Usage:
    .venv/bin/python scripts/test_day9_agents.py

Runs:

    Resume Critic -> Match Scorer -> {Cover Letter, LinkedIn, Skill Gap}

against the seeded master resume + profile and the same standalone sample JD
+ company synthesis fixtures as test_match_scorer.py / test_resume_tailorer.py
(see PROGRESS.md Day 5 note on test postings going stale). Cover Letter,
LinkedIn, and Skill Gap only depend on the critic + scorer + JD + synthesis +
profile, so they're independent of the Resume Tailorer / Grounding Critic
chain and run directly after the Match Scorer.

Validates each response against its schema in llm.schemas, and additionally
checks:
  - Cover Letter: every cited master_resume_entry_id is one of the ids
    actually loaded from Postgres, and the body is under 250 words.
  - LinkedIn: message is under 300 characters.

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
    CoverLetterOutput,
    LinkedInDrafterOutput,
    MatchScorerOutput,
    ResumeCriticOutput,
    SkillGapAnalyzerOutput,
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


def synthesis_lines(synthesis: dict) -> str:
    return "\n".join(
        [
            f"What they do: {synthesis['what_they_do']}",
            f"Recent developments: {', '.join(synthesis['recent_developments'])}",
            f"Tech signals: {', '.join(synthesis['tech_signals'])}",
            f"Company type: {synthesis['company_type']}",
            f"Culture signals: {', '.join(synthesis['culture_signals'])}",
            f"Likely role context: {synthesis['likely_role_context']}",
        ]
    )


def bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["(none)"]


def profile_lines(profile: dict | None) -> str:
    if not profile:
        return "(no user profile on file)"
    return (
        f"Long-term goals: {profile['long_term_goals']}\n"
        f"Target role types: {', '.join(profile['target_role_types'] or [])}"
    )


def build_critic_prompt(entries: list[dict], profile: dict | None, jd: dict, synthesis: dict) -> str:
    entry_lines = "\n".join(
        f"- [{e['category']}] {e['canonical_text']} (tags: {', '.join(e['tags'] or [])})"
        for e in entries
    )
    prompt = "\n\n".join(
        [
            "## Candidate's master resume entries",
            entry_lines,
            "## Candidate's profile",
            profile_lines(profile),
            "## Job description",
            jd_summary_lines(jd),
            "## Company research synthesis",
            synthesis_lines(synthesis),
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def build_scorer_prompt(critic: ResumeCriticOutput, profile: dict | None, jd: dict) -> str:
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
            profile_lines(profile),
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def build_cover_letter_prompt(
    entries: list[dict], jd: dict, synthesis: dict, critic: ResumeCriticOutput, profile: dict | None
) -> str:
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
            "## Company research synthesis",
            synthesis_lines(synthesis),
            f"## Suggested angle\n{critic.suggested_angle}",
            "## Candidate's profile",
            profile_lines(profile),
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def build_linkedin_prompt(jd: dict, synthesis: dict, critic: ResumeCriticOutput) -> str:
    prompt = "\n\n".join(
        [
            "## Job description",
            jd_summary_lines(jd),
            "## Company research synthesis",
            synthesis_lines(synthesis),
            f"## Suggested angle\n{critic.suggested_angle}",
        ]
    )
    return prompt[:MAX_PROMPT_CHARS]


def build_skill_gap_prompt(jd: dict, critic: ResumeCriticOutput, profile: dict | None) -> str:
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
            "## Job description must-haves and nice-to-haves",
            f"Must-haves: {', '.join(jd['must_haves'])}",
            f"Nice-to-haves: {', '.join(jd['nice_to_haves'])}",
            "## Resume Critic output",
            critic_lines,
            "## Candidate's profile",
            profile_lines(profile),
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
    print(f"suggested_angle: {critic.suggested_angle}")

    # Step 2: Match Scorer
    scorer_prompt = build_scorer_prompt(critic, profile, SAMPLE_JD)
    try:
        scorer_data = call_llm(scorer_prompt, "match_scorer")
        scorer = MatchScorerOutput.model_validate(scorer_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"MATCH SCORER FAILED: {e}")
        return

    print(f"\n=== Match Scorer output ===\nscore: {scorer.score}, tier: {scorer.tier.value}")

    # Step 3: Cover Letter Generator
    cover_letter_prompt = build_cover_letter_prompt(entries, SAMPLE_JD, SAMPLE_SYNTHESIS, critic, profile)
    try:
        cover_letter_data = call_llm(cover_letter_prompt, "cover_letter")
        cover_letter = CoverLetterOutput.model_validate(cover_letter_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"COVER LETTER FAILED: {e}")
        return

    print("\n=== Cover Letter output ===")
    print(json.dumps(cover_letter.model_dump(), indent=2))
    if len(cover_letter.paragraphs) != 3:
        print(f"-> WARNING: expected 3 paragraphs, got {len(cover_letter.paragraphs)}")
    word_count = sum(len(p.split()) for p in cover_letter.paragraphs)
    print(f"-> word count: {word_count} (limit 250)")
    if word_count > 250:
        print("-> WARNING: exceeds 250-word limit")
    cited_ids = set(cover_letter.master_resume_entry_ids)
    unknown_ids = cited_ids - entry_ids
    if unknown_ids:
        print(f"-> WARNING: cover letter cited {len(unknown_ids)} id(s) not in master_resume_entry: {unknown_ids}")
    elif not cited_ids:
        print("-> WARNING: cover letter cited zero master_resume_entry_ids")
    else:
        print(f"-> all {len(cited_ids)} cited master_resume_entry_id(s) are valid.")

    # Step 4: LinkedIn Drafter
    linkedin_prompt = build_linkedin_prompt(SAMPLE_JD, SAMPLE_SYNTHESIS, critic)
    try:
        linkedin_data = call_llm(linkedin_prompt, "linkedin_drafter")
        linkedin = LinkedInDrafterOutput.model_validate(linkedin_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"LINKEDIN DRAFTER FAILED: {e}")
        return

    print("\n=== LinkedIn Drafter output ===")
    print(json.dumps(linkedin.model_dump(), indent=2))
    char_count = len(linkedin.message)
    print(f"-> char count: {char_count} (limit 300)")
    if char_count > 300:
        print("-> WARNING: exceeds 300-char limit")

    # Step 5: Skill Gap Analyzer
    skill_gap_prompt = build_skill_gap_prompt(SAMPLE_JD, critic, profile)
    try:
        skill_gap_data = call_llm(skill_gap_prompt, "skill_gap_analyzer")
        skill_gap = SkillGapAnalyzerOutput.model_validate(skill_gap_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"SKILL GAP ANALYZER FAILED: {e}")
        return

    print("\n=== Skill Gap Analyzer output ===")
    print(json.dumps(skill_gap.model_dump(), indent=2))
    print(f"-> verdict: {skill_gap.verdict.value}")


if __name__ == "__main__":
    main()
