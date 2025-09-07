#!/bin/bash
# run-lint-typecheck.sh: Runs pylint and mypy on PetPlantr backend files.
#
# Usage:
#   ./run-lint-typecheck.sh [options] [PROJECT_DIR] [-- FILES...]
#
# Options:
#   -q, --quiet     Reduce output verbosity (pylint short report off; mypy hides context/summary)
#       --no-fail   Always exit 0 even if tools report issues (useful for local dev)
#   -h, --help      Show help

set -euo pipefail

QUIET=false
FAIL_ON_ERROR=true
PROJECT_DIR=""
FILES=()

print_help() {
  cat <<'EOF'
run-lint-typecheck.sh - Run pylint and mypy on PetPlantr backend files.

Usage:
  ./run-lint-typecheck.sh [options] [PROJECT_DIR] [-- FILES...]

Options:
  -q, --quiet     Reduce output verbosity
      --no-fail   Always exit 0 even if tools report issues
  -h, --help      Show this help

Examples:
  ./run-lint-typecheck.sh                       # run in current dir on default files
  ./run-lint-typecheck.sh -q --no-fail          # quiet, don't fail build
  ./run-lint-typecheck.sh /path/to/repo         # run in given dir on default files
  ./run-lint-typecheck.sh -- api_server_minimal.py src/services/mesh_governor.py
EOF
}

# Parse args
FILES_MODE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    -q|--quiet)
      QUIET=true
      shift
      ;;
    --no-fail)
      FAIL_ON_ERROR=false
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    --)
      FILES_MODE=true
      shift
      ;;
    *)
      if [[ "$FILES_MODE" == true ]]; then
        FILES+=("$1")
        shift
      else
        if [[ -z "$PROJECT_DIR" ]]; then
          PROJECT_DIR="$1"
          shift
        else
          # Treat as file list if project dir already set
          FILES+=("$1")
          shift
        fi
      fi
      ;;
  esac
done

# Set project dir (default to current)
if [[ -z "$PROJECT_DIR" ]]; then
  PROJECT_DIR="$(pwd)"
fi

cd "$PROJECT_DIR" || { echo "Error: cannot cd to $PROJECT_DIR" >&2; exit 1; }

# Activate venv if present
if [[ -f "petplantr_env/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source petplantr_env/bin/activate
fi

# Default files to check (expand as needed)
if [[ ${#FILES[@]} -eq 0 ]]; then
  FILES=(
    "api_server_minimal.py"
    "src/services/mesh_governor.py"
  )
fi

# Check tool availability
if ! command -v pylint >/dev/null 2>&1; then
  echo "Error: pylint not found on PATH. Install it (e.g., pip install pylint)." >&2
  PYLINT_MISSING=true
else
  PYLINT_MISSING=false
fi

if ! command -v mypy >/dev/null 2>&1; then
  echo "Error: mypy not found on PATH. Install it (e.g., pip install mypy)." >&2
  MYPY_MISSING=true
else
  MYPY_MISSING=false
fi

if [[ "$PYLINT_MISSING" == true && "$MYPY_MISSING" == true ]]; then
  echo "Nothing to run. Exiting." >&2
  exit 1
fi

EXIT_CODE=0

# Run pylint with config
if [[ "$PYLINT_MISSING" == false ]]; then
  PYLINT_OPTS=("--rcfile=.pylintrc")
  if [[ "$QUIET" == true ]]; then
    # -sn: no score; -rn: no reports
    PYLINT_OPTS+=("-sn" "-rn")
  fi
  echo "Running: pylint ${PYLINT_OPTS[*]} ${FILES[*]}"
  set +e
  pylint "${PYLINT_OPTS[@]}" "${FILES[@]}"
  LINT_RET=$?
  set -e
  if [[ $LINT_RET -ne 0 ]]; then
    echo "pylint reported issues (exit $LINT_RET)" >&2
    EXIT_CODE=1
  fi
fi

# Run mypy with config
if [[ "$MYPY_MISSING" == false ]]; then
  MYPY_OPTS=("--config-file=mypy.ini")
  if [[ "$QUIET" == true ]]; then
    MYPY_OPTS+=("--hide-error-context" "--no-error-summary" "--no-pretty")
  fi
  echo "Running: mypy ${MYPY_OPTS[*]} ${FILES[*]}"
  set +e
  mypy "${MYPY_OPTS[@]}" "${FILES[@]}"
  MYPY_RET=$?
  set -e
  if [[ $MYPY_RET -ne 0 ]]; then
    echo "mypy reported issues (exit $MYPY_RET)" >&2
    EXIT_CODE=1
  fi
fi

if [[ "$FAIL_ON_ERROR" == true ]]; then
  exit $EXIT_CODE
else
  echo "Lint and typecheck completed (exit $EXIT_CODE) for files in $PROJECT_DIR."
  exit 0
fi
