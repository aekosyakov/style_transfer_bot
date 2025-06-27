#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Webhook Deployment Server Setup${NC}"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (sudo)${NC}"
    exit 1
fi

BOT_DIR="/root/upscale_bot"
SERVICE_FILE="/etc/systemd/system/webhook-deploy.service"

# Check if bot directory exists
if [ ! -d "$BOT_DIR" ]; then
    echo -e "${RED}❌ Bot directory $BOT_DIR not found${NC}"
    exit 1
fi

cd "$BOT_DIR"

# Install Flask if not already installed
echo -e "${YELLOW}📦 Installing Flask...${NC}"
./venv/bin/pip install flask

# Copy service file
echo -e "${YELLOW}📋 Installing systemd service...${NC}"
cp webhook-deploy.service "$SERVICE_FILE"

# Generate a random webhook secret if not provided
WEBHOOK_SECRET=${WEBHOOK_SECRET:-$(openssl rand -hex 32)}

# Update service file with actual paths and secret
sed -i "s|your-secret-key-here|$WEBHOOK_SECRET|g" "$SERVICE_FILE"
sed -i "s|/root/upscale_bot|$BOT_DIR|g" "$SERVICE_FILE"

# Reload systemd and enable service
echo -e "${YELLOW}⚙️  Configuring systemd service...${NC}"
systemctl daemon-reload
systemctl enable webhook-deploy.service

# Start the service
echo -e "${YELLOW}🚀 Starting webhook deployment server...${NC}"
systemctl start webhook-deploy.service

# Check status
sleep 2
if systemctl is-active --quiet webhook-deploy.service; then
    echo -e "${GREEN}✅ Webhook deployment server started successfully${NC}"
    
    # Show service status
    echo -e "${BLUE}📊 Service Status:${NC}"
    systemctl status webhook-deploy.service --no-pager -l
    
    echo ""
    echo -e "${GREEN}🎉 Setup Complete!${NC}"
    echo -e "${BLUE}📋 Configuration:${NC}"
    echo -e "${BLUE}   • Webhook URL: http://$(hostname -I | awk '{print $1}'):9000${NC}"
    echo -e "${BLUE}   • Deploy endpoint: http://$(hostname -I | awk '{print $1}'):9000/deploy${NC}"
    echo -e "${BLUE}   • Status endpoint: http://$(hostname -I | awk '{print $1}'):9000/status${NC}"
    echo -e "${BLUE}   • Webhook secret: $WEBHOOK_SECRET${NC}"
    echo ""
    echo -e "${YELLOW}💡 To use from your local machine:${NC}"
    echo -e "${BLUE}   export WEBHOOK_URL=http://$(hostname -I | awk '{print $1}'):9000${NC}"
    echo -e "${BLUE}   ./deploy.sh \"Your commit message\"${NC}"
    echo ""
    echo -e "${YELLOW}📝 Service management:${NC}"
    echo -e "${BLUE}   • Check logs: journalctl -u webhook-deploy.service -f${NC}"
    echo -e "${BLUE}   • Restart: systemctl restart webhook-deploy.service${NC}"
    echo -e "${BLUE}   • Stop: systemctl stop webhook-deploy.service${NC}"
    
else
    echo -e "${RED}❌ Failed to start webhook deployment server${NC}"
    echo -e "${YELLOW}📝 Check logs: journalctl -u webhook-deploy.service -f${NC}"
    exit 1
fi 