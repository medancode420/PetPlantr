# 🔧 Verizon Fios Router Port Forwarding Setup Guide

## Step 1: Access Router
1. Open web browser
2. Go to: `http://192.168.1.1`
3. Enter router password (from sticker)
4. Click "Log In"

## Step 2: Navigate to Port Forwarding
1. Look for menu (left side or top)
2. Click "Firewall" or "Advanced"
3. Click "Port Forwarding" or "Virtual Server"
4. View current rules list

## Step 3: Delete Old Rules
- Find rules for ports 80/443
- Click "Delete" or "Remove"
- Confirm deletion

## Step 4: Add New Rules

### Rule 1: HTTP (8080)
```
Name: PetPlantr-HTTP
External Port: 8080
Internal Port: 8080
Protocol: TCP
Internal IP: 192.168.1.218
```

### Rule 2: HTTPS (8443)
```
Name: PetPlantr-HTTPS
External Port: 8443
Internal Port: 8443
Protocol: TCP
Internal IP: 192.168.1.218
```

## Step 5: Save & Test
1. Click "Apply" or "Save"
2. Wait for router to reboot (1-2 min)
3. Test with:
   ```bash
   curl -s http://petplantr.com:8080
   curl -s -k https://petplantr.com:8443
   ```

## Final URLs
- **Main Site:** `https://petplantr.com:8443`
- **API:** `https://petplantr.com:8443/api/v1/health`
- **Monitoring:** `https://petplantr.com:8443/monitoring`

## Troubleshooting
- Can't find settings? Look under "Advanced"
- Rules not saving? Try different browser
- Tests failing? Verify IP: 192.168.1.218
- Still issues? Contact Verizon support

---
**After completion: Your AI platform will be live worldwide!** 🚀
