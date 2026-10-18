"use client";
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  FlaskConical,
  GitBranch,
  LogOut,
  MessageCircle,
} from "lucide-react";
import type { Mode } from "@/lib/types";
import { api } from "@/lib/api";
import { Brand, Busy, ModeBadge } from "./ui";
import { SignIn } from "@/features/auth/sign-in";
import { useSession } from "@/features/auth/use-session";
import { Conversation } from "@/features/support/conversation";
import { AgentWorkspace } from "@/features/agents/agent-workspace";
import { OperationsWorkspace } from "@/features/operations/operations-workspace";
import { ReviewWorkspace } from "@/features/review/review-workspace";
import { TraceDrawer } from "@/features/traces/trace-drawer";

type View = "support" | "agents" | "operations" | "review";
const navigation = [
  { id: "support" as View, label: "Customer support", icon: MessageCircle },
  { id: "agents" as View, label: "Agent studio", icon: GitBranch },
  { id: "operations" as View, label: "Operations", icon: Activity },
  { id: "review" as View, label: "Evaluation", icon: FlaskConical },
];

export function Workspace() {
  const { session, loading, error, signIn, signOut, setSession, setError } =
    useSession();
  const [view, setView] = useState<View>("support");
  const [trace, setTrace] = useState<string | null>(null);
  const [online, setOnline] = useState(false);
  const support = session?.roles.includes("support-agent") ?? false;
  useEffect(() => {
    api("health")
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
  }, []);
  useEffect(() => {
    setView(support ? "operations" : "support");
    setTrace(null);
  }, [session?.customerId, support]);
  function navigate(view: View) {
    setView(view);
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  function onMode(mode: Mode) {
    setSession((current) => (current ? { ...current, mode } : null));
  }
  if (loading)
    return (
      <main className="app-loading">
        <Brand />
        <Busy label="Opening your workspace" />
      </main>
    );
  if (!session) return <SignIn onSuccess={signIn} connectionError={error} />;
  const visibleNavigation = navigation.filter(
    (item) => support || ["support", "agents"].includes(item.id),
  );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace-main">
        Skip to workspace
      </a>
      <aside className="sidebar">
        <Brand />
        <span className="sidebar-caption">RESOLUTION WORKSPACE</span>
        <nav aria-label="Main workspace">
          {visibleNavigation.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "active" : ""}
              aria-current={view === item.id ? "page" : undefined}
              onClick={() => navigate(item.id)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
              {view === item.id && <span className="nav-current" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-runtime">
          <GitBranch size={18} />
          <strong>Controlled agent workflow</strong>
          <p>Inspect the model, tools and decisions behind each request.</p>
          <button onClick={() => navigate("agents")}>
            Explore agents <ArrowUpRight size={14} />
          </button>
        </div>
        <div className="sidebar-bottom">
          <div className="environment-note">
            <span className="signal-dot" />
            Synthetic assessment
          </div>
          <div className="signed-in">
            <span className="avatar">{support ? "ST" : "CU"}</span>
            <div>
              <strong>{session.customerId}</strong>
              <small>
                {support ? "Support representative" : "Customer account"}
              </small>
            </div>
            <button
              className="icon-button"
              aria-label="Sign out"
              onClick={signOut}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>{navigation.find((item) => item.id === view)?.label}</span>
          <div className="topbar-right">
            <span className="service-status">
              <span className={`signal-dot ${online ? "" : "offline"}`} />
              {online ? "Services connected" : "Service unavailable"}
            </span>
            <ModeBadge mode={session.mode} />
            <button
              className="icon-button mobile-logout"
              aria-label="Sign out"
              onClick={signOut}
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>
        <main id="workspace-main" className="workspace-main">
          {error && (
            <div className="notice error" role="alert">
              {error}
              <button className="text-link" onClick={() => setError("")}>
                Dismiss
              </button>
            </div>
          )}
          {session.mode === "DEGRADED" && (
            <div className="notice degraded-notice">
              Gemini is unavailable for part of this request. The result uses
              deterministic workflow controls and verified enterprise records.
            </div>
          )}
          {view === "support" ? (
            <Conversation
              key={session.customerId}
              session={session}
              onMode={onMode}
              onTrace={setTrace}
            />
          ) : view === "agents" ? (
            <AgentWorkspace session={session} onTrace={setTrace} />
          ) : view === "operations" ? (
            <OperationsWorkspace session={session} onTrace={setTrace} />
          ) : (
            <ReviewWorkspace session={session} onTrace={setTrace} />
          )}
        </main>
      </div>
      <TraceDrawer traceId={trace} onClose={() => setTrace(null)} />
    </div>
  );
}
