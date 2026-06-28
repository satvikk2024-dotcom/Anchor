// Day 9 part 2 smoke test: exercises the Code-node logic added to Workflow 3's
// Phase B chain (Drive folder naming, PDF render-body prep, PDF URL bookkeeping,
// Notion page body, Slack message) without touching Drive, Notion, Slack, or
// Postgres.
//
// Each node's jsCode is extracted live from n8n/workflows/03_match_and_generate.json
// (so this can't drift from what's actually deployed) and run against
// hand-built mock upstream data shaped like real agent outputs. Drive/Notion
// API responses are mocked; the two /render-pdf calls are real (local,
// already-proven-safe fetch service on port 8002).
//
// Usage:
//   node scripts/test_phase_b_codenodes.js
//
// Requires:
//   - Fetch service running: .venv/bin/uvicorn fetch.server:app --port 8002

const fs = require("fs");
const path = require("path");

const WF_PATH = path.join(__dirname, "..", "n8n", "workflows", "03_match_and_generate.json");
const RENDER_URL = "http://127.0.0.1:8002/render-pdf";

const wf = JSON.parse(fs.readFileSync(WF_PATH, "utf8"));
const nodesByName = {};
for (const n of wf.nodes) nodesByName[n.name] = n;

function jsCodeFor(name) {
  const node = nodesByName[name];
  if (!node) throw new Error(`node not found: ${name}`);
  if (!node.parameters || typeof node.parameters.jsCode !== "string") {
    throw new Error(`node has no jsCode: ${name}`);
  }
  return node.parameters.jsCode;
}

// Runs a Code node's jsCode with mocked $ / $json / $input, returns its single
// output item's .json (mirrors how n8n calls Code nodes for one input item).
function runNode(name, { byName = {}, json = {}, input = null } = {}) {
  const code = jsCodeFor(name);
  const $ = (nodeName) => {
    if (!(nodeName in byName)) throw new Error(`${name}: no mock data for $('${nodeName}')`);
    return { item: { json: byName[nodeName] } };
  };
  const $input = input ? { item: { json: input } } : undefined;
  const fn = new Function("$", "$json", "$input", code);
  const result = fn($, json, $input);
  return result[0].json;
}

// ---------------------------------------------------------------------------
// Mock upstream data, shaped like real agent/Postgres outputs (field names per
// llm/schemas.py and the node-by-node read of Workflow 3).
// ---------------------------------------------------------------------------

const finalizeMaterial = {
  application_id: "11111111-1111-1111-1111-111111111111",
  role_title: "Software Engineering Intern - Backend",
  company_name: "Fictional Co",
  material_id: "22222222-2222-2222-2222-222222222222",
  scorer: {
    score: 68,
    tier: "warm",
    reasoning: "Covers all 3 must-haves; CI/CD and distributed-systems gaps noted.",
    top_strengths: ["Python/FastAPI experience", "SQL/Postgres experience"],
    top_gaps: [],
    red_flags: [],
  },
  tailored: {
    summary:
      "Backend-focused software engineering intern candidate with hands-on experience " +
      "building Python services and a strong grounding in SQL and relational database design.",
    sections: [
      {
        category: "experience",
        lines: [
          {
            master_resume_entry_id: "33333333-3333-3333-3333-333333333333",
            text: "Software Engineering Intern, built internal tooling using Python and FastAPI.",
          },
        ],
      },
      {
        category: "skill",
        lines: [
          {
            master_resume_entry_id: "44444444-4444-4444-4444-444444444444",
            text: "Proficient in Python, including FastAPI and async programming.",
          },
          {
            master_resume_entry_id: "55555555-5555-5555-5555-555555555555",
            text: "Experience with SQL and relational database design (Postgres).",
          },
        ],
      },
      {
        category: "education",
        lines: [
          {
            master_resume_entry_id: "66666666-6666-6666-6666-666666666666",
            text: "B.S. Computer Science, expected graduation May 2026.",
          },
        ],
      },
    ],
  },
};

const persistCoverLetter = { id: "77777777-7777-7777-7777-777777777777" };

const parseCoverLetterOutput = {
  company_name: "Fictional Co",
  role_title: "Software Engineering Intern - Backend",
  cover_letter: {
    paragraphs: [
      "I am excited to apply for the Software Engineering Intern - Backend position " +
        "on the Platform Infrastructure team at Fictional Co. Your recent Series B to " +
        "expand the platform team reflects exactly the kind of growth I want to contribute to.",
      "In a prior internship, I built internal tooling using Python and FastAPI, and I " +
        "have hands-on experience with SQL and relational database design in Postgres " +
        "- both core to your tech stack.",
      "I'd welcome the chance to bring that background to your team this summer.",
    ],
    master_resume_entry_ids: [
      "33333333-3333-3333-3333-333333333333",
      "55555555-5555-5555-5555-555555555555",
    ],
    company_detail_referenced: "recent Series B to expand the platform team",
  },
};

