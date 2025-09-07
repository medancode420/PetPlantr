# Canary rollout for api.petplantr.com (10%)

This adds a deterministic 10% canary split for API traffic between v1 (port 8000) and v2 (port 8001) using `split_clients` on `$request_id`.

Steps:

1) Ensure nginx is compiled with the `split_clients` module (default in mainline).
2) Copy `nginx/canary_api.conf` into your `conf.d/` or include it from your main `nginx.conf`.
3) In your existing `server` block for `api.petplantr.com`, change the main `location /` proxy to:

    proxy_pass http://$api_upstream;

4) Start v2 on port 8001 and confirm `/health` is 200.
5) Reload NGINX:

    sudo nginx -t && sudo nginx -s reload

6) Verify split with a few curl requests; check your access logs for upstream used.

Rollback:
- Set `split_clients` to 0% v2 or comment out the `map` and `split_clients` (fallback to v1), then reload.
