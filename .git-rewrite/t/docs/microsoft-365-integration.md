# Microsoft 365 Email Integration for PetPlantr

## Overview

This document describes the integration of Daniel@PetPlantr.com Microsoft 365 email account with the PetPlantr system. The integration provides professional email communication using Microsoft Graph API.

## Features

### ✅ Email Types Supported

1. **Order Confirmation** - Sent immediately after payment
2. **Order Completion** - Sent when STL file is ready with download link
3. **Order Status Updates** - Sent for processing updates or issues
4. **Internal Notifications** - Alerts sent to Daniel for new orders and system events

### ✅ Email Capabilities

- **Professional Branding**: All emails sent from Daniel@PetPlantr.com
- **Rich HTML Templates**: Modern, responsive email designs
- **Automatic Fallback**: Falls back to AWS SES if Microsoft Graph unavailable
- **Download Links**: Secure, time-limited STL file downloads
- **Print Instructions**: Detailed 3D printing specifications included

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Stripe Webhook  │───▶│ Enhanced Email   │───▶│ Microsoft Graph │
│ (Payment)       │    │ Service          │    │ API             │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
┌─────────────────┐    ┌──────────────────┐              │
│ Notify Customer │───▶│ Microsoft Graph  │              │
│ (Completion)    │    │ Service          │              │
└─────────────────┘    └──────────────────┘              │
                                │                        │
                       ┌──────────────────┐              │
                       │ AWS Secrets      │◀─────────────┘
                       │ Manager          │
                       │ (Credentials)    │
                       └──────────────────┘
```

## Email Templates

### Order Confirmation Email
- **Trigger**: Stripe webhook (payment success)
- **Sender**: Daniel@PetPlantr.com  
- **Subject**: "Order Confirmed: PetPlantr #[ORDER_ID]"
- **Content**: Order details, timeline, next steps
- **Style**: Blue theme, professional layout

### Order Completion Email  
- **Trigger**: STL generation complete
- **Sender**: Daniel@PetPlantr.com
- **Subject**: "🎉 Your Custom PetPlantr is Ready! Order #[ORDER_ID]"
- **Content**: Download link, printing specs, tips
- **Style**: Green theme, celebration design

### Internal Notifications
- **Trigger**: New orders, system alerts
- **Sender**: Daniel@PetPlantr.com
- **Recipient**: Daniel@PetPlantr.com
- **Content**: Order details, system status, alerts

## Setup Instructions

### 1. Azure App Registration

Run the setup script to get step-by-step instructions:

```bash
./scripts/setup-microsoft-graph.sh
```

Or follow these manual steps:

1. **Create App Registration**:
   - Go to [Azure Portal > App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps)
   - Click "New registration"
   - Name: "PetPlantr Email Service"
   - Account types: "Accounts in this organizational directory only"
   - Click "Register"

2. **Configure API Permissions**:
   - Go to "API permissions"
   - Add permission > Microsoft Graph > Application permissions
   - Add:
     - `Mail.Send` (Send mail as any user)
     - `User.Read.All` (Read all users' full profiles)
   - Click "Grant admin consent"

3. **Create Client Secret**:
   - Go to "Certificates & secrets"
   - New client secret: "PetPlantr Production"
   - Expires: 24 months
   - Copy the secret value

4. **Get Credentials**:
   - Copy Tenant ID from Overview
   - Copy Client ID from Overview

### 2. AWS Secrets Manager Setup

Store credentials securely:

```bash
# Run the setup script
./scripts/setup-microsoft-graph.sh

# Or manually create the secret
aws secretsmanager create-secret \
  --name "petplantr/microsoft/graph-config" \
  --description "Microsoft Graph configuration for PetPlantr email service" \
  --secret-string '{
    "tenantId": "YOUR_TENANT_ID",
    "clientId": "YOUR_CLIENT_ID", 
    "clientSecret": "YOUR_CLIENT_SECRET",
    "emailAddress": "Daniel@PetPlantr.com"
  }'
