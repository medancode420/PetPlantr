#!/bin/bash#!/bin/bash



# VS Code Binary and System Architecture Analysis# VS Code Binary and System Architecture Analysis

# Analyzes what architecture VS Code and system tools will use# Analyzes what architecture VS Code and system tools will use



echo "=== Apple Silicon Native Analysis ==="echo "=== Apple Silicon Native Analysis ==="

echo "Date: $(date)"echo "Date: $(date)"

echo "System Architecture: $(uname -m)"echo "System Architecture: $(uname -m)"

echo ""echo ""



# Check system architecture# Check system architecture

if [[ "$(uname -m)" != "arm64" ]]; thenif [[ "$(uname -m)" != "arm64" ]]; then

    echo "❌ Not running on Apple Silicon (arm64)"    echo "❌ Not running on Apple Silicon (arm64)"

    exit 1    exit 1

fifi

echo "✅ Running on Apple Silicon (arm64)"echo "✅ Running on Apple Silicon (arm64)"

echo ""echo ""



# Check VS Code installation# Check VS Code installation

echo "=== VS Code Installation Analysis ==="echo "=== VS Code Installation Analysis ==="

VSCODE_PATH="/Applications/Visual Studio Code.app"VSCODE_PATH="/Applications/Visual Studio Code.app"

if [[ ! -d "$VSCODE_PATH" ]]; thenif [[ ! -d "$VSCODE_PATH" ]]; then

    echo "❌ VS Code not found at $VSCODE_PATH"    echo "❌ VS Code not found at $VSCODE_PATH"

    exit 1    exit 1

fifi



echo "✅ VS Code found at $VSCODE_PATH"echo "✅ VS Code found at $VSCODE_PATH"



# Check VS Code binary architectures# Check VS Code binary architectures

echo ""echo ""

echo "=== VS Code Binary Architecture Support ==="echo "=== VS Code Binary Architecture Support ==="

ELECTRON_PATH="$VSCODE_PATH/Contents/MacOS/Electron"ELECTRON_PATH="$VSCODE_PATH/Contents/MacOS/Electron"

PLUGIN_HELPER_PATH="$VSCODE_PATH/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin)"PLUGIN_HELPER_PATH="$VSCODE_PATH/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin)"



if [[ -f "$ELECTRON_PATH" ]]; thenif [[ -f "$ELECTRON_PATH" ]]; then

    echo "Main Electron binary:"    echo "Main Electron binary:"

    lipo -info "$ELECTRON_PATH" | sed 's/^/  /'    lipo -info "$ELECTRON_PATH" | sed 's/^/  /'

    if lipo -info "$ELECTRON_PATH" | grep -q "arm64"; then    if lipo -info "$ELECTRON_PATH" | grep -q "arm64"; then

        echo "  ✅ Supports Apple Silicon (arm64)"        echo "  ✅ Supports Apple Silicon (arm64)"

    else    else

        echo "  ❌ Does not support Apple Silicon"        echo "  ❌ Does not support Apple Silicon"

    fi    fi

elseelse

    echo "❌ Electron binary not found"    echo "❌ Electron binary not found"

fifi



if [[ -f "$PLUGIN_HELPER_PATH" ]]; thenif [[ -f "$PLUGIN_HELPER_PATH" ]]; then

    echo ""    echo ""

    echo "Plugin Helper binary:"    echo "Plugin Helper binary:"

    lipo -info "$PLUGIN_HELPER_PATH" | sed 's/^/  /'    lipo -info "$PLUGIN_HELPER_PATH" | sed 's/^/  /'

    if lipo -info "$PLUGIN_HELPER_PATH" | grep -q "arm64"; then    if lipo -info "$PLUGIN_HELPER_PATH" | grep -q "arm64"; then

        echo "  ✅ Supports Apple Silicon (arm64)"        echo "  ✅ Supports Apple Silicon (arm64)"

    else    else

        echo "  ❌ Does not support Apple Silicon"        echo "  ❌ Does not support Apple Silicon"

    fi    fi

elseelse

    echo "❌ Plugin Helper binary not found"    echo "❌ Plugin Helper binary not found"

fifi



# Check Node.js# Check Node.js

echo ""echo ""

echo "=== Node.js Architecture ==="echo "=== Node.js Architecture ==="

if command -v node >/dev/null 2>&1; thenif command -v node >/dev/null 2>&1; then

    echo "Node.js location: $(which node)"    echo "Node.js location: $(which node)"

    echo "Node.js architecture: $(node -e 'console.log(process.arch)')"    echo "Node.js architecture: $(node -e 'console.log(process.arch)')"

    echo "Node.js binary analysis:"    echo "Node.js binary analysis:"

    file "$(which node)" | sed 's/^/  /'    file "$(which node)" | sed 's/^/  /'

        

    if [[ "$(node -e 'console.log(process.arch)')" == "arm64" ]]; then    if [[ "$(node -e 'console.log(process.arch)')" == "arm64" ]]; then

        echo "  ✅ Node.js is Apple Silicon native"        echo "  ✅ Node.js is Apple Silicon native"

    else    else

        echo "  ❌ Node.js is not Apple Silicon native"        echo "  ❌ Node.js is not Apple Silicon native"

    fi    fi

