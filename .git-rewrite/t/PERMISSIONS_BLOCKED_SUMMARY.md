# 🔧 PetPlantr AWS Permissions - RESOLUTION REQUIRED

## 🚨 CURRENT STATUS
**BLOCKED**: Terraform deployment failed due to insufficient AWS permissions for user `petplantr-cli`.

**What's Working:**
- ✅ S3 Bucket (deployed)
- ✅ CloudFront CDN (deployed) 
- ✅ Development environment

**What's Blocked:**
- ⏸️ Lambda Functions (3x)
- ⏸️ SQS Queues (3x)
- ⏸️ Step Functions
- ⏸️ CloudWatch Monitoring
- ⏸️ Security (KMS, WAF)
- ⏸️ Notifications (SNS)

## 🎯 REQUIRED ACTION

**Someone with AWS admin access needs to run ONE of these commands:**

### Option 1: Quick Fix (Recommended)
```bash
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

### Option 2: Minimal Permissions
```bash
# Add each policy individually:
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSKeyManagementServicePowerUser
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AWSWAFv2FullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
aws iam attach-user-policy --user-name petplantr-cli --policy-arn arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess
```

### Option 3: AWS Console
1. Go to IAM Console → Users → petplantr-cli
2. Add permissions → Attach policies directly
3. Search and attach "PowerUserAccess"

## 🚀 AFTER PERMISSIONS ARE FIXED

Run this to complete the deployment:
```bash
cd /Users/medan/Downloads/PetPlantr/infra
terraform apply -var-file="terraform.tfvars"
```

**Expected result:** 34 new AWS resources created in 5-10 minutes.

## 🔄 ALTERNATIVE: DEPLOY WITH ADMIN CREDENTIALS

If you have admin AWS credentials available:

```bash
# Set admin credentials temporarily
export AWS_ACCESS_KEY_ID=your_admin_access_key
export AWS_SECRET_ACCESS_KEY=your_admin_secret_key

# Deploy infrastructure  
cd /Users/medan/Downloads/PetPlantr/infra
terraform apply -var-file="terraform.tfvars"

# Restore original credentials after deployment
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
```

## 📋 VERIFICATION

After permissions are added, verify with:
```bash
aws sts get-caller-identity
aws iam list-attached-user-policies --user-name petplantr-cli
```

## 📞 WHO CAN HELP

**Authorized users who can fix this:**
- AWS account administrator
- IAM users with `IAMFullAccess` or `AdministratorAccess`
- AWS root account user
- Organization administrators (if using AWS Organizations)

---

**🎯 BOTTOM LINE:** Need 1 command from an AWS admin to complete the deployment. Everything else is ready to go!
