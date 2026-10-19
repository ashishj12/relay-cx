"use client";
import { useState } from "react";
import {
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  LockKeyhole,
  Network,
  ShieldCheck,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Session } from "@/lib/types";
import { Brand } from "@/components/ui";
import { decodeSession } from "./session";

const accounts = [
  {
    name: "Alex Morgan",
    username: "alex.morgan",
    password: "ReviewerPass-1001",
    role: "Home internet customer",
  },
  {
    name: "Jordan Lee",
    username: "jordan.lee",
    password: "ReviewerPass-1002",
    role: "Mobile customer",
  },
  {
    name: "Support team",
    username: "support.agent",
    password: "ReviewerPass-3001",
    role: "Operations & evaluation",
  },
  {
    name: "Admin",
    username: "admin",
    password: "admin@123",
    role: "Operations & evaluation",
  },
];

export function SignIn({
  onSuccess,
  connectionError,
}: {
  onSuccess: (session: Session) => void;
  connectionError?: string;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const session = decodeSession(
        await api<unknown>("login", { username: username.trim(), password }),
      );
      setPassword("");
      onSuccess(session);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="entry-page">
      <header className="entry-nav">
        <Brand />
        <span>Customer resolution, connected.</span>
        <a href="#how-it-works">
          How it works <ArrowRight size={16} />
        </a>
      </header>
      <div className="entry-grid">
        <section className="entry-story">
          <span className="overline">
            <span className="signal-dot" /> ACCOUNT. CONNECTION. RESOLUTION.
          </span>
          <h1>
            A better way to
            <br />
            sort out <em>your service.</em>
          </h1>
          <p>
            One conversation for your plan, your bill, or a connection that
            needs attention. With the context kept along the way.
          </p>
          <div className="request-path" id="how-it-works">
            <div className="path-heading">
              <Network size={18} />
              <span>What happens behind the conversation</span>
            </div>
            <div className="path-step">
              <span className="path-number">1</span>
              <div>
                <strong>We understand the request</strong>
                <p>
                  A router identifies the right specialist and asks when
                  something is missing.
                </p>
              </div>
              <span className="path-type">ROUTE</span>
            </div>
            <div className="path-step">
              <span className="path-number">2</span>
              <div>
                <strong>The specialist checks your records</strong>
                <p>
                  Account, billing and service tools stay bound to your
                  authenticated account.
                </p>
              </div>
              <span className="path-type">VERIFY</span>
            </div>
            <div className="path-step">
              <span className="path-number">3</span>
              <div>
                <strong>You decide what happens next</strong>
                <p>
                  Approve a support case, inspect the evidence, or bring in a
                  person.
                </p>
              </div>
              <span className="path-type">RESOLVE</span>
            </div>
          </div>
          <div className="entry-principles">
            <span>
              <ShieldCheck size={16} /> Verified account access
            </span>
            <span>
              <Check size={16} /> Explicit action approval
            </span>
          </div>
        </section>
        <section className="auth-card" aria-labelledby="sign-in-heading">
          <div className="auth-icon">
            <LockKeyhole size={21} />
          </div>
          <h2 id="sign-in-heading">Welcome to Relay.</h2>
          <p>Sign in to your resolution workspace.</p>
          <form onSubmit={submit}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              autoComplete="username"
              placeholder="Your username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              maxLength={100}
              required
              disabled={busy}
            />
            <label htmlFor="password">Password</label>
            <div className="password-input">
              <input
                id="password"
                type={visible ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                maxLength={200}
                required
                disabled={busy}
              />
              <button
                type="button"
                className="icon-button"
                aria-label={visible ? "Hide password" : "Show password"}
                onClick={() => setVisible(!visible)}
              >
                {visible ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {(error || connectionError) && (
              <p className="form-error" role="alert">
                {error || connectionError}
              </p>
            )}
            <button className="button primary auth-submit" disabled={busy}>
              {busy ? "Signing in…" : "Open workspace"}
              <ArrowRight size={17} />
            </button>
          </form>
          <details className="sample-accounts">
            <summary>
              Try a supplied sample account <span>+</span>
            </summary>
            <p>Challenge fixtures only. No real customer records.</p>
            {accounts.map((account) => (
              <button
                key={account.username}
                type="button"
                onClick={() => {
                  setUsername(account.username);
                  setPassword(account.password);
                  setError("");
                }}
              >
                <span>
                  <strong>{account.name}</strong>
                  <small>{account.role}</small>
                </span>
                <ArrowRight size={16} />
              </button>
            ))}
          </details>
          <p className="auth-footnote">
            <ShieldCheck size={14} /> Your session stays on this device.
          </p>
        </section>
      </div>
      <footer className="entry-footer">
        <span>Relay / Enterprise customer experience</span>
        <span>
          Synthetic assessment environment <span className="footer-dot" /> Built
          with Google ADK
        </span>
      </footer>
    </main>
  );
}
