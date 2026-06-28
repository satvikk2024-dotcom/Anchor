"""
One-off script: generate a comprehensive technical-overview PDF of the Anchor project.

Writes: Anchor_Overview.pdf in the project root.

Usage:
    .venv/bin/python scripts/build_overview_pdf.py
"""

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / "docs" / "canvas-screenshots"
OUT_PDF = ROOT / "Anchor_Overview.pdf"


def img_b64(name: str) -> str:
    p = SCREENSHOTS / name
    if p.exists():
        return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
    return ""


def html_img(filename: str, alt: str, width: str = "100%") -> str:
    src = img_b64(filename)
    if not src:
        return f'<p style="color:#999;font-style:italic">[Screenshot: {alt} — not found]</p>'
    return f'<img src="{src}" alt="{alt}" style="width:{width};border-radius:6px;border:1px solid #ddd;margin:8px 0;">'


def build_html() -> str:
    wf_img_row = f"""
<table style="width:100%;border-collapse:collapse;margin:16px 0;">
  <tr>
    <td style="width:50%;padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Workflow 1 — Job Intake</p>
      {html_img("01_job_intake.png","Workflow 1 canvas")}
    </td>
    <td style="width:50%;padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Workflow 2 — Job Processor (22 nodes)</p>
      {html_img("02_job_processor.png","Workflow 2 canvas")}
    </td>
  </tr>
  <tr>
    <td style="padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Workflow 3 — Match & Generate (67 nodes)</p>
      {html_img("03_match_and_generate.png","Workflow 3 canvas")}
    </td>
    <td style="padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Workflow 4 — Follow-up Scheduler (14 nodes)</p>
      {html_img("04_follow_up_scheduler.png","Workflow 4 canvas")}
    </td>
  </tr>
  <tr>
    <td style="padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Workflow 5 — Weekly Reflection (8 nodes)</p>
      {html_img("05_weekly_reflection.png","Workflow 5 canvas")}
    </td>
    <td style="padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Error Handler (6 nodes, wired to all 5)</p>
      {html_img("00_error_handler.png","Error Handler canvas")}
    </td>
  </tr>
</table>"""

    dashboard_img_row = f"""
<table style="width:100%;border-collapse:collapse;margin:16px 0;">
  <tr>
    <td style="width:50%;padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Welcome / Landing</p>
      {html_img("dashboard_welcome.png","Dashboard welcome")}
    </td>
    <td style="width:50%;padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Applications Kanban</p>
      {html_img("dashboard_kanban.png","Dashboard kanban")}
    </td>
  </tr>
  <tr>
    <td style="padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Decisions Audit Log</p>
      {html_img("dashboard_decisions.png","Dashboard decisions")}
    </td>
    <td style="padding:6px;vertical-align:top">
      <p style="font-size:11px;color:#56687A;margin:0 0 4px 0;font-weight:600">Weekly Insights</p>
      {html_img("dashboard_insights.png","Dashboard insights")}
    </td>
  </tr>
</table>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 13px;
    line-height: 1.55;
    color: #1D2226;
    background: #FAF7F2;
    padding: 0;
  }}
  .page {{ padding: 48px 56px; max-width: 900px; margin: 0 auto; background: #FAF7F2; }}

  /* Title page */
  .title-page {{
    background: #2F6B66;
    color: white;
    padding: 80px 56px 64px;
    margin: -48px -56px 48px;
  }}
  .title-page h1 {{ font-size: 42px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 8px; }}
  .title-page .subtitle {{ font-size: 18px; opacity: 0.85; margin-bottom: 32px; }}
  .title-page .meta {{ font-size: 13px; opacity: 0.65; line-height: 2; }}
  .title-page .badge {{
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    margin-right: 6px;
    margin-top: 20px;
  }}

  /* Section headings */
  h2 {{
    font-size: 20px; font-weight: 700; color: #2F6B66;
    margin: 40px 0 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #ECE6DC;
  }}
  h3 {{ font-size: 15px; font-weight: 600; color: #1D2226; margin: 20px 0 8px; }}
  h4 {{ font-size: 13px; font-weight: 600; color: #56687A; margin: 14px 0 6px; text-transform: uppercase; letter-spacing: 0.5px; }}

  p {{ margin-bottom: 10px; }}
  ul {{ margin: 8px 0 12px 20px; }}
  li {{ margin-bottom: 4px; }}

  /* Tables */
  table.data {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 12px; }}
  table.data th {{ background: #2F6B66; color: white; padding: 8px 10px; text-align: left; font-weight: 600; }}
  table.data td {{ padding: 7px 10px; border-bottom: 1px solid #ECE6DC; vertical-align: top; }}
  table.data tr:nth-child(even) td {{ background: #f5f1ea; }}

  /* Code / mono */
  code {{ background: #ECE6DC; padding: 1px 5px; border-radius: 3px; font-size: 11.5px; font-family: 'SF Mono', 'Monaco', monospace; }}
  pre {{ background: #1D2226; color: #E8E4DC; padding: 14px 16px; border-radius: 6px; font-size: 11px; font-family: monospace; overflow: hidden; margin: 12px 0; white-space: pre-wrap; word-break: break-all; }}

  /* Callout boxes */
  .callout {{
    background: #fff;
    border-left: 4px solid #2F6B66;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin: 16px 0;
    font-size: 12.5px;
  }}
  .callout.warning {{ border-left-color: #B7791F; background: #fffbf0; }}
  .callout.info {{ border-left-color: #3D8B5C; background: #f0faf5; }}

  /* Tags */
  .tag {{
    display: inline-block;
    background: #2F6B6614;
    color: #2F6B66;
    border: 1px solid #2F6B6640;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    margin: 2px 3px 2px 0;
    font-weight: 500;
  }}

  /* ADR card */
  .adr-card {{
    background: white;
    border: 1px solid #ECE6DC;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 12px 0;
  }}
  .adr-card h3 {{ margin: 0 0 6px 0; font-size: 14px; color: #2F6B66; }}
  .adr-card .decision {{ font-weight: 600; font-size: 12px; color: #1D2226; margin-bottom: 6px; }}
  .adr-card p {{ font-size: 12px; color: #56687A; margin-bottom: 0; }}

  /* Page break */
  .break {{ page-break-before: always; }}

  /* Metric cards */
  .metric-row {{ display: flex; gap: 12px; margin: 16px 0; }}
  .metric-card {{
    flex: 1;
    background: white;
    border: 1px solid #ECE6DC;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
  }}
  .metric-card .value {{ font-size: 28px; font-weight: 700; color: #2F6B66; }}
  .metric-card .label {{ font-size: 11px; color: #56687A; margin-top: 4px; }}
</style>
</head>
<body>
<div class="page">

  <!-- TITLE PAGE -->
  <div class="title-page">
    <h1>Anchor</h1>
    <div class="subtitle">Personal AI Job-Application Pipeline</div>
    <div class="meta">
      Satvik Krishna &nbsp;·&nbsp; satvikkrishna06@gmail.com<br>
      RV College of Engineering, Bengaluru &nbsp;·&nbsp; 2026 Internship Search<br>
      github.com/satvikk2024-dotcom
    </div>
    <div>
      <span class="badge">n8n</span>
      <span class="badge">Postgres</span>
      <span class="badge">Ollama · qwen2.5:7b</span>
      <span class="badge">Next.js Dashboard</span>
      <span class="badge">Playwright</span>
      <span class="badge">Google Drive · Notion · Slack</span>
    </div>
  </div>

  <!-- EXECUTIVE SUMMARY -->
  <h2>Executive Summary</h2>
  <p>
    Anchor is a personal, n8n-orchestrated AI pipeline that takes a job-posting URL and produces a
    researched, <strong>factually-grounded</strong> application packet — tailored resume, cover letter,
    LinkedIn connection message, and skill-gap report — ready for review in Notion, with PDFs uploaded
    to Google Drive. It replaces roughly 90 minutes of manual research-and-tailoring work per application
    with roughly 8 minutes of human review and submission.
  </p>
  <p>
    The system is built for a single user (Satvik, 2026 internship search) and is not a product.
    Its purpose is two-fold: it is a practical daily tool, and it is a portfolio demonstration of
    advanced n8n orchestration, factual-grounding techniques applied to generation problems, and
    rigorous eval methodology.
  </p>
  <div class="callout">
    <strong>The grounding bet.</strong> Generated resumes hallucinate experience — that's the headline
    failure mode of "tailor my resume to this JD" tools. Anchor's core architectural bet is to decompose
    the master resume into structured, addressable <code>master_resume_entry</code> rows, make tailoring a
    <em>selection + rephrasing</em> operation over those entries, and enforce that every tailored line
    cites its source by database foreign key. An adversarial Grounding Critic agent checks each line
    against its cited source before anything is shipped. This structure makes the failure mode
    (hallucinated experience) impossible by construction rather than statistically unlikely.
  </div>

  <div class="metric-row">
    <div class="metric-card"><div class="value">5</div><div class="label">n8n workflows</div></div>
    <div class="metric-card"><div class="value">11</div><div class="label">AI agent calls<br>per application</div></div>
    <div class="metric-card"><div class="value">67</div><div class="label">nodes in Workflow 3<br>(Match & Generate)</div></div>
    <div class="metric-card"><div class="value">10</div><div class="label">Postgres tables</div></div>
    <div class="metric-card"><div class="value">~8 min</div><div class="label">review time vs.<br>~90 min manual</div></div>
  </div>

  <!-- ARCHITECTURE -->
  <h2 class="break">System Architecture</h2>
  <p>
    Five n8n workflows, each triggered differently (webhook, sub-workflow execution, cron), share a single
    Postgres database as the source of truth. All AI calls go through a local FastAPI wrapper
    (<code>llm/</code>) around Ollama's <code>qwen2.5:7b</code> — no paid LLM APIs. A Playwright microservice
    (<code>fetch/</code>) handles JD page fetching, company research scraping, and PDF rendering.
  </p>
  <pre>
You (browser) ──POST /webhook/intake──▶ Workflow 1: Job Intake
                                              │  respond &lt;500ms · insert application row
                                              ▼
                                        Workflow 2: Job Processor
                                              │  Playwright JD fetch → JD Parser agent
                                              │  4 parallel research branches (news/homepage/about/careers)
                                              │  Company Synthesizer agent
                                              │  status: researched
                                              ▼
                                        Workflow 3: Match & Generate (67 nodes)
                                              │  Resume Critic → Match Scorer
                                              │  IF score &lt; 60 → Slack + Wait for human
                                              │  Resume Tailorer → Grounding Critic (1 retry)
                                              │  Cover Letter / LinkedIn / Skill Gap agents
                                              │  PDF render → Drive upload → Notion page
                                              │  Slack "ready for review"
                                              │  status: awaiting_review

Workflow 4: Follow-up Scheduler (cron 8am)
  └─ submitted apps past nudge window → Follow-up Decision agent → Slack digest

Workflow 5: Weekly Reflection (cron Sun 7pm)
  └─ last 4 weeks aggregated → Pattern Detector agent (min-N=5) → Slack digest

Error Workflow (n8n error trigger, wired to all 5)
  └─ retry transient errors (max 2, 2s backoff) → Slack alert on permanent failure
  </pre>

  <h3>Workflow Summary</h3>
  <table class="data">
    <tr><th>Workflow</th><th>Trigger</th><th>Nodes</th><th>Key Patterns</th></tr>
    <tr><td><strong>1 · Job Intake</strong></td><td>Webhook POST /webhook/intake</td><td>~8</td><td>Sync response &lt;500ms; async hand-off via Execute Workflow; URL format + ATS-host detection</td></tr>
    <tr><td><strong>2 · Job Processor</strong></td><td>Execute Workflow</td><td>22</td><td>Playwright JD fetch; parallel research branches each tolerant of fetch failure (onError: continueRegularOutput); queryReplacement rule (simple field access only)</td></tr>
    <tr><td><strong>3 · Match & Generate</strong></td><td>Execute Workflow</td><td>67</td><td>Match gate at 60; Grounding Critic retry loop; binary-response state-carrying rule; Drive/Notion export; all HTTP nodes have retryOnFail max 3</td></tr>
    <tr><td><strong>4 · Follow-up Scheduler</strong></td><td>Cron, daily 8am</td><td>14</td><td>Precomputed "window reached: yes/no" to prevent model re-deriving; Wait Until 9am before digest send</td></tr>
    <tr><td><strong>5 · Weekly Reflection</strong></td><td>Cron, Sun 7pm</td><td>8</td><td>Min-N=5 guard precomputed; Pattern Detector reads verbatim evidence from input (no re-derivation)</td></tr>
    <tr><td><strong>0 · Error Handler</strong></td><td>n8n error trigger</td><td>6</td><td>Catches all 5 workflows; application_id always NULL (not available from Error Trigger); Slack alert includes execution URL + UPDATE template</td></tr>
  </table>

  <!-- WORKFLOW CANVASES -->
  <h2 class="break">Workflow Canvases</h2>
  <p>All six canvases captured from the live n8n instance (localhost:5678). Workflows are exported to
  <code>n8n/workflows/</code> as JSON and can be imported fresh on any n8n instance.</p>
  {wf_img_row}

  <!-- AGENT PIPELINE -->
  <h2 class="break">Agent Pipeline</h2>
  <p>
    All agents follow the same calling convention: the n8n workflow builds a text prompt in a Code
    node and POSTs to <code>http://localhost:8001/complete</code> with
    <code>{"{"}"prompt": "...", "system_prompt_name": "agent_name", "json_mode": true{"}"}</code>.
    The wrapper reads <code>prompts/&lt;name&gt;.md</code> as the system prompt, calls Ollama, and caches
    the response on disk by <code>(model, prompt, system, json_mode)</code> hash for reproducible evals.
    All structured outputs are validated in Python (<code>llm/schemas.py</code>, Pydantic v2) before
    any downstream node consumes them.
  </p>

  <h3>Workflow 2 Agents</h3>
  <table class="data">
    <tr><th>Agent</th><th>Input</th><th>Output contract</th><th>Key prompt decisions</th></tr>
    <tr>
      <td><strong>JD Parser</strong><br><code>jd_parser.md</code></td>
      <td>Raw JD page HTML/text</td>
      <td><code>JDParserOutput</code>: company_name, role_title, must_haves[], nice_to_haves[], responsibilities[], tech_stack[], culture_signals[], location_type (enum)</td>
      <td>location_type must be "exactly one" value — fixing pipe-joined enum bug found in smoke test</td>
    </tr>
    <tr>
      <td><strong>Company Synthesizer</strong><br><code>company_synthesizer.md</code></td>
      <td>Merged news + homepage + about + careers text</td>
      <td><code>CompanySynthesizerOutput</code>: what_they_do, recent_developments[], tech_signals[], company_type (enum), culture_signals[], likely_role_context</td>
      <td>Input-tolerant (any subset of 4 sources may be empty); output is stored as JSONB in <code>company.synthesis</code></td>
    </tr>
  </table>

  <h3>Workflow 3 Agents</h3>
  <table class="data">
    <tr><th>Agent</th><th>Input</th><th>Output contract</th><th>Key prompt decisions</th></tr>
    <tr>
      <td><strong>Resume Critic</strong><br><code>resume_critic.md</code></td>
      <td>All master_resume_entry rows + user_profile + JD + synthesis</td>
      <td><code>ResumeCriticOutput</code>: strengths_for_this_role[], weaknesses_to_address[], gaps_unfixable_in_this_application[], suggested_angle</td>
      <td>Rigorous honesty constraint — "accurate over encouraging"; result feeds downstream agents, not the user directly</td>
    </tr>
    <tr>
      <td><strong>Match Scorer</strong><br><code>match_scorer.md</code></td>
      <td>ResumeCriticOutput + user_profile + JD</td>
      <td><code>MatchScorerOutput</code>: score (0–100), tier (hot/warm/cold), reasoning, top_strengths[], top_gaps[{"{"}gap,severity{"}"}], red_flags[]</td>
      <td>score &lt; 60 → Slack Wait node for human decision; score never inflated; severity enum: minor/significant/dealbreaker</td>
    </tr>
    <tr>
      <td><strong>Resume Tailorer</strong><br><code>resume_tailorer.md</code></td>
      <td>Entries + JD + ResumeCriticOutput (+ optional violations feedback on retry)</td>
      <td><code>ResumeTailorerOutput</code>: summary, sections[{"{"}category, lines[{"{"}master_resume_entry_id, text{"}"}]{"}"}]</td>
      <td>Every line must cite a master_resume_entry_id — tailoring is selection + rephrasing only, never invention</td>
    </tr>
    <tr>
      <td><strong>Grounding Critic</strong><br><code>grounding_critic.md</code></td>
      <td>"Lines to check" paired format: each line with its cited source entry</td>
      <td><code>GroundingCriticOutput</code>: passes (bool), violations[]</td>
      <td>Paired format (fixed Day 11) eliminates false positives from cross-list comparison; 1 retry max, then escalate to Slack</td>
    </tr>
    <tr>
      <td><strong>Cover Letter</strong><br><code>cover_letter.md</code></td>
      <td>Entries + JD + synthesis + ResumeCriticOutput + profile</td>
      <td><code>CoverLetterOutput</code>: paragraphs[], master_resume_entry_ids[], company_detail_referenced</td>
      <td>Citation strip field_validator backstop (model sometimes inlines "(id=...)" markers); &lt;250 word limit</td>
    </tr>
    <tr>
      <td><strong>LinkedIn Drafter</strong><br><code>linkedin_drafter.md</code></td>
      <td>JD + synthesis + ResumeCriticOutput</td>
      <td><code>LinkedInDrafterOutput</code>: message (&lt;300 chars), company_detail_referenced</td>
      <td>Word-count proxy (25 words) instead of char limit — qwen2.5:7b can't reliably hit a char count directly</td>
    </tr>
    <tr>
      <td><strong>Skill Gap Analyzer</strong><br><code>skill_gap_analyzer.md</code></td>
      <td>JD must_haves/nice_to_haves + ResumeCriticOutput + profile</td>
      <td><code>SkillGapAnalyzerOutput</code>: gaps[{"{"}requirement, category (must_have/nice_to_have), severity (minor/significant/dealbreaker), how_to_close{"}"}], verdict (apply_now/address_gap_first/not_recommended)</td>
      <td>category/severity field rules tightened (Day 16 fix): "never copy input field names; omit non-gap items rather than padding with invalid enum values"</td>
    </tr>
  </table>

  <h3>Workflow 4 &amp; 5 Agents</h3>
  <table class="data">
    <tr><th>Agent</th><th>Single-call design</th><th>Key guard</th></tr>
    <tr>
      <td><strong>Follow-up Decision</strong><br><code>follow_up_decision.md</code></td>
      <td>Decides whether to nudge AND drafts the nudge in one pass; 2+ nudges already sent forces wait</td>
      <td>"Follow-up window reached: yes/no" precomputed — model can't reliably do days-vs-window arithmetic</td>
    </tr>
    <tr>
      <td><strong>Pattern Detector</strong><br><code>pattern_detector.md</code></td>
      <td>Aggregated 4-week stats → patterns[], summary; each pattern needs ≥2 applications per compared group</td>
      <td>Min-N=5 guard: if N &lt; 5, patterns[] must be empty; evidence must be copied verbatim, never re-derived</td>
    </tr>
  </table>

  <!-- DATABASE -->
  <h2 class="break">Database Schema</h2>
  <p>
    10 tables in <code>db/schema.sql</code>. Postgres is the single source of truth for all
    application/company/material/agent-run state. UUID PKs via <code>pgcrypto</code>. All
    timestamps are <code>timestamptz</code>. Closed sets use native <code>ENUM</code> types.
    Agent outputs are stored as <code>jsonb</code>.
  </p>
  <table class="data">
    <tr><th>Table</th><th>Key columns</th><th>Purpose</th></tr>
    <tr><td><code>company</code></td><td>id, name (unique lowercase), domain, synthesis (jsonb)</td><td>One row per employer; upserted by Workflow 2 on conflict lower(name)</td></tr>
    <tr><td><code>application</code></td><td>id, company_id, url, role_title, status (enum, 11 values), match_score, match_tier</td><td>Central entity; status is the pipeline's state machine</td></tr>
    <tr><td><code>master_resume_entry</code></td><td>id, category (enum: experience|project|skill|education|achievement), canonical_text, tags (text[])</td><td>Structured master resume — every tailored line must cite one of these rows</td></tr>
    <tr><td><code>generated_material</code></td><td>id, application_id, type (enum), content_json (jsonb), pdf_drive_url</td><td>One row per generated artefact (tailored_resume, cover_letter, linkedin_message, skill_gap_report, follow_up_nudge)</td></tr>
    <tr><td><code>material_grounding</code></td><td>generated_material_id, master_resume_entry_id</td><td>FK join table — every cited entry creates a row; grounding is verifiable in one SQL join</td></tr>
    <tr><td><code>agent_run</code></td><td>id, application_id, agent_name, workflow_name, input_hash, output_json (jsonb), latency_ms, critic_passed</td><td>Full audit log of every LLM call — surfaced in the /decisions dashboard page</td></tr>
    <tr><td><code>application_event</code></td><td>id, application_id (nullable), event_type, payload (jsonb)</td><td>Append-only event log; used by Error Workflow (application_id NULL for system errors)</td></tr>
    <tr><td><code>weekly_insight</code></td><td>id, week_start, insights (jsonb: {"{"}patterns[], summary{"}"})</td><td>Written by Workflow 5 each Sunday; surfaced in the /insights dashboard page</td></tr>
    <tr><td><code>user_profile</code></td><td>id, long_term_goals, target_role_types (text[])</td><td>Single row; read by Resume Critic, Match Scorer, Skill Gap Analyzer</td></tr>
    <tr><td><code>role_recommendation</code></td><td>application_id, recommended_angle, suggested_frame</td><td>Optional Workflow 2 output; not yet consumed downstream (reserved)</td></tr>
  </table>

  <h3>application_status state machine (11 values)</h3>
  <pre>
intake_received → researched → [low_match_waiting] → awaiting_review
                                      ↕ human decision
                              → submitted → responded → interview
                                         ↘ rejected
                                         ↘ ghosted (auto after 21 days)
                                         ↘ withdrawn (human via Slack)
                                         ↘ errored (error workflow)
  </pre>

  <!-- FACTUAL GROUNDING -->
  <h2 class="break">Factual Grounding System</h2>
  <p>
    This is Anchor's most important architectural feature. Every tailored resume line passes through
    a three-layer grounding chain:
  </p>
  <ol style="margin:10px 0 16px 20px;">
    <li style="margin-bottom:8px"><strong>Structural constraint.</strong> The Resume Tailorer's output contract
    (<code>ResumeTailorerOutput</code>) requires every line to carry a <code>master_resume_entry_id</code>.
    The Pydantic model rejects any output that omits it — the model physically cannot produce an
    unattributed line without the call failing.</li>
    <li style="margin-bottom:8px"><strong>ID validity check.</strong> Workflow 3 verifies that every cited ID
    actually exists in the loaded entry set. A hallucinated UUID fails here.</li>
    <li style="margin-bottom:8px"><strong>Semantic grounding check.</strong> The Grounding Critic agent reads
    each line paired with its cited source entry and checks whether the tailored text's claims are
    supported by that specific entry. It can fail the whole output (triggering one retry with the
    violation list as feedback), and if still failing after retry, escalates to a Slack alert — no
    ungrounded material is ever written to <code>generated_material</code>.</li>
  </ol>
  <div class="callout info">
    The paired "Lines to check" format (each line presented alongside its source, not as two separate
    lists) was the key fix that eliminated false positives in the Grounding Critic (Day 11). The model
    was previously comparing two independent lists and matching by position rather than by content.
  </div>
  <p>
    Every accepted grounded line creates a <code>material_grounding</code> row (FK to
    <code>generated_material</code> + <code>master_resume_entry</code>), making the full citation
    trail queryable in one SQL join — surfaced in the /decisions audit log.
  </p>

  <!-- DASHBOARD -->
  <h2 class="break">Dashboard</h2>
  <p>
    A Next.js 14.2 App Router app (<code>dashboard/</code>) that queries Postgres directly from Server
    Components via a <code>pg.Pool</code> singleton (<code>dashboard/lib/db.ts</code>). No backend API,
    no auth (single local user), no SSE. All routes are <code>export const dynamic = "force-dynamic"</code>
    to prevent static prerendering from freezing Postgres data at build time.
  </p>
  <table class="data">
    <tr><th>Route</th><th>Data source</th><th>What it shows</th></tr>
    <tr><td><code>/</code></td><td>None</td><td>Animated welcome page (CSS fade-in-up) with feature cards</td></tr>
    <tr><td><code>/dashboard</code></td><td>application + company JOIN</td><td>Kanban: all 11 status values grouped into Active Pipeline / Outcomes / Errors; MatchScoreBadge color-coded by tier</td></tr>
    <tr><td><code>/decisions</code></td><td>agent_run + application + company JOIN</td><td>Expandable &lt;details&gt; cards, one per LLM call — agent name, latency, critic_passed, full output_json viewer</td></tr>
    <tr><td><code>/insights</code></td><td>weekly_insight</td><td>Pattern cards with evidence and suggested actions; empty-state cites min-N=5 guard and Sunday 7pm schedule</td></tr>
  </table>
  <p>Design tokens: cream background <code>#FAF7F2</code>, deep-teal accent <code>#2F6B66</code>,
  white card surfaces. Header shortcuts to Notion / Google Drive / n8n editor.</p>
  {dashboard_img_row}

  <!-- EVALUATION -->
  <h2 class="break">Evaluation Framework (Day 15/16)</h2>
  <p>
    Per planning doc §10.1, a Material Quality Eval runs 20 standalone applications through Anchor's
    full agent chain and through a naive single-prompt baseline (no critic, no grounding instructions),
    then compares factual grounding pass rates as the headline metric.
  </p>
  <h3>Methodology</h3>
  <ul>
    <li><strong>Fixtures:</strong> 20 fictional-company JD + synthesis pairs (<code>eval/jd_fixtures.py</code>),
    spanning good/medium/poor fit for Satvik's profile (8 good, 6 medium, 6 poor).</li>
    <li><strong>Anchor chain:</strong> Resume Critic → Match Scorer → Resume Tailorer → Grounding Critic
    (1 retry max) → Cover Letter → LinkedIn Drafter → Skill Gap Analyzer. Same qwen2.5:7b model,
    same prompts as the live pipeline.</li>
    <li><strong>Baseline:</strong> Single-prompt tailor (<code>prompts/baseline_tailor.md</code>) —
    "write the strongest possible application" with no grounding instructions, no critic, no
    structured entry IDs. Output format has no per-line source citations.</li>
    <li><strong>Grounding check:</strong> The <em>same</em> Grounding Critic agent checks both outputs.
    Anchor lines are paired against their single cited entry. Baseline lines are paired against the
    candidate's full resume (the fairest equivalent check: "is this claim supported anywhere in the
    resume?").</li>
  </ul>
  <h3>Rubric dimensions</h3>
  <table class="data">
    <tr><th>#</th><th>Dimension</th><th>Method</th><th>Scale</th></tr>
    <tr><td>1</td><td><strong>Factual grounding</strong> (headline)</td><td>Automated — Grounding Critic agent, both Anchor + baseline</td><td>Binary pass/fail per application</td></tr>
    <tr><td>2</td><td>JD relevance</td><td>Hand-graded</td><td>1–5</td></tr>
    <tr><td>3</td><td>Cover letter specificity</td><td>Hand-graded</td><td>1–5</td></tr>
    <tr><td>4</td><td>Tone match (Anchor only)</td><td>Hand-graded</td><td>1–5</td></tr>
  </table>
  <div class="callout warning">
    <strong>Eval status:</strong> The 20-application tailored batch and the 20-application baseline
    batch are currently running (background process). Results will be written to
    <code>eval/results_summary.md</code> and <code>eval/scores_template.csv</code> once complete,
    and the README eval table will be updated with final numbers.
    <br><br>
    <strong>Expected outcome (planning doc §10.1):</strong> Anchor's grounding pass rate should
    substantially exceed baseline. Prior testing estimated baseline hallucination rates at ~20–30%.
    The structural constraint (every line must cite a master_resume_entry_id, validated at schema
    parse time) makes 100% schema-level grounding a floor — semantic grounding (does the tailored
    text actually follow from the cited entry?) is what the Grounding Critic measures and the retry
    loop enforces.
  </div>

  <!-- DESIGN DECISIONS -->
  <h2 class="break">Design Decisions (ADRs)</h2>
  <p>Full ADR files in <code>docs/decisions/</code>.</p>

  <div class="adr-card">
    <h3>ADR-001 · n8n, not custom Python, for orchestration</h3>
    <div class="decision">Decision: Use n8n as orchestration layer; AI logic in Python FastAPI wrapper.</div>
    <p>The visual workflow canvas is itself the portfolio asset. All 5 workflows + error handler are
    exported as importable JSON. AI logic stays cleanly separated from orchestration, testable via
    extracted <code>jsCode</code> in standalone smoke-test scripts.</p>
  </div>

  <div class="adr-card">
    <h3>ADR-002 · Ollama (qwen2.5:7b) local, not paid API</h3>
    <div class="decision">Decision: All agent calls to local Ollama; zero marginal cost per run.</div>
    <p>Every prompt-reliability issue found (char limits, enum drift, numeric reasoning, JSON citation
    leakage) was fixed by tightening prompt field rules and re-running smoke tests — never by
    upgrading the model. This discipline is a transferable signal for cost-constrained production
    systems.</p>
  </div>

  <div class="adr-card">
    <h3>ADR-003 · Postgres as single source of truth</h3>
    <div class="decision">Decision: Postgres for all state; n8n data store for workflow-internal bookkeeping only.</div>
    <p>Cross-workflow queries are trivial SQL. The dashboard is "just SQL" — no backend API layer needed.
    The agent_run audit log is a queryable table, not a log file.</p>
  </div>

  <div class="adr-card">
    <h3>ADR-004 · Manual URL paste, not job scraping</h3>
    <div class="decision">Decision: Anchor processes jobs already found; does not discover or search for them.</div>
    <p>Keeps scope bounded. The orchestration story — research, critique, grounded generation,
    follow-up, reflection — is the project, not scraping fragility. A bookmarklet is in FUTURE.md.</p>
  </div>

  <div class="adr-card">
    <h3>ADR-005 · Anchor drafts; I send — no auto-submit</h3>
    <div class="decision">Decision: Hard boundary — nothing is submitted without human review.</div>
    <p>Removes entire failure categories (wrong company, garbled PDF, mis-stated claim) by construction.
    The ~8-minute review step is irreducible by design, not a v2 feature to automate away.</p>
  </div>

  <div class="adr-card">
    <h3>ADR-006 · Master resume as structured data, not a text blob</h3>
    <div class="decision">Decision: Decompose resume into master_resume_entry rows; tailoring = selection + rephrasing.</div>
    <p>The same architectural move that made Meridian's citation grounding work, applied to generation.
    Every accepted line has a material_grounding row. The failure mode (hallucinated experience)
    is impossible by construction: the Tailorer can't produce an unattributed line, the ID-validity
    check rejects hallucinated IDs, and the Grounding Critic checks semantic consistency against
    the specific cited entry.</p>
  </div>

  <!-- SETUP -->
  <h2 class="break">Local Setup</h2>
  <h3>Prerequisites</h3>
  <ul>
    <li>macOS (Homebrew), PostgreSQL 16, Node.js ≥ 18, Python 3.11, Ollama with qwen2.5:7b</li>
    <li>n8n owner account (created via REST API on Day 2; credentials in <code>.env</code>)</li>
    <li>Google OAuth2 credentials + Notion integration + Slack webhook (see <code>.env.example</code>)</li>
  </ul>
  <h3>Services</h3>
  <pre>
# 1. Postgres
brew services start postgresql@16
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
createdb anchor
psql -d anchor -f db/schema.sql
psql -d anchor -f db/seed_master_resume.sql

# 2. LLM wrapper (port 8001)
.venv/bin/uvicorn llm.server:app --reload --port 8001

# 3. Fetch/PDF service (port 8002)
.venv/bin/uvicorn fetch.server:app --reload --port 8002

# 4. n8n (port 5678)
npx n8n start

# 5. Dashboard (port 3000)
cd dashboard && npm run dev
  </pre>

  <!-- STATUS -->
  <h2>Status (as of 2026-06-16)</h2>
  <table class="data">
    <tr><th>Day</th><th>Deliverable</th><th>Status</th></tr>
    <tr><td>1–2</td><td>Infrastructure + Workflow 1 (Job Intake)</td><td>✅ Live</td></tr>
    <tr><td>3–5</td><td>JD Parser + Workflow 2 (Job Processor)</td><td>✅ Live</td></tr>
    <tr><td>6–9</td><td>Resume Critic + Match Scorer + Tailorer + Grounding Critic + Cover Letter + Drive + Notion — Workflow 3 (Match & Generate)</td><td>✅ Live (67 nodes)</td></tr>
    <tr><td>10</td><td>First real application via Anchor</td><td>⏳ Pending (awaiting Phase B run with strong-match posting)</td></tr>
    <tr><td>11</td><td>Workflow 4 (Follow-up Scheduler)</td><td>✅ Built, imported, inactive until first submitted application</td></tr>
    <tr><td>12</td><td>Error workflow + retry logic</td><td>✅ Live, active, end-to-end tested</td></tr>
    <tr><td>13</td><td>Workflow 5 (Weekly Reflection)</td><td>✅ Built, imported, inactive until N≥5 applications</td></tr>
    <tr><td>14</td><td>Dashboard skeleton</td><td>✅ Running at localhost:3000</td></tr>
    <tr><td>15–16</td><td>Material Quality Eval (20 applications, baseline comparison)</td><td>🔄 Eval batch running — results pending</td></tr>
    <tr><td>17</td><td>README, ADRs, demo video</td><td>🔄 README + ADRs done; video pending</td></tr>
    <tr><td>18</td><td>Public deploy, LinkedIn post, resume bullet</td><td>⏳ Pending</td></tr>
  </table>

  <div style="margin-top:48px;padding-top:24px;border-top:1px solid #ECE6DC;text-align:center;color:#8E8C84;font-size:11px;">
    Anchor · Personal AI Job-Application Pipeline · Satvik Krishna · 2026 Internship Search<br>
    github.com/satvikk2024-dotcom · satvikkrishna06@gmail.com
  </div>
</div>
</body>
</html>"""


def main() -> None:
    html = build_html()
    html_path = ROOT / "Anchor_Overview.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"Written HTML: {html_path}")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path}", wait_until="networkidle")
        page.pdf(
            path=str(OUT_PDF),
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()

    html_path.unlink()  # clean up temp HTML
    print(f"PDF written: {OUT_PDF}")


if __name__ == "__main__":
    main()
