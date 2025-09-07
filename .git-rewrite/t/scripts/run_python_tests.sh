#!/bin/bash
# Lightweight Python test detector/runner for PetPlantr
# - Detects tests in ./tests and top-level test_*.py files
# - Runs pytest if available, prints a compact summary, returns pytest exit code

set -eo pipefail

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR"

echo "[PYTEST] Detecting Python tests..."

HAS_TEST_DIR=0
HAS_TOP_LEVEL_TESTS=0

if [ -d "tests" ]; then
  HAS_TEST_DIR=1
fi

shopt -s nullglob
TOP_LEVEL_TESTS=( test_*.py )
if [ ${#TOP_LEVEL_TESTS[@]} -gt 0 ]; then
  HAS_TOP_LEVEL_TESTS=1
fi
shopt -u nullglob

PYTEST_CMD=(pytest)
CHECK_PY="python"

if ! command -v pytest >/dev/null 2>&1; then
  # Try project virtualenv first
  VENV_PY="$ROOT_DIR/petplantr_env/bin/python"
  if [ -x "$VENV_PY" ]; then
    PYTEST_CMD=("$VENV_PY" -m pytest)
    echo "[PYTEST] Using virtualenv Python: $VENV_PY -m pytest"
    CHECK_PY="$VENV_PY"
  else
    # Fallback to system python -m pytest if available
    if python -c "import pytest" >/dev/null 2>&1; then
      PYTEST_CMD=(python -m pytest)
      echo "[PYTEST] Using system Python -m pytest"
      CHECK_PY="python"
    else
      echo "[PYTEST][WARN] pytest not found in PATH and not importable. Skipping Python tests."
      exit 0
    fi
  fi
fi

if [ $HAS_TEST_DIR -eq 0 ] && [ $HAS_TOP_LEVEL_TESTS -eq 0 ]; then
  echo "[PYTEST] No Python tests detected."
  exit 0
fi

ARGS=( -q --maxfail=1 --disable-warnings )

# Skip list for optional dependency tests
SKIP_FILES=()

# Conditionally skip Flickr tests if flickrapi is not installed
if ! "$CHECK_PY" - <<'PY'
import sys
try:
  import flickrapi  # noqa: F401
except Exception:
  sys.exit(1)
sys.exit(0)
PY
then
  if printf '%s\n' "${TOP_LEVEL_TESTS[@]}" | grep -q '^test_flickr_collection.py$'; then
    SKIP_FILES+=( test_flickr_collection.py )
  fi
fi

# Build final test list excluding SKIP_FILES
FINAL_TOP_LEVEL_TESTS=()
if [ $HAS_TOP_LEVEL_TESTS -eq 1 ]; then
  for f in "${TOP_LEVEL_TESTS[@]}"; do
    skip=0
    for s in "${SKIP_FILES[@]}"; do
      if [ "$f" = "$s" ]; then
        skip=1; break
      fi
    done
    if [ $skip -eq 0 ]; then
      FINAL_TOP_LEVEL_TESTS+=( "$f" )
    fi
  done
fi

if [ ${#SKIP_FILES[@]} -gt 0 ]; then
  echo "[PYTEST] Skipping optional tests: ${SKIP_FILES[*]} (missing optional deps)"
fi

if [ $HAS_TEST_DIR -eq 1 ]; then
  ARGS+=( tests )
fi

if [ ${#FINAL_TOP_LEVEL_TESTS[@]} -gt 0 ]; then
  ARGS+=( "${FINAL_TOP_LEVEL_TESTS[@]}" )
fi

echo "[PYTEST] Running: ${PYTEST_CMD[*]} ${ARGS[*]}"
set +e
"${PYTEST_CMD[@]}" "${ARGS[@]}"
RC=$?
set -e

if [ $RC -eq 0 ]; then
  echo "[PYTEST] ✅ Python tests passed"
else
  echo "[PYTEST] ❌ Python tests failed (exit code $RC)"
fi

exit $RC
