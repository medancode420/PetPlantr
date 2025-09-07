#!/bin/bash

# setup-cost-guardrails.sh
# Set up AWS and Replicate budget alerts and cost monitoring

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_color() {
    echo -e "${1}${2}${NC}"
}

# Configuration
ALERT_EMAIL="${ALERT_EMAIL:-$(git config user.email || echo 'admin@petplantr.com')}"
DAILY_BUDGET_USD="${DAILY_BUDGET_USD:-50}"
MONTHLY_BUDGET_USD="${MONTHLY_BUDGET_USD:-1000}"

echo_color "$BLUE" "💰 Setting up Cost Guardrails for PetPlantr"
echo "============================================"
echo "Daily Budget: \$${DAILY_BUDGET_USD}"
echo "Monthly Budget: \$${MONTHLY_BUDGET_USD}"
echo "Alert Email: ${ALERT_EMAIL}"
echo ""

# Check AWS CLI availability
if ! command -v aws &> /dev/null; then
    echo_color "$RED" "❌ AWS CLI not found. Please install it first:"
    echo "  macOS: brew install awscli"
    echo "  Linux: apt-get install awscli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo_color "$RED" "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

echo_color "$GREEN" "✅ AWS CLI configured"

# Create SNS topic for budget alerts
setup_aws_budget_alerts() {
    echo_color "$BLUE" "Setting up AWS budget alerts..."
    
    # Create SNS topic for alerts
    topic_arn=$(aws sns create-topic --name petplantr-cost-alerts --query 'TopicArn' --output text 2>/dev/null || echo "")
    
    if [ -n "$topic_arn" ]; then
        echo_color "$GREEN" "✅ SNS topic created: $topic_arn"
        
        # Subscribe email to topic
        aws sns subscribe --topic-arn "$topic_arn" --protocol email --notification-endpoint "$ALERT_EMAIL" > /dev/null
        echo_color "$GREEN" "✅ Email subscription added (check your email for confirmation)"
        
        # Create daily budget alert
        cat > /tmp/daily-budget.json << EOF
{
    "BudgetName": "PetPlantr-Daily-Budget",
    "BudgetLimit": {
        "Amount": "$DAILY_BUDGET_USD",
        "Unit": "USD"
    },
    "TimeUnit": "DAILY",
    "TimePeriod": {
        "Start": "$(date +%Y-%m-01)",
        "End": "$(date -d 'next month' +%Y-%m-01)"
    },
    "CostFilters": {
        "Service": [
            "Amazon Simple Storage Service",
            "AWS Lambda",
            "Amazon API Gateway"
        ]
    },
    "BudgetType": "COST"
}
EOF
        
        # Create monthly budget alert  
        cat > /tmp/monthly-budget.json << EOF
{
    "BudgetName": "PetPlantr-Monthly-Budget",
    "BudgetLimit": {
        "Amount": "$MONTHLY_BUDGET_USD",
        "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "TimePeriod": {
        "Start": "$(date +%Y-%m-01)",
        "End": "$(date -d 'next month' +%Y-%m-01)"
    },
    "BudgetType": "COST"
}
EOF

        # Create budget notifications
        cat > /tmp/budget-notifications.json << EOF
[
    {
        "Notification": {
            "NotificationType": "ACTUAL",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 80,
            "ThresholdType": "PERCENTAGE"
        },
        "Subscribers": [
            {
                "SubscriptionType": "EMAIL",
                "Address": "$ALERT_EMAIL"
            },
            {
                "SubscriptionType": "SNS",
                "Address": "$topic_arn"
            }
        ]
    },
    {
        "Notification": {
            "NotificationType": "FORECASTED",
            "ComparisonOperator": "GREATER_THAN", 
            "Threshold": 100,
            "ThresholdType": "PERCENTAGE"
        },
        "Subscribers": [
            {
                "SubscriptionType": "EMAIL", 
                "Address": "$ALERT_EMAIL"
            }
        ]
    }
]
EOF
        
        # Create the budgets
        aws budgets create-budget \
            --account-id "$(aws sts get-caller-identity --query Account --output text)" \
            --budget file:///tmp/daily-budget.json \
            --notifications-with-subscribers file:///tmp/budget-notifications.json > /dev/null 2>&1 || echo "Daily budget may already exist"
            
        aws budgets create-budget \
            --account-id "$(aws sts get-caller-identity --query Account --output text)" \
            --budget file:///tmp/monthly-budget.json \
            --notifications-with-subscribers file:///tmp/budget-notifications.json > /dev/null 2>&1 || echo "Monthly budget may already exist"
        
        echo_color "$GREEN" "✅ AWS budget alerts configured"
        
        # Cleanup temp files
        rm -f /tmp/daily-budget.json /tmp/monthly-budget.json /tmp/budget-notifications.json
        
    else
        echo_color "$RED" "❌ Failed to create SNS topic"
    fi
}

