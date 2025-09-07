#!/usr/bin/env bash
set -euo pipefail
CMD=${1:-}
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python3 - <<'PY'
import os
need = [
  "pytest>=7.4",
  "pytest-asyncio>=0.23",
  "pytest-cov>=4.1",
  "respx>=0.21",
  "httpx==0.27.*",
]
print("[run_tests] Ensuring core test deps are installed (best-effort)...")
os.system("python3 -m pip install -q " + " ".join(need))
PY

if [[ "$CMD" == "coverage" ]]; then
  python3 -m pytest -p pytest_asyncio -p respx -p pytest_cov -m "not ml or sprint_c" --cov=src --cov-report=term-missing -c pytest.ini
else
  python3 -m pytest -p pytest_asyncio -p respx -m sprint_c -c pytest.ini
fi
