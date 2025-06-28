#!/bin/bash

echo "🔍 Style Transfer Bot Debug Script"
echo "=================================="

BOT_DIR="/root/style_transfer_bot"
SERVICE_NAME="style-transfer-bot.service"

# Check if we're in the right directory
if [ ! -f "run_bot.py" ]; then
    echo "❌ Error: run_bot.py not found. Make sure you're in the bot directory."
    exit 1
fi

echo ""
echo "1. 📁 Checking file structure..."
ls -la run_bot.py src/

echo ""
echo "2. 🐍 Testing Python import manually..."
source venv/bin/activate
python3 -c "
try:
    print('Testing imports...')
    import sys
    sys.path.append('/root/style_transfer_bot')
    sys.path.append('/root/style_transfer_bot/src')
    
    print('✅ Basic imports OK')
    
    from src.config import config
    print('✅ Config import OK')
    
    from src.bot import StyleTransferBot
    print('✅ Bot import OK')
    
    print('✅ All imports successful!')
    
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "3. 📋 Checking .env file..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    echo "Environment variables (values hidden):"
    grep -E "^[A-Z_]+" .env | sed 's/=.*/=***hidden***/'
else
    echo "❌ .env file missing!"
    echo "Please create .env file with:"
    echo "STYLE_TRANSFER_BOT_TOKEN=your_token"
    echo "REPLICATE_API_TOKEN=your_token"
    echo "PROVIDER_TOKEN=your_token"
    echo "REDIS_URL=redis://localhost:6379/0"
fi

echo ""
echo "4. 🔧 Testing Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is running and accessible"
    else
        echo "❌ Redis connection failed"
        echo "Try: sudo systemctl start redis-server"
    fi
else
    echo "❌ redis-cli not found"
fi

echo ""
echo "5. 📦 Checking Python dependencies..."
source venv/bin/activate
python3 -c "
import pkg_resources
required = []
with open('requirements.txt', 'r') as f:
    required = f.read().splitlines()

installed = [pkg.key for pkg in pkg_resources.working_set]
missing = []

for req in required:
    pkg_name = req.split('==')[0].split('>=')[0].split('<=')[0].lower()
    if pkg_name and pkg_name not in installed:
        missing.append(req)

if missing:
    print(f'❌ Missing packages: {missing}')
    print('Run: pip install -r requirements.txt')
else:
    print('✅ All requirements installed')
"

echo ""
echo "6. 🚀 Testing manual bot startup..."
echo "Running bot manually to see detailed error:"
echo "----------------------------------------"
source venv/bin/activate
python3 run_bot.py --debug

echo ""
echo "If the manual run failed, fix the errors above and then:"
echo "sudo systemctl restart style-transfer-bot.service" 