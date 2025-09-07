# PetPlantr NGINX Canary Configuration

## Overview
This configuration implements a 10% canary deployment with cookie-based stickiness and proper SSE (Server-Sent Events) proxying for the PetPlantr API.

## Configuration

```nginx
## PetPlantr Canary Split: 10% to canary with cookie-based stickiness and SSE proxying

http {
	split_clients "${remote_addr}" $backend {
		10% canary_backend;  # 10% to canary
		*   stable_backend;  # 90% to stable
	}

	map $cookie_petplantr_canary $sticky_backend {
		default $backend;     # Fallback to split
		canary  canary_backend;  # Sticky to canary if cookie set
		stable  stable_backend;  # Sticky to stable
	}

	upstream stable_backend { server stable.petplantr.svc:8000; }
	upstream canary_backend { server canary.petplantr.svc:8000; }

	server {
		listen 80;
		server_name _;

		location / {
			proxy_pass http://$sticky_backend;
			proxy_set_header Host $host;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header Cookie $http_cookie;  # Pass cookie for sticky

			# SSE proxying config
			proxy_http_version 1.1;
			proxy_set_header Connection "keep-alive";
			proxy_buffering off;
			proxy_cache off;
		}
	}
}
```

## Features

- **10% Traffic Split**: Uses `split_clients` to route 10% of traffic to canary backend
- **Cookie-Based Stickiness**: Users with `petplantr_canary` cookie set to `canary` or `stable` will stick to that backend
- **SSE Support**: Proper proxying configuration for Server-Sent Events with:
  - HTTP/1.1 protocol
  - Keep-alive connections
  - Buffering disabled
  - Caching disabled

## Usage

1. Deploy stable and canary backends as separate services
2. Apply this NGINX configuration
3. Monitor canary traffic and error rates
4. If stable, increase canary percentage or promote to stable

## Validation

Test the canary split:
```bash
# Test normal traffic (should go to stable 90% of time)
curl -H "Host: api.petplantr.com" http://nginx/api/v1/health

# Test canary stickiness
curl -H "Host: api.petplantr.com" -H "Cookie: petplantr_canary=canary" http://nginx/api/v1/health

# Test SSE endpoint
curl -H "Host: api.petplantr.com" -H "Accept: text/event-stream" http://nginx/api/v1/ops/synthetic/live
```