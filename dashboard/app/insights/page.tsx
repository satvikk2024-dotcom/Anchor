import { Sparkles } from "lucide-react";
import { getWeeklyInsights } from "@/lib/queries";
import EmptyState from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

export default async function InsightsPage() {
  const weeks = await getWeeklyInsights();

  if (weeks.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          icon={Sparkles}
          title="No weekly reflections yet"
          description="Workflow 5 runs Sundays at 7pm and needs at least 5 applications in the last 4 weeks before it reports patterns. Check back after a few more applications."
        />
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 flex flex-col gap-6">
      <h1 className="text-h2 font-semibold text-fg-primary mb-2">Insights</h1>
      {weeks.map((week) => (
        <div key={week.id} className="rounded-card border border-border-default bg-bg-surface p-5">
          <h2 className="text-h3 font-medium text-fg-primary mb-1">
            Week of {new Date(week.week_start).toLocaleDateString()}
          </h2>
          {week.insights?.summary && (
            <p className="text-small text-fg-secondary mb-4">{week.insights.summary}</p>
          )}
          {week.insights?.patterns?.length ? (
            <div className="flex flex-col gap-3">
              {week.insights.patterns.map((p, i) => (
                <div key={i} className="rounded-card border border-border-subtle p-3">
                  <p className="text-small font-medium text-fg-primary">{p.observation}</p>
                  <p className="text-micro text-fg-secondary mt-1">Evidence: {p.evidence}</p>
                  <p className="text-micro text-accent mt-1">→ {p.suggested_action}</p>
                  <span className="text-micro text-fg-muted">Confidence: {p.confidence}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-micro text-fg-muted">No patterns identified this week (insufficient data).</p>
          )}
        </div>
      ))}
    </div>
  );
}
