from dataclasses import dataclass
from typing import Any

from relay_api.domain.models import Interpretation
from relay_api.infrastructure.enterprise import Gateway, IntegrationError


@dataclass(frozen=True)
class EvidenceBundle:
    facts: list[str]
    conflict: str | None = None
    customer_reply: str | None = None


class ServiceNotOnAccount(IntegrationError):
    def __init__(self, requested: str, available: list[str]):
        super().__init__("account-service", "service_not_owned")
        self.requested = requested
        self.available = available


class EnterpriseEvidence:
    def __init__(self, gateway: Gateway) -> None:
        self.gateway = gateway

    def collect(self, session: dict[str, Any], trace_id: str, decision: Interpretation) -> EvidenceBundle:
        """Resolve identifiers from authenticated records, never model arguments."""
        profile = self.gateway.profile(session, trace_id)
        account = self.gateway.account(session, trace_id, session["accountId"])
        if decision.intent == "account":
            return EvidenceBundle(
                [
                    f"Account service: your plan is {account.plan.name}; monthly plan price "
                    f"{account.plan.monthlyPrice:.2f}; account status {account.status}."
                ]
            )
        if decision.intent == "billing":
            bill = self.gateway.billing(session, trace_id, account.accountId)
            return EvidenceBundle(
                [f"Billing service: {bill.period} total {bill.total:.2f}."]
                + [f"Billing item: {item.description}: {item.amount:.2f}." for item in bill.items]
            )
        service = next(
            (item for item in account.services if decision.service in ("unknown", item.type)), None
        )
        if service is None:
            raise ServiceNotOnAccount(decision.service, sorted({item.type for item in account.services}))
        facts: list[str] = []
        session["facts"] = facts
        outage = None
        if decision.intent == "network":
            outage = self.gateway.network(session, trace_id, profile)
            facts.append(f"Network service reports {outage.status}; incident {outage.incidentId or 'none'}.")
            diagnostic = self.gateway.diagnostics(session, trace_id, service.serviceId)
            if outage.estimatedRestoration:
                facts.append(f"Source restoration estimate (may be stale): {outage.estimatedRestoration}.")
            facts.append(f"Diagnostics: {diagnostic.result}.")
        legacy = self.gateway.legacy(session, trace_id, service.serviceId)
        facts.append(
            f"Legacy XML: subscriber {legacy['subscriberStatus']}; network {legacy['networkStatus']}; "
            f"observed {legacy['observedAt']}."
        )
        conflict = None
        if outage and (outage.status == "unknown" or outage.status != legacy["networkStatus"]):
            conflict = "conflicting_or_unknown_network_status"
        if service.status != legacy["subscriberStatus"]:
            conflict = "conflicting_subscriber_status"
        return EvidenceBundle(facts, conflict)
