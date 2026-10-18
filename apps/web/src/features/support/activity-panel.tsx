import {
  ArrowUpRight,
  Check,
  Circle,
  LoaderCircle,
  ShieldCheck,
  X,
} from "lucide-react";
import { titleCase } from "@/lib/api";
import type { TelemetryEvent } from "@/lib/types";

export function ActivityPanel({
  events,
  busy,
  traceId,
  onTrace,
}: {
  events: TelemetryEvent[];
  busy: boolean;
  traceId: string | null;
  onTrace: (id: string) => void;
}) {
  const steps = events
    .filter((event) =>
      [
        "agent.invoked",
        "agent.tool_requested",
        "tool.finished",
        "authorization.denied",
        "confirmation.requested",
        "action.completed",
        "provider.fallback",
        "workflow.escalated",
      ].includes(event.eventType),
    )
    .slice(-12);
  return (
    <aside className="activity-panel">
      <div className="panel-heading">
        <span className={busy ? "signal-dot pulse" : "signal-dot"} />
        <h2>Agent activity</h2>
        <span className="small-label">ACTUAL EVENTS</span>
      </div>
      {busy && (
        <div className="activity-working" role="status">
          <LoaderCircle size={16} className="spin" /> Working on your request
        </div>
      )}
      {steps.length ? (
        <ol className="activity-list">
          {steps.map((event) => (
            <li key={event.eventId}>
              <span className={`event-icon ${event.status}`}>
                {["failure", "denied"].includes(event.status) ? (
                  <X size={13} />
                ) : event.status === "pending" ? (
                  <Circle size={12} />
                ) : (
                  <Check size={13} />
                )}
              </span>
              <div>
                <strong>{titleCase(event.component)}</strong>
                <span>{titleCase(event.eventType.replaceAll(".", " "))}</span>
                {typeof event.metadata.tool === "string" && (
                  <code>{event.metadata.tool}</code>
                )}
              </div>
              {event.durationMs > 0 && (
                <small>{Math.round(event.durationMs)}ms</small>
              )}
            </li>
          ))}
        </ol>
      ) : (
        <div className="activity-empty">
          <div className="quiet-network">
            <span />
            <span />
            <span />
          </div>
          <h3>The work will show up here.</h3>
          <p>
            As your request runs, see the agents, access checks and enterprise
            tools involved.
          </p>
        </div>
      )}
      {traceId && (
        <button
          className="text-link activity-trace"
          onClick={() => onTrace(traceId)}
        >
          Open full execution trace <ArrowUpRight size={15} />
        </button>
      )}
      <div className="activity-note">
        <ShieldCheck size={17} />
        <p>
          Agents can read authorized records. Only your explicit confirmation
          can submit a support case.
        </p>
      </div>
    </aside>
  );
}
