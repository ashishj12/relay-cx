import hashlib
import json
import re
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE_PYTHON = sys.executable


def verify():
    output = ROOT / "evidence/current/clean-verification.json"
    work = ROOT / ".local" / ("clean-" + str(int(time.time())))
    work.mkdir(parents=True)
    archive_path = ROOT / "release/relay-cx-production-source.zip"
    archive_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (work / member.filename).resolve()
            if not target.is_relative_to(work.resolve()):
                raise ValueError("unsafe_archive_path")
        archive.extractall(work)
    manifest = json.loads((work / "relay-cx/SOURCE_MANIFEST.json").read_text())
    if not all(
        hashlib.sha256((work / "relay-cx" / name).read_bytes()).hexdigest() == value
        for name, value in manifest.items()
    ):
        raise ValueError("source_manifest_mismatch")
    source = work / "relay-cx"
    env = dict(os.environ)
    for key in ("GEMINI_API_KEY", "GEMINI_MODEL", "PYTHONPATH", "PUBLIC_ORIGIN", "DATABASE_PATH"):
        env.pop(key, None)
    env["APP_MODE"] = "REVIEWER"
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    env["NO_COLOR"] = "1"
    commands = []

    def run(args):
        result = subprocess.run(
            args,
            cwd=source,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        commands.append(
            {
                "command": " ".join(str(x) for x in args),
                "exitCode": result.returncode,
                "output": result.stdout[-8000:],
            }
        )
        print(Path(str(args[0])).name, "PASS" if result.returncode == 0 else "FAIL", flush=True)
        if result.returncode:
            raise RuntimeError("clean_command_failed")

    try:
        run([BASE_PYTHON, "-m", "venv", str(source / ".venv")])
        python = source / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", "-r", "requirements-dev.txt"])
        run([shutil.which("bun"), "install", "--frozen-lockfile"])
        run([str(python), "-m", "ruff", "check", "apps/api", "services", "tests", "tools"])
        run([str(python), "-m", "ruff", "format", "--check", "apps/api", "services", "tests", "tools"])
        run([str(python), "-m", "pytest", "-q", "--junitxml=evidence/current/pytest.xml"])
        run([str(python), "tools/evaluate.py", "--mode", "REVIEWER"])
        for script in ("test:web", "typecheck", "build"):
            run([shutil.which("bun"), "run", script])
        status = "PASS"
    except Exception:
        status = "FAIL"
    output.write_text(
        json.dumps(
            {
                "status": status,
                "isolatedSource": str(source),
                "credentialsPresent": False,
                "sourceArchiveSha256": archive_hash,
                "sourceManifest": manifest,
                "commands": commands,
            },
            indent=2,
        )
    )
    if status == "PASS":
        shutil.copyfile(source / "evidence/current/pytest.xml", ROOT / "evidence/current/pytest.xml")
        web_test = next(c for c in commands if "test:web" in c["command"])["output"]
        tests = re.search(r"(\d+) pass\b", web_test)
        assertions = re.search(r"(\d+) expect\(\) calls", web_test)
        (ROOT / "evidence/current/frontend-verification.json").write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "tests": int(tests[1]) if tests else None,
                    "assertions": int(assertions[1]) if assertions else None,
                    "typecheck": "PASS",
                    "productionBuild": "PASS",
                    "executionSource": "isolated clean release",
                    "commands": ["bun run test:web", "bun run typecheck", "bun run build"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        shutil.copyfile(
            source / "evidence/current/http-scenarios.json",
            ROOT / "evidence/current/clean-http-scenarios.json",
        )
    return status


if __name__ == "__main__":
    sys.exit(0 if verify() == "PASS" else 1)
