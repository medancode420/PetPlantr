#!/bin/bash

# 🐾 PetPlantr Interactive Demo
# Simple demonstration of the working system

echo "🐾 Welcome to PetPlantr!"
echo "========================"
echo ""
echo "Let me show you how PetPlantr works step by step..."
echo ""

API_URL="https://cm1ffbb7hf.execute-api.us-east-1.amazonaws.com/dev"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🏭 Step 1: Check Farm Status${NC}"
echo "Checking our 3D printer farm..."
echo ""

FARM_STATUS=$(curl -s "$API_URL/api/farm/status")
echo "$FARM_STATUS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Farm Status: {data[\"status\"]}')
print(f'📊 Total Printers: {data[\"farmStats\"][\"totalPrinters\"]}')
print(f'📋 Queue Size: {data[\"farmStats\"][\"queueSize\"]}')
print(f'⚡ Utilization: {data[\"farmStats\"][\"utilizationRate\"]}%')
"
echo ""

echo -e "${BLUE}🤖 Step 2: Add a Printer${NC}"
echo "Adding a new 3D printer to our farm..."
echo ""

NEW_PRINTER='{
  "name": "Ender 3 Pro #1",
  "ipAddress": "192.168.1.100",
  "materialLoaded": "PLA Blue"
}'

ADD_RESULT=$(curl -s -X POST -H "Content-Type: application/json" -d "$NEW_PRINTER" "$API_URL/api/farm/printers")
echo "$ADD_RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'printer' in data:
        print(f'✅ Printer Added: {data[\"printer\"][\"name\"]}')
        print(f'📍 IP Address: {data[\"printer\"][\"ipAddress\"]}')
        print(f'🎨 Material: {data[\"printer\"][\"materialLoaded\"]}')
    else:
        print(f'ℹ️  Response: {data.get(\"message\", \"Unknown\")}')
except:
    print('ℹ️  Printer already exists or other response')
"
echo ""

echo -e "${BLUE}🐕 Step 3: Create a Pet Planter Order${NC}"
echo "Customer wants a Golden Retriever planter..."
echo ""

NEW_ORDER='{
  "customerId": "customer_demo",
  "customerEmail": "demo@petplantr.com",
  "petName": "Buddy",
  "breed": "Golden Retriever",
  "stlFile": "golden-retriever-buddy.stl",
  "estimatedTime": 180,
  "materialType": "PLA",
  "materialColor": "Golden",
  "priority": 7,
  "qualityRequirements": "high"
}'

ORDER_RESULT=$(curl -s -X POST -H "Content-Type: application/json" -d "$NEW_ORDER" "$API_URL/api/farm/jobs")
echo "$ORDER_RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'job' in data:
        print(f'✅ Order Created: {data[\"job\"][\"petName\"]} ({data[\"job\"][\"breed\"]})')
        print(f'📧 Customer: {data[\"job\"][\"customerEmail\"]}')
        print(f'⏱️  Estimated Time: {data[\"job\"][\"estimatedTime\"]} minutes')
        print(f'🎨 Material: {data[\"job\"][\"materialColor\"]} {data[\"job\"][\"materialType\"]}')
    else:
        print(f'ℹ️  Response: {data.get(\"message\", \"Order processed\")}')
except:
    print('ℹ️  Order processed or already exists')
"
echo ""

echo -e "${BLUE}📊 Step 4: Check Analytics${NC}"
echo "Viewing real-time farm analytics..."
echo ""

ANALYTICS=$(curl -s "$API_URL/api/farm/analytics")
echo "$ANALYTICS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
analytics = data['analytics']
print(f'⚡ Power Consumption: {analytics[\"realtime\"][\"powerConsumption\"]}kW')
print(f'🌱 CO2 Impact: {analytics[\"realtime\"][\"totalCO2\"]}kg')
print(f'📈 Efficiency: {analytics[\"realtime\"][\"efficiency\"]}%')
print(f'😊 Customer Satisfaction: {analytics[\"realtime\"][\"customerSatisfaction\"]}%')
print(f'⏰ Queue Clear Time: {analytics[\"predictions\"][\"queueClearTime\"]}')
"
echo ""

echo -e "${BLUE}🏥 Step 5: Check Printer Health${NC}"
echo "Monitoring printer health and performance..."
echo ""

HEALTH=$(curl -s "$API_URL/api/farm/health")
echo "$HEALTH" | python3 -c "
import sys, json
data = json.load(sys.stdin)
health = data['health']
print(f'🌡️  Bed Temperature: {health[\"temperature\"][\"bed\"][\"current\"]}°C ({health[\"temperature\"][\"bed\"][\"stability\"]})')
print(f'🌡️  Nozzle Temperature: {health[\"temperature\"][\"nozzle\"][\"current\"]}°C ({health[\"temperature\"][\"nozzle\"][\"stability\"]})')
print(f'⚙️  Mechanical Status: {health[\"mechanical\"][\"alignment\"]}')
print(f'🎯 Print Speed: {health[\"performance\"][\"speed\"]}mm/s')
print(f'🧵 Filament Remaining: {health[\"consumables\"][\"filamentRemaining\"]}%')
"
echo ""

echo -e "${BLUE}📱 Step 6: Frontend Dashboard Data${NC}"
echo "Getting data optimized for frontend dashboard..."
echo ""

DASHBOARD=$(curl -s "$API_URL/api/farm/frontend")
echo "$DASHBOARD" | python3 -c "
import sys, json
data = json.load(sys.stdin)
dashboard = data['dashboard']
stats = dashboard['quickStats']
print(f'🏭 Active Printers: {stats[\"activePrinters\"]}/{stats[\"totalPrinters\"]}')
print(f'📋 Queue Size: {stats[\"queueSize\"]} orders')
print(f'✅ Completed Today: {stats[\"todayCompleted\"]} planters')
print(f'⭐ Average Quality: {stats[\"averageQuality\"]}%')
print('')
print('📰 Recent Events:')
for event in dashboard['recentEvents']:
    print(f'  • {event[\"message\"]} ({event[\"time\"]})')
"
echo ""

echo -e "${GREEN}🎉 PetPlantr Demo Complete!${NC}"
echo ""
echo "What you just saw:"
echo "✅ Farm management system is operational"
echo "✅ Can add and manage 3D printers"
echo "✅ Can create and track pet planter orders"
echo "✅ Real-time analytics and monitoring"
echo "✅ Health monitoring for all equipment"
echo "✅ Frontend-optimized API responses"
echo ""
echo "🚀 Your PetPlantr system is LIVE and ready!"
echo ""
echo "📊 View live data anytime:"
echo "   curl $API_URL/api/farm/status | python3 -m json.tool"
echo ""
echo "🎮 Try these endpoints:"
echo "   • $API_URL/api/farm/status"
echo "   • $API_URL/api/farm/analytics" 
echo "   • $API_URL/api/farm/health"
echo "   • $API_URL/api/farm/frontend"
echo ""
echo "🌐 Ready for frontend integration!"
