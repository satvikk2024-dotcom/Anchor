import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import {
  NotebookPen,
  FolderOpen,
  Workflow,
  LayoutGrid,
  ScrollText,
  Sparkles,
  Settings,
} from "lucide-react";
import ShortcutLink from "@/components/ui/ShortcutLink";
import LogoutButton from "@/components/LogoutButton";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Anchor — Application Pipeline",
  description: "Personal AI job-application pipeline dashboard",
};

const NAV_LINKS = [
  { href: "/dashboard", label: "Applications", icon: LayoutGrid },
  { href: "/decisions", label: "Decisions", icon: ScrollText },
  { href: "/insights", label: "Insights", icon: Sparkles },
  { href: "/setup", label: "Setup", icon: Settings },
];

function getShortcuts() {
  return [
    {
      href: process.env.NOTION_URL || "https://www.notion.so",
      label: "Notion",
      icon: NotebookPen,
    },
    {
      href: process.env.DRIVE_URL || "https://drive.google.com",
      label: "Drive",
      icon: FolderOpen,
    },
    {
      href: process.env.N8N_URL || "http://localhost:5678",
      label: "n8n",
      icon: Workflow,
    },
  ];
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased flex flex-col min-h-screen">
        <header className="flex items-center justify-between px-6 h-16 border-b border-border-subtle bg-bg-surface">
          <Link href="/" className="font-semibold text-h3 text-fg-primary tracking-tight">
            Anchor
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className="inline-flex items-center gap-2 rounded-card px-3 py-2 text-small text-fg-secondary hover:text-accent hover:bg-accent-dim transition-colors"
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-1 border-l border-border-subtle pl-2">
            {getShortcuts().map((s) => (
              <ShortcutLink key={s.label} {...s} />
            ))}
            <LogoutButton />
          </div>
        </header>

        <main className="flex-1 flex flex-col">{children}</main>

        <footer className="flex items-center justify-center h-12 border-t border-border-subtle text-micro text-fg-muted">
          Anchor · personal AI job-application pipeline
        </footer>
      </body>
    </html>
  );
}
