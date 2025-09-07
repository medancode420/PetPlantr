# 🚀 Port Forwarding Setup Guide

## Your Network Details:
- **Local IP:** 192.168.1.218 (your MacBook)
- **Router IPs to try:** 192.168.1.1, 192.168.0.1, 10.0.0.1

## Port Forwarding Rules Needed:

### Rule 1: HTTP (Port 80)
- **Name:** PetPlantr-HTTP
- **External Port:** 80
- **Internal Port:** 80
- **Protocol:** TCP
- **Internal IP:** 192.168.1.218

### Rule 2: HTTPS (Port 443)
- **Name:** PetPlantr-HTTPS
- **External Port:** 443
- **Internal Port:** 443
- **Protocol:** TCP
- **Internal IP:** 192.168.1.218

## Test After Setup:
```bash
# Test HTTP
curl -s http://petplantr.com

# Test HTTPS (after SSL setup)
curl -s -k https://petplantr.com
```

## Common Router Login Credentials:
- **Username:** admin
- **Password:** admin, password, 1234, or check router sticker

## If You Can't Access Router:
- Check network settings on your Mac
- Look for router manual online
- Contact your ISP for assistance
