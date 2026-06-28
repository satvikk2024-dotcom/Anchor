// Day 13 smoke test: exercises the Code-node logic in Workflow 5
// (n8n/workflows/05_weekly_reflection.json) without touching Postgres, the
// LLM wrapper, or Slack.
//
// jsCode is extracted live from the workflow JSON (so this can't drift from
// what's actually deployed) and run against two scenarios through Prepare
// Pattern Detector Input -> (mock LLM) -> Parse Pattern Detector Output ->
// Build Digest:
//
//   A. N=1 (mirrors the real current Postgres state - one application) ->
//      min_n_reached must be false, and Build Digest must not render a
//      "Patterns:" section even if (hypothetically) the LLM ignored the
//      guard and returned one.
//   B. N=6, with a clear startup-vs-enterprise response-rate gap (the kind
//      of pattern called out as an example in planning doc Sec 5.5) ->
//      min_n_reached must be true, and the prompt + digest must carry the
//      exact counts through.
//
// Usage:
//   node scripts/test_weekly_reflection_codenodes.js

const fs = require("fs");
const path = require("path");

const WF_PATH = path.join(__dirname, "..", "n8n", "workflows", "05_weekly_reflection.json");

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

// Runs a Code node's jsCode once for all items (runOnceForAllItems mode),
// where the node reads its own input via $input.all().
function runNodeForAllWithInput(name, inputItems) {
  const code = jsCodeFor(name);
  const $input = {
    all: () => inputItems.map((j) => ({ json: j })),
  };
  const fn = new Function("$input", code);
  return fn($input);
}

const failures = [];
const check = (label, cond) => {
  console.log(`${cond ? "PASS" : "FAIL"} ${label}`);
  if (!cond) failures.push(label);
};

// ---------------------------------------------------------------------------
// Scenario A: N=1 (mirrors the real current Postgres state)
// ---------------------------------------------------------------------------
console.log("\n=== Scenario A: N=1 (below min-N=5) ===");

const aggregateRowsA = [
  {
    application_id: "bfe91458-cd95-429c-8186-54d24bb6c913",
    role_title: "Software Engineer Intern",
    status: "low_match_waiting",
    match_score: 58,
    created_at: "2026-06-10T00:00:00.000Z",
    submitted_at: null,
    responded_at: null,
    company_name: "Airbnb",
    company_type: "enterprise",
    match_tier: "cold",
  },
];

const preparedA = runNodeForAllWithInput("Prepare Pattern Detector Input", aggregateRowsA)[0].json;

check("scenario A: n === 1", preparedA.n === 1);
check("scenario A: min_n_reached === false", preparedA.min_n_reached === false);
check(
  "scenario A: prompt states 'Total applications in window: 1'",
  preparedA.pattern_prompt.includes("Total applications in window: 1")
);
check(
  "scenario A: prompt states 'Minimum sample size reached (N >= 5): no'",
  preparedA.pattern_prompt.includes("Minimum sample size reached (N >= 5): no")
);

// Mock LLM response respecting the min-N guard: patterns must be empty.
const mockResponseA = {
  patterns: [],
  summary:
    "Only 1 application in the last 4 weeks - below the minimum of 5 needed before patterns are surfaced. Expected this early in the project.",
};

const parsedA = runNodeForItem("Parse Pattern Detector Output", {
  all: { "Prepare Pattern Detector Input": [preparedA] },
  input: { text: JSON.stringify(mockResponseA), model: "qwen2.5:7b" },
})[0].json;

check("scenario A: parsed patterns is empty", parsedA.pattern_output.patterns.length === 0);
check(
  "scenario A: parsed summary mentions insufficient data",
  parsedA.pattern_output.summary.includes("1") && parsedA.pattern_output.summary.includes("5")
);

const digestA = runNodeForItem("Build Digest", {
  all: { "Parse Pattern Detector Output": [parsedA] },
})[0].json;
console.log("\n--- slack_text (A) ---\n" + digestA.slack_text + "\n----------------------");

check("scenario A digest mentions 'Applications in window: 1'", digestA.slack_text.includes("Applications in window: 1"));
check("scenario A digest includes the summary text", digestA.slack_text.includes("below the minimum of 5"));
check("scenario A digest has no 'Patterns:' section", !digestA.slack_text.includes("Patterns:"));

// ---------------------------------------------------------------------------
// Scenario B: N=6, clear startup-vs-enterprise response-rate gap
// ---------------------------------------------------------------------------
console.log("\n=== Scenario B: N=6 (min-N=5 reached) ===");

