#!/bin/bash

# PetPlantr Evidence Report Generator
# Utilities for generating HTML evidence reports from CI/CD and deployment logs

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
RUN_LOG=""
REPORT_FILE=""
START_TIME=""
EVIDENCE_DIR="evidence"

# Initialize evidence collection
init_evidence() {
    START_TIME=$(date +%s)
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    # Create evidence directory
    mkdir -p "$EVIDENCE_DIR"
    
    # Create unique log file
    RUN_LOG="$EVIDENCE_DIR/run_log_${timestamp}.log"
    
    # Set default report file if not specified
    if [[ -z "${REPORT_FILE:-}" ]]; then
        REPORT_FILE="$EVIDENCE_DIR/evidence_report_${timestamp}.html"
    fi
    
    # Initialize log with header
    cat > "$RUN_LOG" << EOF
========================================
PetPlantr Evidence Collection Started
========================================
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
User: $(whoami)
Host: $(hostname)
Working Directory: $(pwd)
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")
Git Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "N/A")
========================================

EOF
}

# Enhanced logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local duration=""
    
    if [[ -n "$START_TIME" ]]; then
        local current_time=$(date +%s)
        local elapsed=$((current_time - START_TIME))
        duration=" [+${elapsed}s]"
    fi
    
    # Format log entry
    local log_entry="$timestamp$duration | [$level] $message"
    
    # Write to log file
    echo "$log_entry" | tee -a "$RUN_LOG"
    
    # Also output to console with colors
    case "$level" in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message" >&2
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message" >&2
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message" >&2
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message" >&2
            ;;
        *)
            echo "$message" >&2
            ;;
    esac
}

# Convenience functions for different log levels
log_info() { log "INFO" "$@"; }
log_success() { log "SUCCESS" "$@"; }
log_warning() { log "WARNING" "$@"; }
log_error() { log "ERROR" "$@"; }

# Capture command execution with evidence
run_with_evidence() {
    local description="$1"
    shift
    local command="$*"
    
    log_info "Starting: $description"
    log_info "Command: $command"
    
    local start_time=$(date +%s)
    local temp_output=$(mktemp)
    local exit_code=0
    
    # Run command and capture output
    if eval "$command" > "$temp_output" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log_success "Completed: $description (${duration}s)"
        
        # Append output to evidence log
        echo "--- Output for: $description ---" >> "$RUN_LOG"
        cat "$temp_output" >> "$RUN_LOG"
        echo "--- End Output ---" >> "$RUN_LOG"
        echo "" >> "$RUN_LOG"
    else
        exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log_error "Failed: $description (${duration}s, exit code: $exit_code)"
        
        # Append error output to evidence log
        echo "--- Error Output for: $description ---" >> "$RUN_LOG"
        cat "$temp_output" >> "$RUN_LOG"
        echo "--- End Error Output ---" >> "$RUN_LOG"
        echo "" >> "$RUN_LOG"
    fi
    
    rm -f "$temp_output"
    return $exit_code
}

# Capture file content as evidence
capture_file() {
    local file_path="$1"
    local description="${2:-$file_path}"
    
    if [[ -f "$file_path" ]]; then
        log_info "Capturing file: $description"
        
        echo "--- File Content: $description ($file_path) ---" >> "$RUN_LOG"
        echo "File size: $(wc -c < "$file_path") bytes" >> "$RUN_LOG"
        echo "Last modified: $(date -r "$file_path")" >> "$RUN_LOG"
        echo "" >> "$RUN_LOG"
        cat "$file_path" >> "$RUN_LOG"
        echo "--- End File Content ---" >> "$RUN_LOG"
        echo "" >> "$RUN_LOG"
    else
        log_warning "File not found: $file_path"
        echo "--- File Not Found: $description ($file_path) ---" >> "$RUN_LOG"
        echo "" >> "$RUN_LOG"
    fi
}

# Capture environment variables
capture_env() {
    local prefix="${1:-}"
    local description="Environment Variables"
    
    if [[ -n "$prefix" ]]; then
        description="Environment Variables (${prefix}*)"
    fi
    
    log_info "Capturing: $description"
    
    echo "--- $description ---" >> "$RUN_LOG"
    if [[ -n "$prefix" ]]; then
        env | grep "^${prefix}" | sort >> "$RUN_LOG"
    else
        env | sort >> "$RUN_LOG"
    fi
    echo "--- End Environment Variables ---" >> "$RUN_LOG"
    echo "" >> "$RUN_LOG"
}

