#!/bin/bash
# Comprehensive Deployment and Log Monitoring Script
# Deploys changes and provides real-time log monitoring

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the project root directory (parent of automation)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Comprehensive Deployment + Log Monitoring"
echo "============================================="

# Check if commit message provided
if [ $# -eq 0 ]; then
    echo "❌ Usage: $0 \"commit message\""
    echo "Example: $0 \"Add new feature\""
    exit 1
fi

COMMIT_MESSAGE="$1"

echo "📝 Commit message: $COMMIT_MESSAGE"
echo ""

# Step 1: Run deployment
echo "📦 Step 1: Running deployment..."
cd "$PROJECT_ROOT"
bash ./automation/deploy.sh "$COMMIT_MESSAGE"

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed!"
    exit 1
fi

echo "✅ Deployment completed successfully!"
echo ""

# Step 2: Ensure log monitor is running
echo "📡 Step 2: Checking log monitor status..."
if python3 automation/log_monitor.py --mode status | grep -q "✅ Log monitor is running"; then
    echo "✅ Log monitor is already running"
else
    echo "🔄 Starting log monitor..."
    nohup python3 automation/log_monitor.py --mode stream --background > logs/log_monitor_output.log 2>&1 &
    sleep 3
    if python3 automation/log_monitor.py --mode status | grep -q "✅ Log monitor is running"; then
        echo "✅ Log monitor started successfully"
    else
        echo "⚠️  Log monitor may not have started properly"
    fi
fi

echo ""

# Step 3: Wait for deployment to propagate
echo "⏳ Step 3: Waiting for deployment to propagate (10 seconds)..."
sleep 10

# Step 4: Check for deployment activity in logs
echo "🔍 Step 4: Checking for deployment activity..."
RESTART_FOUND=$(tail -20 logs/server_logs.jsonl 2>/dev/null | jq -r '.message' 2>/dev/null | grep -c "Started upscale-bot.service" || echo "0")

if [ "$RESTART_FOUND" -gt 0 ]; then
    echo "✅ Service restart detected in logs"
    
    # Show recent restart activity
    echo ""
    echo "📋 Recent deployment activity:"
    tail -20 logs/server_logs.jsonl 2>/dev/null | jq -r '.message' 2>/dev/null | grep -E "(Stopped|Started|python.*INFO.*root)" | tail -3 || echo "No restart messages found in recent logs"
else
    echo "⚠️  No service restart detected yet (may take a few more seconds)"
fi

echo ""

# Step 5: Analyze current log status
echo "📊 Step 5: Analyzing current log status..."
python3 automation/log_analyzer.py

echo ""

# Step 6: Show useful commands
echo "💡 Useful monitoring commands:"
echo "  python3 automation/log_monitor.py --mode status     # Check monitor status"
echo "  python3 automation/log_monitor.py --mode stop       # Stop monitoring"
echo "  python3 automation/log_analyzer.py                  # Analyze logs"
echo "  tail -f logs/server_logs.jsonl | jq -r '.message'   # Watch live logs"
echo ""

# Step 7: Automatic real-time monitoring
echo "🔄 Starting live log monitoring automatically (Ctrl+C to stop)"
sleep 2

echo ""
echo "📺 Live log monitoring (Ctrl+C to stop):"
echo "----------------------------------------"

# Watch for errors and important events
tail -f logs/server_logs.jsonl 2>/dev/null | while read line; do
    if [ -n "$line" ]; then
        # Parse JSON and extract important info
        TIMESTAMP=$(echo "$line" | jq -r '.timestamp' 2>/dev/null || echo "Unknown")
        LEVEL=$(echo "$line" | jq -r '.level' 2>/dev/null || echo "INFO")
        MESSAGE=$(echo "$line" | jq -r '.message' 2>/dev/null || echo "$line")
        
        # Color code by level
        case "$LEVEL" in
            "ERROR")
                echo "🔴 [$TIMESTAMP] ERROR: $MESSAGE"
                ;;
            "WARNING")
                echo "🟡 [$TIMESTAMP] WARNING: $MESSAGE"
                ;;
            "INFO")
                # Only show interesting INFO messages
                if echo "$MESSAGE" | grep -qE "(ERROR|Failed|Exception|Started|Stopped|Update.*handled)"; then
                    echo "🔵 [$TIMESTAMP] INFO: $MESSAGE"
                fi
                ;;
            *)
                echo "⚪ [$TIMESTAMP] $LEVEL: $MESSAGE"
                ;;
        esac
    fi
done 