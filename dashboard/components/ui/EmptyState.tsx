import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
}

export default function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center text-fg-muted">
      {Icon && <Icon size={28} className="mb-1" />}
      <p className="text-small font-medium text-fg-secondary">{title}</p>
      {description && <p className="text-micro max-w-xs">{description}</p>}
    </div>
  );
}
