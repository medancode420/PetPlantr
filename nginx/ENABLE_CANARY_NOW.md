# Enable 10% Canary for api.petplantr.com

This assumes NGINX is installed on your host and your existing config for api.petplantr.com is under /etc/nginx. Adjust paths if different.

## Steps

1) Copy the canary split config to conf.d

sudo mkdir -p /etc/nginx/conf.d
sudo cp nginx/canary_api.conf /etc/nginx/conf.d/canary_api.conf

2) Update your api server block to use $api_upstream (already done in repo file nginx-petplantr.conf). If your live server block differs, edit it to:

location / {
  proxy_pass http://$api_upstream;
  # ...headers/timeouts...
}

3) Reload NGINX

sudo nginx -t && sudo nginx -s reload

4) Verify

# 10-20 requests should show distribution in access logs
# Optional quick curl loop (replace host if needed):
for i in {1..20}; do curl -s -o /dev/null -w "%{http_code}\n" https://api.petplantr.com/health || true; done

## Rollback

- Comment out the split_clients/map blocks in /etc/nginx/conf.d/canary_api.conf or set split to 0% v2.
- Reload NGINX again.

