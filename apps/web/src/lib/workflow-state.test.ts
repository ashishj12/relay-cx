import { expect, test } from "bun:test";
import { workflowOutcome } from "./workflow-state";
import type { TelemetryEvent } from "./types";

const event = (
  eventType: string,
  status = "success",
  metadata = {},
): TelemetryEvent => ({
  eventType,
  status,
  metadata,
  eventId: eventType,
  traceId: "request",
  sessionId: "session",
  timestamp: "2026-10-19T00:00:00Z",
  component: "orchestrator",
  durationMs: 0,
});
test("a failed overview never appears stuck in fetching", () => {
  expect(
    workflowOutcome([
      event("workflow.transition", "success", {
        current: "FETCHING_ENTERPRISE_DATA",
      }),
      event("workflow.failed", "failure"),
      event("request.finished", "failure"),
    ]),
  ).toBe("FAILED");
});
test("a recorded escalation retains its actual outcome", () => {
  expect(
    workflowOutcome([
      event("workflow.failed", "failure", { finalState: "ESCALATED" }),
      event("request.finished", "failure"),
    ]),
  ).toBe("ESCALATED");
});
test("an access denial remains explicit", () => {
  expect(workflowOutcome([event("authorization.denied", "denied")])).toBe(
    "Access denied",
  );
});
test("an unfinished workflow remains in progress", () => {
  expect(workflowOutcome([event("request.received")])).toBe("In progress");
});
