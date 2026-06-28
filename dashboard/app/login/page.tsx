"use client";

import { useState } from "react";
import { Anchor, Loader2, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (res.ok) {
        window.location.href = "/dashboard";
      } else {
        setError("Invalid username or password");
      }
    } catch {
      setError("Could not connect to the server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8 animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-accent text-white mb-4">
            <Anchor size={28} />
          </div>
          <h1 className="text-h1 font-semibold text-fg-primary">Anchor</h1>
          <p className="text-small text-fg-secondary mt-1">
            Sign in to your application pipeline
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-card border border-border-default bg-bg-surface p-6 flex flex-col gap-4 animate-fade-in-up"
          style={{ animationDelay: "0.1s" }}
        >
          <div>
            <label className="block text-small font-medium text-fg-secondary mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2.5 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent"
              placeholder="admin"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-small font-medium text-fg-secondary mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-card border border-border-default bg-bg-primary px-3 py-2.5 text-small text-fg-primary placeholder:text-fg-muted focus:outline-none focus:border-accent"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <p className="flex items-center gap-2 text-small text-danger">
              <AlertCircle size={14} /> {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-card bg-accent text-white py-2.5 text-small font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 size={16} className="animate-spin" /> Signing in…
              </span>
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        <p className="text-center text-micro text-fg-muted mt-6">
          Anchor · personal AI job-application pipeline
        </p>
      </div>
    </div>
  );
}
