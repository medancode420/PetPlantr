#!/bin/bash
# PetPlantr Startup Script
# This script provides clean startup with proper environment setup

set -e  # Exit on any error

echo "🐾 Starting PetPlantr..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Set environment variables for clean startup
export ENABLE_SYNTHETIC_MONITOR=true
export SYNTHETIC_MONITOR_PERIOD_MS=5000
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the API server
echo "🚀 Starting API server..."
python api_server.py
