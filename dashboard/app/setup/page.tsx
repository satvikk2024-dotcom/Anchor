import { Plus, Settings, User, Trash2, Upload } from "lucide-react";
import Link from "next/link";
import { getResumeEntries, getUserProfile } from "@/lib/queries";
import type { ResumeEntryCategory } from "@/lib/types";
import { updateProfile, deleteEntry } from "./actions";
import ResumeUpload from "@/components/ResumeUpload";

export const dynamic = "force-dynamic";

const CATEGORY_LABELS: Record<ResumeEntryCategory, string> = {
  education: "Education",
  experience: "Experience",
  project: "Projects",
  skill: "Skills",
  achievement: "Achievements",
};

const CATEGORY_ORDER: ResumeEntryCategory[] = [
  "education",
  "experience",
  "project",
  "skill",
  "achievement",
];

export default async function SetupPage() {
  const [entries, profile] = await Promise.all([
    getResumeEntries(),
    getUserProfile(),
  ]);

  const grouped = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    label: CATEGORY_LABELS[cat],
    entries: entries.filter((e) => e.category === cat),
  }));

  return (
    <div className="flex-1 p-6 flex flex-col gap-8 max-w-4xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-h2 font-semibold text-fg-primary flex items-center gap-2">
          <Settings size={24} /> Setup
        </h1>
        <Link
          href="/setup/entries/new"
          className="inline-flex items-center gap-2 rounded-card bg-accent text-white px-4 py-2 text-small font-medium hover:opacity-90 transition-opacity"
        >
          <Plus size={16} /> Add Entry
        </Link>
      </div>

      {/* Resume Upload */}
      <section className="rounded-card border border-border-default bg-bg-surface p-5">
        <h2 className="text-h3 font-medium text-fg-primary flex items-center gap-2 mb-4">
          <Upload size={18} /> Import Resume from PDF
        </h2>
        <p className="text-small text-fg-secondary mb-4">
          Upload your resume as a PDF — the AI will extract and decompose it into
          structured entries automatically. You can replace all existing entries
          or append to them.
        </p>
        <ResumeUpload />
      </section>

      {/* User Profile */}
      <section className="rounded-card border border-border-default bg-bg-surface p-5">
        <h2 className="text-h3 font-medium text-fg-primary flex items-center gap-2 mb-4">
          <User size={18} /> Your Profile
        </h2>
        <form action={updateProfile} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-small font-medium text-fg-secondary mb-1">Name</label>
              <input type="text" name="name" defaultValue={profile?.name ?? ""} className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent" placeholder="Satvik Krishna" />
            </div>
            <div>
              <label className="block text-small font-medium text-fg-secondary mb-1">Email</label>
              <input type="email" name="email" defaultValue={profile?.email ?? ""} className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent" placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-small font-medium text-fg-secondary mb-1">Phone</label>
              <input type="text" name="phone" defaultValue={profile?.phone ?? ""} className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent" placeholder="+91-XXXXXXXXXX" />
            </div>
            <div>
              <label className="block text-small font-medium text-fg-secondary mb-1">Location</label>
              <input type="text" name="location" defaultValue={profile?.location ?? ""} className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent" placeholder="Bengaluru, India" />
            </div>
            <div>
              <label className="block text-small font-medium text-fg-secondary mb-1">LinkedIn</label>
              <input type="text" name="linkedin_url" defaultValue={profile?.linkedin_url ?? ""} className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent" placeholder="linkedin.com/in/your-name" />
            </div>
            <div>
              <label className="block text-small font-medium text-fg-secondary mb-1">GitHub</label>
              <input type="text" name="github_url" defaultValue={profile?.github_url ?? ""} className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent" placeholder="github.com/your-username" />
            </div>
          </div>
          <div>
            <label className="block text-small font-medium text-fg-secondary mb-1">
              Career Goals
            </label>
            <textarea
              name="long_term_goals"
              defaultValue={profile?.long_term_goals ?? ""}
              rows={3}
              className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent resize-y"
              placeholder="e.g. Seeking ML engineering / AI infrastructure / backend internships for Summer 2026…"
            />
          </div>
          <div>
            <label className="block text-small font-medium text-fg-secondary mb-1">
              Target Role Types
              <span className="font-normal text-fg-muted ml-1">
                (comma-separated)
              </span>
            </label>
            <input
              type="text"
              name="target_role_types"
              defaultValue={profile?.target_role_types?.join(", ") ?? ""}
              className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent"
              placeholder="e.g. ML Engineer, Backend Engineer, AI Research, Data Engineering"
            />
          </div>
          <button
            type="submit"
            className="self-end rounded-card bg-accent text-white px-4 py-2 text-small font-medium hover:opacity-90 transition-opacity"
          >
            Save Profile
          </button>
        </form>
      </section>

      {/* Resume Entries */}
      <section className="flex flex-col gap-6">
        <h2 className="text-h3 font-medium text-fg-primary">
          Master Resume Entries
          <span className="text-small font-normal text-fg-muted ml-2">
            {entries.length} entries
          </span>
        </h2>

        {grouped.map(({ category, label, entries: catEntries }) => (
          <div key={category}>
            <h3 className="text-small font-semibold text-fg-secondary uppercase tracking-wide mb-2">
              {label}
              <span className="ml-2 text-fg-muted font-normal normal-case">
                ({catEntries.length})
              </span>
            </h3>

            {catEntries.length === 0 ? (
              <p className="text-small text-fg-muted py-3 border border-dashed border-border-default rounded-card px-4">
                No {label.toLowerCase()} entries yet.{" "}
                <Link
                  href={`/setup/entries/new?category=${category}`}
                  className="text-accent hover:underline"
                >
                  Add one →
                </Link>
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {catEntries.map((entry) => (
                  <div
                    key={entry.id}
                    className="rounded-card border border-border-default bg-bg-surface p-4 group"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <p className="text-small text-fg-primary leading-relaxed flex-1">
                        {entry.canonical_text}
                      </p>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                        <Link
                          href={`/setup/entries/${entry.id}/edit`}
                          className="rounded px-2 py-1 text-micro text-fg-secondary hover:text-accent hover:bg-accent-dim transition-colors"
                        >
                          Edit
                        </Link>
                        <form action={deleteEntry}>
                          <input type="hidden" name="id" value={entry.id} />
                          <button
                            type="submit"
                            className="rounded p-1 text-fg-muted hover:text-danger transition-colors"
                            title="Delete entry"
                          >
                            <Trash2 size={14} />
                          </button>
                        </form>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 mt-2">
                      {entry.priority && (
                        <span className="text-micro text-fg-muted">
                          Priority: {entry.priority}/5
                        </span>
                      )}
                      {entry.tags.length > 0 && (
                        <div className="flex gap-1 flex-wrap">
                          {entry.tags.slice(0, 6).map((tag) => (
                            <span
                              key={tag}
                              className="inline-block rounded px-1.5 py-0.5 text-micro bg-accent-dim text-accent"
                            >
                              {tag}
                            </span>
                          ))}
                          {entry.tags.length > 6 && (
                            <span className="text-micro text-fg-muted">
                              +{entry.tags.length - 6}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </section>
    </div>
  );
}
