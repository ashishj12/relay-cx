import type { TelemetryEvent } from "./types";

export function currentActivity(
  events: TelemetryEvent[],
  busy: boolean,
  traceId: string | null,
) {
  if (!busy)
    return traceId
      ? events.filter((event) => event.traceId === traceId)
      : events;
  const received = events.findLast(
    (event) => event.eventType === "request.received",
  );
  if (!received) return [];
  const current = events.filter((event) => event.traceId === received.traceId);
  // Until the new request reaches the API, the latest visible request may still
  // be the previous completed turn. Do not present its tools as current work.
  return current.some((event) => event.eventType === "request.finished")
    ? []
    : current;
}