# Capture system information
capture_system_info() {
    log_info "Capturing system information"
    
    echo "--- System Information ---" >> "$RUN_LOG"
    echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$RUN_LOG"
    echo "Hostname: $(hostname)" >> "$RUN_LOG"
    echo "User: $(whoami)" >> "$RUN_LOG"
    echo "Shell: $SHELL" >> "$RUN_LOG"
    echo "PWD: $(pwd)" >> "$RUN_LOG"
    echo "OS: $(uname -a)" >> "$RUN_LOG"
    
    if command -v docker >/dev/null 2>&1; then
        echo "Docker: $(docker --version)" >> "$RUN_LOG"
    fi
    
    if command -v kubectl >/dev/null 2>&1; then
        echo "kubectl: $(kubectl version --client --short 2>/dev/null || echo 'N/A')" >> "$RUN_LOG"
    fi
    
    if command -v python3 >/dev/null 2>&1; then
        echo "Python: $(python3 --version)" >> "$RUN_LOG"
    fi
    
    echo "--- End System Information ---" >> "$RUN_LOG"
    echo "" >> "$RUN_LOG"
}

# Escape HTML entities
escape_html() {
    sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&#39;/g'
}

# Generate comprehensive HTML evidence report
generate_report() {
    local outfile="${1:-$REPORT_FILE}"
    local end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    
    log_info "Generating evidence report: $outfile"
    
    # Ensure output directory exists
    mkdir -p "$(dirname "$outfile")"
    
    # Start HTML document
    cat > "$outfile" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PetPlantr Evidence Report - $(date +%Y-%m-%d)</title>
    <style>
        body {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            line-height: 1.4;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .summary {
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid #28a745;
        }
        .summary h2 {
            margin-top: 0;
            color: #28a745;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .summary-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #007bff;
        }
        .summary-item strong {
            color: #495057;
            display: block;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .summary-item .value {
            font-size: 1.2em;
            color: #007bff;
            font-weight: bold;
        }
        .log-container {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .log-header {
            background: #343a40;
            color: white;
            padding: 15px 25px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .log-content {
            padding: 0;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            background: #fafafa;
        }
        .log-line {
            padding: 8px 25px;
            border-bottom: 1px solid #f1f3f4;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .log-line:hover {
            background-color: #f8f9fa;
        }
        .log-level-INFO { color: #007bff; }
        .log-level-SUCCESS { color: #28a745; font-weight: bold; }
        .log-level-WARNING { color: #ffc107; font-weight: bold; }
        .log-level-ERROR { color: #dc3545; font-weight: bold; }
        .expandable {
            cursor: pointer;
            user-select: none;
        }
        .expandable:before {
            content: "▶ ";
            display: inline-block;
            transition: transform 0.2s;
        }
        .expandable.expanded:before {
            transform: rotate(90deg);
        }
        .collapsible-content {
            display: none;
            background: #f1f3f4;
            margin: 10px 0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #6c757d;
        }
        .footer {
            margin-top: 40px;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 2px solid #e9ecef;
            background: white;
            border-radius: 8px;
        }
        .status-success { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
        .copy-button {
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .copy-button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 PetPlantr Evidence Report</h1>
        <p>Deployment & Testing Evidence Collection</p>
    </div>

    <div class="summary">
        <h2>📊 Execution Summary</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <strong>Report Generated</strong>
                <div class="value">$(date)</div>
            </div>
            <div class="summary-item">
                <strong>Total Duration</strong>
                <div class="value">${total_duration}s</div>
            </div>
            <div class="summary-item">
                <strong>Git Commit</strong>
                <div class="value">$(git rev-parse --short HEAD 2>/dev/null || echo "N/A")</div>
            </div>
            <div class="summary-item">
                <strong>Git Branch</strong>
                <div class="value">$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "N/A")</div>
            </div>
            <div class="summary-item">
                <strong>User</strong>
                <div class="value">$(whoami)</div>
            </div>
            <div class="summary-item">
                <strong>Host</strong>
                <div class="value">$(hostname)</div>
            </div>
        </div>
    </div>

    <div class="log-container">
        <div class="log-header">
            <span>📋 Execution Log</span>
            <button class="copy-button" onclick="copyToClipboard('log-content')">Copy Log</button>
        </div>
        <div class="log-content" id="log-content">
EOF

    # Process log file and add to HTML
    if [[ -f "$RUN_LOG" ]]; then
        local line_number=1
        while IFS= read -r line; do
            local escaped_line=$(echo "$line" | escape_html)
            local css_class=""
            
            # Detect log level and apply appropriate styling
            if [[ "$line" =~ \[INFO\] ]]; then
                css_class="log-level-INFO"
            elif [[ "$line" =~ \[SUCCESS\] ]]; then
                css_class="log-level-SUCCESS"
            elif [[ "$line" =~ \[WARNING\] ]]; then
                css_class="log-level-WARNING"
            elif [[ "$line" =~ \[ERROR\] ]]; then
                css_class="log-level-ERROR"
            fi
            
            # Check if this is a section header (expandable)
            if [[ "$line" =~ ^---.*---$ ]]; then
                echo "            <div class=\"log-line expandable $css_class\" onclick=\"toggleCollapse($line_number)\">$escaped_line</div>" >> "$outfile"
                echo "            <div class=\"collapsible-content\" id=\"collapse-$line_number\">" >> "$outfile"
            elif [[ "$line" =~ ^---\ End.*---$ ]]; then
                echo "            </div>" >> "$outfile"
                echo "            <div class=\"log-line $css_class\">$escaped_line</div>" >> "$outfile"
            else
                echo "            <div class=\"log-line $css_class\">$escaped_line</div>" >> "$outfile"
            fi
            
            ((line_number++))
        done < "$RUN_LOG"
    else
        echo "            <div class=\"log-line log-level-WARNING\">No log file found: $RUN_LOG</div>" >> "$outfile"
    fi

    # Complete HTML document
    cat >> "$outfile" << EOF
        </div>
    </div>

    <div class="footer">
        <p>
            Generated by PetPlantr Evidence Collection System<br>
            <small>
                Report file: <code>$outfile</code><br>
                Log file: <code>$RUN_LOG</code><br>
                For support: <a href="mailto:sre@petplantr.com">sre@petplantr.com</a>
            </small>
        </p>
    </div>

    <script>
        function toggleCollapse(id) {
            const content = document.getElementById('collapse-' + id);
            const trigger = content.previousElementSibling;
            
            if (content.style.display === 'block') {
                content.style.display = 'none';
                trigger.classList.remove('expanded');
            } else {
                content.style.display = 'block';
                trigger.classList.add('expanded');
            }
        }

        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.innerText;
            
            navigator.clipboard.writeText(text).then(function() {
                const button = event.target;
                const originalText = button.innerText;
                button.innerText = 'Copied!';
                button.style.background = '#28a745';
                
                setTimeout(function() {
                    button.innerText = originalText;
                    button.style.background = '#007bff';
                }, 2000);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
            });
        }

        // Auto-expand first few sections for quick viewing
        document.addEventListener('DOMContentLoaded', function() {
            const expandableElements = document.querySelectorAll('.expandable');
            for (let i = 0; i < Math.min(3, expandableElements.length); i++) {
                expandableElements[i].click();
            }
        });
    </script>
</body>
</html>
EOF

    log_success "Evidence report generated: $outfile"
    
    # Output summary statistics
    local log_lines=$(wc -l < "$RUN_LOG" 2>/dev/null || echo "0")
    local success_count=$(grep -c "\[SUCCESS\]" "$RUN_LOG" 2>/dev/null || echo "0")
    local error_count=$(grep -c "\[ERROR\]" "$RUN_LOG" 2>/dev/null || echo "0")
    local warning_count=$(grep -c "\[WARNING\]" "$RUN_LOG" 2>/dev/null || echo "0")
    
    echo ""
    echo "📈 Evidence Collection Summary:"
    echo "   Total log lines: $log_lines"
    echo "   Success events: $success_count"
    echo "   Warning events: $warning_count" 
    echo "   Error events: $error_count"
    echo "   Total duration: ${total_duration}s"
    echo "   Report file: $outfile"
    echo ""
    
    return 0
}

# Set up trap to generate report on exit
setup_trap() {
    trap 'generate_report "$REPORT_FILE"' EXIT
}

# Main function for direct script usage
main() {
    local output_file="${1:-}"
    
    if [[ -n "$output_file" ]]; then
        REPORT_FILE="$output_file"
    fi
    
    init_evidence
    capture_system_info
    
    log_info "Evidence collection initialized"
    log_info "Log file: $RUN_LOG"
    log_info "Report will be generated at: $REPORT_FILE"
    
    # If script is run directly, set up auto-report generation
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        setup_trap
        log_info "Trap set up - report will be generated on script exit"
    fi
}

# Initialize if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
