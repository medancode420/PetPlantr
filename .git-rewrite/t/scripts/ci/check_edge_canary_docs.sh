#!/usr/bin/env bash
# CI guard: verify edge canary rollout docs exist and contain key content
# Safe to run locally or in CI
set -Eeuo pipefail

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; NC=$'\033[0m'
fail() { echo "${RED}✗${NC} $*"; exit 1; }
ok()   { echo "${GREEN}✓${NC} $*"; }
info() { echo "${YELLOW}›${NC} $*"; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
NGINX="$ROOT/docs/edge/canary/nginx.md"
TRAEFIK="$ROOT/docs/edge/canary/traefik.md"
CLOUDFLARE="$ROOT/docs/edge/canary/cloudflare.md"

missing=0
for f in "$NGINX" "$TRAEFIK" "$CLOUDFLARE"; do
  if [[ ! -f "$f" ]]; then
    echo "${RED}✗${NC} Missing: $f"; missing=1
  else
    ok "Found: ${f#$ROOT/}"
  fi
done
[[ $missing -eq 0 ]] || fail "One or more edge canary docs are missing"

# Minimal content checks
info "Validating nginx canary doc content…"
grep -qi 'split_clients' "$NGINX"       || fail "nginx.md missing 'split_clients'"
grep -qi 'X-Route' "$NGINX"             || fail "nginx.md missing 'X-Route'"
grep -qi 'pp_canary' "$NGINX"           || fail "nginx.md missing 'pp_canary' cookie mention"
# Accept either the explicit string 'SSE' or the critical directive disabling proxy buffering
( grep -qi '\bSSE\b' "$NGINX" || grep -qi 'proxy_buffering\s*off' "$NGINX" ) || fail "nginx.md missing SSE hint or proxy_buffering off"
ok "nginx.md content OK"

info "Validating traefik canary doc content…"
grep -qi '\bweighted\b' "$TRAEFIK"     || fail "traefik.md missing 'weighted' service"
grep -qi 'sseTransport' "$TRAEFIK"      || fail "traefik.md missing 'sseTransport'"
grep -qi '\bsticky\b' "$TRAEFIK"       || fail "traefik.md missing 'sticky' configuration"
ok "traefik.md content OK"

info "Validating cloudflare canary doc content…"
grep -qi 'CANARY_PERCENT' "$CLOUDFLARE" || fail "cloudflare.md missing 'CANARY_PERCENT'"
grep -qi 'wrangler.toml' "$CLOUDFLARE"  || fail "cloudflare.md missing 'wrangler.toml' section"
grep -qi 'X-Route' "$CLOUDFLARE"        || fail "cloudflare.md missing 'X-Route'"
ok "cloudflare.md content OK"

ok "Edge canary docs guard passed"
