#!/usr/bin/env python3
"""
Deployment Webhook Server
────────────────────────
Listens for deployment webhooks and automatically updates the bot
"""

import os
import subprocess
import logging
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-secret-key-here')
BOT_DIR = '/root/upscale_bot'
SERVICE_NAME = 'upscale-bot.service'
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '9000'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def verify_signature(payload_body, signature_header):
    """Verify webhook signature for security"""
    if not signature_header:
        return False
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f'sha256={expected_signature}', signature_header)

def run_command(command, cwd=None):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

@app.route('/deploy', methods=['POST'])
def handle_deploy():
    """Handle deployment webhook"""
    try:
        # Check if this is from our deploy script (simple auth)
        deploy_script_auth = request.headers.get('X-Deploy-Script') == 'true'
        
        # Verify signature if secret is provided and not from deploy script
        if WEBHOOK_SECRET != 'your-secret-key-here' and not deploy_script_auth:
            signature = request.headers.get('X-Hub-Signature-256')
            if not verify_signature(request.data, signature):
                logging.warning("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 403
        
        logging.info("🚀 Deployment webhook received")
        
        # Change to bot directory
        os.chdir(BOT_DIR)
        
        # Pull latest changes
        logging.info("📥 Pulling latest changes...")
        success, stdout, stderr = run_command('git pull origin main', BOT_DIR)
        if not success:
            logging.error(f"Git pull failed: {stderr}")
            return jsonify({'error': f'Git pull failed: {stderr}'}), 500
        
        logging.info(f"Git pull output: {stdout}")
        
        # Install/update requirements if requirements.txt changed
        logging.info("📦 Checking requirements...")
        success, stdout, stderr = run_command('pip install -r requirements.txt', BOT_DIR)
        if success:
            logging.info("Requirements updated successfully")
        else:
            logging.warning(f"Requirements update warning: {stderr}")
        
        # Restart the bot service
        logging.info("🔄 Restarting bot service...")
        success, stdout, stderr = run_command(f'sudo systemctl restart {SERVICE_NAME}')
        if not success:
            logging.error(f"Service restart failed: {stderr}")
            return jsonify({'error': f'Service restart failed: {stderr}'}), 500
        
        logging.info("✅ Bot service restarted successfully")
        
        # Check service status
        success, stdout, stderr = run_command(f'sudo systemctl is-active {SERVICE_NAME}')
        service_status = stdout.strip()
        
        logging.info(f"🎉 Deployment completed successfully! Service status: {service_status}")
        
        return jsonify({
            'status': 'success',
            'message': 'Deployment completed successfully',
            'service_status': service_status
        })
        
    except Exception as e:
        logging.error(f"Deployment failed: {str(e)}")
        return jsonify({'error': f'Deployment failed: {str(e)}'}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current bot status"""
    try:
        # Check service status
        success, stdout, stderr = run_command(f'sudo systemctl is-active {SERVICE_NAME}')
        service_status = stdout.strip()
        
        # Get last few log lines
        success, stdout, stderr = run_command(f'sudo journalctl -u {SERVICE_NAME} -n 5 --no-pager')
        recent_logs = stdout.strip()
        
        return jsonify({
            'service_status': service_status,
            'recent_logs': recent_logs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    logging.info(f"🌐 Starting deployment webhook server on port {WEBHOOK_PORT}")
    logging.info(f"📁 Bot directory: {BOT_DIR}")
    logging.info(f"⚙️  Service name: {SERVICE_NAME}")
    
    app.run(
        host='0.0.0.0',
        port=WEBHOOK_PORT,
        debug=False
    ) 