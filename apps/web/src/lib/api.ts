export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T>(path: string, data?: unknown): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    method: data === undefined ? "GET" : "POST",
    headers:
      data === undefined ? undefined : { "Content-Type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data),
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (
      response.status === 401 &&
      !["login", "session"].includes(path) &&
      typeof window !== "undefined"
    )
      window.dispatchEvent(new Event("relay:session-expired"));
    const raw = payload.error ?? payload.detail;
    const messages: Record<string, string> = {
      authentication_failed:
        "Those details didn’t match. Check your username and password.",
      authentication_required: "Your session has ended. Please sign in again.",
      origin_denied:
        "This browser address is not configured. Open localhost:3000 or 127.0.0.1:3000 for the local stack.",
      access_denied: "This account doesn’t have access to that workspace.",
      support_role_required:
        "Sign in with the support representative account to continue.",
      enterprise_unavailable:
        "An account service is temporarily unavailable. Please try again.",
      upstream_unavailable:
        "We couldn’t reach the resolution service. Please try again.",
      login_rate_limited:
        "Too many sign-in attempts. Please wait a minute and try again.",
    };
    throw new ApiError(
      response.status,
      messages[String(raw)] ??
        "We couldn’t complete that request. Please try again.",
    );
  }
  return payload as T;
}
export const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
export const titleCase = (value: string) =>
  value.replaceAll(/[_-]/g, " ").replace(/\b\w/g, (s) => s.toUpperCase());
