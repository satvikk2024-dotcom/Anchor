// Day 12 smoke test: exercises the Code-node logic in the Error Handler
// workflow (n8n/workflows/00_error_handler.json) without touching Postgres
// or Slack.
//
// jsCode is extracted live from the workflow JSON. Runs two scenarios
// through Parse Error Context -> Prepare Error Event -> Prepare Slack Alert:
//   1. A transient-looking error (HTTP 503 from a fetch call)
//   2. A permanent-looking error (a Pydantic validation error)
//
// Usage:
//   node scripts/test_error_handler_codenodes.js

const fs = require("fs");
const path = require("path");

const WF_PATH = path.join(__dirname, "..", "n8n", "workflows", "00_error_handler.json");

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
// json objects, for $('Node').item.json lookups.
function runNodeForItem(name, { all = {}, json = {} } = {}) {
  const code = jsCodeFor(name);
  const $ = (nodeName) => {
    if (!(nodeName in all)) throw new Error(`${name}: no mock data for $('${nodeName}')`);
    return { item: { json: all[nodeName][0] } };
  };
  const fn = new Function("$", "$json", code);
  return fn($, json);
}

const failures = [];
const check = (label, cond) => {
  console.log(`${cond ? "PASS" : "FAIL"} ${label}`);
  if (!cond) failures.push(label);
};

// ---------------------------------------------------------------------------
// Scenario 1: transient error (HTTP 503 from a research-fetch node)
// ---------------------------------------------------------------------------
const transientTrigger = {
  execution: {
    id: "1001",
    url: "http://localhost:5678/execution/1001",
    error: {
      message: "Request failed with status code 503 (Service Unavailable)",
      stack: "HTTPError: Request failed with status code 503\n    at FetchNews.execute",
    },
    lastNodeExecuted: "Fetch News",
    mode: "trigger",
  },
  workflow: { id: "2", name: "02 - Job Processor" },
};

const ctx1 = runNodeForItem("Parse Error Context", { json: transientTrigger })[0].json;
check("ctx1 workflow_name", ctx1.workflow_name === "02 - Job Processor");
check("ctx1 failed_node", ctx1.failed_node === "Fetch News");
check("ctx1 classified transient", ctx1.error_class === "transient (retries exhausted)");
check("ctx1 execution_url carried through", ctx1.execution_url === "http://localhost:5678/execution/1001");

const event1 = runNodeForItem("Prepare Error Event", { json: ctx1 })[0].json;
const payload1 = JSON.parse(event1.event_payload);
check("event1 payload.workflow_name", payload1.workflow_name === "02 - Job Processor");
check("event1 payload.error_class", payload1.error_class === "transient (retries exhausted)");

const slack1 = runNodeForItem("Prepare Slack Alert", { all: { "Parse Error Context": [ctx1] } })[0].json;
check("slack1 mentions workflow name", slack1.slack_text.includes("02 - Job Processor"));
check("slack1 mentions failed node", slack1.slack_text.includes("Fetch News"));
check("slack1 mentions transient class", slack1.slack_text.includes("transient (retries exhausted)"));
check("slack1 includes execution URL", slack1.slack_text.includes("http://localhost:5678/execution/1001"));
check("slack1 includes manual UPDATE hint", slack1.slack_text.includes("UPDATE application SET status = 'errored'"));

// ---------------------------------------------------------------------------
// Scenario 2: permanent error (schema validation failure, no execution URL)
// ---------------------------------------------------------------------------
const permanentTrigger = {
  execution: {
    id: "1002",
    error: {
      message: "1 validation error for ResumeTailorerOutput\nsections -> 0 -> lines\n  field required",
      stack: "ValidationError: 1 validation error for ResumeTailorerOutput",
    },
    lastNodeExecuted: "Parse Tailored Resume",
    mode: "trigger",
  },
  workflow: { id: "3", name: "03 - Match and Generate" },
};

const ctx2 = runNodeForItem("Parse Error Context", { json: permanentTrigger })[0].json;
check("ctx2 classified permanent", ctx2.error_class === "permanent");
check("ctx2 execution_url is null", ctx2.execution_url === null);

const slack2 = runNodeForItem("Prepare Slack Alert", { all: { "Parse Error Context": [ctx2] } })[0].json;
check("slack2 mentions permanent class", slack2.slack_text.includes("permanent"));
check("slack2 omits execution URL line when absent", !slack2.slack_text.includes("Execution: null"));

console.log("\n--- slack1 ---\n" + slack1.slack_text + "\n--------------");
console.log("\n--- slack2 ---\n" + slack2.slack_text + "\n--------------");

console.log(`\n${failures.length === 0 ? "ALL CHECKS PASSED" : `${failures.length} CHECK(S) FAILED`}`);
if (failures.length > 0) {
  for (const f of failures) console.log("  - " + f);
  process.exit(1);
}
