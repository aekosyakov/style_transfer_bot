#!/bin/bash

echo "Add these UPDATED aliases to your ~/.bashrc file:"
echo ""

cat << 'EOF'
# Style Transfer Bot Management Aliases (Updated)

# Check actual bot application logs (where errors will be)
alias bot-logs='sudo tail -f /var/log/style-transfer-bot.log'

# Show recent bot application logs
alias bot-recent='sudo tail -50 /var/log/style-transfer-bot.log'

# Show only errors from application logs
alias bot-errors='sudo grep -i error /var/log/style-transfer-bot.log | tail -20'

# Restart bot and show application logs
alias restart-bot='sudo systemctl restart style-transfer-bot.service && echo "🔄 Service restarted, showing application logs..." && sleep 2 && sudo tail -f /var/log/style-transfer-bot.log'

# Show systemd service status
alias bot-status='sudo systemctl status style-transfer-bot.service --no-pager'

# Show systemd logs (startup/shutdown only)
alias bot-systemd='sudo journalctl -u style-transfer-bot.service -f'

# Combined view: both systemd status and recent app logs
alias bot-check='echo "🤖 Service Status:" && sudo systemctl status style-transfer-bot.service --no-pager -l | head -8 && echo "" && echo "📋 Recent Application Logs:" && sudo tail -10 /var/log/style-transfer-bot.log'

# Webhook logs
alias webhook-logs='sudo tail -f /var/log/webhook-deploy.log'
alias webhook-status='sudo systemctl status webhook-deploy.service --no-pager'

# Clear old logs (if they get too big)
alias bot-clear-logs='sudo truncate -s 0 /var/log/style-transfer-bot.log && echo "Logs cleared"'
EOF

echo ""
echo "🔧 Now run on your server:"
echo "1. Check actual bot logs: sudo tail -f /var/log/style-transfer-bot.log"
echo "2. Try sending an image to the bot while watching logs"
echo "3. Look for error messages in the application logs" 