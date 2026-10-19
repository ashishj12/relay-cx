from unittest.mock import Mock
import json
import sqlite3
import pytest
from relay_api.infrastructure.cloud_export import CloudSink, export_batch
from relay_mock.state import SyntheticState


def test_cloud_export_uses_real_correlated_journal_and_advances_only_on_success(stack, customer):
    service = stack[0]
    session = Mock()
    session.post.return_value.raise_for_status.return_value = None
    sink = CloudSink("synthetic-review-project", session=session)
    service.store.emit(
        "request.finished", "TRACE-" + "a" * 32, customer["id"], duration=100, password="SYNTHETIC_CANARY"
    )
    session.post.return_value.raise_for_status.side_effect = RuntimeError("unavailable")
    with pytest.raises(RuntimeError):
        export_batch(service.store.path, sink)
    with sqlite3.connect(service.store.path) as db:
        assert not db.execute("SELECT * FROM cloud_export").fetchall()
    session.post.return_value.raise_for_status.side_effect = None
    count = export_batch(service.store.path, sink)
    assert count > 0 and export_batch(service.store.path, sink) == 0
    logs = [call for call in session.post.call_args_list if "logging.googleapis.com" in call.args[0]]
    payload = logs[-1].kwargs["json"]
    assert "SYNTHETIC_CANARY" not in json.dumps(payload)
    entry = payload["entries"][-1]
    assert entry["insertId"] and entry["trace"].endswith("a" * 32)
    traces = [call for call in session.post.call_args_list if "cloudtrace.googleapis.com" in call.args[0]]
    span = traces[-1].kwargs["json"]["spans"][-1]
    assert len(span["spanId"]) == 16 and span["startTime"] < span["endTime"]
    assert traces[-1].kwargs["timeout"] == 10


def test_synthetic_receipts_and_hashed_tokens_survive_storage_reopen(tmp_path):
    path = tmp_path / "enterprise.sqlite"
    first = SyntheticState(path)
    token = "synthetic-bearer-canary"
    first.issue(token, "CUST-1001", 10000000000)
    receipt = dict(
        customerId="CUST-1001",
        accountId="ACC-2001",
        idempotencyKey="ACT-" + "a" * 32,
        caseId="CASE-ABC",
        status="open",
        summary="Connection problem",
    )
    assert first.create(receipt)
    reopened = SyntheticState(path)
    assert reopened.identity(token) == ("CUST-1001", 10000000000)
    assert reopened.receipt("CUST-1001", receipt["idempotencyKey"]) == receipt
    assert not reopened.create({**receipt, "caseId": "CASE-DEF"})
    assert reopened.receipt("CUST-1002", receipt["idempotencyKey"]) is None
    assert token.encode() not in path.read_bytes()
