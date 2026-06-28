"""
One-off Day 17 helper: capture n8n workflow-canvas screenshots and dashboard
page screenshots into docs/canvas-screenshots/, for the README.

Usage:
    .venv/bin/python scripts/capture_screenshots.py

Requires: n8n running on :5678 (logged in via N8N_OWNER_EMAIL/PASSWORD from .env),
dashboard running on :3000.
"""

import os
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "canvas-screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N8N_BASE = "http://localhost:5678"
DASHBOARD_BASE = "http://localhost:3000"

WORKFLOW_FILES = [
    "00_error_handler",
    "01_job_intake",
    "02_job_processor",
    "03_match_and_generate",
    "04_follow_up_scheduler",
    "05_weekly_reflection",
]


def load_env() -> dict:
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def n8n_login_cookie() -> str:
    env = load_env()
    email = env["N8N_OWNER_EMAIL"]
    password = env["N8N_OWNER_PASSWORD"]
    resp = httpx.post(
        f"{N8N_BASE}/rest/login",
        json={"emailOrLdapLoginId": email, "password": password},
    )
    resp.raise_for_status()
    cookie = resp.cookies.get("n8n-auth")
    if not cookie:
        raise RuntimeError(f"No n8n-auth cookie in login response: {dict(resp.cookies)}")
    return cookie


def find_workflow_ids(cookie: str) -> dict[str, str]:
    resp = httpx.get(f"{N8N_BASE}/rest/workflows", cookies={"n8n-auth": cookie})
    resp.raise_for_status()
    data = resp.json()["data"]
    by_name = {}
    for wf in data:
        for fname in WORKFLOW_FILES:
            # workflow names don't always match filenames exactly; match by
            # number prefix convention (e.g. "01" in the filename).
            num = fname.split("_")[0]
            if wf["name"].strip().startswith(num) or fname[3:].replace("_", " ") in wf["name"].lower().replace(
                "_", " "
            ):
                by_name[fname] = wf["id"]
    return by_name


def main() -> None:
    cookie = n8n_login_cookie()
    wf_ids = find_workflow_ids(cookie)
    print("Found workflow ids:", wf_ids)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        context.add_cookies(
            [
                {
                    "name": "n8n-auth",
                    "value": cookie,
                    "domain": "localhost",
                    "path": "/",
                }
            ]
        )

        # n8n workflow canvases
        for fname in WORKFLOW_FILES:
            wf_id = wf_ids.get(fname)
            if not wf_id:
                print(f"  SKIP {fname}: workflow id not found")
                continue
            page = context.new_page()
            page.goto(f"{N8N_BASE}/workflow/{wf_id}", wait_until="networkidle")
            time.sleep(2)  # let canvas render/auto-fit
            # try to trigger "zoom to fit" via keyboard shortcut (n8n: "1")
            page.keyboard.press("1")
            time.sleep(1)
            out_path = OUT_DIR / f"{fname}.png"
            page.screenshot(path=str(out_path), full_page=False)
            print(f"  saved {out_path}")
            page.close()

        # dashboard pages
        for route, fname in [
            ("/", "dashboard_welcome"),
            ("/dashboard", "dashboard_kanban"),
            ("/decisions", "dashboard_decisions"),
            ("/insights", "dashboard_insights"),
        ]:
            page = context.new_page()
            page.goto(f"{DASHBOARD_BASE}{route}", wait_until="networkidle")
            time.sleep(1)
            out_path = OUT_DIR / f"{fname}.png"
            page.screenshot(path=str(out_path), full_page=True)
            print(f"  saved {out_path}")
            page.close()

        browser.close()


if __name__ == "__main__":
    main()
