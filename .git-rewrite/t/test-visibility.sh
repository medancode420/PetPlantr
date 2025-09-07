#!/bin/bash

# Simple visibility test
echo "=== PetPlantr Terminal Test ==="
echo "✅ This text should be visible"
echo "🔧 Checking environment..."

# Reset any terminal formatting
printf '\033[0m'

echo "📋 Environment Variables Status:"
echo "- REPLICATE_API_TOKEN: ${REPLICATE_API_TOKEN:0:8}..."
echo "- AWS_S3_BUCKET: ${AWS_S3_BUCKET}"
echo "- CLOUDFRONT_DOMAIN: ${CLOUDFRONT_DOMAIN}"

echo ""
echo "🎯 Ready to proceed with Sprint 1!"
