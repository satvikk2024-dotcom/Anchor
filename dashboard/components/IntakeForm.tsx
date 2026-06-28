"use client";

import { useState } from "react";
import { Send, Loader2, CheckCircle, AlertCircle } from "lucide-react";

export default function IntakeForm() {
  const [url, setUrl] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "success" | "error">(
    "idle"
  );
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setState("loading");
    try {
      const res = await fetch("/api/intake", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setState("success");
        setMessage(
          `Processing started — Application ID: ${data.application_id}`
        );
        setUrl("");
      } else {
        setState("error");
        setMessage(data.error ?? "Submission failed");
      }
    } catch {
      setState("error");
      setMessage(
        "Could not reach the pipeline — is n8n running on port 5678?"
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex gap-3">
        <input
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            if (state !== "idle") setState("idle");
          }}
          placeholder="Paste a job posting URL (LinkedIn, Greenhouse, Lever, Workday…)"
          className="flex-1 rounded-card border border-border-default bg-bg-primary px-4 py-2.5 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent"
          disabled={state === "loading"}
          required
        />
        <button
          type="submit"
          disabled={state === "loading" || !url.trim()}
          className="inline-flex items-center gap-2 rounded-card bg-accent text-white px-5 py-2.5 text-small font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {state === "loading" ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Send size={16} />
          )}
          {state === "loading" ? "Submitting…" : "Submit"}
        </button>
      </div>
      {state === "success" && (
        <p className="flex items-center gap-2 text-small text-success">
          <CheckCircle size={14} /> {message}
        </p>
      )}
      {state === "error" && (
        <p className="flex items-center gap-2 text-small text-danger">
          <AlertCircle size={14} /> {message}
        </p>
      )}
    </form>
  );
}
