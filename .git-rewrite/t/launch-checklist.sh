#!/bin/bash
# PetPlantr Launch Day Final Checklist

echo "🚀 PetPlantr Launch Day Checklist"
echo "================================="
echo "Complete all items before announcing to public"
echo ""

# Colors for checklist
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_item() {
    local item="$1"
    local check_command="$2"
    
    printf "[ ] $item: "
    
    if [ -n "$check_command" ]; then
        if eval "$check_command" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ PASS${NC}"
            return 0
        else
            echo -e "${RED}❌ FAIL${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⏳ MANUAL${NC}"
        return 0
    fi
}

echo "🌐 DNS & Infrastructure"
echo "----------------------"
check_item "DNS resolves to Vercel" "[ \"\$(dig +short api.petplantr.com A)\" = \"76.76.21.21\" ]"
check_item "SSL certificate valid" "curl -s -I https://api.petplantr.com/api/health | grep -q '200 OK'"
check_item "Health endpoint responding" "curl -s https://api.petplantr.com/api/health | jq -e '.pipeline == \"real\"'"
check_item "Main site accessible" "curl -s -I https://petplantr.com | grep -q '200 OK'"

echo ""
echo "🤖 AI Pipeline"
echo "-------------"
check_item "AI models loaded" "curl -s https://api.petplantr.com/api/health | jq -e '.models | length > 0'"
check_item "Breed detection working" "./validate-production-pipeline.sh | grep -q 'PASSED'"
check_item "Upload functionality" "curl -s https://petplantr.com/api/get-upload-url | jq -e '.uploadUrl'"

echo ""
echo "🔐 Security & Secrets"
echo "--------------------"
check_item "Replicate token active" "curl -s https://api.petplantr.com/api/health | jq -e '.environment.hasReplicateToken == true'"
check_item "AWS credentials working" "curl -s https://api.petplantr.com/api/health | jq -e '.environment.hasAwsKey == true and .environment.hasAwsSecret == true'"
check_item "S3 bucket accessible" "curl -s https://api.petplantr.com/api/health | jq -e '.environment.hasS3Bucket == true'"

echo ""
echo "📊 Monitoring & Analytics"
echo "------------------------"
check_item "Metrics endpoint" "curl -s https://api.petplantr.com/api/metrics | jq -e 'type == \"object\"'"
echo "[ ] Vercel Analytics enabled: ⏳ MANUAL (Check Vercel dashboard)"
echo "[ ] StatusCake/UptimeRobot setup: ⏳ MANUAL (External service)"
echo "[ ] Slack/Discord notifications: ⏳ MANUAL (Webhook configured)"

echo ""
echo "🎨 Frontend & UX"
echo "---------------"
check_item "Upload page accessible" "curl -s -I https://petplantr.com/upload | grep -q '200 OK'"
check_item "Frontend builds deployed" "curl -s https://petplantr.com | grep -q 'PetPlantr'"
echo "[ ] Mobile responsiveness tested: ⏳ MANUAL"
echo "[ ] Error handling tested: ⏳ MANUAL"

echo ""
echo "💳 Payment & Legal"
echo "-----------------"
echo "[ ] Stripe webhooks updated: ⏳ MANUAL (Use exact hostname)"
echo "[ ] Privacy policy updated: ⏳ MANUAL"
echo "[ ] Terms of service current: ⏳ MANUAL"

echo ""
echo "🎯 Launch Actions"
echo "----------------"
echo "[ ] Clear CDN/registrar cache: ⏳ MANUAL"
echo "[ ] Test user journey end-to-end: ⏳ MANUAL"
echo "[ ] Prepare announcement content: ⏳ MANUAL"
echo "[ ] Set up 24h log monitoring: ⏳ MANUAL"

echo ""
echo "📱 Announcement Ready"
echo "--------------------"
echo "[ ] Social media posts drafted: ⏳ MANUAL"
echo "[ ] Email newsletter prepared: ⏳ MANUAL"
echo "[ ] Demo video/screenshots ready: ⏳ MANUAL"

echo ""
echo "🎉 POST-LAUNCH ACTIONS"
echo "======================"
echo "After announcing:"
echo "1. Monitor Vercel logs for first 24 hours"
echo "2. Watch error rates in metrics endpoint"
echo "3. Check user feedback channels"
echo "4. Validate payment flows with real users"
echo "5. Monitor DNS propagation globally"

echo ""
echo "🚨 Emergency Contacts"
echo "--------------------"
echo "• Vercel Support: https://vercel.com/help"
echo "• DNS Provider: GoDaddy"
echo "• Replicate Status: https://status.replicate.com"
echo "• AWS Status: https://status.aws.amazon.com"

echo ""
echo "📋 Quick Launch Commands"
echo "========================"
echo "# Last-minute validation"
echo "./validate-production-pipeline.sh"
echo ""
echo "# Monitor real-time"
echo "./monitor-production.sh"
echo ""
echo "# Check error logs"
echo "vercel logs https://api.petplantr.com --follow"
echo ""
echo "# Emergency rollback (if needed)"
echo "vercel rollback https://api.petplantr.com"

echo ""
echo "🎊 Ready to launch? All green items should be ✅"
echo "================================================"
