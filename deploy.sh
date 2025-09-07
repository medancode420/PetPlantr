#!/usr/bin/env bash
# deploy.sh - Simple deployment helper for PetPlantr
# Supports custom project path via PROJECT_DIR env or --dir flag.
# Optional Docker compose deploy and Google Drive sync placeholder.

set -euo pipefail

print_help() {
  cat <<'EOF'
Usage: ./deploy.sh [--dir DIR] [--no-docker] [--pull]

Options:
  --dir DIR      Target directory (default: $PROJECT_DIR or current dir)
  --no-docker    Skip docker compose up/build
  --pull         git pull --rebase before deploy
  -h, --help     Show this help

Environment:
  PROJECT_DIR          If set, used as default target directory
  GOOGLE_DRIVE_SYNC=1  If set, attempt a Google Drive sync (requires tooling)
  GDRIVE_FOLDER_ID     Drive folder ID to sync to (if GOOGLE_DRIVE_SYNC=1)
EOF
}

USE_DOCKER=1
DO_PULL=0
TARGET_DIR="${PROJECT_DIR:-$(pwd)}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) TARGET_DIR="$2"; shift 2;;
    --no-docker) USE_DOCKER=0; shift 1;;
    --pull) DO_PULL=1; shift 1;;
    -h|--help) print_help; exit 0;;
    *) echo "Unknown option: $1"; print_help; exit 1;;
  esac
done

info(){ echo "[deploy] $*"; }
die(){ echo "[deploy][error] $*" >&2; exit 1; }

mkdir -p "$TARGET_DIR" || true
cd "$TARGET_DIR" || die "cannot cd $TARGET_DIR"

if [[ ! -d .git ]]; then
  info "Cloning repository into $TARGET_DIR"
  git clone https://github.com/medancode420/PetPlantr.git . || die "git clone failed"
fi

if [[ "$DO_PULL" -eq 1 ]]; then
  info "Pulling latest changes..."
  git pull --rebase --autostash || true
fi

if [[ "$USE_DOCKER" -eq 1 && -f docker-compose.yml ]]; then
  info "Deploying via docker compose..."
  (docker compose up -d --build || docker-compose up -d --build) || die "docker compose failed"
else
  info "Skipping docker compose (either disabled or file missing)."
fi

# Optional: Google Drive sync placeholder using rclone or gdrive
if [[ "${GOOGLE_DRIVE_SYNC:-0}" == "1" ]]; then
  if command -v rclone >/dev/null 2>&1 && [[ -n "${GDRIVE_FOLDER_ID:-}" ]]; then
    info "Syncing selected artifacts to Google Drive via rclone (remote 'gdrive:')"
    rclone copy ./artifacts "gdrive:${GDRIVE_FOLDER_ID}" --transfers=4 --checkers=8 || true
  else
    info "GOOGLE_DRIVE_SYNC=1 set, but rclone or GDRIVE_FOLDER_ID not available; skipping."
  fi
fi

info "Deploy complete."
