#!/bin/bash
# Setup script for continuous log monitoring

echo "🤖 Setting up Continuous Log Monitoring"
echo "======================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env with:"
    echo "BOT_SERVER=your-server-ip"
    echo "BOT_SERVER_USER=your-username"
    echo "BOT_SERVER_PASSWORD=your-password  # optional if using SSH keys"
    exit 1
fi

# Check if python-dotenv is available
python3 -c "import dotenv" 2>/dev/null || {
    echo "📦 Installing python-dotenv..."
    pip3 install python-dotenv
}

# Check if sshpass is available (needed for password auth on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v sshpass &> /dev/null; then
        echo "⚠️  sshpass not found. Installing..."
        if command -v brew &> /dev/null; then
            brew install hudochenkov/sshpass/sshpass
        else
            echo "❌ Please install Homebrew first, then run: brew install hudochenkov/sshpass/sshpass"
            echo "Or install without password: Use SSH keys instead"
        fi
    fi
fi

# Test connection
echo "🧪 Testing server connection..."
python3 log_monitor.py --mode fetch --lines 5

if [ $? -eq 0 ]; then
    echo "✅ Connection successful!"
    echo ""
    echo "🚀 Starting continuous log monitoring in background..."
    nohup python3 log_monitor.py --mode stream --background > log_monitor_output.log 2>&1 &
    
    echo "✅ Log monitor started!"
    echo ""
    echo "📋 Useful commands:"
    echo "  python3 log_monitor.py --mode status    # Check if running"
    echo "  python3 log_monitor.py --mode stop      # Stop monitoring"  
    echo "  python3 log_monitor.py --mode fetch     # Fetch recent logs"
    echo ""
    echo "🔍 Log files:"
    echo "  server_logs.jsonl           # Collected logs (for AI analysis)"
    echo "  log_monitor_status.json     # Current status"
    echo "  log_monitor.log             # Monitor activity log"
    
else
    echo "❌ Connection failed. Please check your .env credentials."
fi