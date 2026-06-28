"""
Day 5 smoke test: Company Synthesizer agent on real companies.

Usage:
    .venv/bin/python scripts/test_company_synthesizer.py "<company name>" ["<role title>"] ["<team/org>"]

For the given company:
  1. Guess homepage/about/careers URLs the same way Workflow 2 does
     (lowercase, strip non-alphanumeric, + ".com" — a known-imperfect
     heuristic; mismatches are exactly what this agent needs to handle
     honestly).
  2. Fetch each via the Playwright fetch service (localhost:8002), and fetch
     recent news via Google News RSS — failures are tolerated, same as
     Workflow 2's "Continue on Fail" branches.
  3. Assemble the same prompt shape Workflow 2's "Prepare Synthesizer Input"
     node builds, send it to the LLM wrapper with
     prompts/company_synthesizer.md as the system prompt, json_mode=True.
  4. Parse + validate the JSON response against
     llm.schemas.CompanySynthesizerOutput.
  5. Print the structured result.

Requires:
  - LLM wrapper running:   .venv/bin/uvicorn llm.server:app --port 8001
  - Fetch service running: .venv/bin/uvicorn fetch.server:app --port 8002
  - Ollama running with qwen2.5:7b pulled
"""

import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.schemas import CompanySynthesizerOutput  # noqa: E402

LLM_WRAPPER_URL = "http://localhost:8001/complete"
FETCH_SERVICE_URL = "http://127.0.0.1:8002/fetch"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "company_synthesizer.md"
MAX_SOURCE_CHARS = 3000
MAX_PROMPT_CHARS = 12000


def slugify_domain(company_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    return f"{slug}.com"


def fetch_page(url: str) -> tuple[str | None, bool]:
    try:
        resp = httpx.post(FETCH_SERVICE_URL, json={"url": url}, timeout=60.0)
        resp.raise_for_status()
        return resp.json()["text"][:MAX_SOURCE_CHARS], True
    except Exception:
        return None, False


def fetch_news(company_name: str) -> list[dict]:
    query = urllib.parse.quote(company_name)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        resp = httpx.get(url, timeout=30.0)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        items = []
        for item in root.findall("./channel/item")[:5]:
            items.append(
                {
                    "title": item.findtext("title"),
                    "pub_date": item.findtext("pubDate"),
                    "source": item.findtext("source"),
                }
            )
        return items
    except Exception:
        return []


def build_prompt(
    company_name: str,
    role_title: str,
    team_or_org: str | None,
    domain: str,
    news_items: list[dict],
    homepage: str | None,
    homepage_ok: bool,
    about: str | None,
    about_ok: bool,
    careers: str | None,
    careers_ok: bool,
) -> str:
    news_lines = (
        "\n".join(
            f"- {n['title']} ({n['source'] or 'unknown source'}, {n['pub_date'] or 'no date'})"
            for n in news_items
        )
        or "(no news items found)"
    )

    role_line = f"Role being hired for: {role_title}"
    if team_or_org:
        role_line += f" (team: {team_or_org})"

    parts = [
        f"Company: {company_name}",
        f"Domain (best guess, may be wrong): {domain}",
        role_line,
        "",
        "## Recent news headlines",
        news_lines,
        "",
        "## Homepage text" + ("" if homepage_ok else " (unavailable)"),
        homepage if homepage_ok else "(fetch failed or domain guess incorrect)",
        "",
        "## About page text" + ("" if about_ok else " (unavailable)"),
        about if about_ok else "(fetch failed or page does not exist)",
        "",
        "## Careers page text" + ("" if careers_ok else " (unavailable)"),
        careers if careers_ok else "(fetch failed or page does not exist)",
    ]
    return "\n".join(parts)[:MAX_PROMPT_CHARS]


def main(company_name: str, role_title: str, team_or_org: str | None) -> None:
    domain = slugify_domain(company_name)
    print(f"Guessed domain: {domain}")

    homepage, homepage_ok = fetch_page(f"https://www.{domain}")
    about, about_ok = fetch_page(f"https://www.{domain}/about")
    careers, careers_ok = fetch_page(f"https://www.{domain}/careers")
    news_items = fetch_news(company_name)

    print(f"  homepage: {'ok' if homepage_ok else 'FAILED'}")
    print(f"  about:    {'ok' if about_ok else 'FAILED'}")
    print(f"  careers:  {'ok' if careers_ok else 'FAILED'}")
    print(f"  news:     {len(news_items)} items")

    prompt = build_prompt(
        company_name, role_title, team_or_org, domain,
        news_items, homepage, homepage_ok, about, about_ok, careers, careers_ok,
    )
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
        print(f"  PARSE FAILED: {e}\n  raw: {raw_text[:2000]}")
        return

    try:
        validated = CompanySynthesizerOutput.model_validate(data)
    except ValidationError as e:
        print(f"  SCHEMA VALIDATION FAILED: {e}\n  raw: {json.dumps(data, indent=2)[:2000]}")
        return

    print("  PASSED schema validation")
    print(json.dumps(validated.model_dump(), indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: test_company_synthesizer.py "<company name>" ["<role title>"] ["<team/org>"]')
        sys.exit(1)
    company = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "Software Engineering Intern"
    team = sys.argv[3] if len(sys.argv) > 3 else None
    main(company, role, team)
