# PetPlantr – Ops Quick‑Commands (Cheat Sheet)

Set these first (no secrets in history — use envs):

```bash
export API_BASE="https://api.petplantr.com"   # or your staging base URL
export OPS_TOKEN="YOUR_OPS_TOKEN"
```

All token‑gated endpoints expect the header: `X-Ops-Token: $OPS_TOKEN`.

## Health & SSE smoke

```bash
# Health (expect pipeline: real)
curl -s "$API_BASE/api/v1/health" | jq .

# SSE headers + first frames (non-blocking peek)
curl -i "$API_BASE/api/v1/mesh/stream/demo" | head -n 10

# SSE follow stream (Ctrl+C to stop)
curl -N "$API_BASE/api/v1/mesh/stream/demo"
```

## Hedging – read current runtime config

```bash
curl -s -H "X-Ops-Token: $OPS_TOKEN" \
  "$API_BASE/api/v1/ops/hedging/config" | jq .
```

## Update runtime (safe clamps applied)

```bash
# Conservative defaults
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_max_parallel_hedges":1,"hedging_min_delay_ms":300,"hedging_budget_per_min":3}' \
  "$API_BASE/api/v1/ops/hedging/config" | jq .

# Raise delay by +100ms
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_min_delay_ms":400}' "$API_BASE/api/v1/ops/hedging/config" | jq .

# Disable secondaries (cap=0)
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_max_parallel_hedges":0}' "$API_BASE/api/v1/ops/hedging/config" | jq .
```

Note: Turning the feature on/off is via env flag `FEATURE_ADAPTIVE_HEDGING`.

## Kill‑switch (feature‑flag guardrail)

```bash
# Enable kill-switch
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"action":"enable"}' "$API_BASE/api/v1/ops/kill-switch" | jq .

# Disable kill-switch
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"action":"disable"}' "$API_BASE/api/v1/ops/kill-switch" | jq .
```

## Audit trail (ring buffer; optional file sink in prod)

```bash
# Last 10 events
curl -s -H "X-Ops-Token: $OPS_TOKEN" \
  "$API_BASE/api/v1/ops/audit/recent?n=10" | jq .
```

## Chaos / Queue Ladder smoke (staging only)

```bash
# Only works if FEATURE_CHAOS_TEST=true (staging)
curl -s "$API_BASE/api/v1/chaos/force_status?code=429"

# Expect production path to convert upstream 429/503 -> 202 (when FEATURE_QUEUE_LADDER=true)
# Check the header in mesh responses:
curl -s -D - -o /dev/null -F image=@tiny.png "$API_BASE/api/v1/mesh/generate" \
  | grep -i X-Queue-Ladder || true
```

## Gauges & Prometheus

```bash
# Quick gauge peek (snapshot)
curl -s "$API_BASE/metrics" | egrep 'petplantr_(tokens_used|queue_depth|synth_last_latency_ms)'

# Example PromQL (replace PROM_URL)
# Hedge launches (24h delta)
curl -sG "$PROM_URL/api/v1/query" \
  --data-urlencode 'query=sum(increase(petplantr_hedge_launch_total[24h]))' \
  --data-urlencode "time=$(date -u +%s)" | jq .
```

## Rollback (no deploy needed)

- Soft runtime levers: `hedging_max_parallel_hedges=0`, or increase `hedging_min_delay_ms` to `1000+`
- Harder switch: set `FEATURE_ADAPTIVE_HEDGING=false` (env + restart)
- Queue ladder off: `FEATURE_QUEUE_LADDER=false` (env + restart)

## Safety notes

- Never paste real tokens into issues or chat; use `X-Ops-Token` header only.
- All runtime changes are atomic and audited.
- Multi‑instance: hedging cap fan‑out via Redis if configured; min‑delay and budget are per‑instance unless you added sync for them too.

---

## Multi‑instance ops‑sync (Redis)

When multiple app instances run behind a load balancer, runtime ops changes can fan‑out via Redis Pub/Sub if configured.

- Env vars:
  - `REDIS_URL` (e.g. `redis://redis:6379/0`)
  - `OPS_PUBSUB_CHANNEL` (default `petplantr:ops:hedging:pubsub`)
  - `OPS_CAP_KEY` (default `petplantr:ops:hedging_max_parallel_hedges`)
- Supported keys broadcast today:
  - `hedging_max_parallel_hedges` (persisted via `OPS_CAP_KEY`)
  - `hedging_min_delay_ms`, `hedging_budget_per_min` (applied with safety clamps)
- Unknown keys are ignored by subscribers.

Quick publish (ops box) example:

```bash
# Publish new parallel cap to all instances
redis-cli -u "$REDIS_URL" PUBLISH petplantr:ops:hedging:pubsub \
  '{"key":"hedging_max_parallel_hedges","value":3}'
```

Verification tests (local):

- `pytest -q -k ops_sync_subscriber -m sprint_c` (subscriber fan‑out)
- `pytest -q tests/test_ops_sync_subscriber_edges.py -m sprint_c` (edge keys/clamps)
- `pytest -q tests/test_ops_sync_fanout.py` (HTTP publish path)

---

## scripts/ops_quick.sh usage

```bash
source scripts/ops_quick.sh
op_cfg
op_set hedging_min_delay_ms 350 hedging_budget_per_min 4
```
