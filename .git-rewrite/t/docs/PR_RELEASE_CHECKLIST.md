# PetPlantr — PR & Release Checklist

## PR (pre‑merge)
- [ ] Unit/integration tests (non‑ML) green:
  ```bash
  export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
  pytest -q -p pytest_cov -p pytest_asyncio -p respx -m "not ml" \
    --maxfail=1 --cov=src --cov-report=term-missing --cov-report=xml:coverage.xml
  ```
  Coverage ≥ target (≥ 80%).

- [ ] k6 smoke (2m) passes thresholds:

```bash
make load-test BASE_URL=https://staging.api.petplantr.com DURATION=2m \
  BREED_RPS=5 MESH_RPS=1 READ_RPS=0.5 MESH_BULK_RPS=0.2
```

- [ ] Staging soak reporter (1h mini) generated and reviewed:

```bash
OPS_TOKEN=$OPS_TOKEN API_BASE=https://staging.api.petplantr.com WINDOW=1h ./scripts/staging_soak_report.sh
```

- [ ] Security: no secrets in diff (gitleaks or grep quick scan).

- [ ] Release notes updated (docs/releases/...), CHANGELOG updated.

## Release (RC/GA)
- [ ] Feature flags set (prod):

```
FEATURE_ADAPTIVE_HEDGING=false
HEDGING_MAX_PARALLEL_HEDGES=1
HEDGING_MIN_DELAY_MS=300
HEDGING_BUDGET_PER_MIN=3
FEATURE_QUEUE_LADDER=true
FEATURE_SYNTHETIC_MONITOR=true
FEATURE_CHAOS_TEST=false
OPS_TOKEN=<set>
```

- [ ] Health & SSE smoke:

```bash
curl -s https://api.petplantr.com/api/v1/health | jq .
curl -i https://api.petplantr.com/api/v1/mesh/stream/demo | head -n 15
```

- [ ] Queue‑ladder sanity (staging with chaos):

```bash
curl -s "https://staging.api.petplantr.com/api/v1/chaos/force_status?code=429&provider=true" | head
```

- [ ] Tag & GitHub Release:

```bash
git checkout main && git pull
git tag -a vX.Y.Z -m "PetPlantr – <summary>"
git push --tags
gh release create vX.Y.Z --title "PetPlantr – <title>" --notes-file docs/releases/<file>.md
```

## Canary & Rollout
- [ ] Enable hedging for 5–10% traffic; monitor 60–120 min.
- [ ] Watch Grafana dashboard: win‑rate, ladder rate, p95s, synthetic gauge.
- [ ] Roll forward (50% → 100%) or roll back:
  - Runtime: `hedging_max_parallel_hedges=0` or raise `hedging_min_delay_ms>1000`
  - Env: `FEATURE_ADAPTIVE_HEDGING=false`, `FEATURE_QUEUE_LADDER=false`

## Post‑launch (first 48h)
- [ ] Staging soak report (24h) posted to tracking issue.
- [ ] k6 smoke daily (non‑blocking CI) green.
- [ ] Alerts on: HedgeWinRateLow, QueueLadderSpike, SyntheticLatencyHigh, ProviderBusySpike.
- [ ] Audit log spot‑check; verify ops changes are recorded.
