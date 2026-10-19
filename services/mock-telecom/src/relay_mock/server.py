import hmac
import secrets
import threading
import json
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[4] / "resources/challenge"


def load(n):
    return json.loads((BASE / "sample-data" / n).read_text())


CUSTOMERS = load("customers.json")["customers"]
ACCOUNTS = load("accounts.json")["accounts"]
BILLING = load("billing.json")["billing"]
OUTAGES = load("network-status.json")["outages"]
CASES = {}
KEYS = {}
TOKENS = {}
CASE_LOCK = threading.Lock()


def find(xs, k, v):
    return next((x for x in xs if x.get(k) == v), None)


def load_legacy_records():
    # Keep an independent snapshot so discrepancies between the legacy system
    # and the network API remain visible during failure scenarios.
    records = {}
    for account in ACCOUNTS:
        customer = find(CUSTOMERS, "customerId", account["customerId"])
        network = find(OUTAGES, "postalCode", customer["postalCode"])
        for service in account["services"]:
            records[(account["accountId"], service["serviceId"])] = {
                "subscriberStatus": service["status"],
                "networkStatus": network["status"] if network else "unknown",
            }
    return records


LEGACY_RECORDS = load_legacy_records()


class H(BaseHTTPRequestHandler):
    def handle(self):
        try:
            super().handle()
        except ValueError:
            self.js(400, {"error": "invalid_request"})
        except (ConnectionError, TimeoutError):
            pass  # expected when a failure-simulation client times out

    def mode(self, service, default):
        if os.getenv("MOCK_ALLOW_FAILURES") == "true":
            try:
                overrides = json.loads(self.headers.get("X-Reviewer-Failures", "{}"))
                value = overrides.get(service)
                if value in ("normal", "success", "expired", "unavailable", "timeout", "malformed"):
                    return value
            except (ValueError, AttributeError):
                pass
        return os.getenv("MOCK_" + service.upper() + "_MODE", default)

    def js(self, c, o):
        b = json.dumps(o).encode()
        self.send_response(c)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", "0")))

    def identity(self):
        value = self.headers.get("Authorization", "")
        token = value.removeprefix("Bearer ") if value.startswith("Bearer ") else ""
        record = TOKENS.get(token)
        if not record or record["expires"] <= time.time():
            self.js(401, {"error": "enterprise_authentication_required"})
            return None
        return record["customer"]

    def owns(self, customer, *, account=None, service=None, postal=None, customer_id=None):
        allowed = (
            "customer" in customer["roles"]
            and (account is None or account == customer.get("accountId"))
            and (customer_id is None or customer_id == customer["customerId"])
        )
        if service is not None:
            record = find(ACCOUNTS, "accountId", customer.get("accountId")) or {}
            allowed = allowed and service in {s["serviceId"] for s in record.get("services", [])}
        if postal is not None:
            allowed = allowed and postal == customer.get("postalCode")
        if not allowed:
            self.js(403, {"error": "enterprise_access_denied"})
        return allowed

    def do_GET(self):
        p = urlparse(self.path)
        a = p.path.strip("/").split("/")
        if p.path == "/health":
            return self.js(200, {"status": "ok"})
        customer = self.identity()
        if customer is None:
            return
        if len(a) == 3 and a[:2] == ["api", "customers"]:
            if not self.owns(customer, customer_id=a[2]):
                return
            x = find(CUSTOMERS, "customerId", a[2])
            return (
                self.js(200, {k: v for k, v in x.items() if k not in {"username", "testPassword", "email"}})
                if x
                else self.js(404, {"error": "not_found"})
            )
        if len(a) == 3 and a[:2] == ["api", "accounts"]:
            if not self.owns(customer, account=a[2]):
                return
            x = find(ACCOUNTS, "accountId", a[2])
            return (
                self.js(200, {k: v for k, v in x.items() if k not in {"username", "testPassword", "email"}})
                if x
                else self.js(404, {"error": "not_found"})
            )
        if len(a) == 4 and a[:2] == ["api", "accounts"] and a[3] == "billing":
            if not self.owns(customer, account=a[2]):
                return
            m = self.mode("billing", "success")
            if m == "timeout":
                time.sleep(8)
            if m == "unavailable":
                return self.js(503, {"error": "billing_unavailable"})
            if m == "malformed":
                return self.js(200, {"unexpected": True})
            x = find(BILLING, "accountId", a[2])
            return (
                self.js(200, {k: v for k, v in x.items() if k not in {"username", "testPassword", "email"}})
                if x
                else self.js(404, {"error": "not_found"})
            )
        if p.path == "/api/network/outages":
            pc = parse_qs(p.query).get("postalCode", [""])[0]
            if not self.owns(customer, postal=pc):
                return
            return self.js(200, find(OUTAGES, "postalCode", pc) or {"postalCode": pc, "status": "unknown"})
        return self.js(404, {"error": "not_found"})

    def do_POST(self):
        p = urlparse(self.path)
        if p.path == "/api/auth/login":
            m = self.mode("auth", "normal")
            if m == "unavailable":
                return self.js(503, {"error": "auth_unavailable"})
            d = json.loads(self.body() or b"{}")
            c = next(
                (
                    x
                    for x in CUSTOMERS
                    if x.get("username") == d.get("username")
                    and hmac.compare_digest(
                        x.get("testPassword", "").encode("utf-8"), d.get("password", "").encode("utf-8")
                    )
                ),
                None,
            )
            if not c:
                return self.js(401, {"error": "invalid_credentials"})
            token = secrets.token_urlsafe(32)
            TOKENS[token] = {"customer": c, "expires": time.time() + (0 if m == "expired" else 3600)}
            return self.js(
                200,
                {
                    "accessToken": token,
                    "customerId": c["customerId"],
                    "accountId": c.get("accountId"),
                    "roles": c["roles"],
                    "expiresIn": 0 if m == "expired" else 3600,
                },
            )
        customer = self.identity()
        if customer is None:
            return
        if p.path == "/api/support-cases":
            # Consume the POST before replying, including simulated failures, to avoid TCP resets.
            body = self.body()
            if self.mode("case", "success") == "unavailable":
                return self.js(503, {"error": "case_unavailable"})
            d = json.loads(body or b"{}")
            if set(d) != {"customerId", "accountId", "summary", "idempotencyKey"}:
                return self.js(400, {"error": "invalid_case_request"})
            if not self.owns(customer, account=d.get("accountId"), customer_id=d.get("customerId")):
                return
            if not isinstance(d.get("summary"), str) or not 1 <= len(d["summary"]) <= 2000:
                return self.js(400, {"error": "invalid_case_summary"})
            k = d.get("idempotencyKey")
            if not k:
                return self.js(400, {"error": "idempotency_key_required"})
            with CASE_LOCK:
                key = (customer["customerId"], k)
                if key in KEYS:
                    return self.js(409, {"error": "duplicate", "caseId": KEYS[key]})
                cid = "CASE-" + uuid.uuid4().hex[:8].upper()
                KEYS[key] = cid
                CASES[cid] = {"caseId": cid, "status": "open", **d}
            return self.js(201, CASES[cid])
        if p.path == "/api/diagnostics":
            d = json.loads(self.body() or b"{}")
            if not self.owns(customer, service=d.get("serviceId", "")):
                return
            return self.js(
                200,
                {
                    "diagnosticId": "DIAG-" + uuid.uuid4().hex[:6].upper(),
                    "serviceId": d.get("serviceId"),
                    "result": "no_device_fault_detected",
                },
            )
        if p.path == "/api/legacy/subscriber-status":
            m = self.mode("legacy", "success")
            if m == "timeout":
                time.sleep(8)
            if m == "unavailable":
                return self.js(503, {"error": "legacy_unavailable"})
            if m == "malformed":
                raw = b"<SubscriberStatusResponse><BROKEN>"
            else:
                try:
                    r = ET.fromstring(self.body())
                    acct = r.findtext("AccountNumber")
                    svc = r.findtext("ServiceNumber")
                except Exception:
                    acct = svc = ""
                if not self.owns(customer, account=acct, service=svc):
                    return
                record = LEGACY_RECORDS[(acct, svc)]
                # Translate the authorized legacy record into its XML contract.
                response = ET.Element("SubscriberStatusResponse")
                fields = {
                    "ACCT_NO": acct,
                    "SVC_NO": svc,
                    "SVC_STAT": {"active": "A", "suspended": "S", "inactive": "I"}.get(
                        record["subscriberStatus"], "unknown"
                    ),
                    "NET_STAT": record["networkStatus"].upper(),
                    "ERR_CD": "0",
                    "RESP_TS": "2026-10-13T08:30:00Z",
                }
                for name, value in fields.items():
                    ET.SubElement(response, name).text = value
                raw = ET.tostring(response, encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/xml")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            return self.wfile.write(raw)
        return self.js(404, {"error": "not_found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.getenv("MOCK_PORT", "8090"))
    print("Mock services on http://localhost:" + str(port), flush=True)
    ThreadingHTTPServer((os.getenv("MOCK_HOST", "127.0.0.1"), port), H).serve_forever()
