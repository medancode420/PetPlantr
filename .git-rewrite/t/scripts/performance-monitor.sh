#!/bin/bash

echo "🔥 VS Code Performance Monitor - Real Time"
echo "========================================"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "🔥 VS Code Performance Monitor - $(date '+%H:%M:%S')"
    echo "========================================"
    
    # Check VS Code processes
    echo -e "\n📊 VS Code CPU Usage:"
    ps aux | grep -E "Code Helper|Visual Studio Code" | grep -v grep | sort -k3 -nr | head -5 | while read line; do
        CPU=$(echo $line | awk '{print $3}')
        PID=$(echo $line | awk '{print $2}')
        PROCESS=$(echo $line | awk '{print $11}' | sed 's|.*/||' | cut -c1-30)
        
        if (( $(echo "$CPU > 50" | bc -l) )); then
            echo -e "  🔴 ${CPU}% CPU - ${PROCESS} (PID: ${PID})"
        elif (( $(echo "$CPU > 20" | bc -l) )); then
            echo -e "  🟡 ${CPU}% CPU - ${PROCESS} (PID: ${PID})"
        else
            echo -e "  🟢 ${CPU}% CPU - ${PROCESS} (PID: ${PID})"
        fi
    done
    
    # Memory usage
    echo -e "\n💾 Memory Usage:"
    TOTAL_MEM=$(ps aux | grep -E "Code Helper|Visual Studio Code" | grep -v grep | awk '{sum+=$6} END {printf "%.1f", sum/1024/1024}')
    echo "  Total VS Code Memory: ${TOTAL_MEM} GB"
    
    # Extension processes
    echo -e "\n📦 Extension Processes:"
    ps aux | grep -E "server\.js|tsserver|eslint" | grep -v grep | wc -l | xargs echo "  Active extension servers:"
    
    # Recommendations
    echo -e "\n💡 Status:"
    HIGH_CPU_COUNT=$(ps aux | grep -E "Code Helper" | grep -v grep | awk '$3 > 30' | wc -l)
    if [ $HIGH_CPU_COUNT -gt 0 ]; then
        echo "  ⚠️  HIGH CPU DETECTED - $HIGH_CPU_COUNT processes over 30%"
        echo "  🔧 Action: Kill high CPU processes or disable extensions"
    else
        echo "  ✅ Performance looks good"
    fi
    
    sleep 2
done
