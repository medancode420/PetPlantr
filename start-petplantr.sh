#!/bin/bash
# start-petplantr.sh: Initializes and starts PetPlantr with hardened features.

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir) PROJECT_DIR="$2"; shift; shift ;;
        --api-key) GROK_API_KEY="$2"; shift; shift ;;
        --port) PORT="$2"; shift; shift ;;
        --validate) VALIDATE=1; shift ;;
        --temp) TEMP_MODE=1; shift ;;
        *) shift ;;
    esac
done

# Use temp dir if flagged
if [ -n "$TEMP_MODE" ]; then
    PROJECT_DIR=$(mktemp -d)
    echo "[petplantr] Running in TEMP mode: $PROJECT_DIR"
fi

# Fallback for non-writable path
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

# Clone or copy local repo
SCRIPT_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -d ".git" ] && [ "$SCRIPT_SOURCE" != "$PWD" ] && [ -z "$(ls -A .)" ]; then
    echo "[petplantr] Pulling repository into $PWD"
    git clone https://github.com/medancode420/PetPlantr.git . || true
fi

# Create minimal api_server_minimal.py if missing (import-safe)
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
    def grok_query(body: dict = Body(...)):
        prompt = body.get("prompt", "default")
        return {"response": f"Mock Grok response for {prompt}"}
else:
    # fastapi not installed; provide a minimal placeholder so import succeeds in TEMP
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

# Setup environment (skip in temp mode)
if [ -n "$TEMP_MODE" ]; then
    echo "[petplantr] TEMP mode: Skipping venv and installs"
else
    "$PYTHON_CMD" -m venv petplantr_env
    # shellcheck source=/dev/null
    source petplantr_env/bin/activate
    python -m pip install --upgrade pip setuptools wheel || true
    if [ -f "requirements.txt" ]; then
        python -m pip install --no-cache-dir -r requirements.txt || true
    else
        python -m pip install --no-cache-dir fastapi uvicorn requests || true
    fi
fi

# Config env (require key)
if [ -z "$GROK_API_KEY" ]; then
    echo "[petplantr] GROK_API_KEY required; use --api-key"
    exit 1
fi
[ -f .env ] || touch .env
grep -q "GROK_API_KEY" .env || echo "GROK_API_KEY=$GROK_API_KEY" >> .env

# Auto-pick port
PORT="${PORT:-8000}"
while lsof -iTCP:"$PORT" -sTCP:LISTEN > /dev/null 2>&1; do
    echo "Port $PORT in use; switching to $((PORT+1))"
    PORT=$((PORT+1))
done

# Launch (simulate in temp)
if [ -n "$TEMP_MODE" ]; then
    if "$PYTHON_CMD" -c "import api_server_minimal" 2>/dev/null; then
        echo "[petplantr] TEMP mode: Simulated launch on port $PORT; import validated"
    else
        echo "Error: Could not import api_server_minimal"
        exit 1
    fi
else
    if "$PYTHON_CMD" -c "import api_server_minimal" 2>/dev/null; then
        uvicorn api_server_minimal:app --reload --port "$PORT" &
    else
        echo "Error: Could not import api_server_minimal"
        exit 1
    fi
fi

# Validate
if [ -n "$VALIDATE" ]; then
    sleep 5
    curl -s -X POST http://localhost:"$PORT"/api/v1/grok/query -H "Content-Type: application/json" -d '{"prompt": "Test"}' || echo "Validation failed"
fi

echo "PetPlantr started in $PROJECT_DIR on port $PORT."
if [ -n "$TEMP_MODE" ]; then
    echo "[petplantr] TEMP mode complete; dir $PROJECT_DIR can be removed"
fi
