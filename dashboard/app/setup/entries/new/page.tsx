import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import EntryForm from "@/components/EntryForm";
import { createEntry } from "../../actions";

export default async function NewEntryPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string }>;
}) {
  const { category } = await searchParams;

  return (
    <div className="flex-1 p-6 max-w-3xl mx-auto w-full">
      <Link
        href="/setup"
        className="inline-flex items-center gap-1 text-small text-fg-secondary hover:text-accent mb-6"
      >
        <ArrowLeft size={14} /> Back to Setup
      </Link>
      <h1 className="text-h2 font-semibold text-fg-primary mb-6">
        Add Resume Entry
      </h1>
      <div className="rounded-card border border-border-default bg-bg-surface p-6">
        <EntryForm action={createEntry} defaultCategory={category} />
      </div>
    </div>
  );
}
