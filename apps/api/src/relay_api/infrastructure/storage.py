import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from relay_api.ai.providers import redact
from relay_api.core.config import CHALLENGE_ROOT


def uid(prefix):
    return prefix + "-" + uuid.uuid4().hex


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


class WorkflowBusy(Exception):
    """Admission is bounded independently of model and network deadlines."""

    def __init__(self, duration=0):
        self.duration = duration


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._workflows = {}
        self._admission = threading.BoundedSemaphore(8)
        self._local = threading.local()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, expires REAL, data TEXT);
        CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, body TEXT);
        CREATE TABLE IF NOT EXISTS escalations (id TEXT PRIMARY KEY, session TEXT, body TEXT);
        CREATE TABLE IF NOT EXISTS telemetry_rejections (timestamp TEXT, reason TEXT);
        CREATE INDEX IF NOT EXISTS events_trace ON events(json_extract(body, '$.traceId'));
        CREATE INDEX IF NOT EXISTS events_session ON events(json_extract(body, '$.sessionId'));
        CREATE TABLE IF NOT EXISTS actions (
            id TEXT PRIMARY KEY, customer TEXT, account TEXT, status TEXT, body TEXT
        );
        CREATE INDEX IF NOT EXISTS actions_account ON actions(customer, account, status);
        CREATE TABLE IF NOT EXISTS conversations (subject TEXT PRIMARY KEY, body TEXT);
        """)
        # Backfill old session-local markers before allowing a fresh login.
        with self.db:
            for (body,) in self.db.execute("SELECT data FROM sessions").fetchall():
                s = json.loads(body)
                if s.get("pending"):
                    self._save_action(s)
        schema = CHALLENGE_ROOT / "schemas/telemetry-event.schema.json"
        self.validator = Draft202012Validator(json.loads(schema.read_text()), format_checker=FormatChecker())
        self.log_path = Path(os.getenv("STRUCTURED_LOG_PATH", str(Path(path).parent / "events.jsonl")))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def workflow(self, session, wait=2.0):
        if getattr(self._local, "inside", False):
            yield
            return
        key = (session.get("customerId"), session.get("accountId"))
        started = time.monotonic()
        with self.lock:
            lock = self._workflows.setdefault(key, threading.RLock())
        if not self._admission.acquire(timeout=wait):
            raise WorkflowBusy((time.monotonic() - started) * 1000)
        acquired = False
        try:
            acquired = lock.acquire(timeout=wait)
            if not acquired:
                raise WorkflowBusy((time.monotonic() - started) * 1000)
            self._local.inside = True
            yield
        finally:
            self._local.inside = False
            if acquired:
                lock.release()
            self._admission.release()

    def _save_action(self, s):
        action = s["pending"]
        row = self.db.execute("SELECT status,body FROM actions WHERE id=?", (action["id"],)).fetchone()
        allowed = {
            "pending": {"pending", "executing", "cancelled", "expired"},
            "executing": {"executing", "completed", "uncertain"},
            "uncertain": {"uncertain", "completed"},
        }
        if row and action["status"] not in allowed.get(row[0], {row[0]}):
            s["pending"] = json.loads(row[1])
            return
        self.db.execute(
            "INSERT OR REPLACE INTO actions VALUES (?,?,?,?,?)",
            (action["id"], s["customerId"], s.get("accountId"), action["status"], json.dumps(action)),
        )

    def outstanding_action(self, s):
        with self.lock:
            row = self.db.execute(
                "SELECT body FROM actions WHERE customer=? AND account=? "
                "AND status IN ('pending','executing','uncertain') "
                "ORDER BY CASE status WHEN 'uncertain' THEN 0 WHEN 'executing' THEN 1 ELSE 2 END, rowid DESC LIMIT 1",
                (s["customerId"], s.get("accountId")),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def action(self, s, action_id):
        with self.lock:
            row = self.db.execute(
                "SELECT body FROM actions WHERE id=? AND customer=? AND account=?",
                (action_id, s["customerId"], s.get("accountId")),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def account_context(self, s):
        with self.lock:
            row = self.db.execute(
                "SELECT body FROM conversations WHERE subject=?",
                (s["customerId"] + ":" + str(s.get("accountId")),),
            ).fetchone()
        return json.loads(row[0]) if row else {}

    def save(self, s):
        with self.lock, self.db:
            if s.get("pending"):
                self._save_action(s)
            self.db.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?,?,?)", (s["id"], s["expires"], json.dumps(s))
            )
            if s.get("history"):
                context = {
                    key: list(s.get(key) or [])
                    for key in ("history", "messages", "verifiedEvidence", "completedSteps")
                }
                self.db.execute(
                    "INSERT OR REPLACE INTO conversations VALUES (?,?)",
                    (s["customerId"] + ":" + str(s.get("accountId")), json.dumps(context)),
                )

    def session(self, token):
        return self.session_by_id(digest(token))

    def session_by_id(self, session_id):
        with closing(sqlite3.connect(self.path)) as reader:
            row = reader.execute("SELECT data FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            return None
        s = json.loads(row[0])
        return s if s["expires"] > time.time() else None

    def emit(self, kind, trace, session, status="success", component="orchestrator", duration=0, **metadata):
        event = dict(
            eventId=uid("EVT"),
            traceId=trace,
            sessionId=session,
            timestamp=datetime.now(timezone.utc).isoformat(),
            eventType=kind,
            component=component,
            status=status,
            durationMs=max(0, duration),
            metadata=metadata,
        )
        if not self.ingest(event):
            raise ValueError("invalid_internal_telemetry_event")
        return event

    def ingest(self, event):
        """Reject invalid events without storing their potentially sensitive payloads."""

        def sanitize(value, key=""):
            if any(word in key.lower() for word in ("password", "token", "secret", "api_key", "apikey")):
                return "[REDACTED]"
            if isinstance(value, dict):
                return {k: sanitize(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [sanitize(v) for v in value]
            return redact(value) if isinstance(value, str) else value

        try:
            event = sanitize(event)
            self.validator.validate(event)
            encoded = json.dumps(event, allow_nan=False)
        except Exception:
            # Only a category is retained, never raw invalid input or exception text.
            with self.lock, self.db:
                self.db.execute(
                    "INSERT INTO telemetry_rejections VALUES (?,?)",
                    (datetime.now(timezone.utc).isoformat(), "invalid_event_schema"),
                )
            return False
        with self.lock, self.db:
            self.db.execute("INSERT INTO events(body) VALUES (?)", (encoded,))
            try:
                with self.log_path.open("a", encoding="utf-8") as log:
                    log.write(encoded + "\n")
            except OSError:
                pass  # SQLite remains the authoritative event sink if file logging fails.
        return True

    def events(self):
        with closing(sqlite3.connect(self.path)) as reader:
            return [json.loads(row[0]) for row in reader.execute("SELECT body FROM events ORDER BY seq")]

    def trace_events(self, trace_id, session_id=None):
        query = "SELECT body FROM events WHERE json_extract(body, '$.traceId')=?"
        params = [trace_id]
        if session_id is not None:
            query += (
                " AND json_extract(body, '$.sessionId') IN ("
                "SELECT id FROM sessions WHERE id=? OR ("
                "json_extract(data,'$.customerId')=(SELECT json_extract(data,'$.customerId') FROM sessions WHERE id=?) "
                "AND json_extract(data,'$.accountId')=(SELECT json_extract(data,'$.accountId') FROM sessions WHERE id=?)))"
            )
            params.extend([session_id, session_id, session_id])
        with closing(sqlite3.connect(self.path)) as reader:
            return [json.loads(row[0]) for row in reader.execute(query + " ORDER BY seq", params)]

    def recent_events(self, session_id, limit=60):
        """Independent WAL reads let a browser observe an in-flight request."""
        with closing(sqlite3.connect(self.path)) as reader:
            rows = reader.execute(
                "SELECT body FROM events WHERE json_extract(body, '$.sessionId')=? ORDER BY seq DESC LIMIT ?",
                (session_id, min(100, max(1, limit))),
            ).fetchall()
        return [json.loads(row[0]) for row in reversed(rows)]

    def escalate(self, session, record):
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO escalations VALUES (?,?,?)",
                (record["escalationId"], session, json.dumps(record)),
            )

    def escalations(self):
        with self.lock:
            return [(r[0], json.loads(r[1])) for r in self.db.execute("SELECT session,body FROM escalations")]

    def metrics(self):
        events = self.events()

        def count(kind):
            return sum(e["eventType"] == kind for e in events)

        requests = count("request.received")
        tools = [e for e in events if e["eventType"] == "tool.finished"]
        ai = [e for e in events if e["eventType"] == "ai.finished"]
        finished = [e for e in events if e["eventType"] == "request.finished"]

        def ratio(n, d):
            return n / d if d else 0

        with self.lock:
            rejected = self.db.execute("SELECT COUNT(*) FROM telemetry_rejections").fetchone()[0]
        return dict(
            window="all persisted events since database initialization",
            telemetryRejected=rejected,
            sessions=count("session.created"),
            requests=requests,
            resolutionRate=ratio(count("workflow.resolved"), requests),
            escalationRate=ratio(count("workflow.escalated"), requests),
            failureRate=ratio(sum(e["status"] == "failure" for e in finished), requests),
            averageWorkflowMs=ratio(sum(e["durationMs"] for e in finished), len(finished)),
            toolSuccessRate=ratio(sum(e["status"] == "success" for e in tools), len(tools)),
            failuresByIntegration={
                name: sum(e["status"] == "failure" and e["component"] == name for e in tools)
                for name in {e["component"] for e in tools}
            },
            authenticationFailures=count("authentication.failed"),
            authorizationDenials=count("authorization.denied"),
            geminiFailures=sum(e["status"] == "failure" for e in ai),
            geminiLatencyMs=ratio(sum(e["durationMs"] for e in ai), len(ai)),
            retries=count("tool.retry"),
            retryRate=ratio(count("tool.retry"), len(tools)),
            humanHandoffRate=ratio(count("workflow.escalated"), requests),
            toolUsage={
                name: sum(e["component"] == name for e in tools) for name in {e["component"] for e in tools}
            },
            agentUsage={
                name: sum(e["component"] == name for e in events if e["eventType"] == "agent.invoked")
                for name in {e["component"] for e in events if e["eventType"] == "agent.invoked"}
            },
        )
