"use client";

import { useState, useRef } from "react";
import {
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  FileText,
} from "lucide-react";

export default function ResumeUpload() {
  const [state, setState] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<"append" | "replace">("replace");
  const [fileName, setFileName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;

    setState("loading");
    setMessage("Extracting text and decomposing into entries…");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", mode);

    try {
      const res = await fetch("/api/upload-resume", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        setState("success");
        setMessage(
          `Created ${data.entries_created} entries from ${Math.round(data.extracted_chars / 1000)}k chars of resume text.`
        );
        if (fileRef.current) fileRef.current.value = "";
        setFileName("");
      } else {
        setState("error");
        setMessage(data.error || "Upload failed");
      }
    } catch {
      setState("error");
      setMessage("Could not connect — is the LLM wrapper running on port 8001?");
    }
  }

  return (
    <form onSubmit={handleUpload} className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <label
          className="flex-1 flex items-center gap-3 rounded-card border-2 border-dashed border-border-default hover:border-accent px-4 py-4 cursor-pointer transition-colors"
        >
          <FileText size={20} className="text-fg-muted flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-small font-medium text-fg-primary truncate">
              {fileName || "Choose a PDF resume…"}
            </p>
            <p className="text-micro text-fg-muted">
              PDF only — text will be extracted and decomposed by AI
            </p>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              setFileName(e.target.files?.[0]?.name || "");
              if (state !== "idle") setState("idle");
            }}
          />
        </label>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <label className="inline-flex items-center gap-2 text-small text-fg-secondary cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="replace"
              checked={mode === "replace"}
              onChange={() => setMode("replace")}
              className="accent-accent"
            />
            Replace all entries
          </label>
          <label className="inline-flex items-center gap-2 text-small text-fg-secondary cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="append"
              checked={mode === "append"}
              onChange={() => setMode("append")}
              className="accent-accent"
            />
            Append to existing
          </label>
        </div>

        <button
          type="submit"
          disabled={state === "loading" || !fileName}
          className="inline-flex items-center gap-2 rounded-card bg-accent text-white px-4 py-2 text-small font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {state === "loading" ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Upload size={16} />
          )}
          {state === "loading" ? "Processing…" : "Upload & Parse"}
        </button>
      </div>

      {state === "success" && (
        <p className="flex items-center gap-2 text-small text-success">
          <CheckCircle size={14} /> {message}
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="underline ml-1"
          >
            Refresh to see entries
          </button>
        </p>
      )}
      {state === "error" && (
        <p className="flex items-center gap-2 text-small text-danger">
          <AlertCircle size={14} /> {message}
        </p>
      )}
      {state === "loading" && (
        <p className="text-small text-fg-muted">{message}</p>
      )}
    </form>
  );
}
