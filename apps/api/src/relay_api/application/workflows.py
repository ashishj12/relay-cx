import os
from copy import deepcopy
import re
import secrets
import time
from relay_api.infrastructure.enterprise import Gateway, Denied, IntegrationError
from relay_api.ai.providers import LiveAiUnavailable, Reviewer, redact, provider_reason
from relay_api.agents.runtime import AdkProvider
from relay_api.application.evidence import EnterpriseEvidence, ServiceNotOnAccount
from relay_api.infrastructure.storage import Store, digest, uid

TRANSITIONS = {
    "NEW": {"INTERPRETING", "AUTHORIZATION_CHECK"},
    "INTERPRETING": {"NEEDS_CLARIFICATION", "AUTHORIZATION_CHECK", "ESCALATED"},
    "AUTHORIZATION_CHECK": {
        "FETCHING_ENTERPRISE_DATA",
        "EXECUTING_ACTION",
        "RESOLVED",
        "FAILED",
        "ESCALATED",
    },
    "FETCHING_ENTERPRISE_DATA": {
        "ANALYZING_RESULTS",
        "AWAITING_CONFIRMATION",
        "NEEDS_CLARIFICATION",
        "ESCALATED",
    },
    "ANALYZING_RESULTS": {"RESOLVED", "ESCALATED"},
    "EXECUTING_ACTION": {"VERIFYING_ACTION", "ESCALATED"},
    "VERIFYING_ACTION": {"RESOLVED", "ESCALATED"},
}


