import os
import re
from relay_api.domain.models import Interpretation


class LiveAiUnavailable(Exception):
    """A live request must stop when its required model stage fails."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def provider_reason(error):
    if isinstance(error, TimeoutError):
        return "provider_timeout"
    if isinstance(error, ValueError):
        return (
            "configuration_missing" if str(error) == "live_configuration_missing" else "invalid_model_output"
        )
    code = getattr(error, "code", None)
    if code in (400, 401, 403, 408, 429, 500, 502, 503, 504):
        return "provider_http_" + str(code)
    return "provider_unavailable"


def redact(text):
    configured = os.getenv("GEMINI_API_KEY", "")
    if configured:
        text = text.replace(configured, "[REDACTED]")
    text = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_.~-]+", "Bearer [REDACTED]", text)
    text = re.sub(r"\b(?:AIza|AQ\.)[A-Za-z0-9_-]{20,}", "[REDACTED]", text)
    text = re.sub(
        r"(?i)\b(password|passcode|token|secret|api[_ -]?key)\b\s*[:=]\s*([\"'])([^\r\n]*?)\2",
        r"\1 [REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)\b(password|passcode|token|secret|api[_ -]?key)\b\s+(?:is|was|equals)\s+"
        r"[^;\r\n]+?(?=[.!?](?:\s|$)|$)",
        r"\1 [REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)\b(password|passcode|token|secret|api[_ -]?key)\b"
        r"\s*(?:(?:is|was|equals)\s+|[:=]\s*)?[\"']?[^\s,;\"']+",
        r"\1 [REDACTED]",
        text,
    )
    text = re.sub(r"ReviewerPass-\S+", "[REDACTED]", text)
    text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[EMAIL]", text, flags=re.I)
    return text


class Reviewer:
    def interpret(self, messages):
        def service_in(text):
            if re.search(r"\b(mobile|cellular)\b", text):
                return "mobile"
            if re.search(r"\b(internet|broadband|fiber)\b", text):
                return "home-internet"
            return "unknown"

        def intent_in(text):
            for intent, pattern in (
                ("handoff", r"\b(human|agent|escalate)\b"),
                ("case", r"\b(case|ticket)\b"),
                ("legacy", r"\b(legacy|subscriber)\b"),
                ("billing", r"\b(bill|billing|charge|charges|invoice)\b"),
                ("network", r"not working|unavailable|\b(slow|outage|down|dropping|disconnecting)\b"),
                ("account", r"\b(plan|account|subscription)\b"),
            ):
                if re.search(pattern, text):
                    return intent
            return "unknown"

        context = [message.lower() for message in messages[-4:]]
        latest = context[-1] if context else ""
        service = service_in(latest)
        if service == "unknown":
            service = next(
                (service_in(text) for text in reversed(context[:-1]) if service_in(text) != "unknown"),
                "unknown",
            )
        intent = intent_in(latest)
        followup = service_in(latest) != "unknown" or re.search(
            r"\b(that|it|same|again|details|more)\b", latest
        )
        if intent == "unknown" and followup:
            intent = next(
                (intent_in(text) for text in reversed(context[:-1]) if intent_in(text) != "unknown"),
                "unknown",
            )
        return Interpretation(intent=intent, service=service, confidence=1.0)

    def select(self, facts):
        return list(range(len(facts)))
