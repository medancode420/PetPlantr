#!/bin/bash
# Post-deploy canary monitoring script

HEARTBEAT_IMAGE="/tmp/petplantr_heartbeat.jpg"
API_ENDPOINT="${API_ENDPOINT:-https://petplantr.com}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
FAILURE_COUNT=0
MAX_FAILURES=3

# Download a lightweight test image
curl -s "https://images.unsplash.com/photo-1552053831-71594a27632d?w=200" -o "$HEARTBEAT_IMAGE"

while true; do
    # Test breed detection endpoint
    response=$(curl -s -X POST \
        -F "file=@$HEARTBEAT_IMAGE" \
        -F "use_tta=false" \
        "$API_ENDPOINT/api/v1/breed/detect" \
        -w "%{http_code}" -o /dev/null 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "$(date): ✅ Heartbeat successful"
        FAILURE_COUNT=0
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        echo "$(date): ❌ Heartbeat failed (attempt $FAILURE_COUNT/$MAX_FAILURES)"
        
        if [ "$FAILURE_COUNT" -ge "$MAX_FAILURES" ] && [ -n "$SLACK_WEBHOOK" ]; then
            # Send Slack alert
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"🚨 PetPlantr API is down! $MAX_FAILURES consecutive failures detected.\"}" \
                "$SLACK_WEBHOOK"
            
            # Reset counter to avoid spam
            FAILURE_COUNT=0
        fi
    fi
    
    # Wait 5 minutes
    sleep 300
done
