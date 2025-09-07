# PetPlantr v0.3.0 — Sprint C Reliability Completion (2025-08-25)

Highlights
- Synthetic monitor race fixed (FastAPI lifespan, idempotent start, one-shot fallback). `/api/v1/ops/synthetic/live` always registered; gated by `ENABLE_SYNTHETIC_MONITOR`.
- Breed detection wired with lazy model load + ML gating; resilient even when deps absent.
- Canary NGINX validated (10% canary, sticky cookie, SSE proxying).
- Frontend middleware expanded to allow `/upload` and `/api/v1/ops/(.*)` as public.
- Tests: sprint_c markers, fast runs with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, >=90% coverage via `--cov=src`.
- Minimal deps maintained; added `redis==5.0.1`, `pyjwt==2.9.0` safely.

Upgrade notes
1) Set envs as needed:
   - `ENABLE_SYNTHETIC_MONITOR=true`
   - `REDIS_URL` (optional for rate limits/job state; fallback is in-memory)
   - `JWT_SECRET`, `CORS_ORIGINS` (comma-separated)
   - `REPLICATE_API_TOKEN` (sanitized automatically; no quotes/newlines)
2) Run tests:
   - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --cov=src -c pytest.ini`
3) Deploy:
   - `gunicorn -k uvicorn.workers.UvicornWorker -w 4 api_server:app`
   - Smoke test: `GET /api/v1/ops/synthetic/live` (200 JSON when enabled)
4) Canary rollout:
   - Use `nginx/canary_api.conf` (10% split, sticky, SSE). Monitor for ~1h.

Rollback
- `git revert` the release commit, redeploy prior image, set canary weight=0, unset new feature flags. Monitor error rates, p95 latency, and synthetic heartbeat.

References
- CHANGELOG: `CHANGELOG.md` (v0.3.0)
- NGINX: `nginx/canary_api.conf`
- Tests: `pytest.ini`, `Makefile` (target: `test-sprint-c`)
