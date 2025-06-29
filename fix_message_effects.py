#!/usr/bin/env python3
"""Fix script to remove message_effect_id parameters for compatibility with python-telegram-bot 20.7"""

import re

def fix_message_effects():
    """Remove all message_effect_id parameters from bot.py"""
    bot_file = 'src/bot.py'
    
    print("🔧 Fixing message_effect_id compatibility issue...")
    
    # Read the current bot.py file
    with open(bot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count original instances
    original_count = len(re.findall(r'message_effect_id=', content))
    print(f"📊 Found {original_count} instances of message_effect_id")
    
    # Remove all message_effect_id parameters with their values and comments
    # This pattern matches: ,\s*message_effect_id="..." (including comments on same line)
    content = re.sub(r',\s*message_effect_id="[^"]*"[^\n]*', '', content)
    
    # Also handle cases where message_effect_id might be on its own line
    content = re.sub(r'\s*message_effect_id="[^"]*"[^\n]*,?\n', '\n', content)
    
    # Count remaining instances
    remaining_count = len(re.findall(r'message_effect_id=', content))
    
    # Write the fixed content back
    with open(bot_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Removed {original_count - remaining_count} message_effect_id parameters")
    print(f"📊 Remaining instances: {remaining_count}")
    
    if remaining_count == 0:
        print("🎉 All message_effect_id parameters successfully removed!")
        print("🚀 Bot should now be compatible with python-telegram-bot 20.7")
    else:
        print("⚠️  Some instances may need manual review")
    
    return original_count - remaining_count

if __name__ == "__main__":
    removed_count = fix_message_effects()
    print(f"\n🔧 Fix complete: {removed_count} parameters removed") 