# Create cost monitoring script
create_cost_monitor() {
    echo_color "$BLUE" "Creating cost monitoring script..."
    
    cat > monitor-costs.sh << 'EOF'
#!/bin/bash

# monitor-costs.sh - Daily cost monitoring for PetPlantr

set -euo pipefail

ALERT_EMAIL="${ALERT_EMAIL:-admin@petplantr.com}"
DAILY_THRESHOLD="${DAILY_THRESHOLD:-50}"

# Get current month costs
get_current_costs() {
    local start_date=$(date +%Y-%m-01)
    local end_date=$(date +%Y-%m-%d)
    
    aws ce get-cost-and-usage \
        --time-period "Start=$start_date,End=$end_date" \
        --granularity MONTHLY \
        --metrics BlendedCost \
        --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
        --output text 2>/dev/null || echo "0"
}

# Get yesterday's costs
get_daily_costs() {
    local yesterday=$(date -d yesterday +%Y-%m-%d)
    local today=$(date +%Y-%m-%d)
    
    aws ce get-cost-and-usage \
        --time-period "Start=$yesterday,End=$today" \
        --granularity DAILY \
        --metrics BlendedCost \
        --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
        --output text 2>/dev/null || echo "0"
}

# Check Replicate usage (if API available)
check_replicate_usage() {
    if [ -n "${REPLICATE_API_TOKEN:-}" ]; then
        echo "Replicate usage monitoring not yet implemented"
        echo "Consider adding Replicate API calls to check model usage"
    fi
}

echo "💰 PetPlantr Cost Monitoring Report"
echo "===================================="
echo "Date: $(date)"

monthly_cost=$(get_current_costs)
daily_cost=$(get_daily_costs)

echo "Monthly cost (to date): \$${monthly_cost}"
echo "Yesterday's cost: \$${daily_cost}"

# Check if daily cost exceeds threshold
if (( $(echo "$daily_cost > $DAILY_THRESHOLD" | bc -l) )); then
    echo "⚠️  WARNING: Daily cost (\$${daily_cost}) exceeds threshold (\$${DAILY_THRESHOLD})"
    
    # Send alert email (requires sendmail or similar)
    if command -v mail &> /dev/null; then
        echo "Daily AWS costs for PetPlantr exceeded \$${DAILY_THRESHOLD}. Current: \$${daily_cost}" | \
            mail -s "PetPlantr Cost Alert" "$ALERT_EMAIL"
    fi
else
    echo "✅ Daily costs within budget"
fi

# Check Replicate usage
check_replicate_usage

echo ""
echo "💡 Cost optimization tips:"
echo "- Monitor S3 storage usage and clean up old test images"
echo "- Use Replicate's smallest suitable models for development"
echo "- Set up automated cleanup of temporary files"
echo "- Consider using AWS Lambda for infrequent operations"
EOF

    chmod +x monitor-costs.sh
    echo_color "$GREEN" "✅ Cost monitoring script created: monitor-costs.sh"
}

