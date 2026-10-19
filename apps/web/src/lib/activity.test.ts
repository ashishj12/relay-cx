import { expect, test } from "bun:test";
import { currentActivity } from "./activity";
import type { TelemetryEvent } from "./types";

const event = (traceId: string, eventType: string): TelemetryEvent => ({
  traceId,
  eventType,
  eventId: traceId + eventType,
  sessionId: "customer-session",
  timestamp: "2026-10-19T00:00:00Z",
  component: "orchestrator",
  status: "success",
  durationMs: 0,
  metadata: {},
});
const previous = [
  event("old", "request.received"),
  event("old", "tool.finished"),
  event("old", "request.finished"),
];

test("a pending new turn never presents old completed tools as current work", () => {
  expect(currentActivity(previous, true, "old")).toEqual([]);
});
test("an in-flight turn displays only its own trace", () => {
  const latest = [
    event("new", "request.received"),
    event("new", "tool.invoked"),
  ];
  expect(currentActivity([...previous, ...latest], true, "old")).toEqual(
    latest,
  );
});
test("the completed view stays bound to the selected trace", () => {
  expect(
    currentActivity(
      [...previous, event("new", "request.received")],
      false,
      "old",
    ),
  ).toEqual(previous);
});
