#!/bin/bash

# VS Code Architecture Verification Script
# Verifies that VS Code and all its components are running natively on Apple Silicon

echo "=== VS Code Architecture Verification ==="
echo "Date: $(date)"
echo "System: $(uname -m)"
echo ""

# Check if VS Code is running
if ! pgrep -x "Electron" > /dev/null; then
    echo "❌ VS Code is not running. Please start VS Code and try again."
    exit 1
fi

echo "✅ VS Code is running"
echo ""

# Function to check process architecture
check_process_arch() {
    local pid=$1
    local name=$2
    
    if [ -z "$pid" ]; then
        echo "❓ $name - PID not found"
        return
    fi
    
    # Use ps to get process info and check if it's translated (Rosetta)
    local proc_info=$(ps -o pid,ppid,comm,flags -p $pid 2>/dev/null | tail -1)
    local flags=$(echo $proc_info | awk '{print $4}')
    
    # Flag 0x1000000 indicates process is running under Rosetta
    if [[ $((flags & 0x1000000)) -ne 0 ]]; then
        echo "❌ $name (PID: $pid) - Running under Rosetta (x86_64)"
    else
        echo "✅ $name (PID: $pid) - Running natively (arm64)"
    fi
}

# Get VS Code main process
VSCODE_PID=$(pgrep -f "Visual Studio Code.app/Contents/MacOS/Electron" | head -1)
check_process_arch "$VSCODE_PID" "VS Code Main Process"

# Get TypeScript server processes
echo ""
echo "=== TypeScript Server Processes ==="
TS_PIDS=$(pgrep -f "tsserver.js")
if [ -z "$TS_PIDS" ]; then
    echo "❓ No TypeScript server processes found"
else
    echo "$TS_PIDS" | while read pid; do
        local ts_cmd=$(ps -o args -p $pid 2>/dev/null | tail -1)
        local ts_mode=""
        if echo "$ts_cmd" | grep -q "partialSemantic"; then
            ts_mode=" (Semantic Mode)"
        elif echo "$ts_cmd" | grep -q "enableTelemetry"; then
            ts_mode=" (Syntactic Mode)"
        fi
        check_process_arch "$pid" "TypeScript Server$ts_mode"
    done
fi

# Get Node.js processes (language servers)
echo ""
echo "=== Language Server Processes ==="
NODE_PIDS=$(pgrep -f "Code Helper (Plugin)")
if [ -z "$NODE_PIDS" ]; then
    echo "❓ No language server processes found"
else
    echo "$NODE_PIDS" | head -5 | while read pid; do
        check_process_arch "$pid" "Language Server"
    done
fi

# Check binary architectures
echo ""
echo "=== Binary Architecture Support ==="
echo "VS Code Electron: $(lipo -archs /Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron 2>/dev/null || echo 'Not found')"
echo "VS Code Plugin Helper: $(lipo -archs /Applications/Visual\ Studio\ Code.app/Contents/Frameworks/Code\ Helper\ \(Plugin\).app/Contents/MacOS/Code\ Helper\ \(Plugin\) 2>/dev/null || echo 'Not found')"
echo "Node.js: $(file $(which node) | grep -o 'arm64\|x86_64' | head -1)"

# Check system tools
echo ""
echo "=== System Tools Architecture ==="
echo "Node.js process arch: $(node -e 'console.log(process.arch)')"
echo "Homebrew location: $(which brew | grep -o '/opt/homebrew\|/usr/local')"
echo "Shell: $SHELL ($(file $SHELL | grep -o 'arm64\|x86_64' | head -1))"

# Memory and performance info
echo ""
echo "=== Performance Metrics ==="
echo "VS Code Memory Usage:"
ps -o pid,rss,comm -p $VSCODE_PID 2>/dev/null | tail -1 | awk '{printf "  Main Process: %d MB\n", $2/1024}'

total_mem=0
if [ ! -z "$TS_PIDS" ]; then
    echo "TypeScript Server Memory:"
    echo "$TS_PIDS" | while read pid; do
        local mem=$(ps -o rss -p $pid 2>/dev/null | tail -1)
        if [ ! -z "$mem" ] && [ "$mem" != "RSS" ]; then
            echo "  PID $pid: $((mem/1024)) MB"
            total_mem=$((total_mem + mem/1024))
        fi
    done
fi

# Check if any processes are using excessive CPU
echo ""
echo "=== High CPU Processes (>10%) ==="
ps -eo pid,pcpu,comm | awk '$2 > 10 {print $0}' | head -10

echo ""
echo "=== Recommendations ==="

# Check for Rosetta processes
rosetta_count=$(ps -Ao pid,ppid,comm,flags | awk '$4 && ($4 % 33554432) >= 16777216 {count++} END {print count+0}')
if [ $rosetta_count -gt 0 ]; then
    echo "⚠️  $rosetta_count processes running under Rosetta"
    echo "   Consider reinstalling applications that aren't Apple Silicon native"
else
    echo "✅ No processes detected running under Rosetta"
fi

# Check TypeScript memory
if [ ! -z "$TS_PIDS" ]; then
    total_ts_mem=$(echo "$TS_PIDS" | xargs ps -o rss -p 2>/dev/null | awk 'NR>1 {sum+=$1} END {print sum/1024}')
    if [ ! -z "$total_ts_mem" ] && [ "$total_ts_mem" -gt 2000 ]; then
        echo "✅ TypeScript server has sufficient memory allocation (${total_ts_mem}MB)"
    else
        echo "⚠️  TypeScript server may need more memory allocation"
    fi
fi

echo ""
echo "Script completed: $(date)"
