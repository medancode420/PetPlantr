#!/bin/bash
# start-petplantr.sh: Initializes and starts PetPlantr with fixes for circular copy and missing files.

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir) PROJECT_DIR="$2"; shift; shift ;;
        --api-key) GROK_API_KEY="$2"; shift; shift ;;
        --port) PORT="$2"; shift; shift ;;
        --temp) TEMP=1; shift ;;
        --validate) VALIDATE=1; shift ;;
        *) shift ;;
    esac
done

# Fallback for non-writable path, handling spaces
SPECIFIED_DIR="${PROJECT_DIR:-/my directory of grok 4/PetPlantr}"
if ! mkdir -p "$SPECIFIED_DIR" 2>/dev/null || ! touch "$SPECIFIED_DIR/.test_writable" 2>/dev/null; then
    echo "[petplantr] Path not writable: $SPECIFIED_DIR"
    PROJECT_DIR="$HOME$(echo "$SPECIFIED_DIR" | sed 's|^/||')"
    echo "[petplantr] Falling back to: $PROJECT_DIR"
else
    PROJECT_DIR="$SPECIFIED_DIR"
fi
mkdir -p "$PROJECT_DIR"
rm -f "$PROJECT_DIR/.test_writable"
cd "$PROJECT_DIR" || exit 1

# Source dir for copy (script's location parent)
SCRIPT_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# Copy if source != target and target empty. Use rsync (safer for dotfiles) or tar fallback.
if [ "$SCRIPT_SOURCE" != "$PWD" ] && [ -z "$(ls -A .)" ]; then
    echo "[petplantr] Copying from $SCRIPT_SOURCE to $PWD"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude='.git' --exclude 'petplantr_env' --exclude 'node_modules' "$SCRIPT_SOURCE/" "$PWD/"
    else
        # tar approach avoids copying '.' and '..'
        (cd "$SCRIPT_SOURCE" && tar -c --exclude='.git' --exclude='petplantr_env' --exclude='node_modules' .) | (tar -x -C "$PWD")
    fi
else
    echo "[petplantr] Skipping copy (circular or not empty)"
fi

# Always create minimal api_server_minimal.py if missing
if [ ! -f "api_server_minimal.py" ]; then
    echo "[petplantr] Creating minimal api_server_minimal.py"
    cat << 'EOF' > api_server_minimal.py
try:
    from fastapi import FastAPI, Body
    _HAS_FASTAPI = True
except Exception:
    _HAS_FASTAPI = False

if _HAS_FASTAPI:
    app = FastAPI()

    @app.get("/")
    def read_root():
        return {"Hello": "PetPlantr"}

    @app.post("/api/v1/grok/query")
    def grok_query(body=None):
        # 'body' will be a dict when FastAPI is running; keep simple signature to remain import-safe
        prompt = (body or {}).get("prompt", "default")
        return {"response": "Mock Grok response for {}".format(prompt)}
else:
    # fastapi not installed; provide a minimal placeholder so 'import api_server_minimal'
    # succeeds during TEMP simulations. In production the real FastAPI app will be used.
    class _DummyApp(object):
        pass

    app = _DummyApp()
EOF
fi

# Detect python executable (prefer python3)
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "[petplantr] ERROR: No Python executable found (python3 or python). Please install Python 3." >&2
    exit 3
fi

# Setup environment
if [ "${TEMP:-0}" -eq 1 ]; then
    echo "[petplantr] TEMP simulation mode: skipping venv and package installation"
else
    "$PYTHON_CMD" -m venv petplantr_env
    # shellcheck source=/dev/null
    source petplantr_env/bin/activate
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        pip install fastapi uvicorn requests
    fi
fi

# Config env with default key
: "${GROK_API_KEY:=<YOUR_GROK_API_KEY_GOES_HERE>}"
touch .env
grep -q "GROK_API_KEY" .env || echo "GROK_API_KEY=$GROK_API_KEY" >> .env

# Auto-pick port if not specified
PORT="${PORT:-8000}"
if [ -z "$PORT_SPECIFIED" ]; then  # Auto only if not passed
    while lsof -iTCP:"$PORT" -sTCP:LISTEN > /dev/null 2>&1; do
        echo "Port $PORT in use; switching to $((PORT+1))"
        PORT=$((PORT+1))
    done
fi

# Launch with import check
if "$PYTHON_CMD" -c "import api_server_minimal" 2>/dev/null; then
    if [ "${TEMP:-0}" -eq 1 ]; then
        echo "[petplantr] TEMP simulation: api_server_minimal import succeeded (no uvicorn started)"
    else
        uvicorn api_server_minimal:app --reload --port "$PORT" &
    fi
else
    echo "Error: Could not import api_server_minimal in $PWD"
    exit 1
fi

# Validate if flagged
if [ -n "$VALIDATE" ]; then
    sleep 5
    curl -X POST http://localhost:"$PORT"/api/v1/grok/query -H "Content-Type: application/json" -d '{"prompt": "Test Grok integration"}' || echo "Validation failed"
fi

echo "PetPlantr started in $PROJECT_DIR on port $PORT. Access at http://localhost:$PORT"
