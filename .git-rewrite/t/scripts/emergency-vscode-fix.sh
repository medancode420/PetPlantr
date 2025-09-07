#!/bin/bash

echo "🚑 VS Code Emergency Fix"
echo "========================"
echo ""

# Force quit all VS Code processes
echo "1️⃣ Force quitting VS Code..."
pkill -9 -f "Code Helper" 2>/dev/null || true
pkill -9 -f "Visual Studio Code" 2>/dev/null || true
pkill -9 -f "tsserver" 2>/dev/null || true
pkill -9 -f "eslint" 2>/dev/null || true
pkill -9 -f "copilot" 2>/dev/null || true
pkill -9 -f "pylance" 2>/dev/null || true
pkill -9 -f "java.*jdt" 2>/dev/null || true

echo "✅ All VS Code processes terminated"

# Clear caches
echo -e "\n2️⃣ Clearing caches..."
rm -rf ~/Library/Application\ Support/Code/Cache/* 2>/dev/null || true
rm -rf ~/Library/Application\ Support/Code/CachedData/* 2>/dev/null || true
rm -rf ~/Library/Application\ Support/Code/logs/* 2>/dev/null || true
rm -rf ~/.vscode/extensions/*/node_modules/.cache 2>/dev/null || true

echo "✅ Caches cleared"

# Create minimal settings
echo -e "\n3️⃣ Creating minimal VS Code settings..."
mkdir -p .vscode
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
  "typescript.tsserver.maxTsServerMemory": 2048,
  "typescript.disableAutomaticTypeAcquisition": true,
  "github.copilot.enable": {
    "*": false
  },
  "git.enabled": false,
  "npm.autoDetect": "off",
  "editor.minimap.enabled": false,
  "editor.semanticHighlighting.enabled": false
}
EOF

echo "✅ Minimal settings created"

echo -e "\n4️⃣ Opening VS Code in safe mode..."
if command -v code &> /dev/null; then
    code --disable-extensions .
elif [ -d "/Applications/Visual Studio Code.app" ]; then
    open -a "Visual Studio Code" --args --disable-extensions .
else
    echo "⚠️  Please open VS Code manually from Applications folder"
fi

echo ""
echo "✅ Emergency fix complete!"
echo ""
echo "🔄 VS Code should now open with:"
echo "   - All extensions disabled"
echo "   - Minimal settings"
echo "   - Reduced memory usage"
echo ""
echo "📝 To gradually re-enable features:"
echo "   1. Enable essential extensions one by one"
echo "   2. Monitor CPU usage in Activity Monitor"
echo "   3. Stop when you find the problematic extension"
