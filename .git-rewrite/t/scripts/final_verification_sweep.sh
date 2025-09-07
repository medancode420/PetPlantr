#!/usr/bin/env bash
# PetPlantr — final verification sweep (docs, alerts, tests, smoke)
# Safe to run locally or in CI. Skips optional checks when tools are missing.

set -Eeuo pipefail

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; NC=$'\033[0m'
fail() { echo "${RED}✗${NC} $*"; exit 1; }
warn() { echo "${YELLOW}!${NC} $*"; }
ok()   { echo "${GREEN}✓${NC} $*"; }
info() { echo "${CYAN}›${NC} $*"; }

ROOT_RULES="petplantr.rules.yml"
NESTED_RULES="monitoring/prometheus/alerts/petplantr.rules.yml"
DASHBOARD="grafana/dashboards/petplantr_hedging_queue_ladder.json"
DUPE_CHECK="scripts/ci/check_no_dashboard_dupes.sh"
DOCS_GUARD="scripts/ci/check_edge_canary_docs.sh"

need() { command -v "$1" >/dev/null 2>&1; }

echo "=== PetPlantr final verification sweep ==="

# 1) Files present
[[ -f "$DASHBOARD" ]] && ok "Dashboard present: $DASHBOARD" || fail "Missing dashboard: $DASHBOARD"

RULES_PATH=""
if [[ -f "$ROOT_RULES" ]]; then RULES_PATH="$ROOT_RULES"; ok "Alert rules present: $ROOT_RULES"
elif [[ -f "$NESTED_RULES" ]]; then RULES_PATH="$NESTED_RULES"; ok "Alert rules present: $NESTED_RULES"
else fail "Missing Prometheus alert rules (looked for $ROOT_RULES or $NESTED_RULES)"
fi

# 2) Dashboard JSON sanity
if need jq; then
  jq type "$DASHBOARD" >/dev/null && ok "Dashboard JSON parses with jq" || fail "Dashboard JSON invalid"
else
  warn "jq not found — skipping JSON parse check"
fi

# 3) Alert rules lint
if need promtool; then
  promtool check rules "$RULES_PATH" >/dev/null && ok "Prometheus rules lint passed" || fail "Prometheus rules lint failed"
else
  warn "promtool not found — skipping alert lint (run: promtool check rules $RULES_PATH)"
fi

# 4) Duplicate dashboard guard (if present)
if [[ -x "$DUPE_CHECK" ]]; then
  bash "$DUPE_CHECK" && ok "No duplicate dashboard files" || fail "Duplicate dashboard files detected"
else
  info "No dupe-check script found at $DUPE_CHECK (ok)"
fi

# 4b) Edge canary docs guard (optional local)
if [[ -x "$DOCS_GUARD" ]]; then
  bash "$DOCS_GUARD" && ok "Edge canary docs guard passed" || fail "Edge canary docs guard failed"
else
  info "Docs guard script not found at $DOCS_GUARD (ok)"
fi

# 5) Secret scan (quick grep)
if git ls-files >/dev/null 2>&1; then
  if git ls-files | xargs grep -nEI --color=never 'AKIA[0-9A-Z]{16}|r8_[0-9A-Za-z]+' >/dev/null 2>&1; then
    fail "Potential secrets matched (AKIA or r8_). Review and purge before GA."
  else
    ok "Secret scan (AKIA/r8_) — clean"
  fi
else
  warn "git not available — skipping secret scan"
fi

# 6) Tests — non‑ML then Sprint C (markers)
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
if need pytest; then
  info "Running non‑ML suite (markers: not ml)…"
  pytest -q -m "not ml" -c pytest.ini || fail "Non‑ML tests failed"

  info "Running Sprint C tests…"
  pytest -q -m sprint_c -c pytest.ini || fail "Sprint C tests failed"
  ok "Tests green (non‑ML + Sprint C)"
else
  warn "pytest not found — skipping tests"
fi

# 7) k6 smoke (optional)
if need k6; then
  mkdir -p reports
  info "k6 smoke (2m) — BASE_URL=${BASE_URL:-https://staging.api.petplantr.com}"
  BASE_URL="${BASE_URL:-https://staging.api.petplantr.com}" \
  DURATION="${DURATION:-2m}" BREED_RPS="${BREED_RPS:-5}" MESH_RPS="${MESH_RPS:-1}" READ_RPS="${READ_RPS:-0.5}" MESH_BULK_RPS="${MESH_BULK_RPS:-0.2}" \
  k6 run load/k6/petplantr_load.js || fail "k6 thresholds failed"
  ok "k6 smoke passed (artifacts in reports/)"
else
  warn "k6 not found — skipping load smoke"
fi

# 8) Staging soak mini (optional)
if [[ -n "${OPS_TOKEN:-}" && -n "${API_BASE:-}" && -x ./scripts/staging_soak_report.sh ]]; then
  info "Running staging soak mini (1h)…"
  WINDOW=1h ./scripts/staging_soak_report.sh || warn "Soak reporter returned non‑zero (check output)"
  ok "Soak report generated (reports/…md)"
else
  info "Skipping soak reporter — set OPS_TOKEN & API_BASE and ensure script exists"
fi

echo
ok "Final verification sweep complete."
