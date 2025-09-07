# PetPlantr — Canary at the edge (NGINX)

This config sends **10%** of traffic to the *canary* backend and **90%** to *primary*, with:
- Sticky cookie: `pp_canary=1` pins a user to canary
- Manual override via header: `X-Route: canary`
- Response attribution: `X-Route: canary|primary`
- SSE-safe proxying for `/api/v1/mesh/stream/*`

> Adjust upstream addresses and the percentage split to suit.

```nginx
# /etc/nginx/conf.d/petplantr.conf
upstream petplantr_primary {
    server 10.0.0.11:8000 max_fails=3 fail_timeout=30s;
    keepalive 64;
}

upstream petplantr_canary {
    server 10.0.0.21:8000 max_fails=3 fail_timeout=30s;
    keepalive 64;
}

# 10% canary split with stickiness & header override
# 1) header override: X-Route: canary
map $http_x_route $force_canary { default 0; canary 1; }

# 2) sticky cookie (pp_canary=1)
map $cookie_pp_canary $cookie_canary { default 0; 1 1; }

# 3) % split (consistent hash)
split_clients "${remote_addr}${http_user_agent}" $pp_bucket {
    10% 1;
    *   0;
}

# 4) final decision (1 = canary, 0 = primary)
map "$force_canary$cookie_canary$pp_bucket" $pp_is_canary {
    ~1 1;   # any signal sets canary
    default 0;
}

# 5) choose upstream + attribution header
map $pp_is_canary $pp_upstream { 1 "petplantr_canary"; 0 "petplantr_primary"; }
map $pp_is_canary $pp_routehdr { 1 "canary"; 0 "primary"; }

server {
    listen 443 ssl http2;
    server_name api.petplantr.com;

    # TLS config omitted

    # Default location (JSON APIs)
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;

        # Attribution + sticky pin when routed to canary
        add_header X-Route $pp_routehdr always;
        if ($pp_is_canary) {
            add_header Set-Cookie "pp_canary=1; Path=/; Max-Age=86400; SameSite=Lax" always;
        }

        proxy_pass http://$pp_upstream;
    }

    # SSE stream — disable buffering and extend timeouts
    location ^~ /api/v1/mesh/stream/ {
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_buffering off;                 # critical for SSE
        tcp_nodelay on;
        add_header X-Accel-Buffering "no";   # hint for proxies
        add_header Cache-Control "no-cache" always;

        proxy_read_timeout 1h;
        proxy_send_timeout 1h;

        add_header X-Route $pp_routehdr always;
        if ($pp_is_canary) {
            add_header Set-Cookie "pp_canary=1; Path=/; Max-Age=86400; SameSite=Lax" always;
        }

        proxy_pass http://$pp_upstream;
    }

    # (optional) health passthrough
    location = /api/v1/health { proxy_pass http://$pp_upstream; }
}
```

## Change the split quickly
- 50/50: set `split_clients` to `50% 1; * 0;` then `nginx -t && nginx -s reload`.
- Disable canary: set `0% 1; * 0;`.

## Quick test
```bash
# Expect X-Route: primary (most of the time)
curl -s -D - https://api.petplantr.com/api/v1/health -o /dev/null | grep -i ^X-Route:

# Force canary
curl -s -D - -H 'X-Route: canary' https://api.petplantr.com/api/v1/health -o /dev/null | grep -i ^X-Route:
```
