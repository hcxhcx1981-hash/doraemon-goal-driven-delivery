"""Run this repository's pytest suite; retain complete output per invocation."""
from datetime import datetime, timezone
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
logs = root / ".verification"
logs.mkdir(exist_ok=True)
log = logs / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".log")
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
env.pop("PYTEST_ADDOPTS", None)
env.pop("PYTEST_PLUGINS", None)
with log.open("w", encoding="utf-8") as stream:
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-m", "pytest", "-q", "--tb=long"],
        cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT,
    )
output = log.read_text(encoding="utf-8")
if result.returncode:
    print(output, end="")
else:
    print(next((line for line in reversed(output.splitlines()) if line.strip()), ""))
print(f"VERIFY={'PASS' if result.returncode == 0 else 'FAIL'} log={log}")
raise SystemExit(result.returncode)
