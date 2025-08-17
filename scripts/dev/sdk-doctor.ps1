#!/usr/bin/env pwsh
# Windows SDK doctor: strict checks, deterministic, no repo modifications
# - Discovers repo root via script path
# - Verifies Node/npx availability and shows Node version
# - Enforces TypeScript pin parity: Makefile TS_VERSION vs sdk/package.json scripts.typecheck
# - (Optional) warns if CI workflow pin drifts
# - Asserts sdk/tsconfig.json includes the React hook and shim
# - Runs pinned no-emit type-check

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Fail([string]$msg) {
  Write-Host "❌ $msg" -ForegroundColor Red
  exit 1
}
function Note([string]$msg) {
  Write-Host "ℹ︎  $msg" -ForegroundColor Yellow
}
function Ok([string]$msg) {
  Write-Host "✅ $msg" -ForegroundColor Green
}

# Resolve repo root (…/scripts/dev -> repo root)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir   = Resolve-Path (Join-Path $ScriptDir '..' | Join-Path -ChildPath '..')
Set-Location $RootDir

# Node + npx
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Fail 'Node.js not found. Install Node 20 (see .nvmrc).' }
if (-not (Get-Command npx  -ErrorAction SilentlyContinue)) { Fail 'npx not found. Install Node/npm.' }

$nodeVersion = node -p "process.versions.node"
switch -Regex ($nodeVersion) {
  '^20\.' { Ok "Node $nodeVersion detected" }
  '^(21|22)\.' { Ok "Node $nodeVersion detected" }
  default { Note "Node $nodeVersion detected; CI uses 20.x (see .nvmrc)" }
}

# Extract TS pin from Makefile (TS_VERSION) or env
$makefilePath = Join-Path $RootDir 'Makefile'
$makefileTs = $null
if ($env:TS_VERSION) {
  $makefileTs = $env:TS_VERSION
} elseif (Test-Path $makefilePath) {
  $makeContent = Get-Content $makefilePath -Raw
  $m = [regex]::Match($makeContent, 'TS_VERSION\s*\??=\s*([0-9]+\.[0-9]+\.[0-9]+)')
  if ($m.Success) { $makefileTs = $m.Groups[1].Value }
}
if (-not $makefileTs) { Fail 'Could not read TS_VERSION from Makefile or env.' }

# Extract TS pin from sdk/package.json scripts.typecheck
$pkgPath = Join-Path $RootDir 'sdk/package.json'
if (-not (Test-Path $pkgPath)) { Fail 'sdk/package.json not found.' }
$pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
$scriptTypecheck = $pkg.scripts.typecheck
if (-not $scriptTypecheck) { Fail 'sdk/package.json missing scripts.typecheck.' }
$pm = [regex]::Match($scriptTypecheck, 'typescript@([0-9]+\.[0-9]+\.[0-9]+)')
if (-not $pm.Success) { Fail 'Could not extract typescript@X.Y.Z from sdk/package.json scripts.typecheck.' }
$pkgTs = $pm.Groups[1].Value

# Optional: CI workflow pin drift
$wfPath = Join-Path $RootDir '.github/workflows/sdk-typecheck.yml'
if (Test-Path $wfPath) {
  $wfContent = Get-Content $wfPath -Raw
  $wm = [regex]::Match($wfContent, 'typescript@([0-9]+\.[0-9]+\.[0-9]+)')
  if ($wm.Success) {
    $wfTs = $wm.Groups[1].Value
    if ($wfTs -ne $makefileTs) {
      Note "sdk-typecheck.yml pins TypeScript $wfTs, Makefile pins $makefileTs."
    }
  }
}

# Enforce parity Makefile vs package.json
if ($makefileTs -ne $pkgTs) {
  Fail "TypeScript pin mismatch: Makefile=$makefileTs vs sdk/package.json=$pkgTs. Update both to match."
}
$tsv = $makefileTs
Ok "TypeScript pin parity OK ($tsv)"

# Print tsc version (from the pin)
& npx --yes -p "typescript@$tsv" tsc -v | Write-Host

# Ensure tsconfig includes required files
$SdkDir = Join-Path $RootDir 'sdk'
Push-Location $SdkDir
$tsFiles = & npx --yes -p "typescript@$tsv" tsc --listFilesOnly -p tsconfig.json | Out-String
if ($tsFiles -notmatch 'react/useMeshGeneration\.ts') { Pop-Location; Fail 'tsconfig.json does not include react/useMeshGeneration.ts' }
if ($tsFiles -notmatch 'types/react-shim\.d\.ts')     { Pop-Location; Fail 'tsconfig.json does not include types/react-shim.d.ts' }
Ok 'tsconfig includes required files'

# Type-check (no emit)
& npx --yes -p "typescript@$tsv" tsc --noEmit -p tsconfig.json
Ok 'SDK type-check succeeded'

Pop-Location
