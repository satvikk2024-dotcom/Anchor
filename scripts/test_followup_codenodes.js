// Day 11 smoke test: exercises the Code-node logic in Workflow 4
// (n8n/workflows/04_follow_up_scheduler.json) without touching Postgres,
// the LLM wrapper, or Slack.
//
// jsCode is extracted live from the workflow JSON (so this can't drift from
// what's actually deployed) and run against two hand-built "Find Due
// Applications" rows — one that should get a nudge drafted, one that should
// wait — through Prepare Decision Input -> (mock LLM) -> Parse Decision
// Output -> Prepare Follow-up Event, then Build Digest aggregates both via
// $('Parse Decision Output').all().
//
// Usage:
//   node scripts/test_followup_codenodes.js

const fs = require("fs");
const path = require("path");

const WF_PATH = path.join(__dirname, "..", "n8n", "workflows", "04_follow_up_scheduler.json");

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

// Runs a Code node's jsCode for one item. `all` maps node name -> array of
// json objects, for $('Node').all() and $('Node').item.json lookups.
function runNodeForItem(name, { all = {}, json = {}, input = null } = {}) {
  const code = jsCodeFor(name);
  const $ = (nodeName) => {
    if (!(nodeName in all)) throw new Error(`${name}: no mock data for $('${nodeName}')`);
    return {
      item: { json: all[nodeName][0] },
      all: () => all[nodeName].map((j) => ({ json: j })),
    };
  };
  const $input = input ? { item: { json: input } } : undefined;
  const fn = new Function("$", "$json", "$input", code);
  return fn($, json, $input);
}

// Runs a Code node's jsCode once for all items (runOnceForAllItems mode).
function runNodeForAll(name, { all = {} } = {}) {
  const code = jsCodeFor(name);
  const $ = (nodeName) => ({
    all: () => all[nodeName].map((j) => ({ json: j })),
  });
  const fn = new Function("$", code);
  return fn($);
}

const failures = [];
const check = (label, cond) => {
  console.log(`${cond ? "PASS" : "FAIL"} ${label}`);
  if (!cond) failures.push(label);
};

// ---------------------------------------------------------------------------
// Two "Find Due Applications" rows
// ---------------------------------------------------------------------------
const dueApplications = [
  {
    application_id: "11111111-1111-1111-1111-111111111111",
    role_title: "Software Engineering Intern - Backend",
    match_score: 68,
    submitted_at: "2026-06-05T00:00:00.000Z",
    follow_up_window_days: 10,
    days_since_submitted: 10,
    company_name: "Fictional Co",
    company_synthesis: {
      what_they_do: "Fictional Co builds backend infrastructure tooling.",
      company_type: "startup",
      recent_developments: ["Raised a Series B to expand the platform team"],
      likely_role_context: "Platform Infrastructure team",
    },
    follow_up_count: 0,
    last_follow_up_at: null,
  },
  {
    application_id: "22222222-2222-2222-2222-222222222222",
    role_title: "Data Engineering Intern",
    match_score: 72,
    submitted_at: "2026-06-11T00:00:00.000Z",
    follow_up_window_days: 10,
    days_since_submitted: 4,
    company_name: "Other Co",
    company_synthesis: {
      what_they_do: "Other Co provides data pipeline tooling.",
      company_type: "startup",
      recent_developments: [],
      likely_role_context: "(unavailable)",
    },
    follow_up_count: 0,
    last_follow_up_at: null,
  },
];

// ---------------------------------------------------------------------------
// Step 1: Prepare Decision Input for each row
// ---------------------------------------------------------------------------
const prepared = dueApplications.map((row) => runNodeForItem("Prepare Decision Input", { json: row })[0].json);

check(
  "row 0 (10/10 days) marked window reached",
  prepared[0].decision_prompt.includes("Follow-up window reached: yes")
);
check(
  "row 1 (4/10 days) marked window not reached",
  prepared[1].decision_prompt.includes("Follow-up window reached: no")
);
check(
  "row 0 prompt includes the Series B detail",
  prepared[0].decision_prompt.includes("Series B")
);

// ---------------------------------------------------------------------------
// Step 2: mock LLM responses, run Parse Decision Output for each row
// ---------------------------------------------------------------------------
const mockLlmResponses = [
  {
    decision: "send_now",
    reasoning: "10/10 days, no nudges sent yet.",
    nudge_paragraphs: ["Following up on my application for the Backend role..."],
  },
  {
    decision: "wait",
    reasoning: "Only 4/10 days, window not reached.",
    nudge_paragraphs: [],
  },
];

const parsed = prepared.map((prep, i) =>
  runNodeForItem("Parse Decision Output", {
    all: { "Prepare Decision Input": [prep] },
    input: { text: JSON.stringify(mockLlmResponses[i]), model: "qwen2.5:7b" },
  })[0].json
);

check("row 0 parsed decision === 'send_now'", parsed[0].decision.decision === "send_now");
check("row 1 parsed decision === 'wait'", parsed[1].decision.decision === "wait");
check("decision_model_used carried through", parsed[0].decision_model_used === "qwen2.5:7b");

// ---------------------------------------------------------------------------
// Step 3: Prepare Follow-up Event for the send_now row (true branch)
// ---------------------------------------------------------------------------
const persistFollowUpNudge = { id: "33333333-3333-3333-3333-333333333333" };
const followUpEvent = runNodeForItem("Prepare Follow-up Event", {
  all: { "Parse Decision Output": [parsed[0]] },
  json: persistFollowUpNudge,
})[0].json;

check(
  "Prepare Follow-up Event application_id matches row 0",
  followUpEvent.application_id === dueApplications[0].application_id
);
const eventPayload = JSON.parse(followUpEvent.event_payload);
check("event payload material_id === Persist Follow-up Nudge.id", eventPayload.material_id === persistFollowUpNudge.id);
check("event payload decision === 'send_now'", eventPayload.decision === "send_now");

// ---------------------------------------------------------------------------
// Step 4: Build Digest, referencing $('Parse Decision Output').all()
// ---------------------------------------------------------------------------
const digest = runNodeForAll("Build Digest", { all: { "Parse Decision Output": parsed } })[0].json;
console.log("\n--- slack_text ---\n" + digest.slack_text + "\n------------------");

check("digest mentions 2 applications reviewed", digest.slack_text.includes("reviewed 2 application"));
check("digest mentions 1 drafted nudge", digest.slack_text.includes("Drafted 1 follow-up nudge"));
check("digest mentions 1 held-off application", digest.slack_text.includes("Holding off on 1 application"));
check("digest includes Fictional Co line", digest.slack_text.includes("Software Engineering Intern - Backend @ Fictional Co"));
check("digest includes Other Co line", digest.slack_text.includes("Data Engineering Intern @ Other Co"));

console.log(`\n${failures.length === 0 ? "ALL CHECKS PASSED" : `${failures.length} CHECK(S) FAILED`}`);
if (failures.length > 0) {
  for (const f of failures) console.log("  - " + f);
  process.exit(1);
}
