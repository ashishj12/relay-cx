from copy import deepcopy
import time
from typing import TYPE_CHECKING
from relay_api.domain.models import Confirmation
from relay_api.infrastructure.enterprise import Denied, IntegrationError
from relay_api.infrastructure.storage import uid

if TYPE_CHECKING:
    from relay_api.application.workflows import ResolutionService


class CaseActions:
    def __init__(self, workflow: "ResolutionService") -> None:
        self.workflow = workflow

    def confirm(self, session: dict, data: Confirmation) -> dict:
        with self.workflow.store.lock:
            trace_id = uid("TRACE")
            start = time.monotonic()
            self.workflow.store.emit("request.received", trace_id, session["id"])
            session["state"] = "NEW"
            session["facts"] = []
            self.workflow.state(session, trace_id, "AUTHORIZATION_CHECK")
            try:
                self.workflow.gateway.authorize(session, session.get("accountId"), trace_id)
            except Denied:
                session["state"] = "FAILED"
                return self.workflow.finish(
                    session, trace_id, start, {"answer": "Account access denied."}, True
                )
            action = session.get("pending")
            durable = self.workflow.store.session_by_id(session["id"])
            durable_action = (durable or {}).get("pending") or {}
            if durable_action.get("id") == data.actionId and durable_action.get("status") != "pending":
                session["pending"] = deepcopy(durable_action)
                action = session["pending"]
            if not action or action["id"] != data.actionId:
                self.workflow.store.emit(
                    "confirmation.rejected",
                    trace_id,
                    session["id"],
                    status="denied",
                    reason="action_mismatch",
                )
                session["state"] = "FAILED"
                return self.workflow.finish(
                    session,
                    trace_id,
                    start,
                    {"answer": "Confirmation does not match a pending action."},
                    True,
                )
            self.workflow.store.emit(
                "confirmation.received",
                trace_id,
                session["id"],
                actionId=action["id"],
                confirmed=data.confirm,
                replay=action["status"] == "completed",
            )
            if action["status"] == "completed":
                self.workflow.state(session, trace_id, "RESOLVED")
                return self.workflow.finish(
                    session,
                    trace_id,
                    start,
                    {
                        "answer": "This action was already completed. Case " + action["caseId"],
                        "caseId": action["caseId"],
                    },
                )
            if action["status"] != "pending" or time.time() - action["created"] > 600:
                session["state"] = "FAILED"
                return self.workflow.finish(
                    session,
                    trace_id,
                    start,
                    {
                        "answer": "This action cannot be retried. Request human reconciliation or a new proposal."
                    },
                    True,
                )
            if not data.confirm:
                action["status"] = "cancelled"
                self.workflow.state(session, trace_id, "RESOLVED")
                self.workflow.store.emit("action.cancelled", trace_id, session["id"])
                return self.workflow.finish(
                    session, trace_id, start, {"answer": "Case creation cancelled. No case was submitted."}
                )
            self.workflow.state(session, trace_id, "EXECUTING_ACTION")
            action["status"] = "executing"
            action["confirmedAt"] = time.time()
            self.workflow.store.save(session)
            try:
                case = self.workflow.gateway.create_case(session, trace_id, action)
                self.workflow.state(session, trace_id, "VERIFYING_ACTION")
                action.update(status="completed", caseId=case.caseId)
                self.workflow.state(session, trace_id, "RESOLVED")
                self.workflow.store.emit("workflow.resolved", trace_id, session["id"])
                self.workflow.store.emit("action.completed", trace_id, session["id"], caseId=case.caseId)
                return self.workflow.finish(
                    session,
                    trace_id,
                    start,
                    {"answer": "Support case " + case.caseId + " is open.", "caseId": case.caseId},
                )
            except IntegrationError as error:
                action["status"] = "uncertain"
                return self.workflow.finish(
                    session,
                    trace_id,
                    start,
                    self.workflow.escalation(session, trace_id, error.service + ":" + error.reason),
                    True,
                )
            except Exception:
                return self.workflow.internal_failure(session, trace_id, start)
