# 🖨️ 3D Printer Connection Guide for PetPlantr

**Status:** Ready for Setup  
**Supported Printers:** Creality K1 Max (primary), other Moonraker-compatible printers  
**Connection Type:** Network-based via printer bridge  

## 🎯 Overview

Your PetPlantr system includes a complete 3D printer bridge that connects your physical printer to the backend print queue. When customers order 3D printed planters, print jobs are automatically sent to your printer via AWS SNS → Printer Bridge → K1 Max.

## 🏗️ Architecture Flow

```
Customer Order → Backend Lambda → AWS SNS Print Queue → Bridge Agent → K1 Max Printer
```

## 📋 Prerequisites

### Hardware Requirements
- **Creality K1 Max 3D Printer** (or compatible Moonraker printer)
- Network connection for the printer (WiFi or Ethernet)
- Computer/Raspberry Pi to run the bridge agent

### Software Requirements
- Python 3.8+
- Network access to AWS (for SNS queue)
- SuperSlicer (for STL to G-code conversion)

## 🚀 Step 1: Find Your K1 Max on the Network

First, let's discover your printer's IP address:

```bash
cd /Users/medan/Downloads/PetPlantr/bridge
python3 find_k1_max.py
```

This will scan your network and show something like:
```
✅ Found printer at 192.168.1.217:7125 (Moonraker API)
📍 IP: 192.168.1.217
🔌 Port: 7125
🔧 Type: Moonraker API
```

## 🔧 Step 2: Configure the Bridge

1. **Copy the environment template:**
```bash
cd /Users/medan/Downloads/PetPlantr/bridge
cp .env.example .env
```

2. **Edit the `.env` file with your settings:**
```bash
# K1 Max Configuration
K1_HOST=192.168.1.217  # Use the IP found in Step 1
K1_API_KEY=your_k1_api_key_here

# AWS Configuration  
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
QUEUE_ARN=arn:aws:sns:us-east-1:YOUR_ACCOUNT:petplantr-print-queue-dev

# Notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
```

### 🔑 Getting Your K1 Max API Key

1. Access your K1 Max web interface: `http://192.168.1.217` (your IP)
2. Go to Settings → API Keys
3. Generate a new API key for "PetPlantr Bridge"
4. Copy the key to your `.env` file

### ☁️ AWS Configuration

Your AWS credentials should already be configured from the backend deployment. The print queue SNS topic ARN is:
```
arn:aws:sns:us-east-1:YOUR_ACCOUNT:petplantr-print-queue-dev
```

## 🐍 Step 3: Set Up the Bridge Environment

```bash
cd /Users/medan/Downloads/PetPlantr/bridge

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## 🧪 Step 4: Test the Connection

```bash
# Test K1 Max connection
python3 test_k1_direct.py

# Test full end-to-end workflow
python3 test_end_to_end.py

# Test bridge functionality
python3 test_bridge.py
```

Expected output:
```
✅ K1 Max connection: SUCCESS
✅ AWS SNS connection: SUCCESS  
✅ S3 bucket access: SUCCESS
✅ Bridge ready for print jobs
```

## 🚀 Step 5: Start the Print Bridge

### Option A: Interactive Mode (Recommended for testing)
```bash
./start_bridge.sh
```

This will:
- Test all connections
- Show current status
- Monitor for print jobs
- Provide manual processing instructions

### Option B: Background Service
```bash
# Start as background service
python3 k1max_hybrid_bridge.py --daemon

# Or using Docker
docker-compose up -d
```

## 📋 Step 6: Test with a Print Job

### Manual Test
1. **Generate a test print job:**
```bash
python3 test_end_to_end.py --create-test-job
```

2. **Check the print queue:**
   - Log into AWS Console → SNS → Topics → petplantr-print-queue-dev
   - You should see the test message

3. **Process the job:**
   - The bridge will download the STL from S3
   - Slice it to G-code using your K1 Max profile
   - Send to printer or save for manual printing

### Test via Frontend
1. Go to your PetPlantr frontend: `http://localhost:3000/upload`
2. Upload a pet photo
3. Complete the order process
4. The print job should appear in your bridge logs

## 🎛️ Print Job Processing

When a print job is received, the bridge will:

1. **Download STL** from S3 bucket
2. **Slice to G-code** using optimized K1 Max settings:
   - Layer height: 0.2mm
   - PLA temperature: 210°C
   - Bed temperature: 60°C
   - 15% infill for lightweight planters
3. **Send to printer** or save to `~/PetPlantr_Prints/`
4. **Monitor progress** and send status updates
5. **Notify completion** via Slack (if configured)

## 🔧 Troubleshooting

### Connection Issues
```bash
# Check printer network status
curl http://192.168.1.217:7125/api/version

# Test AWS credentials
aws sns list-topics --region us-east-1

# Verify bridge logs
tail -f bridge.log
```

### Common Issues

**1. "K1 Max not found"**
- Check WiFi connection on printer
- Verify IP address hasn't changed
- Try: `python3 find_k1_max.py`

**2. "AWS credentials invalid"**
- Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
- Check IAM permissions for SNS and S3

**3. "Slicing failed"**
- Install SuperSlicer: `brew install superslicer`
- Check config file: `bridge/config/k1max/petplantr.ini`

## 📁 File Locations

- **Bridge code:** `/Users/medan/Downloads/PetPlantr/bridge/`
- **Print files:** `~/PetPlantr_Prints/`
- **Config:** `bridge/config/k1max/petplantr.ini`
- **Logs:** `bridge/bridge.log`

## 🔄 Print Queue Status

The backend `notifyPrinter` Lambda sends jobs to SNS with this format:
```json
{
  "bucket": "petplantr-stl-ready-dev",
  "key": "orders/pp_20250128_abc12/processed.stl",
  "orderId": "pp_20250128_abc12",
  "userId": "user-456",
  "sizeTier": "MEDIUM",
  "printer": "k1max-01",
  "printJobId": "print-pp_20250128_abc12-1738123456789",
  "priority": "normal",
  "timestamp": "2025-01-28T10:30:45.123Z"
}
```

## 🎯 Next Steps

1. **Complete the bridge setup** following steps 1-6
2. **Test with a sample print job**
3. **Configure monitoring** (Slack notifications)
4. **Set up automatic startup** (systemd service or Docker)
5. **Monitor print queue** for customer orders

## 📞 Support

- **Bridge issues:** Check `bridge/bridge.log`
- **AWS issues:** Verify IAM permissions
- **Printer issues:** Check K1 Max web interface
- **Print quality:** Adjust `petplantr.ini` settings

---

**🎉 Your K1 Max is ready to receive PetPlantr print jobs!**

*Once configured, customer orders will automatically flow from the web app to your 3D printer.*
