import type { LucideIcon } from "lucide-react";

interface ShortcutLinkProps {
  href: string;
  label: string;
  icon: LucideIcon;
}

export default function ShortcutLink({ href, label, icon: Icon }: ShortcutLinkProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      title={label}
      className="inline-flex items-center gap-2 rounded-card px-3 py-2 text-small text-fg-secondary hover:text-accent hover:bg-accent-dim transition-colors"
    >
      <Icon size={16} />
      <span className="hidden sm:inline">{label}</span>
    </a>
  );
}
