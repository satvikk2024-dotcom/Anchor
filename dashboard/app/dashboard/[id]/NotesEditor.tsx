"use client";

import { useState, useCallback } from "react";
import { Check } from "lucide-react";

export default function NotesEditor({
  applicationId,
  initialNotes,
}: {
  applicationId: string;
  initialNotes: string;
}) {
  const [notes, setNotes] = useState(initialNotes);
  const [saved, setSaved] = useState(false);
  const [timer, setTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const save = useCallback(
    (text: string) => {
      if (timer) clearTimeout(timer);
      const t = setTimeout(async () => {
        await fetch("/api/update-notes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ applicationId, notes: text }),
        });
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }, 800);
      setTimer(t);
    },
    [applicationId, timer]
  );

  return (
    <div>
      <textarea
        value={notes}
        onChange={(e) => {
          setNotes(e.target.value);
          setSaved(false);
          save(e.target.value);
        }}
        rows={4}
        placeholder="Add notes about this application — interview prep, contact info, follow-up reminders…"
        className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent resize-y"
      />
      {saved && (
        <p className="flex items-center gap-1 text-micro text-success mt-1">
          <Check size={12} /> Saved
        </p>
      )}
    </div>
  );
}
