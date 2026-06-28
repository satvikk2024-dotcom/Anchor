import Link from "next/link";
import { LayoutGrid, ScrollText, Sparkles, ArrowRight } from "lucide-react";

const FEATURES = [
  {
    href: "/dashboard",
    icon: LayoutGrid,
    title: "Applications",
    desc: "Track every application through the pipeline, from intake to outcome.",
  },
  {
    href: "/decisions",
    icon: ScrollText,
    title: "Decisions",
    desc: "Audit every AI agent call — inputs, outputs, latency, critic verdicts.",
  },
  {
    href: "/insights",
    icon: Sparkles,
    title: "Insights",
    desc: "Weekly reflections on patterns across your applications.",
  },
];

export default function WelcomePage() {
  return (
    <section className="flex flex-1 flex-col items-center justify-center gap-10 px-6 py-16 text-center">
      <div className="animate-fade-in-up flex flex-col items-center gap-3">
        <h1 className="text-h1 font-semibold text-fg-primary">Anchor</h1>
        <p className="text-body text-fg-secondary max-w-md">
          Your AI co-pilot for the job hunt — researches companies, tailors resumes,
          drafts cover letters, and tracks every application end to end.
        </p>
        <Link
          href="/dashboard"
          className="mt-2 inline-flex items-center gap-2 rounded-card bg-accent px-6 py-3 text-small font-medium text-white hover:bg-accent/90 transition-colors"
        >
          Enter Dashboard <ArrowRight size={16} />
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl w-full">
        {FEATURES.map((f, i) => (
          <Link
            key={f.href}
            href={f.href}
            style={{ animationDelay: `${0.15 + i * 0.1}s` }}
            className="animate-fade-in-up rounded-card border border-border-default bg-bg-surface p-6 text-left hover:border-accent transition-colors"
          >
            <f.icon size={20} className="text-accent mb-3" />
            <h3 className="text-h3 font-medium text-fg-primary mb-1">{f.title}</h3>
            <p className="text-small text-fg-secondary">{f.desc}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
