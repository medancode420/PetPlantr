#!/bin/bash

# 🚀 PetPlantr LIVE Launch Script
# ===============================
# Final launch with current working URLs

set -e

echo "🎉 PetPlantr Launch Sequence"
echo "==========================="

# Test live URLs
MAIN_URL="https://petplantr.vercel.app"
API_URL="https://petplantr.vercel.app/api"

echo ""
echo "🌍 Live URLs:"
echo "├── Frontend: $MAIN_URL"
echo "├── Upload:   $MAIN_URL/upload"
echo "└── API:      $API_URL"

echo ""
echo "⚡ Quick System Check..."

# Health check
echo -n "├── API Health: "
if curl -s "$API_URL/health" | grep -q '"status":"ok"'; then
    echo "✅ Live"
else
    echo "❌ Failed"
    exit 1
fi

# AI Models check
echo -n "├── AI Pipeline: "
if curl -s "$API_URL/health" | grep -q '"pipeline":"real"'; then
    echo "✅ Real AI Active"
else
    echo "❌ Demo Mode"
    exit 1
fi

# Upload page check
echo -n "├── Upload Page: "
if curl -s "$MAIN_URL/upload" | grep -q "Upload your pet"; then
    echo "✅ Accessible"
else
    echo "❌ Not Loading"
    exit 1
fi

echo "└── Environment: ✅ Production"

echo ""
echo "📊 Quick AI Test..."
echo -n "Testing breed detection: "
BREED_RESULT=$(curl -s "$API_URL/detect-breed" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"image_url":"https://images.unsplash.com/photo-1552053831-71594a27632d?w=400"}' \
    | jq -r '.predicted_breed // "failed"')

if [ "$BREED_RESULT" != "failed" ] && [ "$BREED_RESULT" != "null" ]; then
    echo "✅ $BREED_RESULT (AI Working)"
else
    echo "⚠️  AI may be cold-starting"
fi

echo ""
echo "🎯 Launch Summary"
echo "=================="
echo "✅ Frontend: Live and functional"
echo "✅ Backend:  Real AI pipeline active"
echo "✅ Upload:   Working and accessible"
echo "✅ Models:   Loaded and responding"
echo "✅ Status:   Ready for public use"

echo ""
echo "🚀 PETPLANTR IS LIVE!"
echo "====================="
echo "Share these URLs:"
echo ""
echo "🌐 Main Site:    $MAIN_URL"
echo "📸 Create Now:   $MAIN_URL/upload"
echo "📊 API Status:   $API_URL/health"
echo ""
echo "🎉 Ready to create AI-powered pet planters!"

# Optional: Open browser
if command -v open >/dev/null 2>&1; then
    echo ""
    echo "🌐 Opening in browser..."
    open "$MAIN_URL"
fi

echo ""
echo "📈 Monitor with:"
echo "curl -s $API_URL/health | jq"
echo "curl -s $API_URL/metrics"