elseelse

    echo "❌ Node.js not found"    echo "❌ Node.js not found"

fifi



# Check TypeScript installation# Check TypeScript installation

echo ""echo ""

echo "=== TypeScript Installation ==="echo "=== TypeScript Installation ==="

# Check for workspace TypeScript# Check for workspace TypeScript

if [[ -f "node_modules/.bin/tsc" ]]; thenif [[ -f "node_modules/.bin/tsc" ]]; then

    echo "Local TypeScript found: node_modules/.bin/tsc"    echo "Local TypeScript found: node_modules/.bin/tsc"

    echo "  Will use local installation via Node.js ($(node -e 'console.log(process.arch)'))"    echo "  Will use local installation via Node.js ($(node -e 'console.log(process.arch)'))"

elif [[ -f "frontend/node_modules/.bin/tsc" ]]; thenelif [[ -f "frontend/node_modules/.bin/tsc" ]]; then

    echo "Frontend TypeScript found: frontend/node_modules/.bin/tsc"    echo "Frontend TypeScript found: frontend/node_modules/.bin/tsc"

    echo "  Will use frontend local installation via Node.js ($(node -e 'console.log(process.arch)'))"    echo "  Will use frontend local installation via Node.js ($(node -e 'console.log(process.arch)'))"

elseelse

    echo "No local TypeScript installation found"    echo "No local TypeScript installation found"

    echo "  Will use VS Code's bundled TypeScript"    echo "  Will use VS Code's bundled TypeScript"

fifi



# Check VS Code's bundled TypeScript# Check VS Code's bundled TypeScript

TS_BUNDLED_PATH="$VSCODE_PATH/Contents/Resources/app/extensions/node_modules/typescript"TS_BUNDLED_PATH="$VSCODE_PATH/Contents/Resources/app/extensions/node_modules/typescript"

if [[ -d "$TS_BUNDLED_PATH" ]]; thenif [[ -d "$TS_BUNDLED_PATH" ]]; then

    echo ""    echo ""

    echo "VS Code bundled TypeScript: $TS_BUNDLED_PATH"    echo "VS Code bundled TypeScript: $TS_BUNDLED_PATH"

    if [[ -f "$TS_BUNDLED_PATH/lib/tsserver.js" ]]; then    if [[ -f "$TS_BUNDLED_PATH/lib/tsserver.js" ]]; then

        echo "  ✅ TypeScript server found"        echo "  ✅ TypeScript server found"

        echo "  Will run via VS Code's Node.js process (architecture depends on VS Code)"        echo "  Will run via VS Code's Node.js process (architecture depends on VS Code)"

    fi    fi

fifi



# Check Homebrew# Check Homebrew

echo ""echo ""

echo "=== Homebrew Architecture ==="echo "=== Homebrew Architecture ==="

if command -v brew >/dev/null 2>&1; thenif command -v brew >/dev/null 2>&1; then

    BREW_PATH=$(which brew)    BREW_PATH=$(which brew)

    echo "Homebrew location: $BREW_PATH"    echo "Homebrew location: $BREW_PATH"

        

    if [[ "$BREW_PATH" == "/opt/homebrew/bin/brew" ]]; then    if [[ "$BREW_PATH" == "/opt/homebrew/bin/brew" ]]; then

        echo "  ✅ Using Apple Silicon Homebrew (/opt/homebrew)"        echo "  ✅ Using Apple Silicon Homebrew (/opt/homebrew)"

    elif [[ "$BREW_PATH" == "/usr/local/bin/brew" ]]; then    elif [[ "$BREW_PATH" == "/usr/local/bin/brew" ]]; then

        echo "  ⚠️  Using Intel Homebrew (/usr/local) - consider migrating"        echo "  ⚠️  Using Intel Homebrew (/usr/local) - consider migrating"

    else    else

        echo "  ❓ Homebrew at unexpected location"        echo "  ❓ Homebrew at unexpected location"

    fi    fi

elseelse

    echo "❌ Homebrew not found"    echo "❌ Homebrew not found"

fifi



# Check for Rosetta# Check for Rosetta

echo ""echo ""

echo "=== Rosetta Status ==="echo "=== Rosetta Status ==="

if pgrep -x oahd >/dev/null 2>&1; thenif pgrep -x oahd >/dev/null 2>&1; then

    echo "✅ Rosetta is available (for compatibility)"    echo "✅ Rosetta is available (for compatibility)"

    echo "  Background daemon running (normal for Apple Silicon)"    echo "  Background daemon running (normal for Apple Silicon)"

elseelse

    echo "❓ Rosetta daemon not detected"    echo "❓ Rosetta daemon not detected"

fifi



# Check current running processes for architecture# Check current running processes for architecture

echo ""echo ""

echo "=== Current Process Architecture Sample ==="echo "=== Current Process Architecture Sample ==="