class ResolutionService:
    def overview(self, session):
        """An independent authorized read; never changes an in-flight chat/action."""
        with self.store.lock:
            context = deepcopy(session)
            context["state"] = "NEW"
            trace = uid("TRACE")
            start = time.monotonic()
            self.store.emit("request.received", trace, context["id"])
            try:
                self.state(context, trace, "AUTHORIZATION_CHECK")
                self.gateway.authorize(context, context.get("accountId"), trace)
                self.state(context, trace, "FETCHING_ENTERPRISE_DATA")
                profile = self.gateway.profile(context, trace)
                account = self.gateway.account(context, trace, context["accountId"])
                self.state(context, trace, "ANALYZING_RESULTS")
                self.state(context, trace, "RESOLVED")
                self.store.emit("workflow.resolved", trace, context["id"])
                self.store.emit(
                    "request.finished", trace, context["id"], duration=(time.monotonic() - start) * 1000
                )
                return {
                    "name": profile.name,
                    "account": account.model_dump(),
                    "traceId": trace,
                    "source": "Enterprise account service",
                }
            except (Denied, IntegrationError):
                self.store.emit("workflow.failed", trace, context["id"], status="failure")
                self.store.emit(
                    "request.finished",
                    trace,
                    context["id"],
                    status="failure",
                    duration=(time.monotonic() - start) * 1000,
                )
                raise

    def __init__(self, database=None, base=None):
        self.mode = os.getenv("APP_MODE", "REVIEWER").upper()
        if self.mode not in ("REVIEWER", "LIVE_AI", "DEGRADED"):
            raise ValueError("Invalid APP_MODE")
        self.store = Store(database or os.getenv("DATABASE_PATH", "data/cx.sqlite"))
        self.gateway = Gateway(
            self.store,
            base or os.getenv("ENTERPRISE_API_BASE_URL", os.getenv("MOCK_API_BASE", "http://127.0.0.1:8090")),
            float(os.getenv("REQUEST_TIMEOUT", "2")),
            min(2, max(0, int(os.getenv("MAX_RETRIES", "1")))),
        )
        self.ai = AdkProvider() if self.mode == "LIVE_AI" else Reviewer()
        self.evidence = EnterpriseEvidence(self.gateway)

    def login(self, data):
        trace_id = uid("TRACE")
        anonymous = {"id": "anonymous"}
        self.store.emit("authentication.attempted", trace_id, "anonymous", status="pending")
        try:
            auth = self.gateway.login(data, trace_id, anonymous)
            if (
                "customer" in auth.roles and (not auth.accountId or not auth.customerId.startswith("CUST-"))
            ) or not auth.roles:
                raise IntegrationError("authentication", "invalid_identity")
            if auth.expiresIn <= 0:
                raise IntegrationError("authentication", "expired_identity")
        except IntegrationError:
            self.store.emit("authentication.failed", trace_id, "anonymous", status="failure")
            raise
        token = secrets.token_urlsafe(32)
        session = dict(
            id=digest(token),
            expires=time.time() + min(auth.expiresIn, 3600),
            customerId=auth.customerId,
            accountId=auth.accountId,
            roles=auth.roles,
            enterpriseToken=auth.accessToken,
            messages=[],
            history=[],
            completedSteps=[],
            state="NEW",
            pending=None,
            failures={},
            mode=self.mode,
        )
        self.store.save(session)
        self.store.emit("session.created", trace_id, session["id"])
        self.store.emit("authentication.succeeded", trace_id, session["id"])
        return token, session

    def state(self, session, trace_id, new_state):
        if new_state not in TRANSITIONS.get(session["state"], set()):
            raise RuntimeError("invalid_transition:" + session["state"] + "->" + new_state)
        previous_state = session["state"]
        session["state"] = new_state
        self.store.emit(
            "workflow.transition", trace_id, session["id"], previous=previous_state, current=new_state
        )

    def ai_call(self, session, trace_id, operation, data):
        if isinstance(self.ai, AdkProvider):
            self.ai.emit = lambda kind, **metadata: self.store.emit(kind, trace_id, session["id"], **metadata)
        provider = (
            "gemini"
            if self.mode == "LIVE_AI"
            else "reviewer"
            if self.mode == "REVIEWER"
            else "deterministic-fallback"
        )
        self.store.emit(
            "agent.invoked",
            trace_id,
            session["id"],
            component="request_router"
            if operation == "interpret" and isinstance(self.ai, AdkProvider)
            else provider,
            operation=operation,
            framework="google-adk" if isinstance(self.ai, AdkProvider) else "deterministic",
        )
        if self.mode == "DEGRADED":
            self.store.emit(
                "provider.fallback",
                trace_id,
                session["id"],
                reason="configured_degraded_mode",
                operation=operation,
            )
            session["mode"] = "DEGRADED"
            return getattr(Reviewer(), operation)(data)
        if self.mode == "REVIEWER" and session.get("failures", {}).get("gemini") != "unavailable":
            return getattr(Reviewer(), operation)(data)
        start = time.monotonic()
        try:
            if session.get("failures", {}).get("gemini") == "unavailable":
                raise TimeoutError("simulation")
            result = getattr(self.ai, operation)(data)
            self.store.emit(
                "ai.finished",
                trace_id,
                session["id"],
                component="gemini",
                duration=(time.monotonic() - start) * 1000,
                operation=operation,
                model=os.getenv("GEMINI_MODEL", "unconfigured"),
                simulated=False,
            )
            session["mode"] = "DEGRADED" if session.get("_ai_failed") else "LIVE_AI"
            return result
        except Exception as error:
            self.store.emit(
                "ai.finished",
                trace_id,
                session["id"],
                status="failure",
                component="gemini",
                duration=(time.monotonic() - start) * 1000,
                operation=operation,
                model=os.getenv("GEMINI_MODEL", "unconfigured"),
                reason=provider_reason(error),
                simulated=session.get("failures", {}).get("gemini") == "unavailable",
            )
            if self.mode == "LIVE_AI":
                session["mode"] = "DEGRADED"
                self.store.emit(
                    "provider.unavailable",
                    trace_id,
                    session["id"],
                    status="failure",
                    operation=operation,
                    reason=provider_reason(error),
                )
                raise LiveAiUnavailable(provider_reason(error)) from error
            self.store.emit(
                "provider.fallback",
                trace_id,
                session["id"],
                operation=operation,
                reason=provider_reason(error),
            )
            session["_ai_failed"] = True
            session["mode"] = "DEGRADED"
            return getattr(Reviewer(), operation)(data)

    def gather_evidence(self, session, trace_id, decision):
        cached = None

        def collect():
            nonlocal cached
            if cached is None:
                cached = self.evidence.collect(session, trace_id, decision)
            return cached

        if not isinstance(self.ai, AdkProvider):
            return collect(), None
        if session.get("_ai_failed"):
            bundle = collect()
            return bundle, list(range(len(bundle.facts)))
        self.ai.emit = lambda kind, **metadata: self.store.emit(kind, trace_id, session["id"], **metadata)
        started = time.monotonic()
        try:
            bundle, order = self.ai.gather(decision, collect, question=session["messages"][-1])
            self.store.emit(
                "ai.finished",
                trace_id,
                session["id"],
                component="gemini",
                operation="select",
                model=os.getenv("GEMINI_MODEL", "unconfigured"),
                simulated=False,
                framework="google-adk",
                duration=(time.monotonic() - started) * 1000,
            )
            return bundle, order
        except IntegrationError:
            raise
        except Exception as error:
            self.store.emit(
                "ai.finished",
                trace_id,
                session["id"],
                component="gemini",
                status="failure",
                operation="select",
                model=os.getenv("GEMINI_MODEL", "unconfigured"),
                simulated=False,
                reason=provider_reason(error),
                duration=(time.monotonic() - started) * 1000,
            )
            if self.mode == "LIVE_AI":
                session["mode"] = "DEGRADED"
                self.store.emit(
                    "provider.unavailable",
                    trace_id,
                    session["id"],
                    status="failure",
                    operation="select",
                    reason=provider_reason(error),
                )
                raise LiveAiUnavailable(provider_reason(error)) from error
            self.store.emit("provider.fallback", trace_id, session["id"], reason=provider_reason(error))
            session["_ai_failed"] = True
            session["mode"] = "DEGRADED"
            bundle = collect()
            return bundle, list(range(len(bundle.facts)))

    def escalation(self, session, trace_id, reason):
        steps = list(
            dict.fromkeys(
                session.get("completedSteps", [])
                + [
                    e["component"]
                    for e in self.store.events()
                    if e["traceId"] == trace_id
                    and e["eventType"] == "tool.finished"
                    and e["status"] == "success"
                ]
            )
        )
        events = [e for e in self.store.events() if e["traceId"] == trace_id]
        record = dict(
            escalationId=uid("ESC"),
            traceId=trace_id,
            customerId=session["customerId"],
            requestSummary="; ".join(
                turn["text"] for turn in session.get("history", []) if turn["role"] == "user"
            )[-4000:],
            completedSteps=steps,
            reason=reason,
            recommendedNextStep="Human support should inspect verified facts and integration status; reconcile uncertain actions before retrying.",
            pendingAction=session.get("pending"),
            facts=session.get("facts", []),
            priorVerifiedEvidence=session.get("verifiedEvidence", [])[-8:],
            verifiedContext={
                "accountId": session.get("accountId"),
                "identitySource": "synthetic-authentication-service",
            },
            failedTools=[
                {"component": e["component"], "reason": e["metadata"].get("reason", "integration_failure")}
                for e in events
                if e["eventType"] == "tool.finished" and e["status"] == "failure"
            ],
        )
        self.store.escalate(session["id"], record)
        self.state(session, trace_id, "ESCALATED")
        self.store.emit("workflow.escalated", trace_id, session["id"])
        return {
            "answer": "This request needs human review. No new successful action is claimed. Handoff "
            + record["escalationId"],
            "escalationId": record["escalationId"],
        }

    def finish(self, session, trace_id, start, result, failed=False):
        session["completedSteps"] = list(
            dict.fromkeys(
                session.get("completedSteps", [])
                + [
                    e["component"]
                    for e in self.store.events()
                    if e["traceId"] == trace_id
                    and e["eventType"] == "tool.finished"
                    and e["status"] == "success"
                ]
            )
        )
        session.setdefault("history", []).append(
            {"role": "assistant", "text": result["answer"], "traceId": trace_id}
        )
        session["history"] = session["history"][-40:]
        if session.get("facts"):
            session.setdefault("verifiedEvidence", []).append(
                {"traceId": trace_id, "verifiedAt": time.time(), "facts": list(session["facts"])}
            )
            session["verifiedEvidence"] = session["verifiedEvidence"][-8:]
        self.store.save(session)
        if failed:
            self.store.emit(
                "workflow.failed", trace_id, session["id"], status="failure", finalState=session["state"]
            )
        self.store.emit(
            "request.finished",
            trace_id,
            session["id"],
            status="failure" if failed else "success",
            duration=(time.monotonic() - start) * 1000,
        )
        return deepcopy(
            dict(
                traceId=trace_id,
                state=session["state"],
                mode=session["mode"],
                facts=session.get("facts", []),
                **result,
            )
        )

    def internal_failure(self, session, trace_id, start):
        self.store.emit(
            "processing.failed",
            trace_id,
            session["id"],
            status="failure",
            reason="internal_processing_failure",
        )
        if session.get("pending", {}) and session["pending"]["status"] == "executing":
            session["pending"]["status"] = "uncertain"
        return self.finish(
            session, trace_id, start, self.escalation(session, trace_id, "internal_processing_failure"), True
        )

    def chat(self, session, data):
        with self.store.lock:
            trace_id = uid("TRACE")
            start = time.monotonic()
            self.store.emit("request.received", trace_id, session["id"])
            previous = session["state"]
            session["state"] = "NEW"
            session["facts"] = []
            session["_ai_failed"] = False
            session.setdefault("completedSteps", [])
            message = redact(data.message)
            session.setdefault("history", []).append({"role": "user", "text": message})
            session["messages"] = (session["messages"][-3:] if previous == "NEEDS_CLARIFICATION" else []) + [
                message
            ]
            self.state(session, trace_id, "INTERPRETING")
            try:
                account_references = re.findall(r"\bACC-\d+\b", data.message.upper())
                for account in account_references + ([data.accountId] if data.accountId else []):
                    self.gateway.authorize(session, account, trace_id)
                decision = self.ai_call(session, trace_id, "interpret", session["messages"])
                intent = decision.intent
                self.store.emit(
                    "intent.classified",
                    trace_id,
                    session["id"],
                    intent=intent,
                    service=decision.service,
                    confidence=decision.confidence,
                    mode=session["mode"],
                )
                if (
                    decision.confidence < 0.6
                    or intent == "unknown"
                    or (intent == "network" and decision.service == "unknown")
                ):
                    self.state(session, trace_id, "NEEDS_CLARIFICATION")
                    self.store.emit(
                        "clarification.requested",
                        trace_id,
                        session["id"],
                        status="pending",
                        missingInformation="service_type"
                        if intent == "network"
                        else "supported_request_intent",
                    )
                    return self.finish(
                        session,
                        trace_id,
                        start,
                        {
                            "answer": "Which service is affected: home internet or mobile?"
                            if intent == "network"
                            else "Do you need plan information, billing, network diagnostics, subscriber status, or a support case?"
                        },
                    )
                if intent == "handoff":
                    return self.finish(
                        session,
                        trace_id,
                        start,
                        self.escalation(session, trace_id, "customer_requested_handoff"),
                    )
                self.state(session, trace_id, "AUTHORIZATION_CHECK")
                account = data.accountId or session.get("accountId")
                self.gateway.authorize(session, account, trace_id)
                self.state(session, trace_id, "FETCHING_ENTERPRISE_DATA")
                if intent == "case":
                    self.gateway.profile(session, trace_id)
                    self.gateway.account(session, trace_id, account)
                    existing = session.get("pending") or {}
                    if (
                        existing.get("status") == "completed"
                        and existing.get("summary") == message
                        and time.time() - existing["created"] < 600
                    ):
                        self.state(session, trace_id, "ANALYZING_RESULTS")
                        self.state(session, trace_id, "RESOLVED")
                        self.store.emit("action.replayed", trace_id, session["id"], caseId=existing["caseId"])
                        return self.finish(
                            session,
                            trace_id,
                            start,
                            {
                                "answer": "This request was already completed. Case " + existing["caseId"],
                                "caseId": existing["caseId"],
                            },
                        )
                    if existing.get("status") == "pending" and time.time() - existing["created"] > 600:
                        existing["status"] = "expired"
                        self.store.emit("action.expired", trace_id, session["id"], actionId=existing["id"])
                    if session.get("pending") and session["pending"]["status"] in (
                        "pending",
                        "executing",
                        "uncertain",
                    ):
                        action = session["pending"]
                    else:
                        action = dict(
                            id=uid("ACT"),
                            summary=message,
                            accountId=account,
                            status="pending",
                            created=time.time(),
                        )
                        session["pending"] = action
                    if action["status"] in ("executing", "uncertain"):
                        return self.finish(
                            session,
                            trace_id,
                            start,
                            self.escalation(session, trace_id, "prior_action_requires_reconciliation"),
                        )
                    self.state(session, trace_id, "AWAITING_CONFIRMATION")
                    self.store.emit(
                        "action.proposed", trace_id, session["id"], status="pending", actionId=action["id"]
                    )
                    self.store.emit(
                        "confirmation.requested",
                        trace_id,
                        session["id"],
                        status="pending",
                        actionId=action["id"],
                    )
                    return self.finish(
                        session,
                        trace_id,
                        start,
                        {
                            "answer": "Confirm creation of one support case for your account: "
                            + action["summary"],
                            "pendingAction": action,
                        },
                    )
                bundle, order = self.gather_evidence(session, trace_id, decision)
                facts = session["facts"] = bundle.facts
                if bundle.conflict:
                    return self.finish(
                        session, trace_id, start, self.escalation(session, trace_id, bundle.conflict)
                    )
                self.state(session, trace_id, "ANALYZING_RESULTS")
                if order is None:
                    order = self.ai_call(session, trace_id, "select", facts)
                answer = (
                    bundle.customer_reply
                    if isinstance(self.ai, AdkProvider)
                    else " ".join(facts[i] for i in order)
                )
                if not answer:
                    raise LiveAiUnavailable("invalid_model_output")
                self.state(session, trace_id, "RESOLVED")
                self.store.emit("workflow.resolved", trace_id, session["id"])
                return self.finish(session, trace_id, start, {"answer": answer})
            except LiveAiUnavailable as error:
                result = self.escalation(session, trace_id, "live_ai:" + error.reason)
                explanation = {
                    "provider_http_429": "Gemini is currently rate limited.",
                    "provider_timeout": "Gemini did not respond within the time limit.",
                    "configuration_missing": "Live AI is not configured.",
                    "invalid_model_output": "Gemini did not return a valid response.",
                }.get(error.reason, "Gemini is currently unavailable.")
                result["answer"] = (
                    explanation + " I couldn't complete your live AI request. "
                    "No fallback answer was used. Your request has been saved for review."
                )
                result["providerError"] = error.reason
                return self.finish(session, trace_id, start, result, True)
            except Denied:
                session["state"] = "FAILED"
                return self.finish(session, trace_id, start, {"answer": "Account access denied."}, True)
            except ServiceNotOnAccount as error:
                self.state(session, trace_id, "NEEDS_CLARIFICATION")
                self.store.emit(
                    "clarification.requested",
                    trace_id,
                    session["id"],
                    status="pending",
                    missingInformation="service_on_signed_in_account",
                    availableServices=error.available,
                )
                available = ", ".join(value.replace("-", " ") for value in error.available)
                requested = error.requested.replace("-", " ")
                return self.finish(
                    session,
                    trace_id,
                    start,
                    {
                        "answer": f"This account has {available} service, but no {requested} service. "
                        f"Did you mean {available}? To check {requested}, sign in with the account that owns it."
                    },
                )
            except IntegrationError as error:
                return self.finish(
                    session,
                    trace_id,
                    start,
                    self.escalation(session, trace_id, error.service + ":" + error.reason),
                    True,
                )
            except Exception:
                return self.internal_failure(session, trace_id, start)

    def confirm(self, session, data):
        from relay_api.application.case_actions import CaseActions

        return CaseActions(self).confirm(session, data)
