import type { MasterResumeEntry, ResumeEntryCategory } from "@/lib/types";

const CATEGORIES: { value: ResumeEntryCategory; label: string }[] = [
  { value: "education", label: "Education" },
  { value: "experience", label: "Experience" },
  { value: "project", label: "Project" },
  { value: "skill", label: "Skill" },
  { value: "achievement", label: "Achievement" },
];

interface EntryFormProps {
  entry?: MasterResumeEntry;
  action: (formData: FormData) => Promise<void>;
  defaultCategory?: string;
}

export default function EntryForm({
  entry,
  action,
  defaultCategory,
}: EntryFormProps) {
  return (
    <form action={action} className="flex flex-col gap-5">
      {entry && <input type="hidden" name="id" value={entry.id} />}

      <div>
        <label className="block text-small font-medium text-fg-secondary mb-1">
          Category
        </label>
        <select
          name="category"
          defaultValue={entry?.category ?? defaultCategory ?? "experience"}
          className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2.5 text-small text-fg-primary focus:outline-none focus:border-accent"
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-small font-medium text-fg-secondary mb-1">
          Content
          <span className="font-normal text-fg-muted ml-1">
            (natural language — this is what agents see)
          </span>
        </label>
        <textarea
          name="canonical_text"
          defaultValue={entry?.canonical_text ?? ""}
          rows={5}
          required
          className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent resize-y leading-relaxed"
          placeholder="e.g. Built Meridian, a multi-agent research assistant orchestrating 5 AI agents via n8n workflows…"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-small font-medium text-fg-secondary mb-1">
            Tags
            <span className="font-normal text-fg-muted ml-1">
              (comma-separated)
            </span>
          </label>
          <input
            type="text"
            name="tags"
            defaultValue={entry?.tags?.join(", ") ?? ""}
            className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent"
            placeholder="e.g. python, fastapi, ml, project"
          />
        </div>
        <div>
          <label className="block text-small font-medium text-fg-secondary mb-1">
            Priority
            <span className="font-normal text-fg-muted ml-1">(1–5)</span>
          </label>
          <input
            type="number"
            name="priority"
            min={1}
            max={5}
            defaultValue={entry?.priority ?? 3}
            className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary focus:outline-none focus:border-accent"
          />
        </div>
      </div>

      <div>
        <label className="block text-small font-medium text-fg-secondary mb-1">
          Structured Facts
          <span className="font-normal text-fg-muted ml-1">
            (optional JSON — metadata for agents)
          </span>
        </label>
        <textarea
          name="facts"
          defaultValue={
            entry?.facts ? JSON.stringify(entry.facts, null, 2) : ""
          }
          rows={4}
          className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent resize-y font-mono text-micro"
          placeholder='{"role": "SWE Intern", "company": "Acme", "dates": "Jun–Aug 2025"}'
        />
      </div>

      <div className="flex justify-end gap-3">
        <a
          href="/setup"
          className="rounded-card border border-border-default px-4 py-2 text-small text-fg-secondary hover:bg-bg-primary transition-colors"
        >
          Cancel
        </a>
        <button
          type="submit"
          className="rounded-card bg-accent text-white px-5 py-2 text-small font-medium hover:opacity-90 transition-opacity"
        >
          {entry ? "Save Changes" : "Add Entry"}
        </button>
      </div>
    </form>
  );
}
