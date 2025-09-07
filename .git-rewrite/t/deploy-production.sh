#!/bin/bash
set -euo pipefail

echo "🚀 PetPlantr Production Deploy"

# Ensure correct directory
if [ ! -f "package.json" ]; then
	echo "❌ Run from repo root" >&2; exit 1
fi

# Load production envs
export ENVIRONMENT=prod
if [ -f "PRODUCTION_ENVIRONMENT_COMPLETE.env" ]; then
	export $(grep -v '^#' PRODUCTION_ENVIRONMENT_COMPLETE.env | xargs) || true
fi
if [ -f "production-environment-ready.env" ]; then
	export $(grep -v '^#' production-environment-ready.env | xargs) || true
fi
if [ -f ".env.production" ]; then
	export $(grep -v '^#' .env.production | xargs) || true
fi
if [ -f ".env.production.local" ]; then
	export $(grep -v '^#' .env.production.local | xargs) || true
fi

# Minimal readiness checks
req=(NEXT_PUBLIC_API_BASE_URL AWS_REGION NODE_ENV)
for k in "${req[@]}"; do
	if [ -z "${!k:-}" ]; then echo "❌ Missing $k" >&2; exit 2; fi
done

# Frontend build
echo "📦 Building frontend (Next.js)..."
npm ci
npm run build

echo "✅ Build complete. To start locally in production mode:"
echo "    NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL npm run start"

