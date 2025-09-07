#!/bin/bash

echo "🔍 VS Code Freeze Diagnostic Tool"
echo "================================="
echo ""

# Step 1: Check if VS Code is running and frozen
echo "1️⃣ Checking VS Code Status..."
VSCODE_PIDS=$(pgrep -f "Code Helper\|Visual Studio Code" | head -5)
if [ -z "$VSCODE_PIDS" ]; then
    echo "❌ VS Code is not running"
    exit 1
else
    echo "✅ VS Code processes found: $(echo $VSCODE_PIDS | wc -w) processes"
fi

# Step 2: Identify high CPU processes
echo -e "\n2️⃣ High CPU VS Code Processes:"
ps aux | grep -E "Code Helper|Visual Studio Code" | grep -v grep | sort -k3 -nr | head -5 | while read line; do
    CPU=$(echo $line | awk '{print $3}')
    PID=$(echo $line | awk '{print $2}')
    PROCESS=$(echo $line | awk '{print $11}' | xargs basename)
    
    if (( $(echo "$CPU > 20" | bc -l) )); then
        echo "🔴 HIGH CPU: $CPU% - $PROCESS (PID: $PID)"
        echo "   Sample this process in Activity Monitor!"
    elif (( $(echo "$CPU > 10" | bc -l) )); then
        echo "🟡 Medium CPU: $CPU% - $PROCESS (PID: $PID)"
    else
        echo "🟢 Normal: $CPU% - $PROCESS (PID: $PID)"
    fi
done

# Step 3: Check for common culprits
echo -e "\n3️⃣ Checking for Known Problem Extensions:"
if pgrep -f "copilot" > /dev/null; then
    echo "🤖 GitHub Copilot is running - LIKELY CULPRIT"
fi

if pgrep -f "pylance" > /dev/null; then
    echo "🐍 Python/Pylance is running - LIKELY CULPRIT"
fi

if pgrep -f "java.*jdt" > /dev/null; then
    echo "☕ Java Language Server is running - LIKELY CULPRIT"
fi

# Step 4: Instructions for next steps
echo -e "\n4️⃣ Next Steps:"
echo "==============="
echo ""
echo "📊 To collect evidence:"
echo "   1. Open Activity Monitor"
echo "   2. Find the highest CPU 'Code Helper' process"
echo "   3. Select it and press ⌥⌘S (Sample Process)"
echo "   4. Save as code_sample.txt"
echo ""
echo "🔍 To run Extension Bisect:"
echo "   1. Open VS Code"
echo "   2. Press ⌘⇧P"
echo "   3. Type: Extensions: Bisect - Start"
echo "   4. Follow the prompts"
echo ""
echo "🚑 Emergency fix (if frozen):"
echo "   ./scripts/emergency-vscode-fix.sh"

echo ""
echo "💡 Most likely causes based on your setup:"
echo "   - GitHub Copilot (12% CPU usage detected earlier)"
echo "   - Python/Pylance extension"
echo "   - Java Language Server"
echo "   - Large file opened accidentally"
