#!/bin/bash
# AWS Cost Explorer GPU Budget Alert Setup
# Creates budget alert for GPU costs exceeding $100/month

set -e

# Configuration
BUDGET_NAME="PetPlantr-GPU-Monthly-Budget"
BUDGET_AMOUNT="100.00"
NOTIFICATION_EMAIL="ops-alerts@petplantr.com"
AWS_REGION="us-west-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "🚀 Setting up AWS Cost Explorer GPU Budget Alert..."
log_info "💰 Budget Amount: \$$BUDGET_AMOUNT/month"
log_info "📧 Notification Email: $NOTIFICATION_EMAIL"

# Create budget JSON configuration
BUDGET_JSON=$(cat <<EOF
{
    "BudgetName": "$BUDGET_NAME",
    "BudgetLimit": {
        "Amount": "$BUDGET_AMOUNT",
        "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {
        "Service": [
            "Amazon Elastic Compute Cloud - Compute"
        ],
        "UsageType": [
            "GPU-Instance",
            "GPU-Hours"
        ]
    },
    "CalculatedSpend": {
        "ActualSpend": {
            "Amount": "0.00",
            "Unit": "USD"
        }
    }
}
EOF
)

# Create notification configuration
NOTIFICATION_JSON=$(cat <<EOF
[
    {
        "Notification": {
            "NotificationType": "ACTUAL",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 80.0,
            "ThresholdType": "PERCENTAGE",
            "NotificationState": "ALARM"
        },
        "Subscribers": [
            {
                "SubscriptionType": "EMAIL",
                "Address": "$NOTIFICATION_EMAIL"
            }
        ]
    },
    {
        "Notification": {
            "NotificationType": "FORECASTED",
            "ComparisonOperator": "GREATER_THAN", 
            "Threshold": 100.0,
            "ThresholdType": "PERCENTAGE",
            "NotificationState": "ALARM"
        },
        "Subscribers": [
            {
                "SubscriptionType": "EMAIL",
                "Address": "$NOTIFICATION_EMAIL"
            }
        ]
    }
]
EOF
)

# Check if budget already exists
log_info "🔍 Checking if budget already exists..."
if aws budgets describe-budget \
    --account-id $(aws sts get-caller-identity --query Account --output text) \
    --budget-name "$BUDGET_NAME" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    
    log_warning "⚠️  Budget '$BUDGET_NAME' already exists."
    log_info "Do you want to update it? [y/N]"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Update existing budget
        log_info "🔄 Updating existing budget..."
        aws budgets modify-budget \
            --account-id $(aws sts get-caller-identity --query Account --output text) \
            --new-budget "$BUDGET_JSON" \
            --region "$AWS_REGION"
        log_success "✅ Budget updated successfully"
    else
        log_info "Budget creation skipped"
        exit 0
    fi
else
    # Create new budget
    log_info "📊 Creating new budget..."
    aws budgets create-budget \
        --account-id $(aws sts get-caller-identity --query Account --output text) \
        --budget "$BUDGET_JSON" \
        --notifications-with-subscribers "$NOTIFICATION_JSON" \
        --region "$AWS_REGION"
    log_success "✅ Budget created successfully"
fi

# Verify budget creation
log_info "🔍 Verifying budget configuration..."
BUDGET_INFO=$(aws budgets describe-budget \
    --account-id $(aws sts get-caller-identity --query Account --output text) \
    --budget-name "$BUDGET_NAME" \
    --region "$AWS_REGION" \
    --query 'Budget.{Name:BudgetName,Amount:BudgetLimit.Amount,Unit:BudgetLimit.Unit,Type:BudgetType}' \
    --output table)

echo "$BUDGET_INFO"

# Get current spend
log_info "💳 Checking current GPU spend..."
CURRENT_MONTH=$(date +%Y-%m)
CURRENT_SPEND=$(aws ce get-cost-and-usage \
    --time-period Start=${CURRENT_MONTH}-01,End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE \
    --filter file://<(cat <<EOF
{
    "Dimensions": {
        "Key": "SERVICE",
        "Values": ["Amazon Elastic Compute Cloud - Compute"]
    }
}
EOF
) \
    --query 'ResultsByTime[0].Groups[?Keys[0]==`Amazon Elastic Compute Cloud - Compute`].Metrics.BlendedCost.Amount' \
    --output text 2>/dev/null || echo "0.00")

if [ "$CURRENT_SPEND" != "0.00" ] && [ -n "$CURRENT_SPEND" ]; then
    log_info "💰 Current EC2 spend this month: \$$CURRENT_SPEND"
    
    # Calculate percentage of budget used
    PERCENTAGE=$(python3 -c "print(f'{(float('$CURRENT_SPEND') / float('$BUDGET_AMOUNT')) * 100:.1f}')" 2>/dev/null || echo "0.0")
    log_info "📊 Budget utilization: ${PERCENTAGE}%"
    
    if (( $(echo "$PERCENTAGE > 80" | bc -l) )); then
        log_warning "⚠️  Warning: Over 80% of budget used!"
    fi
else
    log_info "💰 No EC2 charges found for current month"
fi

# Summary
log_success "🎉 AWS Cost Explorer GPU Budget Alert Setup Complete!"
echo ""
log_info "📋 Budget Configuration:"
log_info "   • Name: $BUDGET_NAME"
log_info "   • Amount: \$$BUDGET_AMOUNT/month"
log_info "   • Alert at 80% (actual spend)"
log_info "   • Alert at 100% (forecasted spend)"
log_info "   • Email: $NOTIFICATION_EMAIL"
echo ""
log_info "🔗 Next steps:"
log_info "   1. Check email for AWS Budget confirmation"
log_info "   2. Monitor budget in AWS Console > Billing > Budgets"
log_info "   3. Adjust alert thresholds if needed"

exit 0
