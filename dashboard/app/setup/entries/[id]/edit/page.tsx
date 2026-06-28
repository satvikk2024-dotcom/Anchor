import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getResumeEntry } from "@/lib/queries";
import EntryForm from "@/components/EntryForm";
import { updateEntry } from "../../../actions";

export const dynamic = "force-dynamic";

export default async function EditEntryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const entry = await getResumeEntry(id);
  if (!entry) notFound();

  return (
    <div className="flex-1 p-6 max-w-3xl mx-auto w-full">
      <Link
        href="/setup"
        className="inline-flex items-center gap-1 text-small text-fg-secondary hover:text-accent mb-6"
      >
        <ArrowLeft size={14} /> Back to Setup
      </Link>
      <h1 className="text-h2 font-semibold text-fg-primary mb-6">
        Edit Resume Entry
      </h1>
      <div className="rounded-card border border-border-default bg-bg-surface p-6">
        <EntryForm entry={entry} action={updateEntry} />
      </div>
    </div>
  );
}
