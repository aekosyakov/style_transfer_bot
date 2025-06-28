#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 Style Transfer Bot Server Setup${NC}"
echo "======================================="

# Get current directory (should be style_transfer_bot)
BOT_DIR="$(pwd)"
BOT_NAME="style-transfer-bot"

echo -e "${BLUE}📁 Bot directory: ${BOT_DIR}${NC}"
echo -e "${BLUE}🤖 Service name: ${BOT_NAME}${NC}"

# Check if we're in the right directory
if [[ ! -f "run_bot.py" ]] || [[ ! -d "src" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the style_transfer_bot directory${NC}"
    echo -e "${YELLOW}Current directory should contain run_bot.py and src/ folder${NC}"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Step 1: Setting up Python virtual environment...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}📚 Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Dependencies installed successfully${NC}"

echo -e "${YELLOW}🔍 Step 2: Setting up environment configuration...${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating .env file from example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual API tokens:${NC}"
    echo -e "${BLUE}   • STYLE_TRANSFER_BOT_TOKEN=your_bot_token${NC}"
    echo -e "${BLUE}   • REPLICATE_API_TOKEN=your_replicate_token${NC}"
    echo -e "${BLUE}   • PROVIDER_TOKEN=your_stripe_provider_token${NC}"
    echo -e "${BLUE}   • REDIS_URL=redis://localhost:6379/0${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

echo -e "${YELLOW}🔍 Step 3: Setting up Redis server...${NC}"

# Install and start Redis
if ! command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Redis...${NC}"
    apt update
    apt install -y redis-server
fi

# Start and enable Redis
systemctl start redis-server
systemctl enable redis-server

if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✅ Redis server is running${NC}"
else
    echo -e "${RED}❌ Failed to start Redis server${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Step 4: Creating systemd service for the bot...${NC}"

# Create systemd service file for the bot
SERVICE_FILE="/etc/systemd/system/${BOT_NAME}.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Style Transfer Telegram Bot
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=${BOT_DIR}
Environment=PATH=${BOT_DIR}/venv/bin
ExecStart=${BOT_DIR}/venv/bin/python ${BOT_DIR}/run_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/${BOT_NAME}.log
StandardError=append:/var/log/${BOT_NAME}.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Bot service file created: ${SERVICE_FILE}${NC}"

echo -e "${YELLOW}🔍 Step 5: Setting up webhook deployment system...${NC}"

# Update webhook_deploy.py with correct paths
echo -e "${YELLOW}📝 Updating webhook deployment configuration...${NC}"

# Update the webhook deploy script to use correct paths
sed -i "s|BOT_DIR = '/root/upscale_bot'|BOT_DIR = '${BOT_DIR}'|g" integrations/webhook_deploy.py
sed -i "s|SERVICE_NAME = 'upscale-bot.service'|SERVICE_NAME = '${BOT_NAME}.service'|g" integrations/webhook_deploy.py

# Copy webhook deployment script to root directory
cp integrations/webhook_deploy.py webhook_deploy.py
chmod +x webhook_deploy.py

# Generate webhook secret
WEBHOOK_SECRET=$(openssl rand -hex 32)

# Create webhook systemd service
WEBHOOK_SERVICE_FILE="/etc/systemd/system/webhook-deploy.service"
cat > "$WEBHOOK_SERVICE_FILE" << EOF
[Unit]
Description=Style Transfer Bot Deployment Webhook Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${BOT_DIR}
Environment=WEBHOOK_SECRET=${WEBHOOK_SECRET}
Environment=WEBHOOK_PORT=9000
ExecStart=${BOT_DIR}/venv/bin/python ${BOT_DIR}/webhook_deploy.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/webhook-deploy.log
StandardError=append:/var/log/webhook-deploy.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Webhook service file created: ${WEBHOOK_SERVICE_FILE}${NC}"

echo -e "${YELLOW}🔍 Step 6: Installing Flask for webhook server...${NC}"
source venv/bin/activate
pip install flask

echo -e "${YELLOW}🔍 Step 7: Starting services...${NC}"

# Reload systemd daemon
systemctl daemon-reload

# Enable and start services
systemctl enable ${BOT_NAME}.service
systemctl enable webhook-deploy.service

# Start webhook service first
systemctl start webhook-deploy.service
sleep 2

if systemctl is-active --quiet webhook-deploy.service; then
    echo -e "${GREEN}✅ Webhook deployment server started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start webhook deployment server${NC}"
    echo -e "${YELLOW}Check logs: journalctl -u webhook-deploy.service -f${NC}"
fi

# Start bot service
systemctl start ${BOT_NAME}.service
sleep 3

if systemctl is-active --quiet ${BOT_NAME}.service; then
    echo -e "${GREEN}✅ Style Transfer Bot started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start Style Transfer Bot${NC}"
    echo -e "${YELLOW}Check logs: journalctl -u ${BOT_NAME}.service -f${NC}"
    echo -e "${YELLOW}Make sure you've configured the .env file with valid API tokens${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo -e "${CYAN}=========================================${NC}"
echo ""

# Show service status
echo -e "${BLUE}📊 Service Status:${NC}"
echo -e "${YELLOW}Bot Service:${NC}"
systemctl status ${BOT_NAME}.service --no-pager -l | head -10

echo ""
echo -e "${YELLOW}Webhook Service:${NC}"
systemctl status webhook-deploy.service --no-pager -l | head -10

echo ""
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo -e "${BLUE}   • Bot directory: ${BOT_DIR}${NC}"
echo -e "${BLUE}   • Bot service: ${BOT_NAME}.service${NC}"
echo -e "${BLUE}   • Webhook URL: http://$(hostname -I | awk '{print $1}'):9000${NC}"
echo -e "${BLUE}   • Deploy endpoint: http://$(hostname -I | awk '{print $1}'):9000/deploy${NC}"
echo -e "${BLUE}   • Status endpoint: http://$(hostname -I | awk '{print $1}'):9000/status${NC}"
echo -e "${BLUE}   • Webhook secret: ${WEBHOOK_SECRET}${NC}"

echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "${BLUE}1. Edit .env file with your API tokens:${NC}"
echo -e "${BLUE}   nano .env${NC}"
echo ""
echo -e "${BLUE}2. Restart bot after configuring tokens:${NC}"
echo -e "${BLUE}   systemctl restart ${BOT_NAME}.service${NC}"
echo ""
echo -e "${BLUE}3. Set up local deployment (on your development machine):${NC}"
echo -e "${BLUE}   export WEBHOOK_URL=http://$(hostname -I | awk '{print $1}'):9000${NC}"
echo ""
echo -e "${YELLOW}📝 Useful Commands:${NC}"
echo -e "${BLUE}   • Check bot logs: journalctl -u ${BOT_NAME}.service -f${NC}"
echo -e "${BLUE}   • Check webhook logs: journalctl -u webhook-deploy.service -f${NC}"
echo -e "${BLUE}   • Restart bot: systemctl restart ${BOT_NAME}.service${NC}"
echo -e "${BLUE}   • Restart webhook: systemctl restart webhook-deploy.service${NC}"
echo -e "${BLUE}   • Test webhook: curl http://localhost:9000/health${NC}"

echo ""
echo -e "${GREEN}🚀 Your Style Transfer Bot is ready to go!${NC}" 