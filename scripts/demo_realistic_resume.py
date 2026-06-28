"""
Demo: full Workflow 3 agent chain against the real master resume.

Usage:
    .venv/bin/python scripts/demo_realistic_resume.py

DEMO_ENTRIES and DEMO_PROFILE below match db/seed_master_resume.sql exactly
(updated 2026-06-16 with the real candidate resume). The benchmark.py eval
imports these directly so the eval and the live pipeline use the same content.

Runs the full chain:

    Resume Critic -> Match Scorer -> Resume Tailorer -> Grounding Critic
                   -> Cover Letter / LinkedIn / Skill Gap -> PDF render

against the standalone sample JD + company synthesis.

Requires:
  - LLM wrapper running: .venv/bin/uvicorn llm.server:app --port 8001
  - fetch service running (PDF render): port 8002
  - Ollama running with qwen2.5:7b pulled
"""

import json
import sys
from datetime import date
from pathlib import Path

import httpx
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.schemas import (  # noqa: E402
    CoverLetterOutput,
    GroundingCriticOutput,
    LinkedInDrafterOutput,
    MatchScorerOutput,
    ResumeCriticOutput,
    ResumeTailorerOutput,
    SkillGapAnalyzerOutput,
)

LLM_WRAPPER_URL = "http://localhost:8001/complete"
RENDER_PDF_URL = "http://localhost:8002/render-pdf"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
OUTPUT_DIR = Path("/tmp/anchor_demo")
MAX_PROMPT_CHARS = 12000

