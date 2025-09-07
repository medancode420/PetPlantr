# Where is the Grafana dashboard?

The canonical JSON lives here:

- `grafana/dashboards/petplantr_hedging_queue_ladder.json`

To use it:

1) Import the file in Grafana (or run the provided provisioning bundle under `grafana/provisioning/*`).
2) Map the datasource named **Prometheus** at import time.
3) Optional: `docker-compose -f docker-compose.grafana.yml up -d` with `PROMETHEUS_URL` set.

Why no copy at repo root? To avoid drift; this file is the single source of truth.
