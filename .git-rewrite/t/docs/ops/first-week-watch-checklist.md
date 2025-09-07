# PetPlantr – First‑Week Watch (48‑Hour Playbook)

**Audience:** On‑call / SRE / Release lead  
**Goal:** Boring, safe GA; quick detection and rollback if needed.

## T‑0 (After Deploy)
1. **Health & SSE**
   ```bash
   curl -s $API_BASE/api/v1/health | jq .
   curl -i $API_BASE/api/v1/mesh/stream/demo | head -n 15
   ```
2. Dashboards: open Grafana → PetPlantr — Hedging & Queue Ladder
3. Flags: confirm prod defaults (hedging off; ladder on; synthetic on)
4. Canary Plan (if not already complete)
   - Ramp 10% → 50% → 100%, hold 30–120 min at each step.

## Success gates at each hold
- Breed p95 < 500 ms
- Mesh acceptance p95 < 1500 ms
- Hedge win‑rate ≥ 20%
- Ladder < 10% of mesh
- Error rate < 1%

## Hourly Quick Scan (Day 1)
- Panels: Hedge Win‑Rate, Queue Ladder/min, ProviderBusy by reason, p95s, Synthetic
- Gauges: `petplantr_queue_depth`, `petplantr_tokens_used`, `petplantr_synth_last_latency_ms`
- k6 smoke (non‑blocking):

```bash
make load-test BASE_URL=$API_BASE DURATION=2m BREED_RPS=5 MESH_RPS=1 READ_RPS=0.5 MESH_BULK_RPS=0.2
```

## Day 2 (Trend Check)
- Win‑rate stability, ladder spikes, provider timeouts
- Consider tuning:
  - Improve win‑rate: decrease `hedging_min_delay_ms` by 50–100 ms
  - Reduce cost/secondaries: increase `hedging_min_delay_ms`; keep `hedging_max_parallel_hedges=1`
  - Provider unstable: keep ladder on; raise backoff; notify provider

## Alerting (Prometheus)
- HedgeWinRateLow: win‑rate < 20% for 10m
- QueueLadderSpike: increase > 20 in 5m
- SyntheticLatencyHigh: last latency > 1500 ms for 5m
- ProviderBusySpike: increase > 20 in 5m

## Runtime Ops (copy‑paste)
```bash
# Read config
curl -s -H "X-Ops-Token: $OPS_TOKEN" $API_BASE/api/v1/ops/hedging/config | jq .

# Conservative hedging
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_max_parallel_hedges":1,"hedging_min_delay_ms":300,"hedging_budget_per_min":3}' \
  $API_BASE/api/v1/ops/hedging/config | jq .

# Disable secondaries fast
curl -s -X POST -H "X-Ops-Token: $OPS_TOKEN" -H "Content-Type: application/json" \
  -d '{"hedging_max_parallel_hedges":0}' \
  $API_BASE/api/v1/ops/hedging/config | jq .
```

## Decision Matrix
| Symptom | Likely Cause | Action |
|--|--|--|
| Win‑rate < 15% | Delay too low / traffic burst | Raise `hedging_min_delay_ms` by 100–200 ms |
| Ladder > 15% | Provider throttling | Keep ladder on; raise backoff; notify provider |
| Breed p95 > 500 ms | App regression / overload | Check queue depth; scale app; reduce mesh concurrency |
| Synthetic > 1500 ms | Edge/cold starts | Verify keep‑alives; scale; check ProviderBusy |
| Cost spike | Over‑hedging | Increase delay; ensure `hedging_max_parallel_hedges=1` |

## Staging Soak (daily)
```bash
API_BASE=https://staging.api.petplantr.com OPS_TOKEN=$OPS_TOKEN PROM_URL=$PROM_URL \
WINDOW=24h ./scripts/staging_soak_report.sh
```

## Rollback
- Runtime: `hedging_max_parallel_hedges=0` (immediate) or raise min delay ≥ 1000 ms
- Env: disable `FEATURE_ADAPTIVE_HEDGING` / `FEATURE_QUEUE_LADDER` (restart)
- Hard: revert tag/PR and redeploy
