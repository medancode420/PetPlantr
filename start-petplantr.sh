#!/bin/bash
# start-petplantr.sh: Initializes and starts PetPlantr in the specified directory.

# Set directory (user-provided or default)
PROJECT_DIR="${1:-/my directory of grok 4/PetPlantr}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# Clone repo if not present (assuming public repo; adjust for private)
if [ ! -d ".git" ]; then
    git clone https://github.com/medancode420/PetPlantr.git . || true
fi

# Setup environment
python -m venv petplantr_env
# shellcheck source=/dev/null
source petplantr_env/bin/activate
python -m pip install --upgrade pip setuptools wheel || true
if [ -f "requirements.txt" ]; then
  python -m pip install --no-cache-dir -r requirements.txt || true
fi

# Config env (copy template)
if [ -f ".env.template" ] && [ ! -f ".env" ]; then
  cp .env.template .env
fi

# Launch services
if [ -f "docker-compose.yml" ]; then
  docker-compose up -d || true
fi

# Start backend (dev)
if command -v uvicorn >/dev/null 2>&1; then
  (uvicorn backend.api_server:app --reload &) || true
else
  echo "[petplantr] uvicorn not found in venv; backend not started"
fi

# Start frontend
if [ -d "frontend" ]; then
  cd frontend || true
  if [ -f package.json ]; then
    npm install --no-audit --no-fund || true
    npm run dev || true
  fi
  cd - >/dev/null || true
fi

echo "PetPlantr started in $PROJECT_DIR. Access at http://localhost:3000"
