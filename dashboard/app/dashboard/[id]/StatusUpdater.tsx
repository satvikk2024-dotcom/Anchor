"use client";

import { useState } from "react";
import type { ApplicationStatus } from "@/lib/types";

const OPTIONS: { value: ApplicationStatus; label: string }[] = [
  { value: "intake_received", label: "Intake Received" },
  { value: "researched", label: "Researched" },
  { value: "low_match_waiting", label: "Low Match" },
  { value: "awaiting_review", label: "Awaiting Review" },
  { value: "submitted", label: "Submitted" },
  { value: "responded", label: "Responded" },
  { value: "interview", label: "Interview" },
  { value: "rejected", label: "Rejected" },
  { value: "ghosted", label: "Ghosted" },
  { value: "withdrawn", label: "Withdrawn" },
  { value: "errored", label: "Errored" },
];

export default function StatusUpdater({
  applicationId,
  currentStatus,
}: {
  applicationId: string;
  currentStatus: ApplicationStatus;
}) {
  const [status, setStatus] = useState(currentStatus);
  const [saving, setSaving] = useState(false);

  async function handleChange(newStatus: ApplicationStatus) {
    setSaving(true);
    setStatus(newStatus);
    await fetch("/api/update-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ applicationId, status: newStatus }),
    });
    setSaving(false);
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-micro font-medium text-fg-secondary">Status:</span>
      <select
        value={status}
        onChange={(e) => handleChange(e.target.value as ApplicationStatus)}
        disabled={saving}
        className="rounded-card border border-border-default bg-bg-primary px-3 py-1.5 text-small text-fg-primary focus:outline-none focus:border-accent disabled:opacity-50"
      >
        {OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      {saving && <span className="text-micro text-fg-muted">Saving…</span>}
    </div>
  );
}
