import React, { useState } from "react";
import { useAppState } from "../state/appState";

export function Onboarding() {
  const { ensureOnboarded, currentUser } = useAppState();
  const [username, setUsername] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;
    setBusy(true);
    setError(undefined);
    try {
      await ensureOnboarded(username.trim());
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setBusy(false);
    }
  };

  if (currentUser) return null;

  return (
    <div className="onboarding">
      <h2>Welcome to QChat</h2>
      <p>Choose a username and generate end-to-end encryption keys.</p>
      <form onSubmit={submit}>
        <input
          placeholder="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={busy}
        />
        <button type="submit" disabled={busy || !username.trim()}>
          {busy ? "Setting up..." : "Continue"}
        </button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
