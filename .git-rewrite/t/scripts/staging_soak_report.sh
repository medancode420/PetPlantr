#!/usr/bin/env bash
# Staging soak report generator for PetPlantr
# - Summarizes last 24h (configurable) hedging & ladder metrics
# - Snapshots ops config and SSE health
# - Optionally posts the report as a GitHub Issue comment via `gh`

set -Eeuo pipefail

# ========= Config =========
API_BASE="${API_BASE:-https://staging.api.petplantr.com}"
OPS_TOKEN="${OPS_TOKEN:-}"              # optional, required for /ops endpoints
PROM_URL="${PROM_URL:-}"                # e.g. http://prometheus:9090 ; optional
WINDOW="${WINDOW:-24h}"                 # supported: "<H>h" (e.g., 24h)
ISSUE_NUMBER="${ISSUE_NUMBER:-}"        # optional; if set and gh is available -> comment
GH_REPO="${GH_REPO:-}"                  # optional; owner/repo (if not current)

OUTDIR="${OUTDIR:-reports}"
mkdir -p "$OUTDIR"

# ========= Helpers =========
need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1"; exit 1; }; }
need curl
need jq

# Cross-platform UTC date from epoch
date_utc() {
  local epoch="$1"
  if command -v gdate >/dev/null 2>&1; then gdate -u -d "@$epoch" +"%Y-%m-%dT%H:%M:%SZ"
  else date -u -d "@$epoch" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -r "$epoch" +"%Y-%m-%dT%H:%M:%SZ"
  fi
}

# Parse WINDOW (H hours)
WINDOW_H="${WINDOW%h}"
[[ "$WINDOW" == "${WINDOW_H}h" && "$WINDOW_H" =~ ^[0-9]+$ ]] || { echo "WINDOW must look like 24h (got: $WINDOW)"; exit 1; }

END_EPOCH="${END_EPOCH:-$(date -u +%s)}"
START_EPOCH="${START_EPOCH:-$(( END_EPOCH - WINDOW_H*3600 ))}"
START_ISO="$(date_utc "$START_EPOCH")"
END_ISO="$(date_utc "$END_EPOCH")"

hdr_ops=()
[[ -n "$OPS_TOKEN" ]] && hdr_ops=(-H "X-Ops-Token: $OPS_TOKEN")

# Prometheus helpers (if PROM_URL set)
prom_query() {
  # $1 query, $2 time (epoch)
  curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=$1" \
    --data-urlencode "time=$2" | jq -r '.data.result[0].value[1] // empty'
}

prom_increase_24h() {
  # sum(increase(metric[WINDOW])) at END_EPOCH
  local metric="$1"
  [[ -z "$PROM_URL" ]] && { echo ""; return; }
  prom_query "sum(increase($metric[$WINDOW]))" "$END_EPOCH"
}

prom_rate_hist_p95_24h() {
  # histogram_quantile(0.95, sum(rate(<hist>_bucket[WINDOW])) by (le)) at END
  local hist="$1"
  [[ -z "$PROM_URL" ]] && { echo ""; return; }
  prom_query "histogram_quantile(0.95, sum(rate(${hist}_bucket[$WINDOW])) by (le))" "$END_EPOCH"
}

# `/metrics` snapshot helper (fallback; instantaneous)
scrape_metrics() {
  curl -s "$API_BASE/metrics"
}

grep_metric() {
  # Grep an instant metric value, returns first match (very naive)
  local name="$1"
  echo "$METRICS" | awk -v n="$name" '$1==n {print $2; exit}'
}

num_or_na() { [[ -n "${1:-}" ]] && printf "%s" "$1" || printf "N/A"; }

# ========= Collect =========
echo "Collecting from $API_BASE ($START_ISO → $END_ISO) …" 1>&2

HEALTH_JSON="$(curl -s "$API_BASE/api/v1/health" || true)"
HEALTH_PIPELINE="$(echo "$HEALTH_JSON" | jq -r '.pipeline // empty')"

# Ops config (if token available)
OPS_CFG_JSON=""
if [[ -n "$OPS_TOKEN" ]]; then
  OPS_CFG_JSON="$(curl -s "${hdr_ops[@]}" "$API_BASE/api/v1/ops/hedging/config" || true)"
fi

# SSE smoke (headers only)
SSE_HEAD="$(curl -sI "$API_BASE/api/v1/mesh/stream/demo" || true)"
SSE_CT="$(echo "$SSE_HEAD" | awk -F': ' 'tolower($1)=="content-type"{print tolower($2)}' | tr -d '\r')"

