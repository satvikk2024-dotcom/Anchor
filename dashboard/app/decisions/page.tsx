import { ScrollText } from "lucide-react";
import { getAgentRuns } from "@/lib/queries";
import EmptyState from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

export default async function DecisionsPage() {
  const runs = await getAgentRuns();

  if (runs.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          icon={ScrollText}
          title="No agent runs yet"
          description="Every AI agent call will be logged here once a workflow executes."
        />
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 flex flex-col gap-3">
      <h1 className="text-h2 font-semibold text-fg-primary mb-2">Decisions</h1>
      {runs.map((run) => (
        <details key={run.id} className="rounded-card border border-border-default bg-bg-surface group">
          <summary className="flex items-center justify-between gap-4 p-4 cursor-pointer list-none">
            <div className="flex flex-col">
              <span className="text-small font-medium text-fg-primary">
                {run.agent_name} <span className="text-fg-muted">·</span> {run.workflow_name}
              </span>
              <span className="text-micro text-fg-secondary">
                {run.company_name ?? "—"}
                {run.role_title ? ` · ${run.role_title}` : ""}
              </span>
            </div>
            <div className="flex items-center gap-4 text-micro text-fg-muted">
              <span>{run.latency_ms != null ? `${run.latency_ms}ms` : "latency: n/a"}</span>
              <span>
                {run.critic_passed == null
                  ? "critic: n/a"
                  : run.critic_passed
                    ? "critic: pass"
                    : "critic: fail"}
              </span>
              <span>{new Date(run.created_at).toLocaleString()}</span>
            </div>
          </summary>
          <pre className="border-t border-border-subtle p-4 text-micro overflow-x-auto bg-bg-primary rounded-b-card">
            {JSON.stringify(run.output_json, null, 2)}
          </pre>
        </details>
      ))}
    </div>
  );
}
