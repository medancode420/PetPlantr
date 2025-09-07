# PetPlantr Live Monitoring Setup

## Current Health Endpoint
✅ **Live endpoint**: https://petplantr.com/api/healthz
✅ **Success string**: `"model":"s3://petplantr-models/models/unet256_stage2_best.pth"`
✅ **Response format**: JSON with status, model paths, and system health

## Monitoring Recommendations

### 1. External Monitoring (Pingdom/UptimeRobot)
```
URL: https://petplantr.com/api/healthz
Method: GET
Check Interval: 5 minutes
Success Criteria: 
- HTTP Status: 200
- Response contains: "status":"healthy"
- Response contains: "model":"s3://petplantr-models/models/unet256_stage2_best.pth"
```

### 2. CloudWatch Alarms
```bash
# Lambda Error Rate Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "PetPlantr-Lambda-Errors" \
  --alarm-description "Lambda function errors > 0" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=petplantr-pipeline-prod-generateSTL \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:ops-alerts

# Lambda Duration Alarm  
aws cloudwatch put-metric-alarm \
  --alarm-name "PetPlantr-Lambda-Duration" \
  --alarm-description "Lambda duration > 8 minutes" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 480000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=petplantr-pipeline-prod-generateSTL
```

### 3. Slack Integration
The system already has Slack webhooks configured for:
- `ORDER_PAID` events
- `PRINT_DONE` notifications  
- Error alerts via CloudWatch → SNS → Slack

### 4. Email Monitoring
- Customer emails: Daniel@PetPlantr.com (Microsoft Graph)
- Fallback: noreply@petplantr.com (SES)
- Internal alerts: ops-alerts@petplantr.com

## Health Check Response Example
```json
{
  "status": "healthy",
  "timestamp": "2025-06-26T02:10:22.843Z",
  "version": "1.6.0",
  "models": {
    "stage1": "s3://petplantr-models/models/unet128_stage1_best.pth",
    "stage2": "s3://petplantr-models/models/unet256_stage2_best.pth"
  },
  "services": {
    "s3": "accessible",
    "stripe": "configured", 
    "email": "microsoft-graph-ready"
  }
}
```

## Current Status: ✅ MONITORING READY
- Health endpoint: Live and tested
- Performance metrics: 13/13 tests passing
- Error logging: CloudWatch enabled
- Notification system: Slack + Email configured

**Next**: Ready for first live order! 🚀
