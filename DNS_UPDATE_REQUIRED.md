# 🚨 DNS Configuration Required

## Current Status
- **Domain**: petplantr.com ✅ Purchased
- **Current DNS**: 76.76.21.21 ❌ (Wrong IP)
- **Required DNS**: 96.245.127.40 ✅ (Your server IP)

## 📋 DNS Records to Update

### A Records (REQUIRED)
```
@     A     96.245.127.40    ; Root domain
www   A     96.245.127.40    ; WWW subdomain
api   A     96.245.127.40    ; API subdomain
```

### CNAME Records (Optional)
```
mail  CNAME  ghs.google.com  ; Gmail integration
```

## 🛠️ How to Update DNS

1. **Go to your domain registrar** (where you purchased petplantr.com)
2. **Navigate to DNS settings**
3. **Update the A records** to point to `96.245.127.40`
4. **Wait 5-30 minutes** for DNS propagation
5. **Test the changes** with: `dig +short petplantr.com`

## ✅ After DNS Update
Once DNS is updated, run:
```bash
./deploy_production.sh
```

## 🔍 DNS Propagation Check
```bash
# Check current DNS
dig +short petplantr.com

# Should return: 96.245.127.40
```

---
**Status**: ⏳ Waiting for DNS update to 96.245.127.40
