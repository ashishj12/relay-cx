import os
import re
from relay_api.domain.models import Interpretation


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
    text = re.sub(r"(?i)(password|token|secret|api[_ -]?key)\s*[:=]?\s*\S+", r"\1 [REDACTED]", text)
    text = re.sub(r"ReviewerPass-\S+", "[REDACTED]", text)
    text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[EMAIL]", text, flags=re.I)
    return text


class Reviewer:
    def interpret(self, messages):
        m = " ".join(messages[-2:]).lower()
        service = (
            "home-internet"
            if any(w in m for w in ("internet", "broadband", "fiber"))
            else "mobile"
            if "mobile" in m
            else "unknown"
        )
        intent = "unknown"
        if any(w in m for w in ("human", "agent", "escalate")):
            intent = "handoff"
        elif any(w in m for w in ("case", "ticket")):
            intent = "case"
        elif any(w in m for w in ("legacy", "subscriber")):
            intent = "legacy"
        elif any(w in m for w in ("bill", "charge", "invoice")):
            intent = "billing"
        elif any(w in m for w in ("not working", "unavailable", "slow", "outage", "down")):
            intent = "network"
        elif any(w in m for w in ("plan", "account", "subscription")):
            intent = "account"
        return Interpretation(intent=intent, service=service, confidence=1.0)

    def select(self, facts):
        return list(range(len(facts)))
