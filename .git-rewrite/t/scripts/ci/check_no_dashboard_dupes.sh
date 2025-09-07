#!/usr/bin/env bash
set -euo pipefail
root="./petplantr_hedging_queue_ladder.json"
canon="./grafana/dashboards/petplantr_hedging_queue_ladder.json"
if [[ -f "$root" && -f "$canon" && ! -L "$root" ]]; then
  echo "Duplicate dashboard JSON detected (root & grafana/dashboards)."
  echo "Keep only the canonical file under grafana/dashboards/ or make the root a symlink."
  exit 1
fi
