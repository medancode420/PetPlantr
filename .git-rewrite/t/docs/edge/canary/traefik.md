# PetPlantr — Canary with Traefik (weighted services)

Weighted split (90/10) with:
- Sticky cookie `pp_canary` to pin users
- Extended timeouts for SSE via `serversTransport`
- Optional headers middleware for `X-Accel-Buffering: no` and `Cache-Control: no-cache`

> Traefik can’t attach branch‑specific response headers in a weighted service. For attribution, set `X-Route` from the app, or use separate routers.

## Dynamic config (file provider)

```yaml
# traefik_dynamic.yml
http:
  routers:
    petplantr:
      rule: Host(`api.petplantr.com`)
      entryPoints: [websecure]
      tls: true
      service: petplantr-split
      middlewares:
        - pp-sse-hints
        - pp-sec-headers

  middlewares:
    pp-sse-hints:
      headers:
        customResponseHeaders:
          X-Accel-Buffering: "no"
          Cache-Control: "no-cache"
    pp-sec-headers:
      headers:
        frameDeny: true
        contentTypeNosniff: true

  services:
    primary:
      loadBalancer:
        servers:
          - url: "http://10.0.0.11:8000"
        healthCheck:
          path: "/api/v1/health"
          interval: "10s"
        serversTransport: sseTransport

    canary:
      loadBalancer:
        servers:
          - url: "http://10.0.0.21:8000"
        healthCheck:
          path: "/api/v1/health"
          interval: "10s"
        serversTransport: sseTransport

    petplantr-split:
      weighted:
        sticky:
          cookie:
            name: pp_canary
            httpOnly: true
            sameSite: lax
            secure: true
        services:
          - name: primary
            weight: 90
          - name: canary
            weight: 10

  serversTransports:
    sseTransport:
      forwardingTimeouts:
        dialTimeout: "30s"
        responseHeaderTimeout: "30s"
        idleConnTimeout: "600s"    # long-lived SSE
```

### Change weights (50/50)

```yaml
services:
  petplantr-split:
    weighted:
      services:
        - name: primary
          weight: 50
        - name: canary
          weight: 50
```

Reload the dynamic file.

### Response attribution
Prefer emitting X-Route from the app (e.g., env per deployment) for reliable attribution with weighted services.
