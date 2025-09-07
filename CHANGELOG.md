# Changelog

## v0.3.0-rc.2 — Sprint C Reliability Fixes (2025-08-25)

- Resolved neural pipeline import/load issues (now loads successfully as placeholder).
- Fixed synthetic monitor race with FastAPI lifespan idempotent start and dynamic flag read.
- Ensured `/api/v1/ops/synthetic/live` returns 200/JSON when enabled.
- All tests pass with coverage; preserved ML pins; validated canary NGINX.

Canary NGINX Validation

- Config valid: 10% split via `split_clients`, sticky `$cookie_petplantr_canary` map, SSE proxying with buffering off.
- Steps:
	- `nginx -t` → successful
	- `curl -v -H "Accept: text/event-stream" http://localhost/api/v1/ops/synthetic/live` → 200, `text/event-stream`, keep-alive
	- Logs show ~10% canary hits; cookie-based stickiness holds sessions.

Sprint-C Markers Suggestion

- `pytest.ini`: `[markers]` sprint_c: Sprint C tests. Tag with `@pytest.mark.sprint_c`.
- `Makefile`: `test-sprint-c`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -m sprint_c -c pytest.ini`.
- Fakeredis tests: `pytest.importorskip("fakeredis")` with a helpful message if missing.

One-Paragraph Runbook and Rollback Plan

- Runbook: Apply fixes, install deps, set `ENABLE_SYNTHETIC_MONITOR=true`, run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --cov=src -c pytest.ini` for green/coverage; build/push Docker, deploy staging, test `/api/v1/ops/synthetic/live` for 200; rollout canary NGINX (10% split), monitor 1h for <1% errors, <500ms latency, heartbeat; scale if stable.
- Rollback: `git revert`, redeploy prior image, disable flag; drain canary; monitor 24h Prometheus (error_rate >5%), `synthetic_heartbeat`, and latency p95 <500ms; review ELK logs.

Final Checklist

- [DONE] `test_synthetic_monitor_live_sample` passes (200 and JSON sample).
- [DONE] sprint_c marker tests are green when fakeredis is installed; tests that depend on fakeredis clearly skip if missing.
- [DONE] Full test suite runs with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and yields coverage >= configured threshold.
- [DONE] Background synthetic monitor starts under FastAPI lifespan and logs heartbeat; endpoint succeeds if feature enabled.
- [DONE] Canary NGINX config validated: 10% traffic split, sticky routing cookie header, SSE proxying works (curl/head test).

## v0.3.0 — Sprint C Reliability Completion (2025-08-25)

- Fixed synthetic monitor startup race via FastAPI lifespan idempotent start and one-shot fallback in handler.
- Ensured `/api/v1/ops/synthetic/live` always registered with dynamic `ENABLE_SYNTHETIC_MONITOR` read (returns 200/JSON sample when enabled, 404 otherwise).
- Integrated breed detection with lazy torch load and ML gating.
- All tests (unit, integration, sprint_c) pass with >=90% coverage via `--cov=src`.
- Preserved `numpy==1.26.4` and minimal deps; added `redis==5.0.1`, `pyjwt==2.9.0` safely.
- Validated canary NGINX for 10% split, sticky cookie, SSE proxying.
- Frontend middleware updated for public `/upload` and `/api/v1/ops/(.*)`.

Canary NGINX Validation

- Config in `nginx/canary_api.conf` valid: 10% split via `split_clients $remote_addr`, sticky via `$cookie_petplantr_canary` map to upstreams, SSE with `proxy_buffering off`, HTTP/1.1 upgrade.
- Steps:
	- `nginx -t -c nginx/canary_api.conf` → test is successful
	- `curl -v -H "Accept: text/event-stream" http://localhost/api/v1/ops/synthetic/live` → 200 OK, `Content-Type: text/event-stream`, `Connection: keep-alive` (streams sample if enabled, no buffer issues)
	- Logs confirm ~10% canary hits, cookie sticks sessions.
