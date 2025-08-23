#!/bin/bash
# start-petplantr.sh: Initializes and starts PetPlantr in the specified directory.

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir) PROJECT_DIR="$2"; shift; shift ;;
        --api-key) GROK_API_KEY="$2"; shift; shift ;;
        --production) PRODUCTION=1; shift ;;
        *) shift ;;
    esac
done

# Fallback to writable path under $HOME if specified dir not writable
SPECIFIED_DIR="${PROJECT_DIR:-/my directory of grok 4/PetPlantr}"
if ! mkdir -p "$SPECIFIED_DIR" 2>/dev/null || ! touch "$SPECIFIED_DIR/.test_writable" 2>/dev/null; then
    echo "[petplantr] Path not writable: $SPECIFIED_DIR"
    PROJECT_DIR="$HOME$(echo "$SPECIFIED_DIR" | sed 's|^/||')"
    echo "[petplantr] Falling back to: $PROJECT_DIR"
else
    PROJECT_DIR="$SPECIFIED_DIR"
fi
mkdir -p "$PROJECT_DIR"
rm -f "$PROJECT_DIR/.test_writable" 2>/dev/null
cd "$PROJECT_DIR" || exit 1

# Clone repo if not present (assuming public repo; adjust for private)
if [ ! -d ".git" ]; then
    git clone https://github.com/medancode420/PetPlantr.git . || true
fi

# Detect python executable (prefer python3)
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=python
else
  echo "[petplantr] ERROR: No Python executable found (python3 or python)." >&2
  exit 3
fi

# Setup environment
$PYTHON_CMD -m venv petplantr_env
# shellcheck source=/dev/null
source petplantr_env/bin/activate
python -m pip install --upgrade pip setuptools wheel || true
if [ -f "requirements.txt" ]; then
  python -m pip install --no-cache-dir -r requirements.txt || true
fi

# Production-specific deps
if [ -n "${PRODUCTION:-}" ]; then
  python -m pip install --no-cache-dir gunicorn uvicorn || true
fi

# Config env (copy template if present)
if [ -f ".env.template" ] && [ ! -f ".env" ]; then
  cp .env.template .env
fi
if [ -n "${PRODUCTION:-}" ]; then
  # Ensure ENV=production in .env
  grep -q "^ENV=" .env 2>/dev/null && sed -i.bak "s/^ENV=.*/ENV=production/" .env || echo "ENV=production" >> .env
fi

# Require api key for production
if [ -n "${PRODUCTION:-}" ]; then
  if [ -z "$GROK_API_KEY" ]; then
    echo "[petplantr] GROK_API_KEY required in production; use --api-key"
    exit 1
  fi
  grep -q "^GROK_API_KEY=" .env 2>/dev/null || echo "GROK_API_KEY=$GROK_API_KEY" >> .env
fi

# Launch services
if [ -f "docker-compose.yml" ]; then
  docker-compose up -d || true
fi

# Backend start: production -> gunicorn (UvicornWorker), dev -> uvicorn with reload
BIND_PORT=8000
if [ -n "${PRODUCTION:-}" ]; then
  if [ -f "backend/api_server.py" ]; then
    echo "[petplantr] Starting backend with gunicorn (production)"
    nohup gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api_server:app --bind 0.0.0.0:${BIND_PORT} --log-level info > gunicorn.log 2>&1 &
  elif [ -f "api_server.py" ]; then
    echo "[petplantr] Starting backend with gunicorn (production)"
    nohup gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app --bind 0.0.0.0:${BIND_PORT} --log-level info > gunicorn.log 2>&1 &
  else
    echo "[petplantr] No backend entrypoint found; skipping backend start"
  fi
else
  if [ -f "backend/api_server.py" ]; then
    echo "[petplantr] Starting backend with uvicorn (dev)"
    (uvicorn backend.api_server:app --reload --port ${BIND_PORT} &) || true
  elif [ -f "api_server.py" ]; then
    echo "[petplantr] Starting backend with uvicorn (dev)"
    (uvicorn api_server:app --reload --port ${BIND_PORT} &) || true
  elif [ -f "api_server_minimal.py" ]; then
    echo "[petplantr] Starting minimal backend with uvicorn (dev)"
    (uvicorn api_server_minimal:app --reload --port ${BIND_PORT} &) || true
  else
    echo "[petplantr] No backend entrypoint found; skipping backend start"
  fi
fi

# Frontend build/start
if [ -d "frontend" ]; then
  cd frontend || true
  if [ -f package.json ]; then
    if [ -n "${PRODUCTION:-}" ]; then
      npm ci --no-audit --no-fund || true
      npm run build || true
      npm run start --prefix . &
    else
      npm install --no-audit --no-fund || true
      npm run dev || true &
    fi
  fi
  cd - >/dev/null || true
fi

echo "PetPlantr started in $PROJECT_DIR (production: ${PRODUCTION:-off}). Backend on http://localhost:${BIND_PORT}"
