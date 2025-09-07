#!/bin/bash

echo "🏭 Farm Manager Only - Quick Deployment"
echo "======================================"
echo

echo "🔨 Building project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "🚀 Deploying Farm Manager only..."
npx serverless deploy --config serverless-farmmanager.yml --stage dev

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Farm Manager deployed successfully!"
    echo
    echo "📊 Getting API URL..."
    API_URL=$(npx serverless info --config serverless-farmmanager.yml --stage dev | grep -o 'https://[^[:space:]]*' | head -1)
    
    if [ ! -z "$API_URL" ]; then
        echo "✅ Farm Manager API is live at: $API_URL"
        echo
        echo "🧪 Test endpoints:"
        echo "• $API_URL/api/farm/status"
        echo "• $API_URL/api/farm/analytics"
        echo "• $API_URL/api/farm/health"
        echo
        echo "🧪 Running quick test..."
        sleep 3
        ./test-farmmanager.sh "$API_URL"
    else
        echo "⚠️  Could not get API URL. Manual info:"
        npx serverless info --config serverless-farmmanager.yml --stage dev
    fi
else
    echo "❌ Deployment failed!"
fi
