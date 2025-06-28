#!/bin/bash
# Add these aliases to your ~/.bashrc file

echo "Add these aliases to your ~/.bashrc file:"
echo ""

cat << 'EOF'
# Style Transfer Bot Management Aliases

# Restart bot and show live logs
alias restart-bot='sudo systemctl restart style-transfer-bot.service && echo "🔄 Service restarted, showing logs..." && sudo journalctl -u style-transfer-bot.service -f'

# Just show live logs
alias bot-logs='sudo journalctl -u style-transfer-bot.service -f'

# Show bot status
alias bot-status='sudo systemctl status style-transfer-bot.service --no-pager'

# Restart webhook and show logs
alias restart-webhook='sudo systemctl restart webhook-deploy.service && echo "🔄 Webhook restarted, showing logs..." && sudo journalctl -u webhook-deploy.service -f'

# Show webhook logs
alias webhook-logs='sudo journalctl -u webhook-deploy.service -f'

# Show webhook status
alias webhook-status='sudo systemctl status webhook-deploy.service --no-pager'

# Combined status check
alias bot-check='echo "🤖 Bot Status:" && sudo systemctl status style-transfer-bot.service --no-pager -l | head -8 && echo "" && echo "🔗 Webhook Status:" && sudo systemctl status webhook-deploy.service --no-pager -l | head -8'

# Quick deployment test
alias test-webhook='curl -X POST http://localhost:9000/health && echo ""'
EOF

echo ""
echo "To add these aliases:"
echo "1. nano ~/.bashrc"
echo "2. Copy and paste the aliases above"
echo "3. source ~/.bashrc"
echo ""
echo "Then you can use:"
echo "  restart-bot     # Restart bot + live logs"
echo "  bot-logs        # Just show live logs"
echo "  bot-status      # Show current status"
echo "  bot-check       # Show both bot and webhook status"
