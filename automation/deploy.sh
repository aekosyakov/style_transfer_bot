#!/bin/bash
set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Upscale Bot Deployment Script${NC}"
echo "=================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Check for Python syntax errors
echo -e "${YELLOW}🔍 Checking Python syntax...${NC}"

# Core bot file
if ! python -m py_compile bot.py; then
    echo -e "${RED}❌ Syntax error in bot.py${NC}"
    exit 1
fi

# Model modules (now in models/ directory)
if ! python -m py_compile models/magic.py; then
    echo -e "${RED}❌ Syntax error in models/magic.py${NC}"
    exit 1
fi

if ! python -m py_compile models/topaz.py; then
    echo -e "${RED}❌ Syntax error in models/topaz.py${NC}"
    exit 1
fi

if ! python -m py_compile models/real_esrgan.py; then
    echo -e "${RED}❌ Syntax error in models/real_esrgan.py${NC}"
    exit 1
fi

if ! python -m py_compile models/controlnet.py; then
    echo -e "${RED}❌ Syntax error in models/controlnet.py${NC}"
    exit 1
fi

if ! python -m py_compile models/google.py; then
    echo -e "${RED}❌ Syntax error in models/google.py${NC}"
    exit 1
fi

# Advanced face enhancement modules
if ! python -m py_compile models/supir.py; then
    echo -e "${RED}❌ Syntax error in models/supir.py${NC}"
    exit 1
fi

if ! python -m py_compile models/ddcolor.py; then
    echo -e "${RED}❌ Syntax error in models/ddcolor.py${NC}"
    exit 1
fi

if ! python -m py_compile models/codeformer_advanced.py; then
    echo -e "${RED}❌ Syntax error in models/codeformer_advanced.py${NC}"
    exit 1
fi

if ! python -m py_compile models/flux_restore.py; then
    echo -e "${RED}❌ Syntax error in models/flux_restore.py${NC}"
    exit 1
fi

# Automation scripts
if ! python -m py_compile automation/log_monitor.py; then
    echo -e "${RED}❌ Syntax error in automation/log_monitor.py${NC}"
    exit 1
fi

if ! python -m py_compile automation/log_analyzer.py; then
    echo -e "${RED}❌ Syntax error in automation/log_analyzer.py${NC}"
    exit 1
fi

# Integration scripts
if ! python -m py_compile integrations/webhook_deploy.py; then
    echo -e "${RED}❌ Syntax error in integrations/webhook_deploy.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All Python files compile successfully${NC}"

# # Check git status
# echo -e "${YELLOW}📊 Checking git status...${NC}"
# if git diff --quiet && git diff --cached --quiet; then
#     echo -e "${YELLOW}⚠️  No changes detected. Nothing to commit.${NC}"
#     exit 0
# fi

# Show current changes
echo -e "${BLUE}📝 Current changes:${NC}"
git status --short

# Get commit message from user or use default
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}💬 Enter commit message (or press Enter for auto-generated):${NC}"
    read -r COMMIT_MSG
    
    if [ -z "$COMMIT_MSG" ]; then
        # Auto-generate commit message based on changed files
        CHANGED_FILES=$(git diff --name-only --cached)
        if [ -z "$CHANGED_FILES" ]; then
            CHANGED_FILES=$(git diff --name-only)
        fi
        
        if echo "$CHANGED_FILES" | grep -q "bot.py"; then
            COMMIT_MSG="Update bot functionality"
        elif echo "$CHANGED_FILES" | grep -q "magic.py"; then
            COMMIT_MSG="Update Magic Image Refiner module"
        elif echo "$CHANGED_FILES" | grep -q "topaz.py"; then
            COMMIT_MSG="Update Topaz module"
        else
            COMMIT_MSG="Update project files"
        fi
        
        # Add timestamp for uniqueness
        COMMIT_MSG="$COMMIT_MSG - $(date '+%Y-%m-%d %H:%M')"
    fi
else
    COMMIT_MSG="$*"
fi

echo -e "${BLUE}📝 Commit message: ${COMMIT_MSG}${NC}"

# Add all files to staging
echo -e "${YELLOW}📦 Adding files to staging...${NC}"
git add .

# Commit changes
echo -e "${YELLOW}💾 Committing changes...${NC}"
git commit -m "$COMMIT_MSG"

# Push to remote
echo -e "${YELLOW}🌐 Pushing to remote repository...${NC}"
if git push origin main; then
    echo -e "${GREEN}🎉 Successfully pushed to GitHub!${NC}"
    echo -e "${GREEN}✅ Changes pushed to origin/main${NC}"
    
    # Try to trigger webhook deployment
    WEBHOOK_URL=${WEBHOOK_URL:-""}
    if [ -n "$WEBHOOK_URL" ]; then
        echo -e "${YELLOW}🔄 Triggering server deployment...${NC}"
        if curl -s -X POST "$WEBHOOK_URL/deploy" \
           -H "Content-Type: application/json" \
           -H "X-Deploy-Script: true" \
           -d '{"source":"deploy_script"}' \
           --max-time 30 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server deployment triggered successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not reach deployment webhook${NC}"
            echo -e "${BLUE}💡 Manual deployment: curl -X POST $WEBHOOK_URL/deploy${NC}"
        fi
    else
        echo ""
        echo -e "${YELLOW}📋 Manual server update required:${NC}"
        echo -e "${BLUE}   git pull && sudo systemctl restart upscale-bot.service${NC}"
        echo -e "${BLUE}   journalctl -u upscale-bot.service -f${NC}"
        echo ""
        echo -e "${BLUE}💡 To enable automatic deployment:${NC}"
        echo -e "${BLUE}   export WEBHOOK_URL=http://your-server:9000${NC}"
    fi
else
    echo -e "${RED}❌ Failed to push to remote repository${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Deployment complete!${NC}" 