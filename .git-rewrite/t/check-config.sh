#!/bin/bash
# 🔧 Fast-Fail Configuration Checker
# Validates environment variables and fails immediately if misconfigured

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo "${BOLD}${BLUE}🔧 Fast-Fail Configuration Checker${NC}"
echo "==================================="
echo ""

# Check if we're in production mode
if [ "${NODE_ENV}" = "production" ] || [ "${ENABLE_PRODUCTION_AI}" = "true" ]; then
    PRODUCTION_MODE=true
    echo "🎯 Production mode detected"
else
    PRODUCTION_MODE=false
    echo "🧪 Development mode detected"
fi

echo ""

# Critical environment variables for production
CRITICAL_VARS=(
    "NEXT_PUBLIC_API_BASE_URL"
    "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"
)

# Optional but recommended variables
RECOMMENDED_VARS=(
    "NEXT_PUBLIC_ENVIRONMENT"
    "NEXT_PUBLIC_SENTRY_DSN"
)

# AI-specific variables (if production AI is enabled)
AI_VARS=(
    "OPENAI_API_KEY"
    "HUGGINGFACE_API_KEY"
)

echo "${BOLD}Checking Critical Variables:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CRITICAL_MISSING=0

for var in "${CRITICAL_VARS[@]}"; do
    if [ -n "${!var}" ]; then
        echo "✅ $var: Set"
    else
        echo "❌ $var: ${RED}MISSING${NC}"
        ((CRITICAL_MISSING++))
    fi
done

echo ""
echo "${BOLD}Checking Recommended Variables:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RECOMMENDED_MISSING=0

for var in "${RECOMMENDED_VARS[@]}"; do
    if [ -n "${!var}" ]; then
        echo "✅ $var: Set"
    else
        echo "⚠️  $var: ${YELLOW}Missing (recommended)${NC}"
        ((RECOMMENDED_MISSING++))
    fi
done

echo ""

if [ "$PRODUCTION_MODE" = true ]; then
    echo "${BOLD}Checking AI Variables (Production AI Enabled):${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    AI_MISSING=0
    
    for var in "${AI_VARS[@]}"; do
        if [ -n "${!var}" ]; then
            echo "✅ $var: Set"
        else
            echo "❌ $var: ${RED}MISSING${NC}"
            ((AI_MISSING++))
        fi
    done
    
    echo ""
fi

# Fast-fail logic
echo "${BOLD}Fast-Fail Assessment:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$CRITICAL_MISSING" -gt 0 ]; then
    echo "${RED}❌ CRITICAL FAILURE: $CRITICAL_MISSING critical variables missing${NC}"
    echo ""
    echo "🚨 Application will not function correctly without these variables."
    echo "   Set the missing variables and restart the application."
    echo ""
    exit 1
fi

if [ "$PRODUCTION_MODE" = true ] && [ "$AI_MISSING" -gt 0 ]; then
    echo "${RED}❌ AI PIPELINE FAILURE: $AI_MISSING AI variables missing${NC}"
    echo ""
    echo "🚨 Production AI mode is enabled but required API keys are missing."
    echo "   Either set the missing keys or disable production AI mode."
    echo ""
    exit 1
fi

if [ "$RECOMMENDED_MISSING" -gt 0 ]; then
    echo "${YELLOW}⚠️  WARNING: $RECOMMENDED_MISSING recommended variables missing${NC}"
    echo "   Application will work but may have limited functionality."
    echo ""
fi

echo "${GREEN}✅ Configuration validation passed!${NC}"
echo ""

if [ "$PRODUCTION_MODE" = true ]; then
    echo "🚀 Production mode configuration is valid"
    echo "🤖 AI pipeline is properly configured"
else
    echo "🧪 Development mode configuration is valid"
fi

echo ""
echo "Next steps:"
echo "• Start application: npm run dev (development) or npm run build && npm start (production)"
echo "• Validate pipeline: ./validate-production-pipeline.sh"
echo "• Check status: Open /production-status.html in browser"

exit 0
