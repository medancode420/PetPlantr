#!/usr/bin/env bash
# Helper functions for PetPlantr ops. Source this file, don't execute.
#   source scripts/ops_quick.sh
# Requires: API_BASE, OPS_TOKEN

set -Eeuo pipefail

: "${API_BASE:?Set API_BASE, e.g., https://api.petplantr.com}"
: "${OPS_TOKEN:?Set OPS_TOKEN}"

_hdr=(-H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json")

op_health() { curl -s "$API_BASE/api/v1/health" | jq .; }
op_sse_head() { curl -sI "$API_BASE/api/v1/mesh/stream/demo" | sed -n '1,20p'; }
op_cfg() { curl -s "${_hdr[@]:0:1}" "$API_BASE/api/v1/ops/hedging/config" | jq .; } # only token header for GET

op_set() {
  # Usage: op_set hedging_min_delay_ms 400 hedging_budget_per_min 5 hedging_max_parallel_hedges 1
  local -a kv=()
  while (( "$#" )); do
    key="$1"; val="$2"; shift 2
    kv+=("\"$key\":$val")
  done
  local body="{${kv[*]// /,}}"
  curl -s -X POST "${_hdr[@]}" -d "$body" "$API_BASE/api/v1/ops/hedging/config" | jq .
}

op_kill_on()  { curl -s -X POST "${_hdr[@]}" -d '{"action":"enable"}'  "$API_BASE/api/v1/ops/kill-switch" | jq .; }
op_kill_off() { curl -s -X POST "${_hdr[@]}" -d '{"action":"disable"}' "$API_BASE/api/v1/ops/kill-switch" | jq .; }
op_audit()    { local n="${1:-10}"; curl -s "${_hdr[@]:0:1}" "$API_BASE/api/v1/ops/audit/recent?n=$n" | jq .; }

# Staging-only chaos
op_chaos429() { curl -s "$API_BASE/api/v1/chaos/force_status?code=429"; }
op_chaos503() { curl -s "$API_BASE/api/v1/chaos/force_status?code=503"; }

# Examples:
#   op_cfg
#   op_set hedging_min_delay_ms 300 hedging_budget_per_min 3 hedging_max_parallel_hedges 1
#   op_kill_on; op_kill_off
#   op_audit 20