```

### 3. Deploy Backend

```bash
cd backend
npm install
npm run build
npm run deploy
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MICROSOFT_GRAPH_ENABLED` | Enable Microsoft Graph | `true` |
| `SENDER_EMAIL` | Primary sender email | `Daniel@PetPlantr.com` |
| `FALLBACK_EMAIL` | Fallback sender email | `noreply@petplantr.com` |
| `SES_ENABLED` | Enable SES fallback | `false` |

### AWS Secrets

| Secret Name | Description |
|-------------|-------------|
| `petplantr/microsoft/graph-config` | Microsoft Graph credentials |
| `petplantr/slack/webhook-url` | Slack webhook for alerts |
| `petplantr/stripe/webhook-secret` | Stripe webhook verification |

## Testing

### 1. Test Email Sending

Create a test order to verify email delivery:

```bash
cd backend
npm run test:smoke-e2e
```

### 2. Manual Testing

```javascript
// Test in Lambda console or locally
const emailService = new EnhancedEmailService();

await emailService.sendOrderConfirmation(
  { email: 'test@example.com', name: 'Test Customer' },
  {
    orderId: 'pp_test_123',
    userId: 'user_123',
    photoCount: 2,
    sizeTier: 'MEDIUM',
    amount: 2999
  }
);
```

### 3. Verify in Microsoft 365

- Check Sent Items in Daniel@PetPlantr.com Outlook
- Verify email delivery to test recipients
- Check message tracking in Exchange admin center

## Monitoring

### Email Delivery Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/petplantr-backend-prod-stripeWebhook --follow

# Check for Microsoft Graph errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/petplantr-backend-prod-notifyCustomer \
  --filter-pattern "Microsoft Graph"
```

### Success Indicators

✅ **Working correctly**:
- Logs show "Microsoft Graph service initialized successfully"
- Emails appear in Daniel@PetPlantr.com Sent Items
- Customers receive emails from Daniel@PetPlantr.com

❌ **Fallback to SES**:
- Logs show "Microsoft Graph not available, falling back to SES"
- Emails sent from noreply@petplantr.com instead
- Check Azure app permissions and secret expiration

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: Failed to acquire Microsoft Graph token: AADSTS7000215
```
- **Solution**: Check admin consent is granted in Azure portal
- **Verify**: App permissions include Mail.Send and User.Read.All

**2. Secret Not Found**
```
Error: Microsoft Graph not available, falling back to SES: Secrets Manager can't find the specified secret
```
- **Solution**: Run `./scripts/setup-microsoft-graph.sh` to create secrets
- **Verify**: Secret exists in AWS Secrets Manager console

**3. Mail Send Permission**
```
Error: Insufficient privileges to complete the operation
```
- **Solution**: Grant admin consent for Mail.Send permission
- **Verify**: Check API permissions in Azure app registration

### Debug Commands

```bash
# Check AWS secrets
aws secretsmanager get-secret-value \
  --secret-id petplantr/microsoft/graph-config \
  --query SecretString --output text | jq .

# Test Lambda function
aws lambda invoke \
  --function-name petplantr-backend-prod-notifyCustomer \
  --payload '{"orderId":"test","userId":"test","readyStlKey":"test.stl","status":"COMPLETED"}' \
  response.json

# Check app registration
az ad app list --query "[?displayName=='PetPlantr Email Service']"
```

## Security Considerations

### Credentials Security
- ✅ Credentials stored in AWS Secrets Manager (encrypted)
- ✅ No credentials in code or environment variables
- ✅ Azure client secret expires in 24 months (set reminder)
- ✅ IAM permissions limit access to specific secrets

### Email Security  
- ✅ DKIM signing via Microsoft 365
- ✅ SPF records configured in DNS
- ✅ Modern authentication (OAuth 2.0)
- ✅ Application permissions (no user context required)

### Monitoring
- ✅ All email sending logged in CloudWatch
- ✅ Failed attempts logged and alerted
- ✅ Fallback to SES if Microsoft Graph unavailable

## Maintenance

### Monthly Tasks
- [ ] Check Azure client secret expiration (24 months)
- [ ] Review email delivery metrics
- [ ] Test backup/fallback systems

### When Adding New Email Types
1. Add method to `MicrosoftGraphService`
2. Add method to `EnhancedEmailService`  
3. Update Lambda functions to use new email type
4. Test with real email addresses
5. Update this documentation

## Production Checklist

- [ ] Azure app registration created and configured
- [ ] Admin consent granted for Microsoft Graph permissions
- [ ] AWS Secrets Manager configured with credentials
- [ ] Lambda functions deployed with latest code
- [ ] Test emails sent and received successfully
- [ ] Email templates reviewed and approved
- [ ] Monitoring and alerting configured
- [ ] Fallback to SES tested and working
- [ ] Documentation updated and team trained

---

**Status**: ✅ Ready for Production  
**Last Updated**: June 25, 2025  
**Contact**: Daniel@PetPlantr.com for support
