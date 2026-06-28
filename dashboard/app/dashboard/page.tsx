import { Inbox } from "lucide-react";
import { getApplications, groupByStatus } from "@/lib/queries";
import type { ApplicationStatus } from "@/lib/types";
import StatusBadge from "@/components/ui/StatusBadge";
import EmptyState from "@/components/ui/EmptyState";
import IntakeForm from "@/components/IntakeForm";
import ApplicationCard from "@/components/ApplicationCard";

export const dynamic = "force-dynamic";

const SECTIONS: { title: string; statuses: ApplicationStatus[] }[] = [
  {
    title: "Active Pipeline",
    statuses: [
      "intake_received",
      "researched",
      "low_match_waiting",
      "awaiting_review",
      "submitted",
      "responded",
      "interview",
    ],
  },
  {
    title: "Outcomes",
    statuses: ["rejected", "ghosted", "withdrawn"],
  },
  {
    title: "Errors",
    statuses: ["errored"],
  },
];

export default async function DashboardPage() {
  const applications = await getApplications();
  const grouped = groupByStatus(applications);

  return (
    <div className="flex-1 p-6 flex flex-col gap-8">
      <section>
        <h1 className="text-h2 font-semibold text-fg-primary mb-4">
          Applications
        </h1>
        <div className="rounded-card border border-border-default bg-bg-surface p-4">
          <p className="text-small text-fg-secondary mb-3">
            Paste a job posting URL to start a new application:
          </p>
          <IntakeForm />
        </div>
      </section>

      {applications.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title="No applications yet"
          description="Use the form above to submit your first job URL."
        />
      ) : (
        SECTIONS.map((section) => (
          <div key={section.title}>
            <h2 className="text-h3 font-medium text-fg-secondary mb-3">
              {section.title}
            </h2>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {section.statuses.map((status) => (
                <div
                  key={status}
                  className="flex-shrink-0 w-64 rounded-card border border-border-default bg-bg-surface p-3"
                >
                  <div className="mb-2">
                    <StatusBadge status={status} />
                  </div>
                  <div className="flex flex-col gap-2">
                    {grouped[status].length === 0 ? (
                      <p className="text-micro text-fg-muted py-4 text-center">
                        —
                      </p>
                    ) : (
                      grouped[status].map((app) => (
                        <ApplicationCard
                          key={app.id}
                          id={app.id}
                          roleTitle={app.role_title}
                          companyName={app.company_name}
                          status={app.status}
                          matchScore={app.match_score}
                          url={app.url}
                          createdAt={app.created_at}
                        />
                      ))
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
