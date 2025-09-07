#!/usr/bin/env bash
# scripts/install_dependencies.sh
# Idempotent local setup for PetPlantr (Python venv, backend deps, optional test + frontend deps)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
CREATE_VENV="${CREATE_VENV:-true}"
INSTALL_TEST_DEPS="${INSTALL_TEST_DEPS:-auto}"   # true|false|auto (auto installs if file exists)
INSTALL_FRONTEND="${INSTALL_FRONTEND:-auto}"     # true|false|auto (auto installs if frontend exists)

echo "[deps] Using python: $PYTHON_BIN"

if [[ "$CREATE_VENV" == "true" && ! -d .venv ]]; then
	echo "[deps] Creating virtualenv at .venv"
	"$PYTHON_BIN" -m venv .venv
fi

if [[ -d .venv ]]; then
	# shellcheck disable=SC1091
	source .venv/bin/activate
fi

python -m pip install --upgrade pip setuptools wheel

if [[ -f requirements.txt ]]; then
	echo "[deps] Installing backend requirements.txt"
	python -m pip install -r requirements.txt
else
	echo "[deps] WARN: requirements.txt not found; installing minimal runtime"
	python -m pip install fastapi uvicorn requests
fi

if [[ "$INSTALL_TEST_DEPS" == "true" || ( "$INSTALL_TEST_DEPS" == "auto" && -f requirements-test-sprint-c.txt ) ]]; then
	if [[ -f requirements-test-sprint-c.txt ]]; then
		echo "[deps] Installing test deps (Sprint C)"
		python -m pip install -r requirements-test-sprint-c.txt
	fi
fi

if [[ "$INSTALL_TEST_DEPS" == "true" || ( "$INSTALL_TEST_DEPS" == "auto" && -f requirements-test.txt ) ]]; then
	if [[ -f requirements-test.txt ]]; then
		echo "[deps] Installing test deps (general)"
		python -m pip install -r requirements-test.txt || true
	fi
fi

# Ensure runtime server deps exist for local runs
python - <<'PY'
import importlib, sys, subprocess
missing = []
for pkg in ("uvicorn", "fastapi"):
		try:
				importlib.import_module(pkg)
		except Exception:
				missing.append(pkg)
if missing:
		print(f"[deps] Installing runtime packages: {missing}")
		subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
else:
		print("[deps] Runtime packages present")
PY

# Frontend (optional)
if [[ "$INSTALL_FRONTEND" == "true" || ( "$INSTALL_FRONTEND" == "auto" && -d frontend ) ]]; then
	if command -v npm >/dev/null 2>&1; then
		echo "[deps] Installing frontend dependencies"
		(cd frontend && npm install --no-audit --no-fund) || true
	else
		echo "[deps] npm not found; skipping frontend"
	fi
fi

echo "[deps] Done. Activate venv with: source .venv/bin/activate"
