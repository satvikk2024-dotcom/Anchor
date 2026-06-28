"""
Day 3 smoke test: JD Parser agent on real job postings.

Usage:
    .venv/bin/python scripts/test_jd_parser.py <url1> [<url2> <url3> ...]

For each URL:
  1. Fetch the rendered page text with Playwright (headless Chromium) — handles
     JS-heavy ATS pages (Greenhouse/Lever/Workday/etc.).
  2. Send the text to the LLM wrapper's /complete endpoint with
     prompts/jd_parser.md as the system prompt, json_mode=True.
  3. Parse + validate the JSON response against llm.schemas.JDParserOutput.
  4. Print the structured result.

Requires:
  - LLM wrapper running: .venv/bin/uvicorn llm.server:app --port 8001
  - Ollama running with qwen2.5:7b pulled
"""

import json
import sys
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.schemas import JDParserOutput  # noqa: E402

LLM_WRAPPER_URL = "http://localhost:8001/complete"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "jd_parser.md"
MAX_CHARS = 12000  # keep prompts within qwen2.5:7b's comfortable context window


def fetch_jd_text(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60_000)
        text = page.inner_text("body")
        browser.close()
    return text.strip()


def parse_jd(jd_text: str) -> tuple[dict, JDParserOutput | None, str | None]:
    system_prompt = PROMPT_PATH.read_text()
    truncated = jd_text[:MAX_CHARS]

    resp = httpx.post(
        LLM_WRAPPER_URL,
        json={
            "prompt": truncated,
            "system": system_prompt,
            "json_mode": True,
        },
        timeout=180.0,
    )
    resp.raise_for_status()
    raw_text = resp.json()["text"]

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        return {"raw": raw_text}, None, f"Invalid JSON: {e}"

    try:
        validated = JDParserOutput.model_validate(data)
    except ValidationError as e:
        return data, None, f"Schema validation failed: {e}"

    return data, validated, None


def main(urls: list[str]) -> None:
    for url in urls:
        print(f"\n{'=' * 70}\n{url}\n{'=' * 70}")
        try:
            jd_text = fetch_jd_text(url)
        except Exception as e:
            print(f"  FETCH FAILED: {e}")
            continue

        print(f"  fetched {len(jd_text)} chars")

        data, validated, error = parse_jd(jd_text)
        if error:
            print(f"  PARSE FAILED: {error}")
            print(f"  raw output: {json.dumps(data, indent=2)[:2000]}")
            continue

        print("  PASSED schema validation")
        print(json.dumps(validated.model_dump(), indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: test_jd_parser.py <url1> [<url2> <url3> ...]")
        sys.exit(1)
    main(sys.argv[1:])
