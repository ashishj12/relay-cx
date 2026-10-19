import type { TelemetryEvent } from "./types";

export function workflowOutcome(events: TelemetryEvent[]): string {
  if (events.some((event) => event.eventType === "authorization.denied"))
    return "Access denied";
  const failed = events.find((event) => event.eventType === "workflow.failed");
  const finished = events.find(
    (event) => event.eventType === "request.finished",
  );
  const transition = events.findLast(
    (event) => event.eventType === "workflow.transition",
  );
  return String(
    failed?.metadata.finalState ??
      (finished?.status === "failure"
        ? "FAILED"
        : (transition?.metadata.current ??
          (finished ? "Complete" : "In progress"))),
  );
}
