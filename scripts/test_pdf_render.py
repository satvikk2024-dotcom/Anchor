"""
Day 9 smoke test: PDF rendering for the tailored resume and cover letter
templates, via the fetch service's POST /render-pdf endpoint
(fetch/server.py).

Usage:
    .venv/bin/python scripts/test_pdf_render.py

Renders both pdf/templates/resume.html and pdf/templates/cover_letter.html
with hand-written sample data (shape of ResumeTailorerOutput /
CoverLetterOutput) and writes the resulting PDFs to data/tmp/ for visual
inspection. Doesn't depend on Ollama — just exercises the Playwright
HTML -> PDF path.

Requires:
  - Fetch service running: .venv/bin/uvicorn fetch.server:app --port 8002
"""

import sys
from pathlib import Path

import httpx

RENDER_URL = "http://localhost:8002/render-pdf"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "tmp"

SAMPLE_RESUME = {
    "summary": "Backend-focused software engineering intern candidate with hands-on "
    "experience building Python services and a strong grounding in SQL and "
    "relational database design.",
    "sections": [
        {
            "category": "experience",
            "lines": [
                {
                    "master_resume_entry_id": "11111111-1111-1111-1111-111111111111",
                    "text": "Software Engineering Intern, built internal tooling using Python and FastAPI.",
                }
            ],
        },
        {
            "category": "skill",
            "lines": [
                {
                    "master_resume_entry_id": "22222222-2222-2222-2222-222222222222",
                    "text": "Proficient in Python, including FastAPI and async programming.",
                },
                {
                    "master_resume_entry_id": "33333333-3333-3333-3333-333333333333",
                    "text": "Experience with SQL and relational database design (Postgres).",
                },
            ],
        },
        {
            "category": "education",
            "lines": [
                {
                    "master_resume_entry_id": "44444444-4444-4444-4444-444444444444",
                    "text": "B.S. Computer Science, expected graduation May 2026.",
                }
            ],
        },
    ],
}

SAMPLE_COVER_LETTER = {
    "company_name": "Fictional Co",
    "role_title": "Software Engineering Intern - Backend",
    "date": "June 15, 2026",
    "paragraphs": [
        "I am excited to apply for the Software Engineering Intern - Backend position "
        "on the Platform Infrastructure team at Fictional Co. Your recent Series B "
        "to expand the platform team reflects exactly the kind of growth I want to "
        "contribute to.",
        "In a prior internship, I built internal tooling using Python and FastAPI, "
        "and I have hands-on experience with SQL and relational database design in "
        "Postgres — both core to your tech stack.",
        "I'd welcome the chance to bring that background to your team this summer.",
    ],
}


def render(template: str, data: dict, out_name: str) -> None:
    resp = httpx.post(RENDER_URL, json={"template": template, "data": data}, timeout=60.0)
    resp.raise_for_status()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / out_name
    out_path.write_bytes(resp.content)
    print(f"{template}: wrote {len(resp.content)} bytes -> {out_path}")


def main() -> None:
    render("resume", SAMPLE_RESUME, "sample_resume.pdf")
    render("cover_letter", SAMPLE_COVER_LETTER, "sample_cover_letter.pdf")

    # Unknown template name is rejected by the Literal["resume","cover_letter"]
    # schema before it ever reaches the handler.
    resp = httpx.post(RENDER_URL, json={"template": "nope", "data": {}}, timeout=10.0)
    if resp.status_code == 422:
        print("unknown template -> 422 as expected")
    else:
        print(f"-> WARNING: unknown template returned {resp.status_code}, expected 422")


if __name__ == "__main__":
    main()
