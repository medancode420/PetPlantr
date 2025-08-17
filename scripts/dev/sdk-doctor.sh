#!/usr/bin/env bash
set -Eeuo pipefail

# Resolve repo root (…/scripts/dev -> repo root)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
cd "$ROOT_DIR"

# Pretty output helpers
red=$'\033[31m'; green=$'\033[32m'; yellow=$'\033[33m'; reset=$'\033[0m'
fail(){ echo "${red}❌ $*${reset}" >&2; exit 1; }
note(){ echo "${yellow}ℹ︎  $*${reset}"; }
ok(){   echo "${green}✅ $*${reset}"; }

# Node and npx presence + breadcrumbs
command -v node >/dev/null 2>&1 || fail "Node.js not found. Install Node 20 (see .nvmrc)."
command -v npx  >/dev/null 2>&1 || fail "npx not found. Install Node/npm."

NODE_VERSION="$(node -p 'process.versions.node')"
case "$NODE_VERSION" in
  20.*|21.*|22.*) ok "Node ${NODE_VERSION} detected";;
  *) note "Node ${NODE_VERSION} detected; CI uses 20.x (see .nvmrc)";;
esac

# TS pins: Makefile (TS_VERSION) and sdk/package.json (scripts.typecheck)
MAKEFILE_TS="${TS_VERSION:-$(awk '
  $1 ~ /^TS_VERSION/ {
    for(i=1;i<=NF;i++) if ($i ~ /^[0-9]+\.[0-9]+\.[0-9]+$/) { print $i; exit }
  }' "$ROOT_DIR/Makefile" || true)}"
[[ -n "${MAKEFILE_TS}" ]] || fail "Could not read TS_VERSION from Makefile or env."

PKG_TS="$(node -e "
  const p=require('${ROOT_DIR}/sdk/package.json');
  const s=(p.scripts && p.scripts.typecheck) || '';
  const m=s.match(/typescript@([0-9]+\.[0-9]+\.[0-9]+)/);
  if(!m){ process.exit(2) } else { console.log(m[1]) }
" || true)"
[[ -n "${PKG_TS}" ]] || fail "Could not extract typescript@X.Y.Z from sdk/package.json scripts.typecheck."

# Optional: check CI workflow pin drift
WORKFLOW_TS="$(grep -RhoE 'typescript@([0-9]+\.[0-9]+\.[0-9]+)' \
  "$ROOT_DIR/.github/workflows/sdk-typecheck.yml" 2>/dev/null | head -n1 | sed -E 's/.*@//' || true)"
if [[ -n "${WORKFLOW_TS}" && "${WORKFLOW_TS}" != "${MAKEFILE_TS}" ]]; then
  note "sdk-typecheck.yml pins TypeScript ${WORKFLOW_TS}, Makefile pins ${MAKEFILE_TS}."
fi

# Enforce parity between Makefile and package.json
if [[ "${MAKEFILE_TS}" != "${PKG_TS}" ]]; then
  fail "TypeScript pin mismatch: Makefile=${MAKEFILE_TS} vs sdk/package.json=${PKG_TS}. Update both to match."
fi
TSV="${MAKEFILE_TS}"
ok "TypeScript pin parity OK (${TSV})"

# Print tsc version
npx --yes -p "typescript@${TSV}" tsc -v

# Ensure tsconfig includes required files
pushd "$ROOT_DIR/sdk" >/dev/null
LIST="$(npx --yes -p "typescript@${TSV}" tsc --listFilesOnly -p tsconfig.json)"
echo "${LIST}" | grep -q 'react/useMeshGeneration\.ts' || fail "tsconfig.json does not include react/useMeshGeneration.ts"
echo "${LIST}" | grep -q 'types/react-shim\.d\.ts'     || fail "tsconfig.json does not include types/react-shim.d.ts"
ok "tsconfig includes required files"

# Type-check (no emit)
npx --yes -p "typescript@${TSV}" tsc --noEmit -p tsconfig.json
ok "SDK type-check succeeded"

popd >/dev/null