# Create cost optimization recommendations
create_cost_optimization_guide() {
    echo_color "$BLUE" "Creating cost optimization guide..."
    
    cat > COST_OPTIMIZATION_GUIDE.md << 'EOF'
# PetPlantr Cost Optimization Guide

## Current Cost Structure

### AWS Services
- **S3 Storage**: Image uploads and generated models
- **API Gateway**: HTTP requests (if using AWS API Gateway)
- **Lambda**: Serverless functions (if applicable)
- **Data Transfer**: Bandwidth costs

### Replicate API
- **Model Inference**: Per-prediction pricing
- **Premium Models**: Higher cost for advanced models
- **Compute Time**: Based on processing duration

## Cost Optimization Strategies

### 1. Image Storage Optimization
```bash
# Set up S3 lifecycle policies to automatically delete temp files
aws s3api put-bucket-lifecycle-configuration \
    --bucket petplantr-storage \
    --lifecycle-configuration file://lifecycle-policy.json
```

### 2. Replicate Usage Optimization
- Use smaller models for development/testing
- Implement caching for repeated requests
- Batch multiple images when possible
- Monitor model performance vs. cost

### 3. Monitoring and Alerts
- Daily cost monitoring: `./monitor-costs.sh`
- AWS Budget alerts at 80% and 100% thresholds
- Replicate usage tracking (implement custom monitoring)

### 4. Development Best Practices
- Use FAST_MODE=true for CI/CD to avoid AI costs
- Implement image compression before upload
- Clean up test artifacts regularly
- Use CDN for static assets

## Emergency Cost Controls

### Immediate Actions if Costs Spike
1. **Disable Auto-scaling**: Prevent runaway usage
2. **Check Replicate Usage**: Review recent API calls
3. **Audit S3 Storage**: Look for large unexpected files
4. **Review API Logs**: Check for abuse or unusual patterns

### Budget Breach Response
```bash
# Emergency cost control - disable expensive features
export ENABLE_PRODUCTION_AI=false
export FAST_MODE=true

# Check current month spending
aws ce get-cost-and-usage \
    --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost
```

## Cost Tracking Dashboard

### Daily Commands
```bash
# Check AWS costs
./monitor-costs.sh

# Check S3 usage
aws s3 ls s3://petplantr-storage --recursive --human-readable --summarize

# Monitor Replicate balance (if API supports it)
curl -H "Authorization: Token $REPLICATE_API_TOKEN" https://api.replicate.com/v1/account
```

### Weekly Review
1. Analyze cost trends
2. Review storage cleanup
3. Optimize model usage patterns
4. Update budget forecasts

## Budget Recommendations

### Development Environment
- Daily: $5-10
- Monthly: $50-150

### Production Environment  
- Daily: $10-50
- Monthly: $300-1000

### Scale Planning
- Plan for 10x usage spikes during marketing campaigns
- Set hard limits at 2x expected usage
- Monitor user growth vs. cost growth ratios
EOF

    echo_color "$GREEN" "✅ Cost optimization guide created: COST_OPTIMIZATION_GUIDE.md"
}

# Main execution
main() {
    echo_color "$BLUE" "Starting cost guardrail setup..."
    
    # Setup AWS budget alerts
    setup_aws_budget_alerts
    
    # Create monitoring tools
    create_cost_monitor
    create_cost_optimization_guide
    
    echo ""
    echo_color "$GREEN" "🎉 Cost guardrails setup complete!"
    echo ""
    echo_color "$YELLOW" "Next steps:"
    echo "1. Check your email and confirm SNS subscription"
    echo "2. Run './monitor-costs.sh' to test cost monitoring"
    echo "3. Add './monitor-costs.sh' to your daily cron jobs"
    echo "4. Review COST_OPTIMIZATION_GUIDE.md for optimization tips"
    echo "5. Set up Replicate account limits in their dashboard"
    echo ""
    echo_color "$BLUE" "Monitoring commands:"
    echo "- Daily costs: ./monitor-costs.sh"
    echo "- AWS budgets: aws budgets describe-budgets --account-id \$(aws sts get-caller-identity --query Account --output text)"
    echo "- S3 usage: aws s3 ls s3://petplantr-storage --recursive --human-readable --summarize"
}

# Verify prerequisites
if [ -z "${AWS_ACCESS_KEY_ID:-}" ] || [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    echo_color "$RED" "❌ AWS credentials not found in environment"
    echo "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    exit 1
fi

main "$@"
