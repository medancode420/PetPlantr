---
name: "Staging Soak Report (24h) – Adaptive Hedging"
about: Summarize a 24h staging soak with hedging enabled (safe defaults).
title: "Staging Soak Report: v1.0.0-rc.1 — <YYYY‑MM‑DD>"
labels: ["staging-soak","ops","observability"]
assignees: []
---

## Window
- Start (UTC): <!-- 2025-08-10T00:00Z -->
- End   (UTC): <!-- 2025-08-11T00:00Z -->

## Flags / Tuning
```
FEATURE_ADAPTIVE_HEDGING=true
hedging_max_parallel_hedges=<1>
hedging_min_delay_ms=<300>
hedging_budget_per_min=<3>
```

## SLOs
- Breed p95: `<ms>` (target < 500 ms)
- Mesh success p95: `<min>` (target < 10 min)
- Error rate: `<%>` (target < 1%)

## Hedging
- Launches: `<n>`
- Wins: `<n>` (win‑rate = `<%>`)
- Skips: budget=`<n>`, capacity=`<n>`, parallel_cap=`<n>`, disabled=`<n>`
- Delay (ms) p50/p95: `<p50>` / `<p95>`

## Queue Ladder
- Activations: `<n>`  (% of mesh requests = `<%>`)

## SSE
- Reconnects / Clients: `<n>` / `<n>`
- Last‑Event‑ID resume: `<pass|fail>`

## Synthetic Monitor
- p95 latency: `<ms>`
- Availability: `<%>`

## Anomalies
- …

## Actions
- Tune min_delay_ms to `<val>` (why)
- Adjust parallel cap to `<val>` (why)
- Keep/disable ladder (why)
