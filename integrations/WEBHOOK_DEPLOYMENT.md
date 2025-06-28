# Webhook Deployment System

This system allows you to automatically deploy your bot updates to the server without manually running `git pull` and `systemctl restart` commands.

## How It Works

1. **Local Deploy Script** (`deploy.sh`) - Pushes code to GitHub and optionally triggers server webhook
2. **Server Webhook** (`webhook_deploy.py`) - Listens for deployment requests and automatically updates the bot
3. **Systemd Service** (`webhook-deploy.service`) - Runs the webhook server as a system service

## Server Setup

### 1. Initial Setup on Server

Run this **once** on your server to set up the webhook deployment system:

```bash
# On your server (as root)
cd /root/upscale_bot
sudo ./setup_webhook.sh
```

This will:
- Install Flask dependency
- Create and start the webhook deployment service
- Generate a secure webhook secret
- Show you the webhook URL to use

### 2. Configure Local Machine

After running the setup script, it will show you a webhook URL like:
```
http://your-server-ip:9000
```

Set this as an environment variable on your local machine:

```bash
# On your local machine
export WEBHOOK_URL=http://your-server-ip:9000
```

You can add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

## Usage

### Automatic Deployment (Recommended)

Once configured, simply use the deploy script as usual:

```bash
./deploy.sh "Your commit message"
```

The script will:
1. ✅ Check Python syntax
2. 📦 Commit and push to GitHub  
3. 🔄 Automatically trigger server deployment
4. ✅ Server pulls changes and restarts bot

### Manual Deployment

If the webhook URL is not set, the script will show manual commands:

```bash
# Manual server update (old way)
git pull && sudo systemctl restart upscale-bot.service
journalctl -u upscale-bot.service -f
```

Or trigger webhook manually:
```bash
curl -X POST http://your-server:9000/deploy
```

## Webhook Endpoints

The webhook server provides several endpoints:

- `POST /deploy` - Trigger deployment (pulls code and restarts bot)
- `GET /status` - Check bot service status and recent logs
- `GET /health` - Simple health check

### Examples

```bash
# Trigger deployment
curl -X POST http://your-server:9000/deploy

# Check bot status
curl http://your-server:9000/status

# Health check
curl http://your-server:9000/health
```

## Service Management

### Webhook Service Commands

```bash
# Check webhook service status
sudo systemctl status webhook-deploy.service

# View webhook logs
sudo journalctl -u webhook-deploy.service -f

# Restart webhook service
sudo systemctl restart webhook-deploy.service

# Stop webhook service
sudo systemctl stop webhook-deploy.service

# Start webhook service
sudo systemctl start webhook-deploy.service
```

### Bot Service Commands (unchanged)

```bash
# Check bot status
sudo systemctl status upscale-bot.service

# View bot logs
sudo journalctl -u upscale-bot.service -f

# Restart bot
sudo systemctl restart upscale-bot.service
```

## Security

- The webhook server uses HMAC-SHA256 signature verification
- Random 256-bit webhook secret is generated during setup
- Server runs on localhost port 9000 by default
- Only accepts POST requests with valid signatures

## Troubleshooting

### Webhook Not Responding

1. Check if webhook service is running:
   ```bash
   sudo systemctl status webhook-deploy.service
   ```

2. Check webhook logs:
   ```bash
   sudo journalctl -u webhook-deploy.service -f
   ```

3. Test webhook manually:
   ```bash
   curl -X POST http://your-server:9000/health
   ```

### Deployment Fails

1. Check webhook logs for detailed error messages
2. Verify git repository is clean on server
3. Ensure proper permissions for systemctl commands
4. Check if bot service exists and is configured correctly

### Port Issues

If port 9000 is in use, you can change it:

1. Edit `/etc/systemd/system/webhook-deploy.service`
2. Change `Environment=WEBHOOK_PORT=9000` to your preferred port
3. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart webhook-deploy.service
   ```

## Benefits

✅ **No more manual deployments** - One command deploys everything
✅ **Faster deployment** - Automatic server updates
✅ **Error checking** - Syntax validation before deployment  
✅ **Consistent process** - Same steps every time
✅ **Better logging** - Deployment activities are logged
✅ **Rollback friendly** - Easy to revert if needed 