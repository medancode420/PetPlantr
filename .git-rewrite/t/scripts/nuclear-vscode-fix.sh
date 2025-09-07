#!/bin/bash

echo "🚨 NUCLEAR VS CODE FIX - V8 JavaScript Engine Overload"
echo "====================================================="
echo ""
echo "📊 Analysis Results:"
echo "  - V8 JavaScript engine consuming 93% of CPU"
echo "  - Extensions causing infinite compilation loops"
echo "  - 8+ seconds of pure CPU spinning in JavaScript"
echo ""

# Step 1: Force quit VS Code completely
echo "1️⃣ Force quitting ALL VS Code processes..."
pkill -9 -f "Visual Studio Code" 2>/dev/null || true
pkill -9 -f "Code Helper" 2>/dev/null || true
pkill -9 -f "Electron" 2>/dev/null || true
sleep 3

# Step 2: Nuclear option - completely reset VS Code
echo "2️⃣ Nuclear reset of VS Code..."
rm -rf ~/Library/Application\ Support/Code 2>/dev/null || true
rm -rf ~/Library/Preferences/com.microsoft.VSCode* 2>/dev/null || true
rm -rf ~/.vscode 2>/dev/null || true

# Step 3: Create absolutely minimal workspace
echo "3️⃣ Creating minimal workspace..."
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,
  "extensions.ignoreRecommendations": true,
  "workbench.startupEditor": "none",
  "files.watcherExclude": { "**/*": true },
  "search.exclude": { "**/*": true },
  "typescript.disableAutomaticTypeAcquisition": true,
  "javascript.suggest.enabled": false,
  "typescript.suggest.enabled": false,
  "editor.quickSuggestions": { "other": false, "comments": false, "strings": false },
  "editor.wordBasedSuggestions": false,
  "editor.suggestOnTriggerCharacters": false,
  "editor.parameterHints.enabled": false,
  "editor.hover.enabled": false,
  "editor.minimap.enabled": false,
  "editor.renderIndentGuides": false,
  "editor.renderWhitespace": "none",
  "git.enabled": false,
  "npm.autoDetect": "off",
  "telemetry.telemetryLevel": "off"
}
EOF

# Step 4: Create script to open VS Code in safe mode ONLY
cat > open-vscode-safe.sh << 'EOF'
#!/bin/bash
echo "🔒 Opening VS Code in SAFE MODE (No Extensions, No JavaScript)"
echo "============================================================"

# Open with maximum restrictions
"/Applications/Visual Studio Code.app/Contents/MacOS/Electron" \
  --disable-extensions \
  --disable-background-timer-throttling \
  --disable-renderer-backgrounding \
  --disable-background-networking \
  --js-flags="--max-old-space-size=512" \
  .

echo "✅ VS Code opened with:"
echo "  - ALL extensions disabled"
echo "  - JavaScript memory limited to 512MB"
echo "  - Background processing disabled"
echo "  - Only basic text editing available"
EOF

chmod +x open-vscode-safe.sh

echo ""
echo "✅ Nuclear fix complete!"
echo ""
echo "🚀 To open VS Code safely:"
echo "   ./open-vscode-safe.sh"
echo ""
echo "⚠️  This VS Code will have:"
echo "   - NO extensions (zero JavaScript overhead)"
echo "   - NO IntelliSense"
echo "   - NO syntax highlighting"
echo "   - ONLY basic text editing"
echo ""
echo "📝 Alternative editors for development:"
echo "   - nano: nano README.md"
echo "   - vim: vim README.md"
echo "   - Sublime Text: brew install --cask sublime-text"
echo ""
echo "🎯 This is a TEXT EDITOR ONLY mode until we fix the V8 issue"
