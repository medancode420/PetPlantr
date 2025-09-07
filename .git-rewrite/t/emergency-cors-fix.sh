#!/bin/bash

# Emergency CORS Fix Script
# Forces CloudFront cache invalidation and S3 CORS re-application

echo "🚨 EMERGENCY CORS FIX - FIXING MISSING HEADERS"
echo "=============================================="
echo "📅 $(date)"
echo ""

# Configuration
CLOUDFRONT_DISTRIBUTION_ID="E1234567890123"  # You may need to update this
S3_BUCKET="petplantr-3d-models"
REGION="us-east-1"

echo "🔧 Step 1: Re-applying S3 CORS configuration..."
echo "----------------------------------------------"

# Create CORS configuration JSON
cat > cors-config.json << 'EOF'
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "HEAD", "PUT", "POST"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag", "x-amz-meta-custom-header"],
            "MaxAgeSeconds": 3600
        }
    ]
}
EOF

echo "📝 CORS configuration:"
cat cors-config.json
echo ""

# Apply CORS to S3 bucket
echo "🔄 Applying CORS to S3 bucket..."
if aws s3api put-bucket-cors --bucket "$S3_BUCKET" --cors-configuration file://cors-config.json; then
    echo "✅ S3 CORS configuration applied successfully"
else
    echo "❌ Failed to apply S3 CORS configuration"
    echo "💡 You may need to run: aws configure"
    echo "💡 Or update the bucket name in this script"
fi

echo ""

echo "🔧 Step 2: Invalidating CloudFront cache..."
echo "------------------------------------------"

# Create invalidation paths
INVALIDATION_PATHS='{"Paths":{"Quantity":2,"Items":["/*","/models/*"]},"CallerReference":"emergency-cors-fix-'$(date +%s)'"}'

echo "📝 Invalidating paths: /* and /models/*"

# Try to create CloudFront invalidation
if command -v aws >/dev/null 2>&1; then
    if aws cloudfront create-invalidation --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" --invalidation-batch "$INVALIDATION_PATHS" 2>/dev/null; then
        echo "✅ CloudFront invalidation created successfully"
    else
        echo "⚠️  CloudFront invalidation failed (may need correct distribution ID)"
        echo "💡 Manual steps:"
        echo "   1. Go to AWS CloudFront console"
        echo "   2. Find your distribution (domain: dpa0b9puwj06h.cloudfront.net)"
        echo "   3. Create invalidation for paths: /* and /models/*"
    fi
else
    echo "⚠️  AWS CLI not available"
    echo "💡 Manual CloudFront invalidation needed"
fi

echo ""

echo "🔧 Step 3: Testing CORS headers immediately..."
echo "--------------------------------------------"

sleep 5  # Wait a moment for changes to start propagating

TEST_URL="https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb"

echo "📍 Testing URL: $TEST_URL"
echo "🌐 Testing with Origin: http://localhost:3000"

CORS_TEST=$(curl -s -H "Origin: http://localhost:3000" -I "$TEST_URL")
HTTP_STATUS=$(echo "$CORS_TEST" | head -1 | cut -d' ' -f2)
CORS_ORIGIN=$(echo "$CORS_TEST" | grep -i "access-control-allow-origin" | cut -d: -f2 | tr -d ' \r\n')
CORS_METHODS=$(echo "$CORS_TEST" | grep -i "access-control-allow-methods" | cut -d: -f2 | tr -d ' \r\n')

echo "📊 HTTP Status: $HTTP_STATUS"
echo "🔒 CORS Origin: '$CORS_ORIGIN'"
echo "🔒 CORS Methods: '$CORS_METHODS'"

if [ "$CORS_ORIGIN" = "*" ] && [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ CORS headers: WORKING!"
    echo "🎉 Emergency fix successful!"
else
    echo "❌ CORS headers: STILL MISSING"
    echo "⏰ This may take 5-15 minutes to propagate globally"
fi

echo ""

echo "🔧 Step 4: Browser cache clearing instructions..."
echo "-----------------------------------------------"
echo "🌐 Clear browser cache to ensure fresh CORS checks:"
echo "   • Chrome: Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)"
echo "   • Firefox: Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)"
echo "   • Safari: Cmd+Option+E"
echo "   • Or use Incognito/Private mode"

echo ""

echo "🔧 Step 5: Alternative browser test..."
echo "------------------------------------"

# Create a quick HTML test file
cat > emergency-cors-test.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Emergency CORS Test</title>
</head>
<body>
    <h1>🚨 Emergency CORS Test</h1>
    <div id="result">Testing...</div>
    
    <script>
        const testUrl = 'https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb';
        const resultDiv = document.getElementById('result');
        
        console.log('Testing CORS:', testUrl);
        
        fetch(testUrl, {
            method: 'HEAD',
            mode: 'cors'
        })
        .then(response => {
            console.log('Response:', response);
            console.log('Status:', response.status);
            console.log('Headers:', [...response.headers.entries()]);
            
            const corsOrigin = response.headers.get('access-control-allow-origin');
            const success = response.ok && corsOrigin === '*';
            
            resultDiv.innerHTML = `
                <h2>${success ? '✅ CORS WORKING!' : '❌ CORS FAILED'}</h2>
                <p><strong>Status:</strong> ${response.status}</p>
                <p><strong>CORS Origin:</strong> ${corsOrigin || 'Missing'}</p>
                <p><strong>URL:</strong> ${testUrl}</p>
                ${success ? '<p>🎉 Your model loading should work now!</p>' : '<p>⏰ Wait 5-15 minutes for propagation</p>'}
            `;
        })
        .catch(error => {
            console.error('CORS Error:', error);
            resultDiv.innerHTML = `
                <h2>❌ CORS ERROR</h2>
                <p><strong>Error:</strong> ${error.message}</p>
                <p>This indicates CORS is still not working properly.</p>
            `;
        });
    </script>
</body>
</html>
EOF

echo "📄 Created emergency-cors-test.html"
echo "🌐 Open this file in your browser to test CORS"

echo ""

echo "🎯 NEXT STEPS"
echo "============="
echo "1. ⏰ Wait 5-15 minutes for global CloudFront propagation"
echo "2. 🌐 Clear browser cache or use incognito mode"
echo "3. 🧪 Open emergency-cors-test.html in browser"
echo "4. 📱 Test your actual frontend application"
echo "5. 🔄 If still failing, run this script again"

echo ""
echo "📞 MANUAL BACKUP PLAN"
echo "====================="
echo "If automated fixes don't work, manually:"
echo "1. 🔧 AWS S3 Console → Your bucket → Permissions → CORS"
echo "2. 🔧 AWS CloudFront Console → Your distribution → Invalidations"
echo "3. 🔧 Create invalidation for paths: /* and /models/*"

echo ""
echo "🚨 Emergency CORS fix completed!"
echo "⏰ Allow up to 15 minutes for global propagation"

# Cleanup
rm -f cors-config.json
