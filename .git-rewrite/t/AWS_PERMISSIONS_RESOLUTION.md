# 🔧 AWS Permissions Resolution Guide

## Current Situation
The user `petplantr-cli` has limited permissions and cannot create the full PetPlantr infrastructure.

**Current Policies:**
- ✅ CloudFrontFullAccess  
- ✅ AmazonS3FullAccess
- ✅ IAMReadOnlyAccess
- ✅ IAMUserChangePassword

**Missing Permissions for:**
- Lambda functions
- SQS queues  
- Step Functions
- CloudWatch logs/alarms
- KMS keys
- WAF rules
- SNS topics
- Budget management
- IAM role creation

## 🚀 SOLUTION OPTIONS

### Option A: Quick Fix - Add AWS Managed Policies (Recommended)

**If you have admin access to AWS Console or CLI:**

```bash
# Add these AWS managed policies to petplantr-cli user:
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess  
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSKeyManagementServicePowerUser
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSWAFv2FullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSBudgetsActionsWithAWSResourceControlAccess

# Most importantly - IAM permissions to create roles:
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
```

### Option B: AWS Console Method

1. **Go to AWS IAM Console** → Users → petplantr-cli
2. **Click "Add permissions"** → "Attach policies directly"  
3. **Search and attach these policies:**
   - `AWSLambda_FullAccess`
   - `AmazonSQSFullAccess`
   - `AWSStepFunctionsFullAccess` 
   - `CloudWatchFullAccess`
   - `AWSKeyManagementServicePowerUser`
   - `AWSWAFv2FullAccess`
   - `AmazonSNSFullAccess`
   - `AmazonEventBridgeFullAccess`
   - `AWSBudgetsActionsWithAWSResourceControlAccess`
   - `IAMFullAccess` (for creating roles)

### Option C: PowerUser Access (Simple but Broad)

```bash
# Single command - gives broad access to most AWS services:
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

### Option D: Administrator Access (Temporary)

```bash
# ⚠️ WARNING: Only for initial setup, remove after deployment!
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Remove after deployment:
aws iam detach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

## 🎯 IMMEDIATE NEXT STEPS

### After Adding Permissions:

1. **Wait 1-2 minutes** for permissions to propagate
2. **Test permissions:**
   ```bash
   aws sts get-caller-identity
   aws iam list-attached-user-policies --user-name petplantr-cli
   ```
3. **Re-run Terraform deployment:**
   ```bash
   cd /Users/medan/Downloads/PetPlantr/infra
   terraform apply -var-file="terraform.tfvars"
   ```

## 🔍 VERIFICATION COMMANDS

```bash
# Check current permissions:
aws iam list-attached-user-policies --user-name petplantr-cli

# Test key services:
aws lambda list-functions --region us-east-1
aws sqs list-queues --region us-east-1  
aws iam list-roles --max-items 5
```

## 🚨 TROUBLESHOOTING

### If you don't have admin access:
1. **Contact your AWS administrator**
2. **Request the policies listed in Option A**
3. **Share this document with them**

### If using AWS SSO:
1. **Log into AWS SSO console**
2. **Request permission set updates**
3. **May need organization admin assistance**

### If using AWS Organizations:
1. **Check for Service Control Policies (SCPs)**
2. **May need organization-level permissions**

## 📊 MINIMAL PERMISSIONS APPROACH

If you want the absolute minimum permissions, create a custom policy with only:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow", 
      "Action": [
        "lambda:*",
        "sqs:*",
        "states:*",
        "logs:*",
        "cloudwatch:*",
        "kms:*",
        "wafv2:*", 
        "sns:*",
        "events:*",
        "budgets:*",
        "iam:CreateRole",
        "iam:DeleteRole", 
        "iam:GetRole",
        "iam:PutRolePolicy",
        "iam:AttachRolePolicy",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🎉 SUCCESS CRITERIA

After applying permissions, you should be able to:
- ✅ Create Lambda functions
- ✅ Create SQS queues
- ✅ Create IAM roles
- ✅ Create Step Functions
- ✅ Set up monitoring

**Deployment should complete in 5-10 minutes with 34 new resources created.**
