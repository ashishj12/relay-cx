import argparse
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlparse
import httpx

def verify(project, origin, output):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,60}", project):
        raise ValueError("invalid_compose_project")
    if urlparse(origin).hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("local_reviewer_stack_required")
    with httpx.Client(base_url=origin, trust_env=False, timeout=30, headers={"Origin": origin}) as client:
        assert client.get("/api/health").json()["mode"] == "REVIEWER"
        credentials = {"username": "jordan.lee", "password": "ReviewerPass-1002"}
        client.post("/api/login", json=credentials).raise_for_status()
        proposal = client.post(
            "/api/chat", json={"message": "Create a support case for my mobile service. Persistence check."}
        ).json()
        action = proposal["pendingAction"]["id"]
        confirmation = client.post("/api/confirm", json={"actionId": action, "confirm": True})
        confirmation.raise_for_status()
        case = confirmation.json()["caseId"]
        subprocess.run(
            ["docker", "compose", "-p", project, "restart", "enterprise"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 20
        while True:
            response = client.get("/api/account/overview")
            if response.status_code == 200:
                break
            if time.monotonic() > deadline:
                raise RuntimeError("session_did_not_survive_restart")
            time.sleep(0.2)
        # Check the actual persisted receipt inside the private enterprise service.
        script = """import json,urllib.request
base='http://127.0.0.1:8090'
data=json.dumps({'username':'jordan.lee','password':'ReviewerPass-1002'}).encode()
request=urllib.request.Request(base+'/api/auth/login',data=data,headers={'Content-Type':'application/json'})
auth=json.load(urllib.request.urlopen(request))
request=urllib.request.Request(base+'/api/support-cases/by-key/'+%r,headers={'Authorization':'Bearer '+auth['accessToken']})
receipt=json.load(urllib.request.urlopen(request))
assert receipt['caseId']==%r and receipt['customerId']=='CUST-1002'
print('receipt restored')
""" % (action, case)
        result = subprocess.check_output(
            ["docker", "compose", "-p", project, "exec", "-T", "enterprise", "python", "-c", script],
            text=True,
        )
        assert "receipt restored" in result
        client.post("/api/logout", json={}).raise_for_status()
        client.post("/api/login", json=credentials).raise_for_status()
        replay = client.post("/api/confirm", json={"actionId": action, "confirm": True}).json()
        assert replay["caseId"] == case
        trace = client.get("/api/traces/" + replay["traceId"]).json()
        assert not any(event["eventType"] == "tool.invoked" for event in trace)
        client.post("/api/logout", json={}).raise_for_status()
    evidence = {
        "status": "PASS",
        "project": project,
        "origin": origin,
        "caseId": case,
        "actionId": action,
        "sessionSurvivedEnterpriseRestart": True,
        "receiptSurvivedEnterpriseRestart": True,
        "reauthenticatedReplayDidNotWrite": True,
        "replayTraceId": replay["traceId"],
    }
    Path(output).write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--output", default="evidence/current/persistence-verification.json")
    args = parser.parse_args()
    verify(args.project, args.origin, args.output)