echo "Checking some common processes:"echo "Checking some common processes:"



# Check shell# Check shell

if [[ -n "$SHELL" ]]; thenif [[ -n "$SHELL" ]]; then

    echo "Shell ($SHELL): $(file "$SHELL" | grep -o 'arm64\|x86_64' | head -1)"    echo "Shell ($SHELL): $(file "$SHELL" | grep -o 'arm64\|x86_64' | head -1)"

fifi



# Check Terminal# Check Terminal

TERMINAL_PID=$(pgrep -x "Terminal" | head -1)TERMINAL_PID=$(pgrep -x "Terminal" | head -1)

if [[ -n "$TERMINAL_PID" ]]; thenif [[ -n "$TERMINAL_PID" ]]; then

    TERMINAL_FLAGS=$(ps -o flags -p "$TERMINAL_PID" 2>/dev/null | tail -1)    TERMINAL_FLAGS=$(ps -o flags -p "$TERMINAL_PID" 2>/dev/null | tail -1)

    if [[ $((TERMINAL_FLAGS & 0x1000000)) -ne 0 ]]; then    if [[ $((TERMINAL_FLAGS & 0x1000000)) -ne 0 ]]; then

        echo "Terminal: Running under Rosetta (x86_64)"        echo "Terminal: Running under Rosetta (x86_64)"

    else    else

        echo "Terminal: Running natively (arm64)"        echo "Terminal: Running natively (arm64)"

    fi    fi

fifi



# Recommendations# Recommendations

echo ""echo ""

echo "=== Recommendations ==="echo "=== Recommendations ==="



# Check if everything is native# Check if everything is native

all_native=trueall_native=true



if [[ "$(node -e 'console.log(process.arch)' 2>/dev/null)" != "arm64" ]]; thenif [[ "$(node -e 'console.log(process.arch)' 2>/dev/null)" != "arm64" ]]; then

    echo "⚠️  Install Apple Silicon native Node.js:"    echo "⚠️  Install Apple Silicon native Node.js:"

    echo "   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"    echo "   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"

    echo "   nvm install node --lts"    echo "   nvm install node --lts"

    all_native=false    all_native=false

fifi



if [[ "$(which brew)" == "/usr/local/bin/brew" ]]; thenif [[ "$(which brew)" == "/usr/local/bin/brew" ]]; then

    echo "⚠️  Migrate to Apple Silicon Homebrew:"    echo "⚠️  Migrate to Apple Silicon Homebrew:"

    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""

    all_native=false    all_native=false

fifi



if lipo -info "$ELECTRON_PATH" 2>/dev/null | grep -q "x86_64" && ! lipo -info "$ELECTRON_PATH" 2>/dev/null | grep -q "arm64"; thenif lipo -info "$ELECTRON_PATH" 2>/dev/null | grep -q "x86_64" && ! lipo -info "$ELECTRON_PATH" 2>/dev/null | grep -q "arm64"; then

    echo "⚠️  Update VS Code to a version with Apple Silicon support"    echo "⚠️  Update VS Code to a version with Apple Silicon support"

    all_native=false    all_native=false

fifi



if $all_native; thenif $all_native; then

    echo "✅ All core components are Apple Silicon native!"    echo "✅ All core components are Apple Silicon native!"

    echo "✅ VS Code should run natively without Rosetta translation"    echo "✅ VS Code should run natively without Rosetta translation"

    echo "✅ TypeScript server will run at native ARM64 performance"    echo "✅ TypeScript server will run at native ARM64 performance"

elseelse

    echo ""    echo ""

    echo "Once the above recommendations are addressed:"    echo "Once the above recommendations are addressed:"

    echo "1. Restart Terminal"    echo "1. Restart Terminal"

    echo "2. Restart VS Code"    echo "2. Restart VS Code"

    echo "3. Run this script again to verify"    echo "3. Run this script again to verify"

fifi



echo ""echo ""

echo "=== Manual Verification Steps ==="echo "=== Manual Verification Steps ==="

echo "After starting VS Code:"echo "After starting VS Code:"

echo "1. Open Command Palette (Cmd+Shift+P)"echo "1. Open Command Palette (Cmd+Shift+P)"

echo "2. Run 'Developer: Open Process Explorer'"echo "2. Run 'Developer: Open Process Explorer'"

echo "3. Check that main VS Code process shows high CPU/memory (indicates it's the native process)"echo "3. Check that main VS Code process shows high CPU/memory (indicates it's the native process)"

echo "4. Run 'Developer: Reload Window' to restart TypeScript server"echo "4. Run 'Developer: Reload Window' to restart TypeScript server"

echo "5. Check TypeScript server memory usage in Process Explorer"echo "5. Check TypeScript server memory usage in Process Explorer"

echo ""echo ""

echo "Or run: ./scripts/vscode-architecture-verification.sh (with VS Code running)"echo "Or run: ./scripts/vscode-architecture-verification.sh (with VS Code running)"



echo ""echo ""

echo "Analysis completed: $(date)"echo "Analysis completed: $(date)"

