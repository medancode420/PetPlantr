# 🚨 BETA-0 EMERGENCY CHEAT SHEET 🚨

## Quick Commands (Copy-Paste Ready)

### 1. Immediate Status Check
```bash
# All systems status
./scripts/beta-diagnostics.sh

# Specific issue
./scripts/beta-diagnostics.sh print-done
./scripts/beta-diagnostics.sh lambda  
./scripts/beta-diagnostics.sh stripe
./scripts/beta-diagnostics.sh stepfunctions
```

### 2. Emergency Fixes
```bash
# Fix PRINT_DONE notifications
./scripts/beta-quick-fix.sh print-done

# Fix specific Lambda function
./scripts/beta-quick-fix.sh lambda stripeWebhook

# Fix Stripe webhooks
./scripts/beta-quick-fix.sh stripe

# Fix Step Functions
./scripts/beta-quick-fix.sh stepfunctions
```

### 3. Manual Emergency Commands

#### Instant Slack Test
```bash
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"text":"🚨 EMERGENCY TEST", "channel":"#ops-alerts"}'
```

#### Check Last 10 Minutes of Errors
```bash
# Any Lambda function
aws logs filter-log-events \
  --log-group-name '/aws/lambda/petplantr-pipeline-dev-FUNCTION' \
  --filter-pattern 'ERROR' \
  --start-time $(date -d '10 minutes ago' +%s)000

# Stripe specifically  
aws logs filter-log-events \
  --log-group-name '/aws/lambda/petplantr-pipeline-dev-stripeWebhook' \
  --filter-pattern 'signature' \
  --start-time $(date -d '10 minutes ago' +%s)000
```

#### Emergency Redeploy
```bash
# Single function
npx dotenv-cli -e .env -- npx serverless deploy --function FUNCTION_NAME

# Full stack (2-3 minutes)
npx dotenv-cli -e .env -- npx serverless deploy
```

## 🎯 Troubleshooting Matrix

| Symptom | 1-Minute Diagnostic | 2-Minute Fix |
|---------|-------------------|-------------|
| **No PRINT_DONE ping** | `./scripts/beta-diagnostics.sh print-done` | `./scripts/beta-quick-fix.sh print-done` |
| **Lambda error alert** | `./scripts/beta-diagnostics.sh lambda` | `./scripts/beta-quick-fix.sh lambda FUNCTION` |  
| **Stripe 400 error** | `./scripts/beta-diagnostics.sh stripe` | `./scripts/beta-quick-fix.sh stripe` |
| **Step Function fails** | `./scripts/beta-diagnostics.sh stepfunctions` | Check AWS Console + IAM roles |

## 📱 Keep These Tabs Open

1. **#ops-alerts**: https://petplantr.slack.com/channels/ops-alerts
2. **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups
3. **Stripe Webhooks**: https://dashboard.stripe.com/webhooks
4. **Step Functions**: https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines

## 🔥 Emergency Escalation

If scripts don't resolve the issue in 5 minutes:

1. **Check this file**: `tail -f /var/log/petplantr-errors.log` (if logging locally)
2. **Ping team**: "🚨 Beta-0 issue: [symptom] - ran diagnostics, need backup"
3. **Fallback**: Pause beta testing, investigate thoroughly

---
*Save this file as a bookmark for instant access during Beta-0*
