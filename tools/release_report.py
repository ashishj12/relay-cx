import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    file = ROOT / "evidence/current" / name
    return json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}


def report():
    suite = ET.parse(ROOT / "evidence/current/pytest.xml").getroot()
    cases = list(suite.iter("testcase"))
    clean = read("clean-verification.json")
    audit = read("compliance-audit.json")
    runtime = {
        name: value
        for name, value in clean.get("sourceManifest", {}).items()
        if name.startswith(("apps/", "services/", "tools/", "tests/"))
        or name in {"compose.yaml", "package.json", "bun.lock", "pyproject.toml", "requirements-dev.txt"}
    }
    drift = [
        name
        for name, value in runtime.items()
        if not (ROOT / name).exists() or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value
    ]
    result = {
        "backend": {
            "tests": len(cases),
            "failures": sum(
                any(t.find(tag) is not None for tag in ("failure", "error", "skipped")) for t in cases
            ),
        },
        "reviewer": read("http-scenarios.json").get("status", "NOT TESTED"),
        "docker": read("docker-verification.json").get("status", "NOT TESTED"),
        "cleanInstall": clean.get("status", "NOT TESTED"),
        "testedRuntimeFiles": len(runtime),
        "runtimeMatchesCleanSource": bool(runtime) and not drift,
        "runtimeDrift": drift,
        "liveGemini": read("live-gemini-evidence.json").get("status", "NOT TESTED"),
        "providerAvailability": read("provider-availability.json"),
        "requirements": audit.get("counts", {}),
        "qualification": audit.get("qualification", "NOT EVALUATED"),
        "cloudDeployed": False,
        "demoVideo": "EXCLUDED_BY_USER",
        "independentScore": None,
    }
    (ROOT / "evidence/current/verification-summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    report()
