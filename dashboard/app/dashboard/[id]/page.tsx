import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink, FileText, Mail, MessageSquare, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { getApplicationDetail } from "@/lib/queries";
import StatusUpdater from "./StatusUpdater";
import NotesEditor from "./NotesEditor";

export const dynamic = "force-dynamic";

function MaterialSection({
  title,
  icon: Icon,
  content,
  pdfUrl,
}: {
  title: string;
  icon: React.ElementType;
  content: unknown;
  pdfUrl?: string | null;
}) {
  return (
    <div className="rounded-card border border-border-default bg-bg-surface p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-small font-semibold text-fg-primary flex items-center gap-2">
          <Icon size={16} className="text-accent" /> {title}
        </h3>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-micro text-accent hover:underline"
          >
            Open PDF <ExternalLink size={12} />
          </a>
        )}
      </div>
      <div className="text-small text-fg-primary leading-relaxed">
        {renderContent(title, content)}
      </div>
    </div>
  );
}

function renderContent(type: string, content: unknown) {
  if (!content || typeof content !== "object") {
    return <p className="text-fg-muted italic">No content generated</p>;
  }

  const c = content as Record<string, unknown>;

  if (type === "Tailored Resume") {
    const sections = (c.sections as Array<{ category: string; lines: Array<{ text: string }> }>) || [];
    return (
      <div className="space-y-3">
        {c.summary ? <p className="italic text-fg-secondary">{String(c.summary)}</p> : null}
        {sections.map((s, i) => (
          <div key={i}>
            <p className="font-medium text-fg-secondary uppercase text-micro tracking-wide mb-1">
              {s.category}
            </p>
            <ul className="list-disc pl-4 space-y-1">
              {s.lines.map((l, j) => (
                <li key={j}>{l.text}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    );
  }

  if (type === "Cover Letter") {
    const paragraphs = (c.paragraphs as string[]) || [];
    return (
      <div className="space-y-3">
        {paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
        {c.company_detail_referenced ? (
          <p className="text-micro text-fg-muted mt-2">
            Company detail referenced: {String(c.company_detail_referenced)}
          </p>
        ) : null}
      </div>
    );
  }

  if (type === "LinkedIn Message") {
    return (
      <div className="rounded border border-border-subtle bg-bg-primary p-3">
        <p>{String(c.message)}</p>
        {c.company_detail_referenced ? (
          <p className="text-micro text-fg-muted mt-2">
            References: {String(c.company_detail_referenced)}
          </p>
        ) : null}
      </div>
    );
  }

  if (type === "Skill Gap Report") {
    const gaps = (c.gaps as Array<{ requirement: string; category: string; severity: string; how_to_close: string }>) || [];
    return (
      <div className="space-y-2">
        {c.verdict ? (
          <p className="font-medium">
            Verdict: <span className="text-accent">{String(c.verdict)}</span>
          </p>
        ) : null}
        {gaps.length === 0 ? (
          <p className="text-fg-muted italic">No skill gaps identified</p>
        ) : (
          gaps.map((g, i) => (
            <div key={i} className="rounded border border-border-subtle p-3">
              <p className="font-medium">{g.requirement}</p>
              <p className="text-micro text-fg-muted">
                {g.category} · {g.severity}
              </p>
              <p className="text-small mt-1">{g.how_to_close}</p>
            </div>
          ))
        )}
      </div>
    );
  }

  return <pre className="text-micro overflow-x-auto">{JSON.stringify(content, null, 2)}</pre>;
}

const MATERIAL_META: Record<string, { title: string; icon: React.ElementType }> = {
  tailored_resume: { title: "Tailored Resume", icon: FileText },
  cover_letter: { title: "Cover Letter", icon: Mail },
  linkedin_message: { title: "LinkedIn Message", icon: MessageSquare },
  skill_gap_report: { title: "Skill Gap Report", icon: AlertTriangle },
};

export default async function ApplicationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const data = await getApplicationDetail(id);
  if (!data) notFound();

  const { app, materials, agentRuns } = data;
  const synthesis = app.synthesis as Record<string, unknown> | null;
  const scorer = agentRuns.find((r: { agent_name: string }) => r.agent_name === "match_scorer");
  const scorerOutput = scorer?.output_json as Record<string, unknown> | null;

  return (
    <div className="flex-1 p-6 max-w-4xl mx-auto w-full flex flex-col gap-6">
      {/* Header */}
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1 text-small text-fg-secondary hover:text-accent mb-4"
        >
          <ArrowLeft size={14} /> Back to Applications
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-h2 font-semibold text-fg-primary">
              {app.role_title ?? "Untitled Role"}
            </h1>
            <p className="text-small text-fg-secondary mt-1">
              {app.company_name ?? "Unknown Company"}
              {app.url && (
                <>
                  {" · "}
                  <a
                    href={app.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:underline inline-flex items-center gap-1"
                  >
                    View posting <ExternalLink size={12} />
                  </a>
                </>
              )}
            </p>
          </div>

          <div className="text-right flex-shrink-0">
            {app.match_score !== null ? (
              <div className="text-h1 font-bold text-accent">{app.match_score}</div>
            ) : null}
            <p className="text-micro text-fg-muted">match score</p>
          </div>
        </div>
      </div>

      {/* Status + dates */}
      <div className="rounded-card border border-border-default bg-bg-surface p-4 flex items-center gap-6 flex-wrap">
        <StatusUpdater applicationId={app.id} currentStatus={app.status} />
        <div className="text-micro text-fg-muted">
          Created: {new Date(app.created_at).toLocaleDateString()}
        </div>
        {app.submitted_at && (
          <div className="text-micro text-fg-muted">
            Submitted: {new Date(app.submitted_at).toLocaleDateString()}
          </div>
        )}
        {app.responded_at && (
          <div className="text-micro text-fg-muted">
            Response: {new Date(app.responded_at).toLocaleDateString()}
          </div>
        )}
      </div>

      {/* Match reasoning */}
      {scorerOutput && (
        <div className="rounded-card border border-border-default bg-bg-surface p-4">
          <h3 className="text-small font-semibold text-fg-primary mb-2">Match Analysis</h3>
          <p className="text-small text-fg-primary">{String(scorerOutput.reasoning)}</p>
          {(scorerOutput.top_strengths as string[])?.length > 0 && (
            <div className="mt-2">
              <p className="text-micro font-medium text-success">Strengths:</p>
              <ul className="list-disc pl-4 text-small">
                {(scorerOutput.top_strengths as string[]).map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {(scorerOutput.top_gaps as Array<{ gap: string }>)?.length > 0 && (
            <div className="mt-2">
              <p className="text-micro font-medium text-warning">Gaps:</p>
              <ul className="list-disc pl-4 text-small">
                {(scorerOutput.top_gaps as Array<{ gap: string }>).map((g, i) => (
                  <li key={i}>{g.gap}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Company research */}
      {synthesis && (
        <div className="rounded-card border border-border-default bg-bg-surface p-4">
          <h3 className="text-small font-semibold text-fg-primary mb-2">Company Research</h3>
          <p className="text-small text-fg-primary">{String(synthesis.what_they_do)}</p>
          {synthesis.recent_developments ? (
            <p className="text-small text-fg-secondary mt-1">
              Recent: {String(synthesis.recent_developments)}
            </p>
          ) : null}
        </div>
      )}

      {/* Generated materials */}
      <h2 className="text-h3 font-medium text-fg-primary">Generated Materials</h2>
      {materials.length === 0 ? (
        <p className="text-small text-fg-muted italic">
          No materials generated yet — the pipeline may still be running.
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          {materials.map((m: { id: string; type: string; content_json: unknown; pdf_drive_url: string | null }) => {
            const meta = MATERIAL_META[m.type] || { title: m.type, icon: FileText };
            return (
              <MaterialSection
                key={m.id}
                title={meta.title}
                icon={meta.icon}
                content={m.content_json}
                pdfUrl={m.pdf_drive_url}
              />
            );
          })}
        </div>
      )}

      {/* Notes */}
      <div className="rounded-card border border-border-default bg-bg-surface p-4">
        <h3 className="text-small font-semibold text-fg-primary mb-2">Notes</h3>
        <NotesEditor applicationId={app.id} initialNotes={app.notes ?? ""} />
      </div>
    </div>
  );
}
