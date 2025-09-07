# PetPlantr — Canary on Cloudflare (Workers)

A Worker that:
- Routes **10%** to canary (sticky cookie `pp_canary=1`)
- Adds `X-Route: canary|primary`
- Disables caching and preserves streaming for SSE
- Falls back to primary on canary 5xx

## worker.js

```js
export default {
  async fetch(request, env, ctx) {
    const PRIMARY = env.PRIMARY_URL; // "https://primary.internal:8000"
    const CANARY  = env.CANARY_URL;  // "https://canary.internal:8000"
    const PCT     = Number(env.CANARY_PERCENT || "10");
    const cookieName = env.CANARY_COOKIE || "pp_canary";

    const url = new URL(request.url);
    const headersIn = new Headers(request.headers);

    // sticky cookie or header override
    const cookie = headersIn.get("Cookie") || "";
    const forced = headersIn.get("X-Route") === "canary";
    const pinned = /(^|;\s*)pp_canary=1(;$|$)/i.test(cookie);

    // simple split; pin most users via cookie
    const roll = Math.floor(Math.random() * 100) + 1;
    let toCanary = forced || pinned || (roll <= PCT);
    const origin = toCanary ? CANARY : PRIMARY;

    const originReq = new Request(origin + url.pathname + url.search, {
      method: request.method,
      headers: headersIn,
      body: ["GET","HEAD"].includes(request.method) ? undefined : request.body,
      redirect: "manual",
      cf: { cacheTtl: 0, cacheEverything: false },
    });

    let originRes;
    try {
      originRes = await fetch(originReq);
      if (!originRes.ok && originRes.status >= 500 && toCanary) {
        // canary failed → fallback to primary
        originRes = await fetch(new Request(PRIMARY + url.pathname + url.search, originReq));
        toCanary = false;
      }
    } catch (e) {
      if (toCanary) {
        originRes = await fetch(new Request(PRIMARY + url.pathname + url.search, originReq));
        toCanary = false;
      } else {
        return new Response("upstream unreachable", { status: 502 });
      }
    }

    const resHdr = new Headers(originRes.headers);
    resHdr.set("X-Route", toCanary ? "canary" : "primary");

    if (url.pathname.startsWith("/api/v1/mesh/stream/")) {
      resHdr.set("Cache-Control", "no-cache");
      resHdr.set("X-Accel-Buffering", "no");
    }
    if (toCanary) {
      resHdr.append("Set-Cookie", `${cookieName}=1; Path=/; Max-Age=86400; SameSite=Lax; Secure`);
    }

    return new Response(originRes.body, { status: originRes.status, headers: resHdr });
  },
};
```

## wrangler.toml

```toml
name = "petplantr-canary"
main = "worker.js"
compatibility_date = "2024-10-01"

[vars]
PRIMARY_URL = "https://primary.internal:8000"
CANARY_URL  = "https://canary.internal:8000"
CANARY_PERCENT = "10"
CANARY_COOKIE = "pp_canary"
```

### Roll forward / back
- Change CANARY_PERCENT (e.g., 10 → 50) and redeploy.
- Disable canary: set CANARY_PERCENT=0.

## Quick test
```bash
curl -s -D - https://api.petplantr.com/api/v1/health -o /dev/null | grep -i ^X-Route:
curl -s -D - -H 'X-Route: canary' https://api.petplantr.com/api/v1/health -o /dev/null | grep -i ^X-Route:
```
