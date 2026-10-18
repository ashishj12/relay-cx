"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TelemetryEvent } from "@/lib/types";

export function useActivity(busy: boolean, traceId: string | null) {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const events = await api<TelemetryEvent[]>("activity");
        if (!cancelled) setEvents(events);
      } catch {
        /* The conversation owns request errors; an activity read never blocks it. */
      }
    }
    refresh();
    const interval = busy ? window.setInterval(refresh, 900) : undefined;
    return () => {
      cancelled = true;
      if (interval) window.clearInterval(interval);
    };
  }, [busy, traceId]);
  return traceId && !busy
    ? events.filter((event) => event.traceId === traceId)
    : events;
}
