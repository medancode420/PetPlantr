#!/usr/bin/env bash
# Lint the YAML code fences inside docs/edge/canary/traefik.md (warn-only).
# Exits 0 even if lint fails (so it won't block CI), but emits GitHub Actions warnings.

set -Eeuo pipefail

DOC="docs/edge/canary/traefik.md"
TMP="/tmp/traefik_snippet.yml"

if [[ ! -f "$DOC" ]]; then
  echo "::warning::$DOC not found; skipping Traefik YAML lint"
  exit 0
fi

if ! command -v yamllint >/dev/null 2>&1; then
  echo "::warning::yamllint not installed; skipping Traefik YAML lint"
  exit 0
fi

# Extract ```yaml ... ``` code fences into a single YAML file
python3 - <<'PY' > "$TMP"
import re, sys, io, os
doc = os.environ.get("DOC", "docs/edge/canary/traefik.md")
with open(doc, "r", encoding="utf-8") as f:
    text = f.read()

blocks = []
for m in re.finditer(r"```(yaml|yml)\n(.*?)\n```", text, re.S | re.M):
    blocks.append(m.group(2).strip())

if not blocks:
    # No yaml blocks -> nothing to lint; exit clean
    sys.exit(0)

out = sys.stdout
for i, b in enumerate(blocks):
    if i:
        out.write("\n---\n")
    out.write(b)
    out.write("\n")
PY

# Lint with relaxed rules (no doc-start, no line-length noise)
yamllint -d '{extends: default, rules: {line-length: disable, document-start: disable}}' "$TMP" && {
  echo "ok: Traefik YAML snippet lint passed"
  exit 0
}

# Warn-only on failures
echo "::warning::yamllint found issues in Traefik snippet (see $TMP and $DOC)."
exit 0
