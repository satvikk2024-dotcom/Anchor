import type { ApplicationStatus } from "@/lib/types";
import { formatStatusLabel } from "@/lib/format";

// Literal class names so Tailwind's content scanner can pick them up —
// dynamically-built `bg-${var}` strings would not be detected.
const STATUS_CLASSES: Record<ApplicationStatus, { dot: string; text: string }> = {
  intake_received: { dot: "bg-fg-secondary", text: "text-fg-secondary" },
  researched: { dot: "bg-fg-secondary", text: "text-fg-secondary" },
  low_match_waiting: { dot: "bg-warning", text: "text-warning" },
  awaiting_review: { dot: "bg-warning", text: "text-warning" },
  submitted: { dot: "bg-accent", text: "text-accent" },
  responded: { dot: "bg-success", text: "text-success" },
  interview: { dot: "bg-success", text: "text-success" },
  rejected: { dot: "bg-fg-muted", text: "text-fg-muted" },
  ghosted: { dot: "bg-fg-muted", text: "text-fg-muted" },
  errored: { dot: "bg-danger", text: "text-danger" },
  withdrawn: { dot: "bg-fg-muted", text: "text-fg-muted" },
};

export default function StatusBadge({ status }: { status: ApplicationStatus }) {
  const cls = STATUS_CLASSES[status];
  return (
    <span className={`inline-flex items-center gap-2 text-small font-medium ${cls.text}`}>
      <span className={`block h-[6px] w-[6px] rounded-full ${cls.dot}`} />
      {formatStatusLabel(status)}
    </span>
  );
}