# ---------------------------------------------------------------------------
# Real candidate master_resume_entry fixtures (Satvik Krishna, 2026-06-16).
# Mirrors db/seed_master_resume.sql exactly — benchmark.py imports these so
# the eval and the live pipeline always run against the same content.
# ---------------------------------------------------------------------------
DEMO_ENTRIES = [
    # ---- Education ----
    {
        "id": "sk-edu-rvce",
        "category": "education",
        "canonical_text": (
            "Pursuing a Bachelor of Engineering in Computer Science at RV College of "
            "Engineering (RVCE), Bengaluru (2024–2028), with a CGPA of 8.98/10. "
            "Relevant coursework: Data Structures, Design and Analysis of Algorithms, "
            "Operating Systems, Computer Networks, Discrete Mathematics, Data Science "
            "for Engineers, Programming in C."
        ),
        "tags": ["education", "computer-science", "rvce", "bengaluru", "india"],
        "priority": 5,
    },
    {
        "id": "sk-edu-nps",
        "category": "education",
        "canonical_text": (
            "Completed Class 1–12 at National Public School, Indiranagar, Bengaluru "
            "(CBSE, 2009–2023), with PCMC (Physics, Chemistry, Mathematics, Computer "
            "Science) specialisation."
        ),
        "tags": ["education", "cbse", "school", "india"],
        "priority": 2,
    },
    # ---- Experience ----
    {
        "id": "sk-exp-kukcl-design",
        "category": "experience",
        "canonical_text": (
            "As Product & Design Intern at KuKClean, a plant-based D2C e-commerce brand "
            "(Bangalore, Jun–Jul 2024), produced end-to-end creative assets across "
            "packaging, social-media campaigns, and storefront visuals — delivering 30+ "
            "design files in Photoshop, Lightroom, and Figma across an 8-week engagement."
        ),
        "tags": ["experience", "design", "figma", "photoshop", "lightroom", "e-commerce", "intern"],
        "priority": 4,
    },
    {
        "id": "sk-exp-kukcl-product",
        "category": "experience",
        "canonical_text": (
            "At KuKClean (Jun–Jul 2024), set up 20+ product listings end-to-end on the "
            "e-commerce storefront — writing product copy, optimising on-page descriptions, "
            "and photographing the catalog to support go-to-market launch. Also built Figma "
            "wireframes and high-fidelity mockups for new product pages, converting "
            "founding-team briefs into design-ready specs for web implementation."
        ),
        "tags": ["experience", "product", "e-commerce", "figma", "copywriting", "photography", "intern"],
        "priority": 3,
    },
    # ---- Projects ----
    {
        "id": "sk-proj-meridian-sys",
        "category": "project",
        "canonical_text": (
            "Designed and shipped Meridian, a 4-agent orchestration system (financial, "
            "market, leadership, sentiment) that produces cited due-diligence memos on "
            "NSE/BSE companies in ~75 seconds, pulling from yfinance, Wikipedia, Reddit "
            "JSON, and Google News RSS in parallel via asyncio. Stack: Python, FastAPI, "
            "Next.js, asyncio, Ollama (qwen2.5:7b), Server-Sent Events, Pydantic, SQLite."
        ),
        "tags": ["project", "python", "fastapi", "asyncio", "ollama", "pydantic", "sqlite",
                 "nextjs", "multi-agent", "llm", "ai", "server-sent-events"],
        "priority": 5,
    },
    {
        "id": "sk-proj-meridian-eval",
        "category": "project",
        "canonical_text": (
            "In Meridian, built a citation-grounded schema where every memo claim links to "
            "evidence rows by database constraint — eliminating unsourced claims by "
            "construction; a content-addressed SHA-256 disk cache makes evals reproducible "
            "and dev iterations near-zero-cost. Ran an evaluation across 9 NSE companies "
            "and 135 verified ground-truth claims: 15% average hallucination rate (financial "
            "agent: 0% across all 9), 79% ground-truth coverage, 11 unique citations per run "
            "vs. 0 for a single-prompt baseline."
        ),
        "tags": ["project", "meridian", "llm-eval", "hallucination", "citation",
                 "grounding", "cache", "evaluation"],
        "priority": 5,
    },
    {
        "id": "sk-proj-anchor-wf",
        "category": "project",
        "canonical_text": (
            "Built Anchor, a 5-workflow n8n orchestration system that turns a job-posting "
            "URL into a researched, factually-grounded application packet — Playwright-driven "
            "JD scraping and parsing, multi-source company research, match scoring, "
            "tailored-material generation, and cron-based follow-up scheduling with "
            "Wait/Resume human-in-loop gates. Stack: n8n, Postgres, Playwright, Notion API, "
            "Google Drive API, Slack Web API, OAuth2."
        ),
        "tags": ["project", "n8n", "postgres", "playwright", "notion", "slack", "oauth2",
                 "orchestration", "ai", "llm", "prompt-engineering"],
        "priority": 5,
    },
    {
        "id": "sk-proj-anchor-grnd",
        "category": "project",
        "canonical_text": (
            "In Anchor, designed a master-resume schema where every tailored line links to "
            "a structured master entry by foreign-key constraint, with an adversarial "
            "Grounding Critic enforcing factual grounding before any material ships; full "
            "observability layer logs every agent run to Postgres (input hash, structured "
            "output, latency, critic verdict) — queryable audit trail across the pipeline."
        ),
        "tags": ["project", "anchor", "grounding", "observability", "postgres",
                 "llm-eval", "prompt-engineering", "agent-orchestration"],
        "priority": 4,
    },
    {
        "id": "sk-proj-crowd-model",
        "category": "project",
        "canonical_text": (
            "Built CrowdSense, a real-time crowd-monitoring platform combining CSRNet "
            "density estimation for dense scenes with YOLOv8 detection for sparse-to-medium "
            "density, dynamically switching between models based on scene density to balance "
            "accuracy and compute. Stack: PyTorch, OpenCV, CSRNet, YOLOv8, optical flow, "
            "RAG-based density estimation, ShanghaiTech Dataset, React, FastAPI, SQLite."
        ),
        "tags": ["project", "pytorch", "opencv", "yolov8", "csrnet", "computer-vision",
                 "ml", "fastapi", "react", "sqlite", "rag"],
        "priority": 4,
    },
    {
        "id": "sk-proj-crowd-risk",
        "category": "project",
        "canonical_text": (
            "In CrowdSense, implemented zone-wise risk detection using OpenCV optical flow "
            "for privacy-preserving movement analysis and published crowd-safety thresholds "
            "(5–6 persons/m² warning, 7–8 critical) for stampede-risk alerts; React + "
            "FastAPI dashboard surfaces live density heatmaps and zone occupancy."
        ),
        "tags": ["project", "crowdsense", "opencv", "optical-flow", "risk-detection",
                 "safety", "react", "fastapi", "dashboard"],
        "priority": 3,
    },
    # ---- Skills ----
    {
        "id": "sk-skill-langs",
        "category": "skill",
        "canonical_text": "Programming languages: Python, C, SQL, HTML, CSS.",
        "tags": ["python", "c", "sql", "html", "css", "programming-languages"],
        "priority": 5,
    },
    {
        "id": "sk-skill-ai-ml",
        "category": "skill",
        "canonical_text": (
            "Python libraries: scikit-learn, pandas, NumPy, Matplotlib, Scrapy, FastAPI, "
            "Pydantic, asyncio, Playwright. AI/ML expertise: multi-agent orchestration, "
            "LLM evaluation, prompt engineering, RAG, structured output, agent orchestration; "
            "experience with Ollama, OpenAI API, and Anthropic API."
        ),
        "tags": ["python", "fastapi", "pydantic", "asyncio", "playwright", "scikit-learn",
                 "pandas", "numpy", "matplotlib", "scrapy", "ollama", "openai", "anthropic",
                 "llm", "rag", "prompt-engineering", "multi-agent", "ai-ml"],
        "priority": 5,
    },
    {
        "id": "sk-skill-tools",
        "category": "skill",
        "canonical_text": (
            "Tools and platforms: n8n, Make.com, Next.js, React, Tailwind CSS, Postgres, "
            "SQLite, Docker, Git, GitHub Copilot, Claude Code, Google Cloud, Google Looker "
            "Studio, Figma, Lovable, Adobe Photoshop, Adobe Lightroom, Blender, DaVinci Resolve."
        ),
        "tags": ["n8n", "nextjs", "react", "tailwind", "postgres", "sqlite", "docker",
                 "git", "google-cloud", "figma", "design-tools"],
        "priority": 4,
    },
    # ---- Achievements ----
    {
        "id": "sk-ach-certs",
        "category": "achievement",
        "canonical_text": (
            "Completed Data Science for Engineers from IIT Madras (2026). Pursuing Machine "
            "Learning Specialization from Stanford Online + DeepLearning.AI (in progress) "
            "and CCNA: Networking Fundamentals from Infosys Springboard (in progress)."
        ),
        "tags": ["certification", "machine-learning", "data-science", "networking",
                 "stanford", "iit-madras"],
        "priority": 3,
    },
]

