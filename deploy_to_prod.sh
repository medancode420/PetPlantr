#!/usr/bin/env bash

# Switch PetPlantr to production mode and deploy with custom domain petplantr.com
# Prereqs:
# - Vercel CLI (npm i -g vercel)
# - Render account (uses render.yaml from repo)
# - Domain petplantr.com (or change below) with DNS access
# Usage: from repo root: bash deploy_to_prod.sh

set -euo pipefail

FRONTEND_ENV_FILE="frontend/.env.production"
BACKEND_ENV_FILE=".env.production"
RENDER_FILE="render.yaml"

echo "==> Writing frontend production env: ${FRONTEND_ENV_FILE}"
cat > "$FRONTEND_ENV_FILE" << 'EOF'
NEXT_PUBLIC_DEV_MODE=false
# Point frontend to your public backend URL
NEXT_PUBLIC_API_BASE_URL=https://api.petplantr.com
EOF

echo "==> Writing backend production env: ${BACKEND_ENV_FILE}"
cat > "$BACKEND_ENV_FILE" << 'EOF'
# Backend env (configure real values in your cloud provider or secrets manager)
ENABLE_PRODUCTION_AI=true
REPLICATE_API_TOKEN=YOUR_REPLICATE_TOKEN
REDIS_URL=YOUR_REDIS_URL
JWT_SECRET=YOUR_SECURE_JWT_SECRET
CORS_ORIGINS=https://petplantr.com,https://www.petplantr.com
PORT=8000
EOF

if [ ! -f "$RENDER_FILE" ]; then
  echo "==> Creating Render service descriptor: ${RENDER_FILE}"
  cat > "$RENDER_FILE" << 'EOF'
services:
  - type: web
    name: petplantr-backend
    env: python
    plan: free # upgrade as needed
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:$PORT api_server:app
    envVars:
      - key: PORT
        value: 8000
      - key: ENABLE_PRODUCTION_AI
        value: true
      - key: CORS_ORIGINS
        value: https://petplantr.com,https://www.petplantr.com
      - key: REPLICATE_API_TOKEN
        sync: false
      - key: REDIS_URL
        sync: false
      - key: JWT_SECRET
        sync: false
EOF
else
  echo "==> Skipping: ${RENDER_FILE} already exists"
fi

echo "==> Frontend deploy (Vercel) — will prompt to link project if not already"
(
  cd frontend
  vercel --prod || true
  echo "==> Optionally add custom domain via CLI (or use Vercel dashboard): vercel domain add petplantr.com"
)

echo "==> Backend deploy (Render)"
echo "- Commit & push to GitHub, create a Render Web Service from this repo with ${RENDER_FILE}"
echo "- Set env vars (REPLICATE_API_TOKEN, REDIS_URL, JWT_SECRET) in Render dashboard"
echo "- Add custom domain api.petplantr.com pointing to Render service"

echo "==> DNS setup"
echo "- Vercel: point petplantr.com (A/CNAME per Vercel guidance)"
echo "- Render: point api.petplantr.com to the Render service"

echo "==> Verify"
echo "- Frontend: https://petplantr.com"
echo "- Backend health: https://api.petplantr.com/api/v1/health"
echo "- Frontend proxy: POST https://petplantr.com/api/generate-enhanced-3d-simple"

echo "Done. Review outputs above for any manual follow-ups."