const parseLinkedInOutput = {
  linkedin: {
    message:
      "Hi - I'm a CS student excited about Fictional Co's platform team after your recent " +
      "Series B. I'd love to connect and learn more about the team's work.",
    company_detail_referenced: "recent Series B",
  },
};

const parseSkillGapOutput = {
  skill_gap: {
    gaps: [
      {
        requirement: "CI/CD pipeline experience",
        category: "nice_to_have",
        severity: "minor",
        how_to_close: "Mention any GitHub Actions / CI usage from coursework or projects in the interview.",
      },
    ],
    verdict: "apply_now",
  },
};

const loadJdUrl = { url: "https://boards.greenhouse.io/fictionalco/jobs/1234567" };

// ---------------------------------------------------------------------------
// Run the Phase B chain
// ---------------------------------------------------------------------------

async function main() {
  const byName = {
    "Finalize Material": finalizeMaterial,
    "Persist Cover Letter": persistCoverLetter,
    "Parse Cover Letter Output": parseCoverLetterOutput,
    "Parse LinkedIn Output": parseLinkedInOutput,
    "Parse Skill Gap Output": parseSkillGapOutput,
    "Load JD URL": loadJdUrl,
  };

  const failures = [];
  const check = (label, cond) => {
    console.log(`${cond ? "PASS" : "FAIL"} ${label}`);
    if (!cond) failures.push(label);
  };

  // --- Prepare Drive Folder Name -------------------------------------------------
  const folderName = runNode("Prepare Drive Folder Name", { byName });
  console.log("\ndrive_folder_name:", folderName.drive_folder_name);
  check(
    "folder name is sanitized company_role_date with no spaces/punctuation",
    /^[A-Za-z0-9_-]+$/.test(folderName.drive_folder_name)
  );
  check(
    "folder name ends with today's ISO date",
    folderName.drive_folder_name.endsWith(new Date().toISOString().slice(0, 10))
  );

  // Mock "Create Drive Folder" output (Drive folder/create, simplifyOutput: true -> {id, name, ...})
  byName["Create Drive Folder"] = { id: "mock_folder_id_123", name: folderName.drive_folder_name };

  // --- Prepare Resume PDF Data ----------------------------------------------------
  const resumePdfData = runNode("Prepare Resume PDF Data", {
    byName,
    json: byName["Create Drive Folder"],
  });
  console.log("\ndrive_folder_url:", resumePdfData.drive_folder_url);
  check("drive_folder_id carried through", resumePdfData.drive_folder_id === "mock_folder_id_123");
  check(
    "drive_folder_url points at the mocked folder id",
    resumePdfData.drive_folder_url === "https://drive.google.com/drive/folders/mock_folder_id_123"
  );
  check("render_resume_body.template === 'resume'", resumePdfData.render_resume_body.template === "resume");
  check(
    "render_resume_body.data has summary + sections",
    typeof resumePdfData.render_resume_body.data.summary === "string" &&
      Array.isArray(resumePdfData.render_resume_body.data.sections)
  );

  // Real call: does this body actually render?
  const resumePdfResp = await fetch(RENDER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resumePdfData.render_resume_body),
  });
  const resumePdfBytes = await resumePdfResp.arrayBuffer();
  console.log(`/render-pdf (resume): HTTP ${resumePdfResp.status}, ${resumePdfBytes.byteLength} bytes`);
  check("resume PDF render succeeded", resumePdfResp.status === 200 && resumePdfBytes.byteLength > 1000);

  // Mock "Upload Resume PDF" output (Drive file/upload -> includes webViewLink)
  byName["Upload Resume PDF"] = {
    id: "mock_resume_file_id",
    name: "Resume.pdf",
    webViewLink: "https://drive.google.com/file/d/mock_resume_file_id/view",
  };
  byName["Prepare Resume PDF Data"] = resumePdfData;

  // --- Prepare Cover Letter PDF Data ----------------------------------------------
  const coverLetterPdfData = runNode("Prepare Cover Letter PDF Data", {
    byName,
    json: byName["Upload Resume PDF"],
  });
  console.log("\nresume_drive_url (from cover-letter step):", coverLetterPdfData.resume_drive_url);
  check(
    "resume_drive_url === Upload Resume PDF's webViewLink",
    coverLetterPdfData.resume_drive_url === byName["Upload Resume PDF"].webViewLink
  );
  check(
    "drive_folder_id carried through from Prepare Resume PDF Data",
    coverLetterPdfData.drive_folder_id === "mock_folder_id_123"
  );
  check(
    "render_cover_letter_body.template === 'cover_letter'",
    coverLetterPdfData.render_cover_letter_body.template === "cover_letter"
  );
  check(
    "render_cover_letter_body.data has company_name/role_title/date/paragraphs",
    coverLetterPdfData.render_cover_letter_body.data.company_name === "Fictional Co" &&
      coverLetterPdfData.render_cover_letter_body.data.role_title ===
        "Software Engineering Intern - Backend" &&
      typeof coverLetterPdfData.render_cover_letter_body.data.date === "string" &&
      Array.isArray(coverLetterPdfData.render_cover_letter_body.data.paragraphs)
  );

  const coverPdfResp = await fetch(RENDER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(coverLetterPdfData.render_cover_letter_body),
  });
  const coverPdfBytes = await coverPdfResp.arrayBuffer();
  console.log(`/render-pdf (cover letter): HTTP ${coverPdfResp.status}, ${coverPdfBytes.byteLength} bytes`);
  check("cover letter PDF render succeeded", coverPdfResp.status === 200 && coverPdfBytes.byteLength > 1000);

  // Mock "Upload Cover Letter PDF" output
  byName["Upload Cover Letter PDF"] = {
    id: "mock_cover_letter_file_id",
    name: "Cover Letter.pdf",
    webViewLink: "https://drive.google.com/file/d/mock_cover_letter_file_id/view",
  };
  byName["Prepare Cover Letter PDF Data"] = coverLetterPdfData;

  // --- Prepare PDF URL Updates -----------------------------------------------------
  const pdfUrlUpdates = runNode("Prepare PDF URL Updates", {
    byName,
    json: byName["Upload Cover Letter PDF"],
  });
  console.log("\npdfUrlUpdates:", pdfUrlUpdates);
  check(
    "resume_material_id === Finalize Material.material_id",
    pdfUrlUpdates.resume_material_id === finalizeMaterial.material_id
  );
  check(
    "cover_letter_material_id === Persist Cover Letter.id",
    pdfUrlUpdates.cover_letter_material_id === persistCoverLetter.id
  );
  check(
    "cover_letter_drive_url === Upload Cover Letter PDF.webViewLink",
    pdfUrlUpdates.cover_letter_drive_url === byName["Upload Cover Letter PDF"].webViewLink
  );
  byName["Prepare PDF URL Updates"] = pdfUrlUpdates;

  // --- Prepare Notion Page -----------------------------------------------------------
  const notionPage = runNode("Prepare Notion Page", { byName });
  console.log("\nnotion_body:\n" + JSON.stringify(notionPage.notion_body, null, 2));

  const props = notionPage.notion_body.properties;
  check(
    "parent.database_id matches the configured Notion database",
    notionPage.notion_body.parent.database_id === "3806af3e78ea805fb6b8d1ca4c58188b"
  );
  check(
    "Name title contains company and role",
    props.Name.title[0].text.content === "Fictional Co — Software Engineering Intern - Backend"
  );
  check("Match Score is a number", props["Match Score"].number === 68);
  check("Match Tier select name === 'warm'", props["Match Tier"].select.name === "warm");
  check("Skill Gap Verdict select name === 'apply_now'", props["Skill Gap Verdict"].select.name === "apply_now");
  check("JD URL set from Load JD URL", props["JD URL"].url === loadJdUrl.url);
  check("Resume PDF url set", props["Resume PDF"].url === byName["Upload Resume PDF"].webViewLink);
  check(
    "Cover Letter PDF url set",
    props["Cover Letter PDF"].url === byName["Upload Cover Letter PDF"].webViewLink
  );
  check(
    "LinkedIn Message rich_text contains the drafted message",
    props["LinkedIn Message"].rich_text[0].text.content === parseLinkedInOutput.linkedin.message
  );
  check("Created date is today (ISO)", props.Created.date.start === new Date().toISOString().slice(0, 10));

  // Mock "Create Notion Page" output
  byName["Create Notion Page"] = { id: "mock-notion-page-id", url: "https://www.notion.so/mock-notion-page-id" };

  // --- Prepare Ready Slack -------------------------------------------------------------
  const readySlack = runNode("Prepare Ready Slack", { byName });
  console.log("\n--- slack_text ---\n" + readySlack.slack_text + "\n------------------");
  check("slack_text mentions the role and company", readySlack.slack_text.includes("Software Engineering Intern - Backend @ Fictional Co"));
  check("slack_text includes the match score", readySlack.slack_text.includes("68/100 (warm)"));
  check("slack_text includes the Drive folder link", readySlack.slack_text.includes(resumePdfData.drive_folder_url));
  check("slack_text includes the Notion page link", readySlack.slack_text.includes(byName["Create Notion Page"].url));
  check("slack_text includes the skill-gap verdict", readySlack.slack_text.includes("apply_now"));

  console.log(`\n${failures.length === 0 ? "ALL CHECKS PASSED" : `${failures.length} CHECK(S) FAILED`}`);
  if (failures.length > 0) {
    for (const f of failures) console.log("  - " + f);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
