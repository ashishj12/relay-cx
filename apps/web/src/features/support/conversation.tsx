"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUp,
  ArrowUpRight,
  Check,
  FileText,
  Headphones,
  MessageCircle,
  ShieldCheck,
  Wifi,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  Action,
  ChatResult,
  HistoryMessage,
  Mode,
  Overview,
  Session,
} from "@/lib/types";
import { ActivityPanel } from "./activity-panel";
import { useActivity } from "./use-activity";

const suggestions = [
  {
    icon: MessageCircle,
    title: "My current plan",
    description: "What’s included in my service?",
    request: "What plan am I currently using?",
  },
  {
    icon: FileText,
    title: "A question about my bill",
    description: "Understand the charges.",
    request: "Show my billing details",
  },
  {
    icon: Wifi,
    title: "A connection problem",
    description: "Check what’s going on.",
    request: "My service is not working.",
  },
];

export function Conversation({
  session,
  onMode,
  onTrace,
}: {
  session: Session;
  onMode: (mode: Mode) => void;
  onTrace: (id: string) => void;
}) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [accountError, setAccountError] = useState("");
  const [messages, setMessages] = useState<HistoryMessage[]>(session.history);
  const [pending, setPending] = useState<Action | null>(
    session.pendingAction?.status === "pending" ? session.pendingAction : null,
  );
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [traceId, setTraceId] = useState<string | null>(
    session.history.filter((message) => message.traceId).at(-1)?.traceId ??
      null,
  );
  const log = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const events = useActivity(busy, traceId);
  const isCustomer = session.roles.includes("customer");

  useEffect(() => {
    if (!isCustomer) return;
    let cancelled = false;
    api<Overview>("account/overview")
      .then((value) => {
        if (!cancelled) setOverview(value);
      })
      .catch((error) => {
        if (!cancelled) setAccountError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [isCustomer, session.customerId]);
  useEffect(() => {
    if (log.current)
      log.current.scrollTo({ top: log.current.scrollHeight, behavior: "auto" });
  }, [messages, pending, busy]);

  function accept(result: ChatResult) {
    setMessages((messages) => [
      ...messages,
      { role: "assistant", text: result.answer, traceId: result.traceId },
    ]);
    setTraceId(result.traceId);
    onMode(result.mode);
    setPending(
      result.pendingAction?.status === "pending" ? result.pendingAction : null,
    );
  }
  async function send(request: string) {
    if (!request.trim() || busy) return;
    setBusy(true);
    setError("");
    setDraft("");
    setMessages((messages) => [
      ...messages,
      { role: "user", text: request.trim() },
    ]);
    try {
      accept(await api<ChatResult>("chat", { message: request.trim() }));
    } catch (error) {
      setError((error as Error).message);
      setDraft(request);
    } finally {
      setBusy(false);
      input.current?.focus();
    }
  }
  async function confirm(approved: boolean) {
    if (!pending || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await api<ChatResult>("confirm", {
        actionId: pending.id,
        confirm: approved,
      });
      setPending(null);
      accept(result);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function requestHumanSupport() {
    if (busy) return;
    setBusy(true);
    setError("");
    setMessages((messages) => [
      ...messages,
      { role: "user", text: "Request human support" },
    ]);
    try {
      accept(await api<ChatResult>("handoff", {}));
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
      input.current?.focus();
    }
  }
  if (!isCustomer)
    return (
      <div className="role-message">
        <Headphones size={24} />
        <h1>You’re in the support workspace.</h1>
        <p>
          Use Operations to investigate requests, or Evaluation to run the
          supplied scenarios. Sign in with a customer account to start a
          customer conversation.
        </p>
      </div>
    );

  return (
    <div className="support-page">
      <div className="support-intro">
        <span className="overline">YOUR RESOLUTION WORKSPACE</span>
        <h1>
          How can we help{overview ? `, ${overview.name.split(" ")[0]}` : ""}?
        </h1>
        <p>
          Ask about your plan, bill or connection. You can also review and
          approve a support case. Plan changes and new services aren't available
          here.
        </p>
      </div>
      <div className="account-ribbon">
        {overview ? (
          <>
            <span className="account-avatar">
              {overview.name
                .split(" ")
                .map((word) => word[0])
                .join("")}
            </span>
            <div>
              <strong>{overview.name}</strong>
              <span>{overview.account.accountId}</span>
            </div>
            <span className="ribbon-divider" />
            <div>
              <strong>{overview.account.plan.name}</strong>
              <span>
                {overview.account.plan.monthlyPrice.toFixed(2)} / month
              </span>
            </div>
            <span className="account-status">
              <span className="signal-dot" />
              {overview.account.status}
            </span>
            <button
              className="icon-button"
              aria-label="Inspect account verification"
              onClick={() => onTrace(overview.traceId)}
            >
              <ShieldCheck size={18} />
            </button>
          </>
        ) : (
          <span>{accountError || "Checking your account…"}</span>
        )}
      </div>
      <div className="conversation-grid">
        <section
          className="conversation-card"
          aria-label="Customer conversation"
        >
          <div className="conversation-heading">
            <span className="assistant-emblem">r</span>
            <div>
              <strong>Relay assistant</strong>
              <span>
                {busy ? "Working on your request" : "Account & service support"}
              </span>
            </div>
            <span className="private-label">
              <ShieldCheck size={14} /> Private conversation
            </span>
          </div>
          <div
            ref={log}
            className="conversation-log"
            role="log"
            aria-label="Support conversation"
            aria-live="polite"
          >
            {!messages.length ? (
              <div className="conversation-start">
                <span className="start-symbol">
                  <MessageCircle size={26} />
                </span>
                <h2>What would you like to sort out?</h2>
                <p>Tell us in your own words, or start with one of these.</p>
                <div className="request-options">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion.title}
                      onClick={() => send(suggestion.request)}
                    >
                      <suggestion.icon size={18} />
                      <span>
                        <strong>{suggestion.title}</strong>
                        <small>{suggestion.description}</small>
                      </span>
                      <ArrowUpRight size={16} />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={`${index}-${message.traceId ?? message.role}`}
                  className={`chat-message ${message.role}`}
                >
                  <span className="message-author">
                    {message.role === "user" ? "You" : "Relay"}
                  </span>
                  <p>{message.text}</p>
                  {message.traceId && (
                    <button
                      className="message-evidence"
                      onClick={() => onTrace(message.traceId!)}
                    >
                      View sources & execution <ArrowUpRight size={13} />
                    </button>
                  )}
                </div>
              ))
            )}
            {busy && (
              <div className="working-message" role="status">
                <span />
                <span />
                <span />
                <span>
                  {session.mode === "LIVE_AI"
                    ? "Checking your account and preparing a reply…"
                    : "Checking the next step…"}
                </span>
              </div>
            )}
            {pending && (
              <div className="confirmation-card">
                <span className="overline">APPROVAL REQUIRED</span>
                <h3>Create this support case?</h3>
                <p>{pending.summary}</p>
                <p>
                  This opens a support case. It does not change your plan or add
                  a paid service. No response time is available here.
                </p>
                <div className="confirmation-account">
                  <ShieldCheck size={14} />
                  {pending.accountId} · One support case
                </div>
                <div className="confirmation-actions">
                  <button
                    className="button primary"
                    onClick={() => confirm(true)}
                    disabled={busy}
                  >
                    <Check size={16} />
                    Confirm & create case
                  </button>
                  <button
                    className="button secondary"
                    onClick={() => confirm(false)}
                    disabled={busy}
                  >
                    <X size={15} />
                    Not now
                  </button>
                </div>
              </div>
            )}
          </div>
          {error && (
            <div className="conversation-error" role="alert">
              {error}
            </div>
          )}
          <form
            className="composer"
            onSubmit={(event) => {
              event.preventDefault();
              send(draft);
            }}
          >
            <label htmlFor="support-message" className="sr-only">
              Your support request
            </label>
            <textarea
              id="support-message"
              ref={input}
              placeholder="Tell us what’s going on…"
              value={draft}
              maxLength={2000}
              disabled={busy}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  send(draft);
                }
              }}
            />
            <button
              aria-label="Send support request"
              disabled={busy || !draft.trim()}
            >
              <ArrowUp size={20} />
            </button>
            <div className="composer-caption">
              <span>Enter to send · Shift + Enter for a new line</span>
              <span>{draft.length}/2000</span>
            </div>
          </form>
          <div className="conversation-footer">
            <ShieldCheck size={13} />
            <span>
              Only your account can be checked. Please don’t send passwords or
              card details.
            </span>
          </div>
        </section>
        <div className="support-aside">
          <details>
            <summary>How your information is checked</summary>
            <ActivityPanel
              events={events}
              busy={busy}
              traceId={traceId}
              onTrace={onTrace}
            />
          </details>
          <div className="human-support">
            <Headphones size={19} />
            <h3>Need a person?</h3>
            <p>
              Save your conversation for review, even when the assistant is
              unavailable. This demo doesn't contact a live support team.
            </p>
            <button
              className="text-link"
              onClick={requestHumanSupport}
              disabled={busy}
            >
              Request human support <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
