"use client";

import { useState } from "react";
import { ChevronDown, ExternalLink } from "lucide-react";
import type { ApplicationStatus } from "@/lib/types";

const STATUS_OPTIONS: { value: ApplicationStatus; label: string }[] = [
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

const SCORE_COLORS: Record<string, string> = {
  high: "bg-success/10 text-success",
  medium: "bg-warning/10 text-warning",
  low: "bg-danger/10 text-danger",
  unknown: "bg-fg-muted/10 text-fg-muted",
};

function scoreTier(score: number | null): string {
  if (score === null) return "unknown";
  if (score >= 75) return "high";
  if (score >= 50) return "medium";
  return "low";
}

interface Props {
  id: string;
  roleTitle: string | null;
  companyName: string | null;
  status: ApplicationStatus;
  matchScore: number | null;
  url: string;
  createdAt: string;
}

export default function ApplicationCard({
  id,
  roleTitle,
  companyName,
  status,
  matchScore,
  url,
  createdAt,
}: Props) {
  const [currentStatus, setCurrentStatus] = useState(status);
  const [open, setOpen] = useState(false);
  const [updating, setUpdating] = useState(false);

  async function handleStatusChange(newStatus: ApplicationStatus) {
    setUpdating(true);
    setOpen(false);
    try {
      const res = await fetch("/api/update-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ applicationId: id, status: newStatus }),
      });
      if (res.ok) {
        setCurrentStatus(newStatus);
      }
    } finally {
      setUpdating(false);
    }
  }

  const tier = scoreTier(matchScore);
  const ago = formatAgo(createdAt);

  return (
    <div className="rounded-card border border-border-subtle p-3 hover:border-accent transition-colors">
      <a href={`/dashboard/${id}`} className="block">
        <div className="flex items-start justify-between gap-1">
          <div className="min-w-0">
            <p className="text-small font-medium text-fg-primary truncate">
              {roleTitle ?? "Untitled Role"}
            </p>
            <p className="text-micro text-fg-secondary truncate">
              {companyName ?? "Unknown Company"}
            </p>
          </div>
          {url && (
            <span
              className="text-fg-muted flex-shrink-0"
              title="Open job posting"
            >
              <ExternalLink size={12} />
            </span>
          )}
        </div>

        <div className="flex items-center justify-between mt-2">
          {matchScore !== null ? (
            <span
              className={`inline-block rounded px-1.5 py-0.5 text-micro font-medium ${SCORE_COLORS[tier]}`}
            >
              {matchScore}
            </span>
          ) : (
            <span className="text-micro text-fg-muted">—</span>
          )}
          <span className="text-micro text-fg-muted">{ago}</span>
        </div>
      </a>

      {/* Status dropdown */}
      <div className="relative mt-2">
        <button
          onClick={() => setOpen(!open)}
          disabled={updating}
          className="w-full flex items-center justify-between rounded border border-border-default px-2 py-1 text-micro text-fg-secondary hover:border-accent transition-colors disabled:opacity-50"
        >
          <span>
            {updating
              ? "Updating…"
              : STATUS_OPTIONS.find((s) => s.value === currentStatus)?.label}
          </span>
          <ChevronDown size={12} />
        </button>

        {open && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setOpen(false)}
            />
            <div className="absolute left-0 right-0 top-full mt-1 z-20 rounded-card border border-border-default bg-bg-surface shadow-lg max-h-48 overflow-y-auto">
              {STATUS_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleStatusChange(opt.value)}
                  className={`w-full text-left px-3 py-1.5 text-micro hover:bg-accent-dim transition-colors ${
                    opt.value === currentStatus
                      ? "text-accent font-medium"
                      : "text-fg-primary"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function formatAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