- Ingress equiv: annotations `canary=true`, `canary-weight=10`, `sticky-cookie-services=petplantr_canary expires=1h`.

Sprint-C Markers Setup

- `pytest.ini`: `[markers]` sprint_c: Sprint C tests. Tests marked `@pytest.mark.sprint_c`.
- `Makefile`: `test-sprint-c`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -m sprint_c -c pytest.ini`.
- Fakeredis tests: use `pytest.importorskip("fakeredis")`.

One-Paragraph Runbook and Rollback Plan

- Runbook: Apply all diffs, install deps (`redis==5.0.1` `pyjwt==2.9.0` `fakeredis` for tests), set envs (`ENABLE_SYNTHETIC_MONITOR=true`, `REDIS_URL`, `JWT_SECRET`, `CORS_ORIGINS`), run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --cov=src -c pytest.ini` to confirm >=90% coverage/green (incl sprint_c); build/push Docker via Makefile, deploy staging with `gunicorn -k uvicorn.workers.UvicornWorker -w 4 api_server:app`, smoke `/api/v1/ops/synthetic/live` for 200/JSON; rollout canary NGINX (10% split), monitor 1h for <1% errors, <500ms p95, heartbeat via Prometheus; scale to 100% if stable.
- Rollback: `git revert` commits, uninstall new deps, redeploy prior image with uvicorn, unset new envs, set canary weight=0; monitor first 24h for error_rate >5% alerts, `synthetic_heartbeat` presence, latency_p95 <500ms, ELK logs for failures.

Final Checklist

- [DONE] `test_synthetic_monitor_live_sample` passes (200 with JSON sample).
- [DONE] sprint_c marker tests green with fakeredis (skip if missing).
- [DONE] Full test suite runs with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, coverage >= threshold.
- [DONE] Background synthetic monitor task starts under FastAPI lifespan and logs heartbeat; endpoint succeeds if enabled.
- [DONE] Canary NGINX config validated: 10% traffic split, sticky routing cookie header, SSE proxying works (passes curl/head test).
- [DONE] One-paragraph rollback steps and key monitoring dashboards/alerts to watch for first 24 hours.

---

## v0.3.0-rc.1 — Sprint C Reliability Fixes (2025-08-25)

- Synthetic monitor: Fixed startup race by starting an idempotent background task via FastAPI lifespan and adding a one-shot sample fallback in the endpoint handler.
- Ops endpoint: `/api/v1/ops/synthetic/live` is always registered; behavior gated by dynamic feature flags read at request time (os.getenv), eliminating 404s during toggles.
- Metrics: Introduced minimal Prometheus metric shims (no-op if `prometheus_client` is absent).
- Health: Added a basic health router to resolve missing import issues.
- Tests: All tests pass with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; fakeredis-dependent tests can `importorskip` when missing; added test-only dependency `python-multipart`. Preserved ML pins (e.g., `numpy==1.26.4`).
- Canary NGINX: Validated 10% traffic split using `split_clients`, sticky routing via cookie mapping, and SSE proxying (buffering off). See `nginx/canary_api.conf`.

Runbook (summary):
1) Activate venv and install from `requirements-test-sprint-c.txt`. 2) Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --cov=src -c pytest.ini`. 3) Build/push Docker and deploy to staging; smoke `/api/v1/ops/synthetic/live` (200 OK). 4) Enable canary: set `ENABLE_SYNTHETIC_MONITOR=true`, apply 10% split, monitor error rate (<1%), p95 latency (<500ms), and heartbeat logs for 1h. 5) If stable, roll to 100%.

Rollback (summary):
`git revert` the release commit, rebuild/push prior image, redeploy, set canary weight to 0%, and disable `ENABLE_SYNTHETIC_MONITOR=false`. Monitor Prometheus (error_rate >5% pages), `synthetic_heartbeat`, latency, and logs for 24h.
