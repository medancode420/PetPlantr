#!/bin/bash
# Setup production monitoring for PetPlantr

echo "🔧 Setting up PetPlantr Production Monitoring"
echo "============================================="

# Configuration
DOMAIN="api.petplantr.com"
HEALTH_ENDPOINT="https://$DOMAIN/api/health"
EMAIL="your-email@example.com"  # Update this
SLACK_WEBHOOK=""  # Update this

echo "📊 1. Testing Current Health Status"
echo "-----------------------------------"

# Test health endpoint
response=$(curl -s --max-time 10 "$HEALTH_ENDPOINT" || echo "FAILED")
if [ "$response" != "FAILED" ]; then
    echo "✅ Health endpoint responding"
    echo "$response" | jq . 2>/dev/null || echo "$response"
else
    echo "❌ Health endpoint not responding"
fi

echo ""
echo "🌐 2. DNS & SSL Status"
echo "----------------------"

# Check DNS
dns_result=$(dig +short $DOMAIN A)
echo "DNS Resolution: $dns_result"
if [ "$dns_result" = "76.76.21.21" ]; then
    echo "✅ DNS correctly pointing to Vercel"
else
    echo "⚠️  DNS may need propagation time"
fi

# Check SSL
ssl_status=$(curl -s -I "https://$DOMAIN/api/health" | head -n 1)
echo "SSL Status: $ssl_status"

echo ""
echo "📱 3. StatusCake Monitoring Setup"
echo "--------------------------------"
echo "Manual setup required at: https://www.statuscake.com"
echo ""
echo "Create uptime test with these settings:"
echo "  Name: PetPlantr API Health"
echo "  URL: $HEALTH_ENDPOINT"
echo "  Test Type: HTTP"
echo "  Check Rate: 30 seconds"
echo "  Contact Email: $EMAIL"
echo "  Expected Status: 200"
echo "  Keyword Check: \"pipeline\":\"real\""

echo ""
echo "📈 4. UptimeRobot Alternative"
echo "----------------------------"
echo "Alternative setup at: https://uptimerobot.com"
echo ""
echo "Monitor settings:"
echo "  Type: HTTP(s)"
echo "  URL: $HEALTH_ENDPOINT"
echo "  Interval: 5 minutes (free tier)"
echo "  Keyword: pipeline"

echo ""
echo "🔔 5. Vercel Analytics Setup"
echo "----------------------------"
echo "To enable Vercel Analytics:"
echo "1. Go to: https://vercel.com/dashboard"
echo "2. Select your PetPlantr project"
echo "3. Navigate to: Analytics → Enable"
echo "4. Turn on 'Web Analytics' and 'Serverless Function Monitoring'"

echo ""
echo "⚙️  6. Environment Monitoring Script"
echo "------------------------------------"

cat > monitor-production.sh << 'EOF'
#!/bin/bash
# Continuous production monitoring for PetPlantr

HEALTH_URL="https://api.petplantr.com/api/health"
METRICS_URL="https://api.petplantr.com/api/metrics"
LOG_FILE="production-monitor.log"

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s --max-time 10 "$HEALTH_URL" 2>/dev/null)
    
    if [ $? -eq 0 ] && [[ "$response" == *'"pipeline":"real"'* ]]; then
        echo "[$timestamp] ✅ Health check passed" >> "$LOG_FILE"
        return 0
    else
        echo "[$timestamp] ❌ Health check failed: $response" >> "$LOG_FILE"
        return 1
    fi
}

check_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s --max-time 10 "$METRICS_URL" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "[$timestamp] 📊 Metrics accessible" >> "$LOG_FILE"
        # Parse key metrics
        echo "$response" | jq -r '. | to_entries[] | "  \(.key): \(.value)"' >> "$LOG_FILE" 2>/dev/null
    else
        echo "[$timestamp] ⚠️  Metrics endpoint unavailable" >> "$LOG_FILE"
    fi
}

# Run checks
echo "🔍 Running production health checks..."
if check_health; then
    echo "✅ Health check passed"
    check_metrics
else
    echo "❌ Health check failed - check $LOG_FILE for details"
    exit 1
fi

echo "📋 Recent logs:"
tail -5 "$LOG_FILE"
EOF

chmod +x monitor-production.sh

echo ""
echo "✅ Monitor script created: ./monitor-production.sh"

echo ""
echo "📅 7. Setup Cron Monitoring (Optional)"
echo "-------------------------------------"
echo "To run automated checks every 5 minutes:"
echo "  crontab -e"
echo "  Add: */5 * * * * /path/to/PetPlantr/monitor-production.sh"

echo ""
echo "🔐 8. Secret Rotation Schedule"
echo "-----------------------------"
echo "Quarterly rotation reminder for:"
echo "  • Replicate API tokens"
echo "  • AWS access keys"
echo "  • Database credentials"
echo "  • SSL certificates (auto-renewed by Vercel)"
echo ""
echo "Setup calendar reminder or use AWS Secrets Manager rotation."

echo ""
echo "🎉 Monitoring Setup Complete!"
echo "=============================="
echo "Manual steps remaining:"
echo "  1. Create StatusCake/UptimeRobot account"
echo "  2. Enable Vercel Analytics"
echo "  3. Update email/Slack webhook variables"
echo "  4. Schedule secret rotation"