const aggregateRowsB = [
  {
    application_id: "11111111-1111-1111-1111-111111111111",
    role_title: "Backend Engineering Intern",
    status: "responded",
    match_score: 78,
    created_at: "2026-06-01T00:00:00.000Z",
    submitted_at: "2026-06-02T00:00:00.000Z",
    responded_at: "2026-06-08T00:00:00.000Z",
    company_name: "Startup Co A",
    company_type: "startup",
    match_tier: "hot",
  },
  {
    application_id: "22222222-2222-2222-2222-222222222222",
    role_title: "Platform Engineering Intern",
    status: "interview",
    match_score: 81,
    created_at: "2026-06-02T00:00:00.000Z",
    submitted_at: "2026-06-03T00:00:00.000Z",
    responded_at: "2026-06-09T00:00:00.000Z",
    company_name: "Startup Co B",
    company_type: "startup",
    match_tier: "hot",
  },
  {
    application_id: "33333333-3333-3333-3333-333333333333",
    role_title: "Infrastructure Intern",
    status: "rejected",
    match_score: 64,
    created_at: "2026-06-03T00:00:00.000Z",
    submitted_at: "2026-06-04T00:00:00.000Z",
    responded_at: "2026-06-12T00:00:00.000Z",
    company_name: "Startup Co C",
    company_type: "startup",
    match_tier: "warm",
  },
  {
    application_id: "44444444-4444-4444-4444-444444444444",
    role_title: "Software Engineer Intern",
    status: "submitted",
    match_score: 62,
    created_at: "2026-06-04T00:00:00.000Z",
    submitted_at: "2026-06-05T00:00:00.000Z",
    responded_at: null,
    company_name: "Enterprise Co A",
    company_type: "enterprise",
    match_tier: "warm",
  },
  {
    application_id: "55555555-5555-5555-5555-555555555555",
    role_title: "Cloud Engineering Intern",
    status: "ghosted",
    match_score: 60,
    created_at: "2026-05-20T00:00:00.000Z",
    submitted_at: "2026-05-21T00:00:00.000Z",
    responded_at: null,
    company_name: "Enterprise Co B",
    company_type: "enterprise",
    match_tier: "warm",
  },
  {
    application_id: "66666666-6666-6666-6666-666666666666",
    role_title: "Systems Engineering Intern",
    status: "rejected",
    match_score: 58,
    created_at: "2026-05-22T00:00:00.000Z",
    submitted_at: "2026-05-23T00:00:00.000Z",
    responded_at: "2026-06-10T00:00:00.000Z",
    company_name: "Enterprise Co C",
    company_type: "enterprise",
    match_tier: "cold",
  },
];

const preparedB = runNodeForAllWithInput("Prepare Pattern Detector Input", aggregateRowsB)[0].json;

check("scenario B: n === 6", preparedB.n === 6);
check("scenario B: min_n_reached === true", preparedB.min_n_reached === true);
check(
  "scenario B: prompt states 'Total applications in window: 6'",
  preparedB.pattern_prompt.includes("Total applications in window: 6")
);
check(
  "scenario B: prompt states 'Minimum sample size reached (N >= 5): yes'",
  preparedB.pattern_prompt.includes("Minimum sample size reached (N >= 5): yes")
);
check(
  "scenario B: prompt shows startup response rate 2/3 (67%)",
  preparedB.pattern_prompt.includes("startup: 3 application(s), response rate 2/3 (67%)")
);
check(
  "scenario B: prompt shows enterprise response rate 0/3 (0%)",
  preparedB.pattern_prompt.includes("enterprise: 3 application(s), response rate 0/3 (0%)")
);

// Mock LLM response: a high-confidence pattern citing the exact counts above.
const mockResponseB = {
  patterns: [
    {
      observation: "Response rate is much higher at startups than at enterprise companies.",
      evidence: "2/3 (67%) startup applications got a response (1 responded, 1 interview) vs. 0/3 (0%) enterprise applications.",
      suggested_action: "Consider prioritizing startup applications given the higher response rate so far.",
      confidence: "medium",
    },
  ],
  summary: "6 applications in the last 4 weeks, overall response rate 2/6 (33%); the clearest pattern is the startup-vs-enterprise response-rate gap above.",
};

const parsedB = runNodeForItem("Parse Pattern Detector Output", {
  all: { "Prepare Pattern Detector Input": [preparedB] },
  input: { text: JSON.stringify(mockResponseB), model: "qwen2.5:7b" },
})[0].json;

check("scenario B: parsed patterns has 1 entry", parsedB.pattern_output.patterns.length === 1);
check("scenario B: pattern_output_json carried through", typeof parsedB.pattern_output_json === "string");
check("scenario B: pattern_model_used === 'qwen2.5:7b'", parsedB.pattern_model_used === "qwen2.5:7b");

const digestB = runNodeForItem("Build Digest", {
  all: { "Parse Pattern Detector Output": [parsedB] },
})[0].json;
console.log("\n--- slack_text (B) ---\n" + digestB.slack_text + "\n----------------------");

check("scenario B digest mentions 'Applications in window: 6'", digestB.slack_text.includes("Applications in window: 6"));
check("scenario B digest has a 'Patterns:' section", digestB.slack_text.includes("Patterns:"));
check("scenario B digest includes the observation", digestB.slack_text.includes("Response rate is much higher at startups"));
check("scenario B digest includes the evidence with exact counts", digestB.slack_text.includes("2/3 (67%) startup applications"));
check("scenario B digest includes the confidence level", digestB.slack_text.includes("(medium confidence)"));

console.log(`\n${failures.length === 0 ? "ALL CHECKS PASSED" : `${failures.length} CHECK(S) FAILED`}`);
if (failures.length > 0) {
  for (const f of failures) console.log("  - " + f);
  process.exit(1);
}