# Prometheus metrics (prefer)
LAUNCH="$(prom_increase_24h petplantr_hedge_launch_total)"
WINS="$(prom_increase_24h petplantr_hedge_win_total)"
SKIP_BUDGET="$(prom_increase_24h petplantr_hedge_skip_budget_total)"
SKIP_CAPACITY="$(prom_increase_24h petplantr_hedge_skip_capacity_total)"
SKIP_PARALLEL="$(prom_increase_24h petplantr_hedge_skip_parallel_total)"
LADDER_ACT="$(prom_increase_24h petplantr_queue_ladder_activated_total)"

# Optional latency histograms if you exported them; else will be empty (N/A)
P95_REPL_PHASE="$(prom_rate_hist_p95_24h petplantr_replicate_phase_seconds)"

# Fallback to /metrics snapshot for gauges
METRICS="$(scrape_metrics || true)"
TOKENS_USED="$(grep_metric petplantr_tokens_used)"
QUEUE_DEPTH="$(grep_metric petplantr_queue_depth)"
SYNTH_LAT_MS="$(grep_metric petplantr_synth_last_latency_ms)"

# Derived
calc_win_rate() {
  local l="$1" w="$2"
  if [[ -n "$l" && -n "$w" && "$l" != "0" ]]; then
    awk -v L="$l" -v W="$w" 'BEGIN{printf "%.1f%%", (W/L)*100.0}'
  else
    echo "N/A"
  fi
}
WIN_RATE="$(calc_win_rate "$LAUNCH" "$WINS")"

# ========= Render =========
OUT="$OUTDIR/staging_soak_${START_ISO//:/-}_to_${END_ISO//:/-}.md"
{
  echo "# PetPlantr Staging Soak – ${WINDOW} Report"
  echo ""
  echo "**Window:** \`$START_ISO\` → \`$END_ISO\`"
  echo ""
  echo "## Summary"
  echo "- Health pipeline: \`${HEALTH_PIPELINE:-N/A}\`"
  echo "- SSE content-type: \`${SSE_CT:-N/A}\` (expect: text/event-stream)"
  echo ""
  echo "## Hedging"
  echo "- Launches (Δ$WINDOW): **$(num_or_na "$LAUNCH")**"
  echo "- Wins (Δ$WINDOW): **$(num_or_na "$WINS")**"
  echo "- Win-rate: **$WIN_RATE**"
  echo "- Skips — budget: **$(num_or_na "$SKIP_BUDGET")**, capacity: **$(num_or_na "$SKIP_CAPACITY")**, parallel: **$(num_or_na "$SKIP_PARALLEL")**"
  echo ""
  echo "## Queue Ladder"
  echo "- Activations (Δ$WINDOW): **$(num_or_na "$LADDER_ACT")**"
  echo ""
  echo "## Latency (if histograms exported)"
  echo "- Replicate phase p95 (s): **$(num_or_na "$P95_REPL_PHASE")**"
  echo ""
  echo "## Gauges (snapshot)"
  echo "- Tokens in use: **$(num_or_na "$TOKENS_USED")**"
  echo "- Queue depth: **$(num_or_na "$QUEUE_DEPTH")**"
  echo "- Synthetic monitor last latency (ms): **$(num_or_na "$SYNTH_LAT_MS")**"
  echo ""
  if [[ -n "$OPS_CFG_JSON" ]]; then
    echo "## Ops Config Snapshot"
    echo '```json'
    echo "$OPS_CFG_JSON" | jq .
    echo '```'
    echo ""
  fi
  echo "## Notes"
  echo "- Missing metrics show as N/A. Set PROM_URL to compute proper 24h deltas."
  echo "- You can tune hedging at runtime via \`/api/v1/ops/hedging/config\`."
} > "$OUT"

echo "Wrote report: $OUT"

# ========= Optional GitHub issue comment =========
if [[ -n "$ISSUE_NUMBER" ]] && command -v gh >/dev/null 2>&1; then
  echo "Posting to GitHub issue #$ISSUE_NUMBER …"
  if [[ -n "$GH_REPO" ]]; then
    gh --repo "$GH_REPO" issue comment "$ISSUE_NUMBER" --body-file "$OUT"
  else
    gh issue comment "$ISSUE_NUMBER" --body-file "$OUT"
  fi
  echo "Comment posted."
else
  echo "Skipped GitHub comment (set ISSUE_NUMBER and install gh to post)."
fi
