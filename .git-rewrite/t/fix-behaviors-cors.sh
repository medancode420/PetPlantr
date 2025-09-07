#!/bin/bash

# CloudFront Behaviors CORS Fix - Configure Response Headers Policy
# Distribution: E501YM9ZMLD5 (PetPlantr CDN)

echo "🎯 CLOUDFRONT BEHAVIORS CORS CONFIGURATION"
echo "=========================================="
echo "📅 $(date)"
echo "🌐 Distribution ID: E501YM9ZMLD5"
echo ""

echo "📊 Current Behaviors Status:"
echo "  0: *.glb     - Response Headers Policy: MISSING ❌"
echo "  1: *.stl     - Response Headers Policy: MISSING ❌"
echo "  2: uploads/* - Response Headers Policy: MISSING ❌"
echo "  3: Default   - Response Headers Policy: MISSING ❌"
echo ""
echo "🚨 This is why CORS headers are missing!"
echo ""

DISTRIBUTION_ID="E501YM9ZMLD5"

echo "🔧 Step 1: Create CORS Response Headers Policy"
echo "--------------------------------------------"

# Create CORS response headers policy via AWS CLI
POLICY_NAME="PetPlantr-CORS-Policy"

echo "📝 Creating policy: $POLICY_NAME"

POLICY_CONFIG='{
  "Name": "PetPlantr-CORS-Policy",
  "Comment": "CORS headers for PetPlantr 3D models and uploads",
  "CORS": {
    "AccessControlAllowOrigins": {
      "Quantity": 1,
      "Items": ["*"]
    },
    "AccessControlAllowHeaders": {
      "Quantity": 1,
      "Items": ["*"]
    },
    "AccessControlAllowMethods": {
      "Quantity": 4,
      "Items": ["GET", "HEAD", "OPTIONS", "PUT"]
    },
    "AccessControlExposeHeaders": {
      "Quantity": 3,
      "Items": ["ETag", "Content-Length", "Content-Type"]
    },
    "AccessControlMaxAgeSec": 3600,
    "OriginOverride": true
  }
}'

# Try to create the policy
if aws cloudfront create-response-headers-policy --response-headers-policy-config "$POLICY_CONFIG" 2>/dev/null; then
    echo "✅ CORS Response Headers Policy created successfully"
    
    # Get the policy ID (we'll need it for behaviors)
    POLICY_ID=$(aws cloudfront list-response-headers-policies --query "ResponseHeadersPolicyList.Items[?ResponseHeadersPolicy.ResponseHeadersPolicyConfig.Name=='PetPlantr-CORS-Policy'].ResponseHeadersPolicy.Id" --output text 2>/dev/null)
    
    if [ -n "$POLICY_ID" ]; then
        echo "📋 Policy ID: $POLICY_ID"
    else
        echo "⚠️  Could not retrieve policy ID"
    fi
else
    echo "⚠️  Policy creation failed (AWS CLI issue or policy exists)"
    echo "💡 Will use managed policy instead"
    
    # Use AWS managed CORS policy
    POLICY_ID="67f7725c-6f97-4210-82d7-5512b31e9d03"  # AWS managed CORS policy
    echo "📋 Using managed policy ID: $POLICY_ID"
fi

echo ""

echo "🔧 Step 2: Manual Behavior Configuration Required"
echo "-----------------------------------------------"

echo "🚨 CRITICAL: You must manually update each behavior in CloudFront Console"
echo ""
echo "📍 Go to: https://console.aws.amazon.com/cloudfront/home#/distribution-settings/E501YM9ZMLD5"
echo ""
echo "🔄 For EACH behavior (*.glb, *.stl, uploads/*, Default), do this:"
echo "1. Click on the behavior (row in the table)"
echo "2. Click 'Edit'"
echo "3. Scroll to 'Response headers policy'"
echo "4. Change from 'None' to one of these options:"
echo ""
echo "   Option A (Recommended): Use Managed Policy"
echo "   🎯 Select: 'Managed-CORS-with-preflight-and-SecurityHeadersPolicy'"
echo ""
echo "   Option B: Use Custom Policy (if created successfully)"
echo "   🎯 Select: 'PetPlantr-CORS-Policy'"
echo ""
echo "5. Click 'Save changes'"
echo "6. Repeat for ALL 4 behaviors"
echo ""

