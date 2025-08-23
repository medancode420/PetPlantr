#!/bin/bash
# start-petplantr.sh: Initializes and starts PetPlantr in the specified directory.

# Set directory (user-provided or default)
PROJECT_DIR="${1:-/my directory of grok 4/PetPlantr}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# Clone repo if not present (assuming public repo; adjust for private)
if [ ! -d ".git" ]; then
    git clone https://github.com/your-repo/PetPlantr.git .
fi

# Setup environment
python -m venv petplantr_env
# shellcheck source=/dev/null
source petplantr_env/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

# Config env (copy template)
if [ -f ".env.template" ]; then
  cp .env.template .env
fi
# Edit .env with defaults or prompt user (e.g., API keys)

# Launch services
if [ -f "docker-compose.yml" ]; then
  docker-compose up -d
fi

# Start backend and frontend where applicable
if [ -f "backend/api_server.py" ]; then
  (uvicorn backend.api_server:app --reload &) || true
elif [ -f "api_server.py" ]; then
  (uvicorn api_server:app --reload &) || true
elif [ -f "api_server_minimal.py" ]; then
  (uvicorn api_server_minimal:app --reload &) || true
fi

if [ -d "frontend" ]; then
  (cd frontend && if [ -f package.json ]; then npm install --no-audit --no-fund && npm run dev & fi) || true
fi

echo "PetPlantr started in $PROJECT_DIR. Access at http://localhost:3000"