DEMO_PROFILE = {
    "long_term_goals": (
        "Computer Science sophomore at RV College of Engineering (CGPA 8.98/10), "
        "building towards ML engineering and AI systems work. My projects — "
        "Meridian (multi-agent research system with a 135-claim grounding eval: "
        "15% avg hallucination rate, financial agent 0%) and Anchor "
        "(n8n-orchestrated job-pipeline with FK-constrained Grounding Critic) — "
        "reflect a preference for building systems where correctness is verifiable, "
        "not assumed. I want to join a team doing serious work at the intersection "
        "of ML/AI and backend systems — whether that's ML infrastructure, data "
        "pipelines, LLM applications, or AI-powered products — as a Summer 2026 intern."
    ),
    "target_role_types": [
        "ML engineering intern",
        "AI/ML intern",
        "software engineering intern",
        "backend engineering intern",
        "AI infrastructure intern",
        "data engineering intern",
    ],
}

# Standalone sample JD (shape of llm.schemas.JDParserOutput) — same fixture as
# test_resume_tailorer.py / test_day9_agents.py, for apples-to-apples comparison.
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
        f"- [{e['category']}] {e['canonical_text']} (tags: {', '.join(e['tags'] or [])})" for e in entries
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
    entries = DEMO_ENTRIES
    profile = DEMO_PROFILE
    entry_ids = {e["id"] for e in entries}

    print(f"Using {len(entries)} demo resume entries (genericized fixture, not Postgres-backed)")

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

    print(f"\n=== Match Scorer output ===\nscore: {scorer.score}, tier: {scorer.tier.value}")
    print(json.dumps(scorer.model_dump(), indent=2))

    if scorer.score < 60:
        print("\n-> score < 60: in Workflow 3 this would go to the low-match Slack/Wait gate.")
        print("   Continuing anyway for demo purposes.")

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

    cited_ids = {line.master_resume_entry_id for section in tailored.sections for line in section.lines}
    unknown_ids = cited_ids - entry_ids
    if unknown_ids:
        print(f"\n-> WARNING: tailorer cited {len(unknown_ids)} id(s) not in the fixture set: {unknown_ids}")
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

    # Step 5: Cover Letter Generator
    cover_letter_prompt = build_cover_letter_prompt(entries, SAMPLE_JD, SAMPLE_SYNTHESIS, critic, profile)
    try:
        cover_letter_data = call_llm(cover_letter_prompt, "cover_letter")
        cover_letter = CoverLetterOutput.model_validate(cover_letter_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"COVER LETTER FAILED: {e}")
        return

    print("\n=== Cover Letter output ===")
    print(json.dumps(cover_letter.model_dump(), indent=2))
    word_count = sum(len(p.split()) for p in cover_letter.paragraphs)
    print(f"-> word count: {word_count} (limit 250)")

    # Step 6: LinkedIn Drafter
    linkedin_prompt = build_linkedin_prompt(SAMPLE_JD, SAMPLE_SYNTHESIS, critic)
    try:
        linkedin_data = call_llm(linkedin_prompt, "linkedin_drafter")
        linkedin = LinkedInDrafterOutput.model_validate(linkedin_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"LINKEDIN DRAFTER FAILED: {e}")
        return

    print("\n=== LinkedIn Drafter output ===")
    print(json.dumps(linkedin.model_dump(), indent=2))
    print(f"-> char count: {len(linkedin.message)} (limit 300)")

    # Step 7: Skill Gap Analyzer
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

    # Step 8: PDF render (resume + cover letter), using template placeholders
    # for name/contact — no real PII is ever passed here.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    resume_payload = {
        "template": "resume",
        "data": {
            "summary": tailored.summary,
            "sections": [
                {
                    "category": section.category.value,
                    "lines": [{"text": line.text} for line in section.lines],
                }
                for section in tailored.sections
            ],
        },
    }
    resp = httpx.post(RENDER_PDF_URL, json=resume_payload, timeout=60.0)
    resp.raise_for_status()
    (OUTPUT_DIR / "resume.pdf").write_bytes(resp.content)
    print(f"\n-> wrote {OUTPUT_DIR / 'resume.pdf'} ({len(resp.content)} bytes)")

    cover_letter_payload = {
        "template": "cover_letter",
        "data": {
            "date": date.today().isoformat(),
            "company_name": SAMPLE_JD["company_name"],
            "role_title": SAMPLE_JD["role_title"],
            "paragraphs": cover_letter.paragraphs,
        },
    }
    resp = httpx.post(RENDER_PDF_URL, json=cover_letter_payload, timeout=60.0)
    resp.raise_for_status()
    (OUTPUT_DIR / "cover_letter.pdf").write_bytes(resp.content)
    print(f"-> wrote {OUTPUT_DIR / 'cover_letter.pdf'} ({len(resp.content)} bytes)")

    print(f"\nDemo complete. PDFs written to {OUTPUT_DIR} (not in the repo, /tmp only).")


if __name__ == "__main__":
    main()
