#!/bin/bash

echo "🚨 VS Code Emergency CPU Fix"
echo "============================"

# Kill the high CPU processes
echo "1️⃣ Killing high CPU VS Code processes..."
HIGH_CPU_PIDS=$(ps aux | grep -E "Code Helper.*Plugin" | grep -v grep | awk '$3 > 50 {print $2}')

if [ -n "$HIGH_CPU_PIDS" ]; then
    echo "Found high CPU processes: $HIGH_CPU_PIDS"
    echo "$HIGH_CPU_PIDS" | xargs kill -9 2>/dev/null
    echo "✅ High CPU processes terminated"
else
    echo "ℹ️  No extremely high CPU processes found"
fi

# Disable specific problematic extensions
echo -e "\n2️⃣ Disabling problematic extensions..."
PROBLEMATIC_EXTENSIONS=(
    "GitHub.copilot"
    "GitHub.copilot-chat"
    "ms-python.python"
    "ms-python.vscode-pylance"
    "redhat.java"
    "googlecloudtools.cloudcode"
    "eamodio.gitlens"
    "ms-azuretools.vscode-docker"
    "visualstudioexptteam.intellicode-api-usage-examples"
)

for ext in "${PROBLEMATIC_EXTENSIONS[@]}"; do
    if command -v code &> /dev/null; then
        code --disable-extension "$ext" 2>/dev/null && echo "  ✅ Disabled: $ext" || echo "  ℹ️  Not found: $ext"
    fi
done

# Create ultra-minimal settings
echo -e "\n3️⃣ Creating ultra-minimal VS Code settings..."
cat > .vscode/settings.json << 'EOF'
{
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/.next/**": true,
    "**/dist/**": true,
    "**/.serverless/**": true
  },
  "typescript.disableAutomaticTypeAcquisition": true,
  "typescript.tsserver.maxTsServerMemory": 2048,
  "git.enabled": false,
  "npm.autoDetect": "off",
  "editor.quickSuggestions": {
    "other": false,
    "comments": false,
    "strings": false
  },
  "editor.wordBasedSuggestions": false,
  "editor.suggestOnTriggerCharacters": false,
  "editor.parameterHints.enabled": false,
  "editor.hover.enabled": false,
  "editor.minimap.enabled": false,
  "telemetry.telemetryLevel": "off"
}
EOF

echo "✅ Ultra-minimal settings applied"

echo -e "\n4️⃣ Checking current performance..."
ps aux | grep -E "Code Helper" | grep -v grep | sort -k3 -nr | head -3 | awk '{printf "  %5s%% CPU - %s\n", $3, $11}'

echo -e "\n✅ Emergency CPU fix complete!"
echo ""
echo "🔄 Please reload VS Code window:"
echo "   Press Cmd+Shift+P → 'Developer: Reload Window'"
