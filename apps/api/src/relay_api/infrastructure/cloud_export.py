"""Export the authoritative event journal with a durable, at-least-once cursor.

Run as a separate process so credential refresh or Google outages cannot hold up
customer requests. Cloud credentials come from ADC, never the Gemini API key.
"""

import hashlib
import json
import os
import re
import signal
from pathlib import Path
import sqlite3
import threading
from contextlib import closing
from datetime import datetime, timedelta


def span_id(value):
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def span(project, event):
    trace = event["traceId"].removeprefix("TRACE-")
    if not re.fullmatch(r"[a-f0-9]{32}", trace):
        return None
    if event["eventType"] not in {"request.finished", "tool.finished", "ai.finished"}:
        return None
    root = event["eventType"] == "request.finished"
    identifier = span_id(event["traceId"] if root else event["eventId"])
    end = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    result = {
        "name": f"projects/{project}/traces/{trace}/spans/{identifier}",
        "spanId": identifier,
        "displayName": {"value": event["component"] + ":" + event["eventType"]},
        "startTime": (end - timedelta(milliseconds=event["durationMs"])).isoformat(),
        "endTime": end.isoformat(),
        "status": {"code": 13 if event["status"] == "failure" else 0},
    }
    if not root:
        result["parentSpanId"] = span_id(event["traceId"])
    return result


class CloudSink:
    def __init__(self, project, session=None):
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", project):
            raise ValueError("valid_google_cloud_project_required")
        self.project = project
        if session is None:
            import google.auth
            from google.auth.transport.requests import AuthorizedSession

            credentials, _ = google.auth.default(
                scopes=[
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/trace.append",
                ]
            )
            session = AuthorizedSession(credentials)
        self.session = session

    def send(self, events):
        entries = []
        spans = []
        for event in events:
            entry = {
                "insertId": event["eventId"],
                "timestamp": event["timestamp"],
                "severity": "ERROR" if event["status"] == "failure" else "INFO",
                "jsonPayload": event,
            }
            trace = event["traceId"].removeprefix("TRACE-")
            if re.fullmatch(r"[a-f0-9]{32}", trace):
                entry["trace"] = f"projects/{self.project}/traces/{trace}"
            entries.append(entry)
            converted = span(self.project, event)
            if converted:
                spans.append(converted)
        self.session.post(
            "https://logging.googleapis.com/v2/entries:write",
            json={
                "logName": f"projects/{self.project}/logs/relay-cx",
                "resource": {"type": "global", "labels": {"project_id": self.project}},
                "entries": entries,
            },
            timeout=10,
        ).raise_for_status()
        if spans:
            self.session.post(
                f"https://cloudtrace.googleapis.com/v2/projects/{self.project}/traces:batchWrite",
                json={"spans": spans},
                timeout=10,
            ).raise_for_status()


def export_batch(database, sink):
    # Never create a missing application database or advance past a failed batch.
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + "?mode=rw", uri=True, timeout=3)) as db:
        db.execute("CREATE TABLE IF NOT EXISTS cloud_export (project TEXT PRIMARY KEY, seq INTEGER)")
        row = db.execute("SELECT seq FROM cloud_export WHERE project=?", (sink.project,)).fetchone()
        cursor = row[0] if row else 0
        records = db.execute(
            "SELECT seq,body FROM events WHERE seq>? ORDER BY seq LIMIT 50", (cursor,)
        ).fetchall()
        db.commit()
    if not records:
        return 0
    sink.send([json.loads(body) for _, body in records])
    with (
        closing(sqlite3.connect(Path(database).resolve().as_uri() + "?mode=rw", uri=True, timeout=3)) as db,
        db,
    ):
        db.execute(
            "INSERT INTO cloud_export VALUES (?,?) ON CONFLICT(project) DO UPDATE SET seq=MAX(seq,excluded.seq)",
            (sink.project, records[-1][0]),
        )
    return len(records)


def main():
    database = os.getenv("DATABASE_PATH", "/app/data/relay.sqlite")
    if not Path(database).is_file():
        raise ValueError("application_database_required")
    sink = CloudSink(os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    failures = 0
    while not stop.is_set():
        try:
            count = export_batch(database, sink)
            failures = 0
            if not count:
                stop.wait(2)
        except Exception:
            failures += 1
            print(json.dumps({"event": "cloud.export_failed", "attempt": failures}), flush=True)
            if failures >= 3:
                raise SystemExit(1)
            stop.wait(2**failures)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"event": "cloud.export_configuration_failed"}), flush=True)
        raise SystemExit(1)
