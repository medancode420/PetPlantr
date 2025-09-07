#!/bin/bash

echo "🔧 Phase 2: Enabling Essential Extensions"
echo "========================================"

echo "1️⃣ Checking current performance before changes..."
CURRENT_CPU=$(ps aux | grep -E "Code Helper" | grep -v grep | awk '{sum+=$3} END {print sum}')
echo "  Current total VS Code CPU: ${CURRENT_CPU}%"

if (( $(echo "$CURRENT_CPU > 25" | bc -l) )); then
    echo "  ⚠️  CPU usage too high ($CURRENT_CPU%). Wait for it to stabilize."
    exit 1
fi

echo -e "\n2️⃣ Enabling essential extensions..."

# Enable Prettier for formatting
if command -v code &> /dev/null; then
    echo "  Enabling Prettier..."
    code --enable-extension esbenp.prettier-vscode 2>/dev/null && echo "    ✅ Prettier enabled" || echo "    ℹ️  Prettier not installed"
    
    # Wait and check performance
    sleep 3
    NEW_CPU=$(ps aux | grep -E "Code Helper" | grep -v grep | awk '{sum+=$3} END {print sum}')
    echo "    CPU after Prettier: ${NEW_CPU}%"
    
    if (( $(echo "$NEW_CPU > 30" | bc -l) )); then
        echo "    ⚠️  CPU spike detected! Disabling Prettier..."
        code --disable-extension esbenp.prettier-vscode
        exit 1
    fi
    
    # Enable basic TypeScript support (built-in)
    echo "  Enabling TypeScript support..."
    cat >> .vscode/settings.json << 'EOF'

  "typescript.tsserver.maxTsServerMemory": 3072,
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "typescript.suggest.autoImports": false,
  "typescript.preferences.lazyProjectLoading": true
}
EOF
    
    # Remove the duplicate closing brace by replacing the file content
    sed -i '' '$d' .vscode/settings.json
    echo '}' >> .vscode/settings.json
    
    echo "    ✅ TypeScript optimizations added"
fi

echo -e "\n3️⃣ Final performance check..."
sleep 2
FINAL_CPU=$(ps aux | grep -E "Code Helper" | grep -v grep | awk '{sum+=$3} END {print sum}')
echo "  Final total VS Code CPU: ${FINAL_CPU}%"

if (( $(echo "$FINAL_CPU > 25" | bc -l) )); then
    echo "  ⚠️  Performance regression detected!"
    echo "  🔄 Reverting to minimal settings..."
    ./scripts/emergency-cpu-fix.sh
else
    echo "  ✅ Phase 2 successful!"
    echo ""
    echo "📝 You can now:"
    echo "  - Format code with Prettier"
    echo "  - Get basic TypeScript IntelliSense"
    echo "  - Edit files with syntax highlighting"
    echo ""
    echo "🔄 Next: Reload VS Code and test for 5 minutes"
    echo "   If stable, run: ./scripts/enable-phase3.sh"
fi
