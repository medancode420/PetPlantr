#!/usr/bin/env bash

# Run PetPlantr locally in "production" mode and route to a local domain
# - Frontend on port 3000 (Next.js production server)
# - Backend on port 8000 (gunicorn + uvicorn worker)
# - Adds /etc/hosts entries for DOMAIN (default petplantr.local) -> 127.0.0.1 (requires sudo)
# - Also maps api.DOMAIN for convenience
# Usage: DOMAIN=petplantr.local FE_PORT=3000 BE_PORT=8000 bash local_prod.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
DOMAIN="${DOMAIN:-petplantr.local}"
FE_PORT="${FE_PORT:-3000}"
BE_PORT="${BE_PORT:-8000}"
BE_PID=""
FE_PID=""
KILL_PORTS="${KILL_PORTS:-true}"

info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err()  { echo -e "\033[1;31m[ERR ]\033[0m $*"; }

write_if_missing() {
  local file="$1"; shift
  local content="$*"
  if [[ -f "$file" ]]; then
    warn "$file exists; leaving as-is"
  else
    info "Creating $file"
    printf "%s\n" "$content" > "$file"
  fi
}

set_env_kv() {
  local file="$1"; local key="$2"; local value="$3"
  if [[ ! -f "$file" ]]; then
    printf "%s=%s\n" "$key" "$value" > "$file"
    return
  fi
  if grep -qE "^${key}=" "$file"; then
    sed -i '' "s|^${key}=.*$|${key}=${value}|" "$file"
  else
    printf "%s=%s\n" "$key" "$value" >> "$file"
  fi
}

port_in_use() {
  local port="$1"
  lsof -ti tcp:"$port" >/dev/null 2>&1
}

free_port() {
  local port="$1"
  if port_in_use "$port"; then
    local pids
    pids=$(lsof -ti tcp:"$port" | tr '\n' ' ')
    if [[ "$KILL_PORTS" == "true" ]]; then
      warn "Port $port in use by PID(s): $pids — terminating"
      # shellcheck disable=SC2086
      kill -9 $pids || true
      sleep 1
    else
      err "Port $port is in use by PID(s): $pids. Set KILL_PORTS=true to auto-kill or free it manually."
      exit 1
    fi
  fi
}

ensure_python_venv() {
  if [[ ! -d "$ROOT_DIR/.venv" ]]; then
    info "Creating Python venv"
    python3 -m venv "$ROOT_DIR/.venv"
  fi
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/bin/activate"
  pip install -U pip >/dev/null
  info "Installing backend deps"
  pip install -r "$ROOT_DIR/requirements.txt" >/dev/null
  pip install gunicorn >/dev/null || true
}

add_hosts_entry() {
  local host="$1"
  if ! grep -qE "(^|[[:space:]])$host([[:space:]]|$)" /etc/hosts; then
    info "Adding /etc/hosts entry for $host -> 127.0.0.1 (sudo required)"
    echo "127.0.0.1 $host" | sudo tee -a /etc/hosts >/dev/null
  else
    warn "/etc/hosts already contains $host"
  fi
}

remove_hosts_entries() {
  local host="$1"
  warn "Removing /etc/hosts entries for $host (sudo required)"
  sudo sed -i '' "/[[:space:]]$host$/d" /etc/hosts || true
}

start_backend() {
  info "Starting backend on :$BE_PORT (gunicorn)"
  pushd "$ROOT_DIR" >/dev/null
  local env_file="$ROOT_DIR/.env.production"
  write_if_missing "$env_file" "ENABLE_PRODUCTION_AI=true
PORT=$BE_PORT
CORS_ORIGINS=http://$DOMAIN,http://$DOMAIN:$FE_PORT,https://$DOMAIN,http://localhost:$FE_PORT
JWT_SECRET=changeme_local
"
  source "$ROOT_DIR/.venv/bin/activate"
  gunicorn -k uvicorn.workers.UvicornWorker -w 2 --preload \
    --env-file "$env_file" \
    --bind 0.0.0.0:$BE_PORT api_server:app &
  BE_PID=$!
  popd >/dev/null
}

start_frontend() {
  info "Starting frontend on :$FE_PORT (Next.js production)"
  pushd "$FRONTEND_DIR" >/dev/null
  write_if_missing "$FRONTEND_DIR/.env.production" "NEXT_PUBLIC_DEV_MODE=false
NEXT_PUBLIC_API_BASE_URL=http://api.$DOMAIN:$BE_PORT
"
  set_env_kv "$FRONTEND_DIR/.env.production" "NEXT_PUBLIC_API_BASE_URL" "http://api.$DOMAIN:$BE_PORT"
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
  npm run build
  PORT=$FE_PORT NODE_ENV=production npm run start &
  FE_PID=$!
  popd >/dev/null
}

print_summary() {
  echo
  info "Production mode active (local)"
  echo "Frontend:   http://$DOMAIN:$FE_PORT"
  echo "Backend:    http://$DOMAIN:$BE_PORT/api/v1/health"
  echo "API (alt):  http://api.$DOMAIN:$BE_PORT/api/v1/health"
  echo "Local URLs: http://localhost:$FE_PORT and http://localhost:$BE_PORT"
  echo "PIDs: FE=$FE_PID, BE=$BE_PID"
  echo
  echo "To stop: kill $BE_PID $FE_PID"
  echo "Revert hosts: sudo sed -i '' '/$DOMAIN/d' /etc/hosts && sudo sed -i '' '/www.$DOMAIN/d' /etc/hosts && sudo sed -i '' '/api.$DOMAIN/d' /etc/hosts"
}

main() {
  info "Root: $ROOT_DIR"
  info "Domain: $DOMAIN | FE_PORT=$FE_PORT | BE_PORT=$BE_PORT"

  # Prepare env files (non-destructive + enforce API URL)
  write_if_missing "$FRONTEND_DIR/.env.production" "NEXT_PUBLIC_DEV_MODE=false
NEXT_PUBLIC_API_BASE_URL=http://api.$DOMAIN:$BE_PORT"
  set_env_kv "$FRONTEND_DIR/.env.production" "NEXT_PUBLIC_API_BASE_URL" "http://api.$DOMAIN:$BE_PORT"

  write_if_missing "$ROOT_DIR/.env.production" "ENABLE_PRODUCTION_AI=true
PORT=$BE_PORT
CORS_ORIGINS=http://$DOMAIN,http://$DOMAIN:$FE_PORT,https://$DOMAIN,http://localhost:$FE_PORT
JWT_SECRET=changeme_local"

  # Hosts mapping
  add_hosts_entry "$DOMAIN"
  add_hosts_entry "www.$DOMAIN"
  add_hosts_entry "api.$DOMAIN"

  # Backend
  ensure_python_venv
  free_port "$BE_PORT"
  start_backend

  # Frontend
  free_port "$FE_PORT"
  start_frontend

  print_summary
}

trap 'warn "Caught signal, not auto-stopping processes. Use: kill $BE_PID $FE_PID"' INT TERM
main "$@"
