# 📋 DNS Records for petplantr.com

## A Records to Update:
```
Host: @
Type: A
Value: 96.245.127.40
TTL: Auto (or 600)

Host: www
Type: A  
Value: 96.245.127.40
TTL: Auto (or 600)

Host: api
Type: A
Value: 96.245.127.40
TTL: Auto (or 600)
```

## Current Status:
- ❌ Domain: petplantr.com (registered ✅)
- ❌ DNS: Currently pointing to wrong IP
- ✅ Server: 96.245.127.40 (ready)

## Test After Update:
```bash
dig +short petplantr.com
# Should return: 96.245.127.40
```

## Next Step:
Once DNS is updated, run:
```bash
./deploy_production.sh
```
