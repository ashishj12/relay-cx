"use client";
import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Braces,
  GitBranch,
  ShieldCheck,
  Wrench,
} from "lucide-react";
import { api, titleCase } from "@/lib/api";
import type { Session, TelemetryEvent } from "@/lib/types";

type AgentDefinition = {
  name: string;
  label: string;
  purpose: string;
  tools: string[];
  stage: string;
};
export function AgentWorkspace({
  session,
  onTrace,
}: {
  session: Session;
  onTrace: (id: string) => void;
}) {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api<{ agents: AgentDefinition[] }>("agents"),
      api<TelemetryEvent[]>(
        session.roles.includes("support-agent") ? "ops/events" : "activity",
      ),
    ])
      .then(([catalog, events]) => {
        if (!cancelled) {
          setAgents(catalog.agents);
          setEvents(events);
        }
      })
      .catch((error) => {
        if (!cancelled) setError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [session.roles]);
  const runs = events.filter((event) => event.eventType === "agent.invoked");
  return (
    <div className="agent-workspace">
      <div className="page-intro">
        <div>
          <span className="overline">RUNTIME & CAPABILITIES</span>
          <h1>The agents behind a request.</h1>
          <p>
            Bounded responsibilities. Authorized tools. A trace for every run.
          </p>
        </div>
        <span className="framework-label">
          <GitBranch size={16} />
          Google ADK
        </span>
      </div>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      <div className="agent-mode-note">
        <ShieldCheck size={19} />
        <div>
          <strong>
            {session.mode === "REVIEWER"
              ? "Reviewer mode uses deterministic interpretation."
              : session.mode === "LIVE_AI"
                ? "Live mode uses Gemini to write replies from verified challenge records."
                : "The provider is degraded. Check the execution trace for the failure reason."}
          </strong>
          <p>
            The catalog below describes the configured system. Execution history
            contains only recorded events. Model output never grants permission
            or submits a case.
          </p>
        </div>
      </div>
      <div className="agent-flow">
        <span>Customer request</span>
        <ArrowUpRight size={17} />
        <span>Router</span>
        <ArrowUpRight size={17} />
        <span>Specialist & read tool</span>
        <ArrowUpRight size={17} />
        <span>Verified answer / approval</span>
      </div>
      <div className="agent-catalog">
        {agents.map((agent, index) => (
          <article key={agent.name}>
            <div className="agent-card-top">
              <span>{String(index + 1).padStart(2, "0")}</span>
              <span>
                {agent.stage === "deterministic"
                  ? "APPLICATION CONTROL"
                  : "ADK AGENT"}
              </span>
            </div>
            <h2>{agent.label}</h2>
            <p>{agent.purpose}</p>
            <div className="agent-tools">
              <Wrench size={14} />
              {agent.tools.length ? (
                agent.tools.map((tool) => <code key={tool}>{tool}</code>)
              ) : (
                <span>Validated structured routing</span>
              )}
            </div>
          </article>
        ))}
      </div>
      <section className="agent-run-history">
        <div className="section-heading">
          <h2>Recorded invocations</h2>
          <span>{runs.length} events in this view</span>
        </div>
        {runs.length ? (
          <div className="run-list">
            {runs
              .slice(-20)
              .reverse()
              .map((event) => (
                <button
                  key={event.eventId}
                  onClick={() => onTrace(event.traceId)}
                >
                  <span className="run-node">
                    <Braces size={16} />
                  </span>
                  <span>
                    <strong>{titleCase(event.component)}</strong>
                    <small>
                      {String(event.metadata.operation ?? "workflow")} ·{" "}
                      {typeof event.metadata.framework === "string"
                        ? event.metadata.framework
                        : "deterministic provider"}
                    </small>
                  </span>
                  <time>{new Date(event.timestamp).toLocaleTimeString()}</time>
                  <ArrowUpRight size={16} />
                </button>
              ))}
          </div>
        ) : (
          <div className="empty-state">
            <h3>No agent invocation has been recorded in this view.</h3>
            <p>
              Start a customer conversation or run an evaluation, then return
              here.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
