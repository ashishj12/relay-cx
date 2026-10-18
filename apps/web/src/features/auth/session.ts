import type { Session } from "@/lib/types";

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** The network boundary is untyped even when the caller uses TypeScript. */
export function decodeSession(value: unknown): Session {
  if (
    !record(value) ||
    typeof value.customerId !== "string" ||
    !(value.accountId === null || typeof value.accountId === "string") ||
    !Array.isArray(value.roles) ||
    !value.roles.every(
      (role) => role === "customer" || role === "support-agent",
    ) ||
    !["REVIEWER", "LIVE_AI", "DEGRADED"].includes(String(value.mode)) ||
    typeof value.state !== "string" ||
    !Array.isArray(value.history) ||
    !value.history.every(
      (item) =>
        record(item) &&
        ["user", "assistant"].includes(String(item.role)) &&
        typeof item.text === "string",
    ) ||
    !(
      value.pendingAction === null ||
      (record(value.pendingAction) &&
        typeof value.pendingAction.id === "string" &&
        typeof value.pendingAction.status === "string")
    )
  ) {
    throw new Error(
      "The server returned an incomplete session. Please retry sign-in.",
    );
  }
  return value as Session;
}
