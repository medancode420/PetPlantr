# PetPlantr — Canary Rollout Runbook (v1.0.0)

Goal: Safely enable Adaptive Hedging in production using a staged canary: 10% → 50% → 100%, with clear success gates, one‑line rollbacks, and live tuning.

Audience: Release lead / SRE / On‑call

---

## 0) Preconditions
RC built & deployed; CI green; validation script green.

OPS_TOKEN configured in prod (ops endpoints are token‑gated).

Prod defaults (env):

- `FEATURE_ADAPTIVE_HEDGING=false`
- `HEDGING_MAX_PARALLEL_HEDGES=1`
- `HEDGING_MIN_DELAY_MS=300`
- `HEDGING_BUDGET_PER_MIN=3`
- `FEATURE_QUEUE_LADDER=true`
- `FEATURE_SYNTHETIC_MONITOR=true`
- `FEATURE_CHAOS_TEST=false`

Observability live:

- Grafana dashboard: `grafana/dashboards/petplantr_hedging_queue_ladder.json`
- Alerts validated:

```bash
promtool check rules monitoring/prometheus/alerts/petplantr.rules.yml
```

---

## 1) Quick preflight (5 min)
```bash
# Health (expect pipeline: real)
curl -s https://api.petplantr.com/api/v1/health | jq .

# SSE headers (expect 200 + text/event-stream + retry + id)
curl -i https://api.petplantr.com/api/v1/mesh/stream/demo | head -n 15
```

Optional smoke (2 minutes, light traffic):
```bash
make load-test BASE_URL=https://api.petplantr.com DURATION=2m \
  BREED_RPS=5 MESH_RPS=1 READ_RPS=0.5 MESH_BULK_RPS=0.2
```

---

## 2) Routing strategy (pick one)
A) Instance/Pool canary (recommended)
- Run a single replica or region with `FEATURE_ADAPTIVE_HEDGING=true`.
- Route 5–10% traffic to this pool via LB/edge.

B) Percent split at edge
- Route 5–10% to a hedging‑enabled deployment (same service, different env).
- If your edge supports labeling, add `X-Route: canary` for log attribution.

Note: enabling/disabling hedging itself is env‑gated (`FEATURE_ADAPTIVE_HEDGING`). Runtime POST only tunes delay/budget/cap.

---

## 3) Enable hedging on the canary pool
Verify access & current runtime config:
```bash
curl -s -H "X-Ops-Token: $OPS_TOKEN" \
  https://api.petplantr.com/api/v1/ops/hedging/config | jq .
```

Apply conservative tuning (runtime, atomic):
```bash
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_max_parallel_hedges":1,"hedging_min_delay_ms":300,"hedging_budget_per_min":3}' \
  https://api.petplantr.com/api/v1/ops/hedging/config | jq .
```

---

## 4) Start canary at 5–10% (hold 30–60 min)
Success gates (all must hold):

- Breed p95 < 500 ms
- Mesh acceptance p95 (202 path) < 1500 ms
- Hedge win‑rate ≥ 20%
- Queue‑ladder activations < 10% of mesh requests
- Error rate < 1%

Quick checks:
```bash
# Gauges snapshot
curl -s https://api.petplantr.com/metrics | egrep 'petplantr_(queue_depth|tokens_used|synth_last_latency_ms)'

# Ladder incidence on a mesh request (look for X-Queue-Ladder)
curl -s -D - -o /dev/null -F image=@<(printf x) \
  https://api.petplantr.com/api/v1/mesh/generate | grep -i X-Queue-Ladder || true
```

---

## 5) Ramp schedule
- Step 1 → 10% (hold 30–60 min)
- Step 2 → 50% (hold 60–120 min)
- Step 3 → 100%

At each hold:
- Check Grafana: Hedge Win‑Rate, Queue Ladder Activations/min, ProviderBusy by reason, p95s, Synthetic monitor.
- If win‑rate < 15% or breed p95 worsens → increase `hedging_min_delay_ms` by +100–200 ms.
- If cost/secondaries feel high → keep `hedging_max_parallel_hedges=1` (don’t raise it yet).

---

## 6) Live tuning (runtime ops commands)
Raise delay (fewer secondaries/cost):
```bash
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_min_delay_ms":400}' \
  https://api.petplantr.com/api/v1/ops/hedging/config | jq .
```

Drop to zero secondaries quickly:
```bash
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_max_parallel_hedges":0}' \
  https://api.petplantr.com/api/v1/ops/hedging/config | jq .
```

Audit recent ops changes:
```bash
curl -s -H "X-Ops-Token: $OPS_TOKEN" \
  https://api.petplantr.com/api/v1/ops/audit/recent?n=20 | jq .
```

---

## 7) Rollback (no redeploy in most cases)
Soft disable (runtime):
```bash
# Stop secondaries immediately
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_max_parallel_hedges":0}' \
  https://api.petplantr.com/api/v1/ops/hedging/config | jq .
```

- Reduce canary weight back to 0% at the LB/edge.
- Hard disable (env + restart): set `FEATURE_ADAPTIVE_HEDGING=false` on canary pool.
- Queue ladder off (only if necessary): set `FEATURE_QUEUE_LADDER=false` (env + restart)—you’ll see raw provider 429/503 again.

---

## 8) Success criteria → 100%
Proceed to full rollout when 50% for 60–120 min meets gates:

- Breed p95 < 500 ms
- Mesh acceptance p95 < 1500 ms
- Hedge win‑rate ≥ 20% (stable)
- Queue‑ladder < 10% and trending down
- No error spikes / incidents

---

## 9) After 100% (48‑hour watch)
- Keep Grafana dashboard open; alerts active (`HedgeWinRateLow`, `QueueLadderSpike`, `SyntheticLatencyHigh`, `ProviderBusySpike`).
- Daily staging soak report:
```bash
API_BASE=https://staging.api.petplantr.com OPS_TOKEN=$OPS_TOKEN PROM_URL=$PROM_URL \
WINDOW=24h ./scripts/staging_soak_report.sh
```
- Keep the non‑blocking k6 smoke CI job.

---

## 10) Decision matrix
Symptom | Likely cause | Action
--- | --- | ---
Hedge win‑rate < 15% | Delay too low / burst | Increase `hedging_min_delay_ms` by 100–200 ms
Ladder > 15% | Provider throttling | Keep ladder on; raise backoff; notify provider
Breed p95 > 500 ms | App regression / overload | Check queue depth; reduce mesh concurrency; scale
Synthetic > 1500 ms | Edge/cold starts | Verify keep‑alives; scale; inspect ProviderBusy
Cost spike | Over‑hedging | Raise delay; ensure `hedging_max_parallel_hedges=1`

---

## 11) Notes & guarantees
- Internal 429s remain 429. Only provider 429/503/timeouts are laddered to 202 with `X-Queue-Ladder: true`.
- Ops endpoints are token‑gated; all changes are audited (ring buffer + optional file sink).
- Runtime tuning is atomic and per‑instance unless you enabled config fan‑out.

---

## 12) Handy one‑liners
```bash
# Health
curl -s https://api.petplantr.com/api/v1/health | jq .

# SSE headers
curl -i https://api.petplantr.com/api/v1/mesh/stream/demo | head -n 15

# Read hedging config
curl -s -H "X-Ops-Token: $OPS_TOKEN" \
  https://api.petplantr.com/api/v1/ops/hedging/config | jq .
```

---

If desired, prepare edge config snippets (NGINX / Traefik / Cloudflare) for a clean 90/10 → 50/50 → 100/0 split and optional `X-Route: canary` attribution.
