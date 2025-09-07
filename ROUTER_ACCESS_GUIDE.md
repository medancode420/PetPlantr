# 🔧 Router Access & Port Forwarding Guide

## Step 1: Find Your Router IP
Your local IP: `192.168.1.218`
Your router IP: `192.168.1.1` (most likely)

## Step 2: Access Router Admin Panel
Open your web browser and go to:
- `http://192.168.1.1` (most common)
- `http://192.168.0.1`
- `http://10.0.0.1`
- `http://192.168.1.254`

## Step 3: Login Credentials
Try these common combinations:
- Username: `admin`, Password: `admin`
- Username: `admin`, Password: `password`
- Username: `admin`, Password: `1234`
- Username: `admin`, Password: `12345`

**Check the sticker on your router for exact credentials!**

## Step 4: Find Port Forwarding Settings
Look for these menu options:
- Port Forwarding
- Virtual Server
- NAT Settings
- Advanced Settings > Port Forwarding
- Firewall > Port Forwarding

## Step 5: Add Port Forwarding Rules

### Rule 1: HTTP (Port 80)
```
Name: PetPlantr-HTTP
External Port: 80
Internal Port: 80
Protocol: TCP
Internal IP: 192.168.1.218
```

### Rule 2: HTTPS (Port 443)
```
Name: PetPlantr-HTTPS
External Port: 443
Internal Port: 443
Protocol: TCP
Internal IP: 192.168.1.218
```

## Step 6: Save & Test
1. Save the settings
2. Test with: `curl http://petplantr.com`

## 🔍 Troubleshooting
- If login doesn't work, try different URLs
- Check router manual online by brand/model
- Contact your ISP if you can't access router
- Some routers require app-based setup

## 📞 Need Help?
- Check router brand sticker for model number
- Search online: "[router brand] port forwarding setup"
- Contact router manufacturer support

---
**After port forwarding: Your site will be live at https://petplantr.com**