echo "🎯 Behaviors That Need CORS Headers Policy:"
echo "┌─────────────┬─────────────────────────────┬─────────────────┐"
echo "│ Precedence  │ Path Pattern                │ Status          │"
echo "├─────────────┼─────────────────────────────┼─────────────────┤"
echo "│ 0           │ *.glb                       │ ❌ NEEDS POLICY │"
echo "│ 1           │ *.stl                       │ ❌ NEEDS POLICY │"
echo "│ 2           │ uploads/*                   │ ❌ NEEDS POLICY │"
echo "│ 3           │ Default (*)                 │ ❌ NEEDS POLICY │"
echo "└─────────────┴─────────────────────────────┴─────────────────┘"

echo ""

echo "🔧 Step 3: Create Cache Invalidation (Already Done)"
echo "-------------------------------------------------"
echo "✅ Previous invalidation: I1ID5U6AIH1BP3HESHQ4XWJ9HM"
echo "⏰ This invalidation is still processing"

echo ""

echo "🔧 Step 4: Test After Configuration"
echo "----------------------------------"

echo "⏰ After configuring response headers policy for all behaviors:"
echo "1. Wait 5-15 minutes for propagation"
echo "2. Test using: http://localhost:3000/cors-emergency-test.html"
echo "3. Test command line:"

echo ""
echo "curl -H \"Origin: http://localhost:3000\" -I \\"
echo "  \"https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb\" \\"
echo "  | grep -i access-control"
echo ""

echo "🎯 Expected Results After Fix:"
echo "✅ access-control-allow-origin: *"
echo "✅ access-control-allow-methods: GET, HEAD, OPTIONS, PUT"
echo "✅ access-control-expose-headers: ETag, Content-Length, Content-Type"

echo ""

echo "🚨 WHY THIS FIXES THE ISSUE"
echo "==========================="
echo "Root Cause: All 4 behaviors have 'Response headers policy: -' (None)"
echo "Solution: Add CORS policy to each behavior"
echo "Result: CloudFront will add CORS headers to ALL responses"
echo ""
echo "Current Problem:"
echo "  Browser requests → CloudFront → No CORS headers → Browser blocks"
echo ""
echo "After Fix:"
echo "  Browser requests → CloudFront + CORS headers → Browser allows ✅"

echo ""

echo "📋 PRIORITY ORDER FOR MANUAL CONFIGURATION"
echo "=========================================="
echo "1. 🎯 HIGHEST: *.glb behavior (3D models)"
echo "2. 🎯 HIGH: Default (*) behavior (fallback)"
echo "3. 🎯 MEDIUM: *.stl behavior (3D printing)"
echo "4. 🎯 LOW: uploads/* behavior (upload endpoint)"

echo ""

echo "🔗 QUICK LINKS"
echo "=============="
echo "CloudFront Console: https://console.aws.amazon.com/cloudfront/home#/distribution-settings/E501YM9ZMLD5"
echo "Test Page: http://localhost:3000/cors-emergency-test.html"
echo "Behaviors Tab: Click 'Behaviors' then edit each one"

echo ""

echo "⏰ TIMELINE AFTER MANUAL CONFIGURATION"
echo "====================================="
echo "0-5 min:   Configure response headers policy (manual)"
echo "5-15 min:  CloudFront global propagation"
echo "15+ min:   CORS headers working, models loading! 🎉"

echo ""
echo "🎉 Configuration guide completed!"
echo "🚨 Manual behavior configuration is REQUIRED and CRITICAL!"
