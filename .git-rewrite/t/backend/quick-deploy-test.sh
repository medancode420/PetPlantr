#!/bin/bash

echo "🚀 Quick Deploy and Test Script"
echo "==============================="
echo

echo "This script will:"
echo "1. Deploy your Farm Manager to AWS"
echo "2. Run comprehensive tests"
echo "3. Show you the results"
echo

read -p "Deploy to development environment? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔨 Building project..."
    npm run build
    
    echo "🚀 Deploying to AWS development..."
    npx serverless deploy --stage dev
    
    echo "📊 Getting API URL..."
    API_URL=$(npx serverless info --stage dev | grep -o 'https://[^[:space:]]*')
    
    if [ ! -z "$API_URL" ]; then
        echo "✅ Deployment successful!"
        echo "API URL: $API_URL"
        echo
        
        echo "🧪 Running tests..."
        ./test-farmmanager.sh "$API_URL"
        
        echo
        echo "🎉 Testing complete!"
        echo "Your Farm Manager is live at: $API_URL"
        echo
        echo "Try these endpoints:"
        echo "• $API_URL/api/farm/status"
        echo "• $API_URL/api/farm/analytics"
        echo "• $API_URL/api/farm/health"
        
    else
        echo "❌ Could not get API URL. Check deployment output above."
    fi
else
    echo "Deployment cancelled."
    echo "To test manually:"
    echo "1. npx serverless deploy --stage dev"
    echo "2. ./test-farmmanager.sh [YOUR_API_URL]"
fi
