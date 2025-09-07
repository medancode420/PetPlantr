# 🎯 CLOUDFRONT CORS CONFIGURATION - STEP BY STEP

**Distribution ID**: E501YM9ZMLD5  
**Domain**: dpa0b9puwj06h.cloudfront.net  
**Invalidation Created**: ✅ I1ID5U6AIH1BP3HESHQ4XWJ9HM (in progress)

---

## 🚨 CRITICAL: Configure Response Headers Policy

Your CloudFront invalidation is running, but you need to configure the **Response Headers Policy** to add CORS headers. Here's exactly how:

### **Step 1: Go to CloudFront Console**
```
https://console.aws.amazon.com/cloudfront/home#/distribution-settings/E501YM9ZMLD5
```

### **Step 2: Configure Behaviors**
1. **Click "Behaviors" tab**
2. **Select the default behavior** (the one with Path pattern "*")
3. **Click "Edit"**

### **Step 3: Add Response Headers Policy**
Scroll down to **"Response headers policy"** section:

**Option A: Use Managed Policy (Easiest)**
- Change from "None" to **"Managed-CORS-with-preflight-and-SecurityHeadersPolicy"**
- This adds all necessary CORS headers automatically

**Option B: Create Custom Policy (Recommended)**
1. Click **"Create response headers policy"**
2. **Policy name**: `PetPlantr-CORS-Policy`
3. **Description**: `CORS headers for PetPlantr 3D models`

**In CORS section, add:**
- ✅ **Access-Control-Allow-Origin**: `*`
- ✅ **Access-Control-Allow-Headers**: `*`
- ✅ **Access-Control-Allow-Methods**: `GET, HEAD, OPTIONS`
- ✅ **Access-Control-Max-Age**: `3600`
- ✅ **Access-Control-Expose-Headers**: `ETag, Content-Length`
- ✅ **Origin override**: Yes

### **Step 4: Save and Wait**
1. **Click "Save changes"**
2. **Wait 5-15 minutes** for global propagation
3. **The invalidation is already running** (I1ID5U6AIH1BP3HESHQ4XWJ9HM)

---

## 🧪 TEST AFTER CONFIGURATION

### **Test 1: Browser Test**
Open: `http://localhost:3000/cors-emergency-test.html`
- Click "Test CORS Headers"
- Should show: ✅ CORS HEADERS: WORKING!

### **Test 2: Command Line Test**
```bash
curl -H "Origin: http://localhost:3000" -I \
  "https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb" \
  | grep -i access-control
```

**Expected output:**
```
access-control-allow-origin: *
access-control-allow-methods: GET, HEAD, OPTIONS
access-control-expose-headers: ETag, Content-Length
```

### **Test 3: Model Viewer Test**
Your actual model viewer should now load 3D models without CORS errors.

---

## 📊 CURRENT STATUS

- ✅ **CloudFront Distribution**: E501YM9ZMLD5 (identified)
- ✅ **Cache Invalidation**: I1ID5U6AIH1BP3HESHQ4XWJ9HM (in progress)
- ⏳ **Response Headers Policy**: Needs manual configuration (critical step)
- ⏳ **Propagation**: 5-15 minutes after headers policy is configured

---

## 🎯 SUCCESS CRITERIA

Once the headers policy is configured and propagated:
- ✅ `access-control-allow-origin: *` in response headers
- ✅ 3D models load successfully in browser
- ✅ No CORS policy errors in browser console
- ✅ Model viewer displays pet planters correctly

---

## 🔧 ALTERNATIVE: Quick AWS CLI Method

If you prefer command line and have AWS CLI configured:

```bash
# Create response headers policy
aws cloudfront create-response-headers-policy \
  --response-headers-policy-config '{
    "Name": "PetPlantr-CORS-Policy",
    "Comment": "CORS headers for PetPlantr 3D models",
    "CORS": {
      "AccessControlAllowOrigins": {
        "Quantity": 1,
        "Items": ["*"]
      },
      "AccessControlAllowHeaders": {
        "Quantity": 1,
        "Items": ["*"]
      },
      "AccessControlAllowMethods": {
        "Quantity": 3,
        "Items": ["GET", "HEAD", "OPTIONS"]
      },
      "AccessControlExposeHeaders": {
        "Quantity": 2,
        "Items": ["ETag", "Content-Length"]
      },
      "AccessControlMaxAgeSec": 3600,
      "OriginOverride": true
    }
  }'
```

Then update the distribution behavior to use this policy.

---

## ⏰ TIMELINE

- **Now**: Configure response headers policy (5 minutes)
- **5-15 minutes**: Global CloudFront propagation
- **Result**: CORS headers working, models loading successfully

---

**🎯 NEXT ACTION**: Configure the response headers policy in CloudFront console using the steps above. This is the critical missing piece!

---

*Configuration guide created: $(date)*
