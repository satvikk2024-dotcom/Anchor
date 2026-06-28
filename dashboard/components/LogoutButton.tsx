"use client";

import { LogOut } from "lucide-react";

export default function LogoutButton() {
  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  }

  return (
    <button
      onClick={handleLogout}
      className="rounded p-2 text-fg-muted hover:text-danger hover:bg-accent-dim transition-colors"
      title="Sign out"
    >
      <LogOut size={16} />
    </button>
  );
}
