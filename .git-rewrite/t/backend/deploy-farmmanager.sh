#!/bin/bash

echo "🚀 PetPlantr Farm Manager Deployment Script"
echo "==========================================="
echo

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "⚠️  No .env file found. Using default values..."
fi

# Set default values for missing variables
export STRIPE_PRICE_PET_PLANTER_BASIC=${STRIPE_PRICE_PET_PLANTER_BASIC:-"price_dev_default"}
export STRIPE_PRICE_SMOKE_TEST=${STRIPE_PRICE_SMOKE_TEST:-"price_dev_default"}
export UPLOAD_BUCKET=${UPLOAD_BUCKET:-"petplantr-uploads-dev"}
export RAW_STL_BUCKET=${RAW_STL_BUCKET:-"petplantr-stl-raw-dev"}
export READY_STL_BUCKET=${READY_STL_BUCKET:-"petplantr-stl-ready-dev"}
export ORDER_EVENT_BUS_NAME=${ORDER_EVENT_BUS_NAME:-"petplantr-orderbus-dev"}
export STAGE=${STAGE:-"dev"}
export AWS_REGION=${AWS_REGION:-"us-east-1"}

echo "🔧 Environment Configuration:"
echo "   STAGE: $STAGE"
echo "   AWS_REGION: $AWS_REGION"
echo "   UPLOAD_BUCKET: $UPLOAD_BUCKET"
echo "   RAW_STL_BUCKET: $RAW_STL_BUCKET"
echo "   READY_STL_BUCKET: $READY_STL_BUCKET"
echo "   ORDER_EVENT_BUS_NAME: $ORDER_EVENT_BUS_NAME"
echo

echo "🔨 Building project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed! Please fix TypeScript errors."
    exit 1
fi

echo "✅ Build successful!"
echo

echo "🚀 Deploying to AWS..."
echo "   Stage: $STAGE"
echo "   Region: $AWS_REGION"
echo

# Deploy with environment variables
npx serverless deploy --stage $STAGE --region $AWS_REGION

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Deployment successful!"
    echo
    echo "📊 Getting service information..."
    API_URL=$(npx serverless info --stage $STAGE | grep -o 'https://[^[:space:]]*' | head -1)
    
    if [ ! -z "$API_URL" ]; then
        echo "✅ Farm Manager API is live at:"
        echo "   $API_URL"
        echo
        echo "🧪 Test endpoints:"
        echo "   Farm Status:    $API_URL/api/farm/status"
        echo "   Farm Analytics: $API_URL/api/farm/analytics"
        echo "   Printer Health: $API_URL/api/farm/health"
        echo "   Live Data:      $API_URL/api/farm/live"
        echo
        echo "🧪 Run comprehensive tests:"
        echo "   ./test-farmmanager.sh $API_URL"
        echo "   ./test-advanced-backend.sh $API_URL"
        echo
        
        # Automatically run basic test
        echo "🧪 Running quick test..."
        ./test-farmmanager.sh "$API_URL"
        
    else
        echo "⚠️  Could not extract API URL. Check serverless info output above."
        npx serverless info --stage $STAGE
    fi
else
    echo "❌ Deployment failed! Check the error messages above."
    exit 1
fi
