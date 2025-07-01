#!/usr/bin/env python3
"""Main Telegram Style Transfer Bot."""

import os
import sys
import json
import asyncio
import argparse
import traceback
import logging
import time
import uuid
import random
from typing import Dict, Any, Optional, Final
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, PreCheckoutQueryHandler
)
from telegram.error import TimedOut, NetworkError, RetryAfter

from config import config
from localization import L
from redis_client import redis_client
from flux_api import flux_api
from kling_api import kling_api
from payments import payment_processor
from stars_billing import stars_billing

# Import hairstyle and dress generators
try:
    from src.hairstyles import hairstyle_generator
except ImportError:
    logger.warning("Could not import hairstyle_generator")
    hairstyle_generator = None

try:
    from src.dresses import dress_generator
except ImportError:
    logger.warning("Could not import dress_generator")
    dress_generator = None

# Configure logging with safe file handler
def setup_logging():
    """Setup logging with safe file handler that creates directory if needed."""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Try to create file handler, but don't fail if logs directory doesn't exist
    try:
        import os
        os.makedirs('logs', exist_ok=True)
        handlers.append(logging.FileHandler('logs/bot.log'))
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}")
        print("Logging to console only.")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        handlers=handlers
    )

setup_logging()
logger = logging.getLogger(__name__)

def generate_request_id() -> str:
    """Generate unique request ID for tracing."""
    return f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"

async def retry_telegram_request(operation, max_retries=3, initial_delay=1.0):
    """
    Retry Telegram API requests with exponential backoff for timeout and network errors.
    
    Args:
        operation: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
    
    Returns:
        Result of the operation or None if all retries failed
    """
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except (TimedOut, NetworkError) as e:
            if attempt < max_retries:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Telegram API timeout/network error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                logger.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed for Telegram API call: {e}")
                raise e
        except RetryAfter as e:
            if attempt < max_retries:
                delay = e.retry_after + 1  # Add 1 second buffer
                logger.warning(f"Telegram rate limit hit (attempt {attempt + 1}/{max_retries + 1}): retry after {e.retry_after}s")
                logger.info(f"Waiting {delay} seconds before retry...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Rate limit exceeded after {max_retries + 1} attempts: {e}")
                raise e
        except Exception as e:
            # Don't retry for other types of errors
            logger.error(f"Non-retryable error in Telegram API call: {type(e).__name__}: {e}")
            raise e
    
    return None

def log_user_action(user_id: int, action: str, details: Dict[str, Any] = None, request_id: str = None):
    """Log user action with context."""
    log_data = {
        "user_id": user_id,
        "action": action,
        "request_id": request_id or generate_request_id(),
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    logger.info(f"👤 USER_ACTION: {json.dumps(log_data)}")

def log_api_call(api_name: str, request_id: str, user_id: int, params: Dict[str, Any], duration: float = None, success: bool = None, error: str = None):
    """Log API call with timing and result information."""
    log_data = {
        "api": api_name,
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "params": params,
        "duration_seconds": duration,
        "success": success,
        "error": error
    }
    if success:
        logger.info(f"🌐 API_SUCCESS: {json.dumps(log_data)}")
    else:
        logger.error(f"🌐 API_FAILURE: {json.dumps(log_data)}")

def log_processing_step(step: str, request_id: str, user_id: int, details: Dict[str, Any] = None, success: bool = True, error: str = None):
    """Log processing step with context."""
    log_data = {
        "step": step,
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "details": details or {},
        "error": error
    }
    if success:
        logger.info(f"⚙️  PROCESSING: {json.dumps(log_data)}")
    else:
        logger.error(f"⚙️  PROCESSING_ERROR: {json.dumps(log_data)}")

# Success effect IDs for random selection - DISABLED due to invalid IDs causing crashes
# SUCCESS_EFFECT_IDS: Final[list[str]] = [
#     "5104841245755180586",  # 🔥
#     "5044134455711629726",  # ❤️
#     "5046509860389126442",  # 🎉
# ]


class StyleTransferBot:
    """Main bot class handling all operations."""
    
    def __init__(self, debug: bool = False):
        """Initialize the Style Transfer Bot."""
        self.debug = debug
        
        # Configure application with better timeout settings
        self.app = (
            Application.builder()
            .token(config.bot_token)
            .connection_pool_size(8)  # Increase connection pool
            .connect_timeout(30.0)    # 30 second connect timeout
            .read_timeout(60.0)       # 60 second read timeout
            .write_timeout(60.0)      # 60 second write timeout
            .pool_timeout(10.0)       # 10 second pool timeout
            .build()
        )
        
        self._setup_handlers()
    
    def _get_random_success_effect_id(self) -> str:
        """Get a random success effect ID - DISABLED to prevent crashes."""
        return None  # Disabled to prevent Effect_id_invalid crashes
    
    def _setup_handlers(self) -> None:
        """Set up all bot handlers."""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("premium", self.premium_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("settings", self.settings_command))
        self.app.add_handler(CommandHandler("feedback", self.feedback_command))
        self.app.add_handler(CommandHandler("about", self.about_command))
        self.app.add_handler(CommandHandler("invite", self.invite_command))
        self.app.add_handler(CommandHandler("support", self.support_command))
        
        # Stars billing commands
        self.app.add_handler(CommandHandler("quota", self.quota_command))
        self.app.add_handler(CommandHandler("buy", self.buy_command))
        self.app.add_handler(CommandHandler("style", self.style_command))
        self.app.add_handler(CommandHandler("video", self.video_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Debug commands (only in debug mode)
        if self.debug:
            self.app.add_handler(CommandHandler("debug_premium", self.debug_premium_command))
            self.app.add_handler(CommandHandler("debug_revoke", self.debug_revoke_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Callback query handlers
        self.app.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Payment handlers
        self.app.add_handler(PreCheckoutQueryHandler(self.handle_pre_checkout_query))
        self.app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.handle_successful_payment))
        
        logger.info("Bot handlers configured")
    
    def _get_user_language(self, telegram_user) -> str:
        """Get user's preferred language, checking Redis first, then Telegram detection."""
        user_id = telegram_user.id
        
        # First check Redis for stored language preference
        stored_lang = redis_client.get_user_language(user_id)
        if stored_lang and stored_lang in L.get_available_languages():
            logger.debug(f"Using stored language preference for user {user_id}: {stored_lang}")
            return stored_lang
        
        # Fall back to Telegram's language detection
        detected_lang = L.get_user_language(telegram_user)
        logger.debug(f"Using detected language for user {user_id}: {detected_lang}")
        return detected_lang
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        try:
            user = update.effective_user
            user_lang = self._get_user_language(user)
            
            # Store user language preference
            redis_client.set_user_language(user.id, user_lang)
            
            # Check if this is a new user by looking at their quota
            flux_quota = stars_billing.get_user_quota(user.id, "flux")
            kling_quota = stars_billing.get_user_quota(user.id, "kling")
            
            welcome_msg = L.get("msg.welcome", user_lang, name=user.first_name)
            
            # Add quota info for new users who just got free credits
            if flux_quota <= 5 and kling_quota <= 1:
                welcome_msg += f"\n\n{L.get('billing.free_trial_header', user_lang)}\n🎨 {flux_quota} style generations\n🎬 {kling_quota} video animation"
            
            keyboard = self._get_main_menu_keyboard(user_lang, user.id)
            
            await update.message.reply_text(
                welcome_msg,
                reply_markup=keyboard,
                parse_mode='Markdown'
                # Removed effect ID to prevent "Effect_id_invalid" crashes
            )
            
            logger.info(f"User {user.id} started the bot with {flux_quota} FLUX / {kling_quota} Kling quota")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            fallback_msg = L.get("msg.welcome_fallback", self._get_user_language(update.effective_user))
            await update.message.reply_text(fallback_msg)
    

    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /premium command."""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        is_premium = redis_client.is_user_premium(user_id)
        
        if is_premium:
            await update.message.reply_text(
                L.get("premium.already_active", user_lang)
            )
        else:
            await self._show_premium_options(update, context)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        is_premium = redis_client.is_user_premium(user_id)
        
        status_text = f"{L.get('status.title', user_lang)}\n\n"
        status_text += f"{L.get('status.user_id', user_lang, user_id=user_id)}\n"
        
        if is_premium:
            status_text += L.get('status.premium_active', user_lang)
        else:
            status_text += L.get('status.premium_inactive', user_lang)
            status_text += L.get('status.upgrade_note', user_lang)
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command."""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        
        settings_text = (
            "⚙️ **Personal Settings**\n\n"
            f"🌐 Language: {L.get('lang_name', user_lang)}\n"
            f"👤 User ID: `{user_id}`\n"
            f"📊 Status: {'Premium' if redis_client.is_user_premium(user_id) else '🆓 Free'}\n\n"
            "Use the buttons below to modify your settings:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        try:
            await update.message.reply_text(
                settings_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            await update.message.reply_text("Settings will be available soon!")
    
    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /feedback command."""
        user_lang = self._get_user_language(update.effective_user)
        
        feedback_text = (
            "💬 **Send Us Your Feedback**\n\n"
            "We value your opinion! Help us improve the bot by sharing:\n\n"
            "• 🐛 Bug reports\n"
            "• 💡 Feature suggestions\n"
            "• 📈 Performance feedback\n"
            "• 🎨 Style requests\n\n"
            "Simply reply to this message with your feedback, "
            "or contact us at @StyleTransferSupport"
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 Contact Support", url="https://t.me/StyleTransferSupport")],
            [InlineKeyboardButton("⭐ Rate Us", url="https://t.me/share/url?url=Check%20out%20this%20amazing%20style%20transfer%20bot!")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(
            feedback_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /about command."""
        user_lang = self._get_user_language(update.effective_user)
        
        about_text = (
            "ℹ️ **About Style Transfer Bot**\n\n"
            "🎨 Transform your photos with AI-powered style transfer!\n\n"
            "**Features:**\n"
            "• 🖼️ Style Transfer - 15 unique artistic styles\n"
            "• 🌅 Background Swap - 21 stunning backgrounds\n"
            "• ✨ Object Editing - Smart object modifications\n"
            "• 📝 Text Editing - Add/remove text from images\n"
            "• 👤 Face Enhancement - Professional photo touch-ups\n"
            "• 🎬 Animation - Bring your photos to life\n\n"
            "**Technology:**\n"
            "• Powered by FLUX Kontext Pro AI\n"
            "• Kling AI for animations\n"
            "• High-quality image processing\n\n"
            "**Version:** 2.0\n"
            "**Last Update:** December 2024"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Try Premium", callback_data="premium_info")],
            [InlineKeyboardButton("🤝 Invite Friends", callback_data="invite_friends")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(
            about_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def invite_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /invite command."""
        user_lang = self._get_user_language(update.effective_user)
        bot_username = "StyleTransferBot"  # Replace with actual bot username
        
        invite_text = (
            "🤝 **Invite Friends & Earn Rewards**\n\n"
            "Share the magic of AI-powered photo transformation!\n\n"
            "**Your Referral Benefits:**\n"
            "• 🎁 Get 1 week free premium for each friend\n"
            "• 🏆 Unlock exclusive styles at 5 referrals\n"
            "• 🏆 Permanent premium at 10 referrals\n\n"
            f"**Your Invite Link:**\n"
            f"`https://t.me/{bot_username}?start=ref_{update.effective_user.id}`\n\n"
            "**Share Message:**\n"
            "_Transform your photos with AI! Check out this amazing style transfer bot 🎨_"
        )
        
        share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=ref_{update.effective_user.id}&text=Transform%20your%20photos%20with%20AI!%20Check%20out%20this%20amazing%20style%20transfer%20bot%20🎨"
        
        keyboard = [
            [InlineKeyboardButton("📤 Share Invite Link", url=share_url)],
            [InlineKeyboardButton("📊 My Referrals", callback_data="referral_stats")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(
            invite_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /support command."""
        user_lang = self._get_user_language(update.effective_user)
        
        support_text = (
            "🛠️ **Support & Help Center**\n\n"
            "Need assistance? We're here to help!\n\n"
            "**Quick Help:**\n"
            "• 📸 Upload any photo to start\n"
            "• 🎨 Choose from 50+ style options\n"
            "• ⏱️ Processing takes 30-60 seconds\n"
            "• 💾 Results are saved for 24 hours\n\n"
            "**Troubleshooting:**\n"
            "• Photo not processing? Try a smaller file\n"
            "• Styles locked? Upgrade to premium\n"
            "• Bot not responding? Contact support\n\n"
            "**Contact Options:**\n"
            "• 💬 Telegram: @StyleTransferSupport\n"
            "• 📧 Email: support@styletransfer.bot\n"
            "• ⏰ Response time: Under 2 hours"
        )
        
        keyboard = [
            [InlineKeyboardButton("💬 Live Chat", url="https://t.me/StyleTransferSupport")],
            [InlineKeyboardButton("📚 FAQ", callback_data="show_faq")],
            [InlineKeyboardButton("🐛 Report Bug", callback_data="report_bug")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(
            support_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def quota_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /quota command - show current quota status."""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        
        # Get current pass and quota info
        pass_info = stars_billing.get_user_pass_info(user_id)
        flux_quota = stars_billing.get_user_quota(user_id, "flux")
        kling_quota = stars_billing.get_user_quota(user_id, "kling")
        
        if pass_info:
            expires_dt = datetime.fromisoformat(pass_info["expires_at"])
            time_left = expires_dt - datetime.now()
            days_left = max(0, time_left.days)
            hours_left = max(0, time_left.seconds // 3600)
            
            status_text = L.get("billing.current_status", user_lang,
                               pass_name=L.get(stars_billing.passes[pass_info["pass_type"]]["name_key"], user_lang),
                               days=days_left,
                               hours=hours_left,
                               flux=flux_quota,
                               kling=kling_quota)
        else:
            # Check if user has free daily credits
            if flux_quota <= 5 and kling_quota <= 1 and (flux_quota > 0 or kling_quota > 0):
                status_text = L.get("billing.free_trial_status", user_lang, flux=flux_quota, kling=kling_quota)
            else:
                status_text = L.get("billing.no_active_pass", user_lang,
                                   flux=flux_quota,
                                   kling=kling_quota)
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def buy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /buy command - show billing menu."""
        await stars_billing.show_billing_menu(update, context)
    
    async def style_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /style command - quick style transfer."""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        
        # Check if user has FLUX quota
        if not stars_billing.has_quota(user_id, "flux", user_obj=update.effective_user):
            await stars_billing.check_quota_and_upsell(update, context, "flux")
            return
        
        # Prompt user to upload photo
        await update.message.reply_text(
            L.get("msg.photo_upload_prompt", user_lang),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(L.get("btn.upload_photo", user_lang), callback_data="upload_photo")]
            ])
        )
    
    async def video_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /video command - quick video/animation creation."""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        
        # Check if user has Kling quota
        if not stars_billing.has_quota(user_id, "kling", user_obj=update.effective_user):
            await stars_billing.check_quota_and_upsell(update, context, "kling")
            return
        
        # Prompt user to upload photo for animation
        await update.message.reply_text(
            L.get("msg.photo_upload_prompt", user_lang),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(L.get("btn.upload_photo", user_lang), callback_data="upload_photo")]
            ])
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command - show comprehensive help."""
        user_lang = self._get_user_language(update.effective_user)
        
        help_text = (
            "🤖 **Style Transfer Bot Help**\n\n"
            "**📋 Available Commands:**\n"
            "• `/start` - Start the bot\n"
            "• `/quota` - Check your current quota\n"
            "• `/buy` - Purchase passes or extra quota\n"
            "• `/style` - Quick style transfer\n"
            "• `/video` - Quick video/animation\n"
            "• `/help` - Show this help message\n\n"
            "**🎨 How to Use:**\n"
            "1. Upload any photo\n"
            "2. Choose enhancement type\n"
            "3. Select specific style/effect\n"
            "4. Wait for AI processing\n\n"
            "**💰 Billing System:**\n"
            "• **Passes** - Better value for regular use\n"
            "• **Pay-as-you-go** - Perfect for occasional use\n"
            "• **FLUX** - High-quality image generation\n"
            "• **Kling** - Professional video/animation\n\n"
            "**🎁 Need Help?**\n"
            "Contact: @StyleTransferSupport"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎟️ View Passes", callback_data="billing_passes")],
            [InlineKeyboardButton("⚡ Buy Extra", callback_data="billing_payg")],
            [InlineKeyboardButton("📊 Check Quota", callback_data="billing_menu")]
        ]
        
        await update.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def debug_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Debug command to grant premium status."""
        if not self.debug:
            return
        
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        
        # Grant premium for 30 days
        success = redis_client.set_user_premium(user_id, True, 30)
        
        if success:
            await update.message.reply_text(
                "🎉 DEBUG: Premium status granted for 30 days!\n"
                "You now have access to all premium style transfer options including:\n"
                "• 🌸 Anime Style\n"
                "• 💥 Comic Book\n"
                "• 🌌 Sci-Fi Art\n"
                "• 🎮 Pixel Art\n"
                "• And many more!"
                # Removed effect ID to prevent "Effect_id_invalid" crashes
            )
        else:
            await update.message.reply_text("❌ DEBUG: Failed to grant premium status")
    
    async def debug_revoke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Debug command to revoke premium status."""
        if not self.debug:
            return
        
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        
        # Revoke premium
        success = redis_client.set_user_premium(user_id, False)
        
        if success:
            await update.message.reply_text("🔒 DEBUG: Premium status revoked. You now have free tier access only.")
        else:
            await update.message.reply_text("❌ DEBUG: Failed to revoke premium status")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo messages."""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            # Get the largest photo
            photo = update.message.photo[-1]
            
            # Store photo info in context
            context.user_data['current_photo'] = photo.file_id
            
            # DETAILED LOGGING FOR DEBUGGING
            logger.info(f"📷 PHOTO_UPLOAD_DEBUG for user {user_id}:")
            logger.info(f"   - Photo file_id: '{photo.file_id}'")
            logger.info(f"   - File_id length: {len(photo.file_id)}")
            logger.info(f"   - Photo file_unique_id: '{photo.file_unique_id}'")
            logger.info(f"   - Photo width: {photo.width}, height: {photo.height}")
            logger.info(f"   - Photo file_size: {photo.file_size}")
            logger.info(f"   - Context user_data keys: {list(context.user_data.keys())}")
            logger.info(f"   - Stored in context: '{context.user_data.get('current_photo')}'")
            
            # Show enhancement options
            keyboard = self._get_enhancement_keyboard(user_lang, user_id)
            
            await update.message.reply_text(
                L.get("msg.photo_received", user_lang),
                reply_markup=keyboard
            )
            
            logger.info(f"User {user_id} uploaded photo: {photo.file_id}")
            
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            user_lang = self._get_user_language(update.effective_user)
            await update.message.reply_text(L.get("msg.error_photo", user_lang))
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle document messages that might be images."""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            document = update.message.document
            
            # Check if the document is an image
            if not document.mime_type or not document.mime_type.startswith('image/'):
                logger.info(f"User {user_id} sent non-image document: {document.mime_type}")
                await update.message.reply_text(
                    "📷 Please send an image file (JPEG, PNG, GIF, etc.) or use the camera button to take a photo."
                )
                return
            
            # Check file size (Telegram limit is 20MB for bots, but we'll be conservative)
            if document.file_size and document.file_size > 10 * 1024 * 1024:  # 10MB limit
                await update.message.reply_text(
                    "📏 Image file is too large. Please send an image smaller than 10MB."
                )
                return
            
            # Store document file_id in context (same as photo)
            context.user_data['current_photo'] = document.file_id
            
            # DETAILED LOGGING FOR DEBUGGING
            logger.info(f"📁 DOCUMENT_UPLOAD_DEBUG for user {user_id}:")
            logger.info(f"   - Document file_id: '{document.file_id}'")
            logger.info(f"   - File_id length: {len(document.file_id)}")
            logger.info(f"   - Document file_unique_id: '{document.file_unique_id}'")
            logger.info(f"   - Document mime_type: {document.mime_type}")
            logger.info(f"   - Document file_name: {document.file_name}")
            logger.info(f"   - Document file_size: {document.file_size}")
            logger.info(f"   - Context user_data keys: {list(context.user_data.keys())}")
            logger.info(f"   - Stored in context: '{context.user_data.get('current_photo')}'")
            
            # Show enhancement options (same as photo upload)
            keyboard = self._get_enhancement_keyboard(user_lang, user_id)
            
            await update.message.reply_text(
                L.get("msg.photo_received", user_lang),
                reply_markup=keyboard
            )
            
            logger.info(f"User {user_id} uploaded image document: {document.file_id}")
            
        except Exception as e:
            logger.error(f"Error handling document: {e}")
            user_lang = self._get_user_language(update.effective_user)
            await update.message.reply_text(L.get("msg.error_photo", user_lang))
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages."""
        text = update.message.text.lower()
        user_lang = self._get_user_language(update.effective_user)
        
        if "premium" in text:
            await self.premium_command(update, context)
        else:
            await update.message.reply_text(
                L.get("msg.photo_upload_prompt", user_lang)
            )
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards."""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            logger.debug(f"Callback query from user {user_id}: {data}")
            
            if data == "main_menu":
                await self._show_main_menu(update, context)
            elif data == "premium_info":
                await self._show_premium_options(update, context)
            
            # Stars billing callbacks
            elif data == "billing_menu":
                await stars_billing.show_billing_menu(update, context)
            elif data == "billing_passes":
                await stars_billing.show_passes_menu(update, context)
            elif data == "billing_payg":
                await stars_billing.show_payg_menu(update, context)
            elif data.startswith("buy_pass_"):
                pass_id = data.split("buy_pass_")[1]
                await stars_billing.create_stars_invoice(update, context, "pass", pass_id)
            elif data.startswith("buy_payg_"):
                payg_id = data.split("buy_payg_")[1]
                await stars_billing.create_stars_invoice(update, context, "payg", payg_id)
            elif data == "back_to_enhancements":
                await self._show_enhancement_menu(update, context)
            elif data == "upload_prompt":
                await self._show_upload_prompt(update, context)
            elif data == "help":
                await self._show_help_message(update, context)
            elif data == "lang_en":
                await self._handle_language_change(update, context, 'en')
            elif data == "lang_ru":
                await self._handle_language_change(update, context, 'ru')
            elif data == "invite_friends":
                await self._handle_invite_callback(update, context)
            elif data == "referral_stats":
                await self._show_referral_stats(update, context)
            elif data == "show_faq":
                await self._show_faq(update, context)
            elif data == "report_bug":
                await self._show_bug_report(update, context)
            elif data == "retry":
                await self._handle_retry(update, context)
            elif data == "repeat_video":
                await self._handle_repeat_video(update, context)
            elif data == "restart":
                await self._handle_restart(update, context)
            elif data == "animate_result":
                await self._handle_animate_result(update, context)
            elif data.startswith("upgrade_"):
                plan_type = data.replace("upgrade_", "")
                await payment_processor.create_premium_invoice(update, context, plan_type)
            elif data.startswith("category_"):
                await self._handle_category_selection(update, context, data)
            elif data in ["new_look_men", "new_look_women", "new_look_random", "new_hairstyle_men", "new_hairstyle_women", "new_hairstyle_random", "cartoon", "anime", "comics", "art_styles"]:
                # Handle submenu navigation - treat as category selection
                await self._handle_category_selection(update, context, f"category_{data}")
            elif data.startswith("option_"):
                await self._handle_option_selection(update, context, data)
            elif data.startswith("animate_"):
                await self._handle_animation_request(update, context, data)
            else:
                try:
                    await query.edit_message_text(L.get("msg.unknown_option", user_lang))
                except Exception as e:
                    # If edit_message_text fails, it might be a photo message, try edit_message_caption
                    if "no text in the message to edit" in str(e).lower():
                        logger.info("Message has no text, trying to edit caption instead for unknown option")
                        await query.edit_message_caption(caption=L.get("msg.unknown_option", user_lang))
                    else:
                        raise e
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle pre-checkout queries."""
        query = update.pre_checkout_query
        # Auto-approve all payments for now
        await query.answer(ok=True)
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle successful payments."""
        # Check if it's a Stars payment or traditional payment
        if update.message.successful_payment and update.message.successful_payment.invoice_payload.startswith("stars_"):
            await stars_billing.handle_successful_stars_payment(update, context)
            # Check for auto-resume after successful Stars payment
            await self._check_and_handle_auto_resume(update, context)
        else:
            await payment_processor.handle_successful_payment(update, context)
    
    def _get_main_menu_keyboard(self, lang: str, user_id: int) -> InlineKeyboardMarkup:
        """Get main menu keyboard."""
        is_premium = redis_client.is_user_premium(user_id)
        
        premium_text = L.get("btn.premium_features", lang) if is_premium else L.get("btn.upgrade_to_premium", lang)
        
        keyboard = [
            [InlineKeyboardButton(L.get("btn.upload_photo", lang), callback_data="upload_prompt")],
            [InlineKeyboardButton("📊 Check Quota", callback_data="billing_menu")],
            [InlineKeyboardButton("🎟️ Buy Passes", callback_data="billing_passes")],
            [InlineKeyboardButton(premium_text, callback_data="premium_info")],
            [InlineKeyboardButton(L.get("btn.help", lang), callback_data="help")],
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def _get_enhancement_keyboard(self, lang: str, user_id: int) -> InlineKeyboardMarkup:
        """Get enhancement options keyboard."""
        is_premium = redis_client.is_user_premium(user_id)
        
        keyboard = [
            [InlineKeyboardButton(L.get("btn.style_transfer", lang), callback_data="category_style_transfer")],
            [InlineKeyboardButton(L.get("btn.new_look", lang), callback_data="category_new_look")],
            [InlineKeyboardButton(L.get("btn.new_hairstyle", lang), callback_data="category_new_hairstyle")],
            [InlineKeyboardButton(L.get("btn.change_background", lang), callback_data="category_change_background")],
            [InlineKeyboardButton(L.get("btn.replace_text", lang), callback_data="category_replace_text")],
            [InlineKeyboardButton(L.get("btn.animate", lang), callback_data="category_animate")],
        ]
        
        if not is_premium:
            keyboard.append([InlineKeyboardButton(L.get("btn.unlock_all_features", lang), callback_data="premium_info")])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show main menu."""
        user_lang = self._get_user_language(update.effective_user)
        keyboard = self._get_main_menu_keyboard(user_lang, update.effective_user.id)
        
        await update.callback_query.edit_message_text(
            L.get("msg.main_menu", user_lang),
            reply_markup=keyboard
        )
    
    async def _show_premium_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show premium subscription options."""
        user_lang = self._get_user_language(update.effective_user)
        
        premium_text = (
            f"{L.get('premium.title', user_lang)}\n\n"
            f"{L.get('premium.features', user_lang)}\n\n"
            f"{L.get('premium.choose_plan', user_lang)}"
        )
        
        keyboard = [
            [InlineKeyboardButton(L.get("btn.monthly_plan", user_lang), callback_data="upgrade_monthly")],
            [InlineKeyboardButton(L.get("btn.yearly_plan", user_lang), callback_data="upgrade_yearly")],
            [InlineKeyboardButton(L.get("btn.back", user_lang), callback_data="main_menu")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                premium_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                premium_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    async def _show_enhancement_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show enhancement options menu."""
        user_lang = self._get_user_language(update.effective_user)
        user_id = update.effective_user.id
        keyboard = self._get_enhancement_keyboard(user_lang, user_id)
        
        await update.callback_query.edit_message_text(
            L.get("msg.photo_received", user_lang),
            reply_markup=keyboard
        )
    
    async def _show_upload_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show upload photo prompt."""
        user_lang = self._get_user_language(update.effective_user)
        
        await update.callback_query.edit_message_text(
            L.get("msg.photo_upload_prompt", user_lang)
        )
    
    async def _show_help_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help message."""
        user_lang = self._get_user_language(update.effective_user)
        
        help_text = (
            f"{L.get('help.title', user_lang)}\n\n"
            f"{L.get('help.how_to_use', user_lang)}\n\n"
            f"{L.get('help.features', user_lang)}\n\n"
            f"{L.get('help.premium_benefits', user_lang)}\n\n"
            f"{L.get('help.upgrade_note', user_lang)}"
        )
        
        keyboard = [
            [InlineKeyboardButton(L.get("btn.back", user_lang), callback_data="main_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _handle_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
        """Handle category selection."""
        category = data.replace("category_", "")
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        is_premium = redis_client.is_user_premium(user_id)
        
        # Get available options for category (always show all options for better UX)
        options = config.get_category_options(category, is_premium, show_all=True)
        
        if not options:
            try:
                await update.callback_query.edit_message_text(L.get("msg.no_options", user_lang))
            except Exception as e:
                # If edit_message_text fails, it might be a photo message, try edit_message_caption
                if "no text in the message to edit" in str(e).lower():
                    logger.info("Message has no text, trying to edit caption instead for no options")
                    await update.callback_query.edit_message_caption(caption=L.get("msg.no_options", user_lang))
                else:
                    raise e
            return
        
        # Store category in context
        context.user_data['current_category'] = category
        
        # Create keyboard with options
        keyboard = []
        
        # Check if this is a submenu category
        if config.is_submenu_category(category):
            # Handle submenu options (they have callback_data instead of hash-based identifiers)
            for option in options:
                label_text = L.get(option.get('label_key', option.get('label', 'Unknown')), user_lang)
                callback_data = option.get('callback_data', f"category_{option.get('label_key', 'unknown')}")
                keyboard.append([InlineKeyboardButton(
                    label_text, 
                    callback_data=callback_data
                )])
        else:
            # Handle regular options
            for option in options:
                # Use translation key if available, fallback to label
                label_text = L.get(option.get('label_key', option.get('label', 'Unknown')), user_lang)
                # Create unique identifier for the option
                option_id = option.get('label_key', option.get('label', 'unknown'))
                keyboard.append([InlineKeyboardButton(
                    label_text, 
                    callback_data=f"option_{category}_{hash(option_id)}"
                )])
        
        keyboard.append([InlineKeyboardButton(L.get("btn.back", user_lang), callback_data="back_to_enhancements")])
        
        # Get localized category name
        category_name = L.get(f"category.{category}", user_lang)
        
        # Check if the message has a photo (from restart button) or is a text message
        try:
            await update.callback_query.edit_message_text(
                L.get("msg.category_selection", user_lang, category=category_name),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            # If edit_message_text fails, it might be a photo message, try edit_message_caption
            if "no text in the message to edit" in str(e).lower():
                logger.info("Message has no text, trying to edit caption instead")
                await update.callback_query.edit_message_caption(
                    caption=L.get("msg.category_selection", user_lang, category=category_name),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                raise e
    
    async def _handle_option_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
        """Handle specific option selection and process image."""
        try:
            logger.info(f"Processing option selection: {data}")
            
            # Extract category from callback data format "option_{category}_{hash}"
            if not data.startswith("option_"):
                logger.error(f"Invalid option data format: {data}")
                return
            
            # Remove "option_" prefix
            data_without_prefix = data[7:]  # "option_" is 7 characters
            
            # Find the last underscore (separates category from hash)
            last_underscore = data_without_prefix.rfind("_")
            if last_underscore == -1:
                logger.error(f"Invalid option data format: {data}")
                return
            
            category = data_without_prefix[:last_underscore]
            option_hash = data_without_prefix[last_underscore + 1:]
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            is_premium = redis_client.is_user_premium(user_id)
            
            logger.info(f"User {user_id} selected category: {category}, option hash: {option_hash}")
            
            # Get the selected option details
            options = config.get_category_options(category, is_premium)
            selected_option = None
            for option in options:
                # Check both old 'label' format and new 'label_key' format
                option_id = option.get('label_key', option.get('label', 'unknown'))
                if str(hash(option_id)) == option_hash:
                    selected_option = option
                    break
            
            if not selected_option:
                logger.error(f"Could not find selected option for hash {option_hash}")
                try:
                    await update.callback_query.edit_message_text(
                        L.get("msg.error_occurred", user_lang)
                    )
                except Exception as e:
                    # If edit_message_text fails, it might be a photo message, try edit_message_caption
                    if "no text in the message to edit" in str(e).lower():
                        logger.info("Message has no text, trying to edit caption instead for error message")
                        await update.callback_query.edit_message_caption(
                            caption=L.get("msg.error_occurred", user_lang)
                        )
                    else:
                        raise e
                return
            
            logger.info(f"Selected option: {selected_option}")
            
            # 🔍 DETAILED LOGGING FOR OPTION SELECTION DEBUGGING
            logger.info(f"🎯 OPTION_SELECTION_DEBUG for user {user_id}:")
            logger.info(f"   📦 Category: '{category}'")
            logger.info(f"   🏷️  Label key: '{selected_option.get('label_key', 'N/A')}'")
            logger.info(f"   📝 Prompt: '{selected_option.get('prompt', 'N/A')}'")
            logger.info(f"   🔄 Is retry: False (this is new selection)")
            logger.info(f"   🖼️  Photo file_id: '{context.user_data.get('current_photo', 'N/A')}'")
            
            # Check if this is a premium option and user has premium access
            # Use label_key if available, fallback to label for backward compatibility
            option_identifier = selected_option.get('label_key', selected_option.get('label', ''))
            is_premium_option = config.is_premium_option(category, option_identifier)
            
            # Check if premium features are temporarily free for testing
            user_has_premium_access = is_premium or config.premium_features_free
            
            if config.premium_features_free and is_premium_option and not is_premium:
                logger.info(f"🎉 TESTING MODE: Granting free access to premium option {option_identifier} for user {user_id}")
            
            if is_premium_option and not user_has_premium_access:
                # User selected premium option but doesn't have premium access
                logger.info(f"User {user_id} tried to use premium option {option_identifier} without premium access")
                
                # Get translated label for display
                option_display_name = L.get(option_identifier, user_lang) if selected_option.get('label_key') else option_identifier
                
                upgrade_text = (
                    f"🔒 **{option_display_name}** is a premium feature!\n\n"
                    f"Upgrade to premium to unlock:\n"
                    f"• 🌸 Anime Style\n"
                    f"• 💥 Comic Book\n"
                    f"• 🎞️ 90s Cartoon\n"
                    f"• 🌌 Sci-Fi Art\n"
                    f"• And many more exciting styles!\n\n"
                    f"✨ Get unlimited access to all premium features!"
                )
                
                keyboard = [
                    [InlineKeyboardButton("🚀 Upgrade to Premium", callback_data="premium_info")],
                    [InlineKeyboardButton("⬅️ Back to Styles", callback_data="category_style_transfer")]
                ]
                
                try:
                    await update.callback_query.edit_message_text(
                        upgrade_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    # If edit_message_text fails, it might be a photo message, try edit_message_caption
                    if "no text in the message to edit" in str(e).lower():
                        logger.info("Message has no text, trying to edit caption instead for upgrade message")
                        await update.callback_query.edit_message_caption(
                            caption=upgrade_text,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode='Markdown'
                        )
                    else:
                        raise e
                return
            
            # Use clean generation manager - single entry point with quota handling
            from generation_manager import generation_manager
            
            photo_file_id = context.user_data.get('current_photo')
            
            # ENHANCED DEBUGGING FOR CHAINED EDITS
            logger.info(f"📷 PHOTO_RETRIEVAL_DEBUG for user {user_id}:")
            logger.info(f"   - Retrieved file_id: '{photo_file_id}'")
            logger.info(f"   - File_id type: {type(photo_file_id)}")
            logger.info(f"   - File_id length: {len(photo_file_id) if photo_file_id else 'None'}")
            logger.info(f"   - Context user_data keys: {list(context.user_data.keys())}")
            logger.info(f"   - Current category: {category}")
            logger.info(f"   - Selected option: {selected_option}")
            logger.info(f"   - Last processing data: {context.user_data.get('last_processing')}")
            if context.user_data.get('last_processing'):
                last_proc = context.user_data['last_processing']
                logger.info(f"   - Last processing photo_file_id: '{last_proc.get('photo_file_id')}'")
                logger.info(f"   - Last processing category: {last_proc.get('category')}")
                logger.info(f"   - File_id match: {photo_file_id == last_proc.get('photo_file_id')}")
            # logger.info(f"   - All context user_data: {context.user_data}")  # Commented to reduce noise
            
            if not photo_file_id:
                logger.warning(f"No photo found in context for user {user_id}")
                
                try:
                    await update.callback_query.edit_message_text(
                        L.get("msg.upload_photo_first", user_lang)
                    )
                except Exception as e:
                    if "no text in the message to edit" in str(e).lower():
                        await update.callback_query.edit_message_caption(
                            caption=L.get("msg.upload_photo_first", user_lang)
                        )
                    else:
                        raise e
                return
            
            # Single call to generation manager - handles everything
            if category == "animate":
                animation_prompt = selected_option.get('kling_prompt', '')
                await generation_manager.generate_video(
                    update, context, photo_file_id, animation_prompt, user_lang
                )
            else:
                await generation_manager.generate_image(
                    update, context, photo_file_id, category, selected_option, user_lang
                )
                
        except Exception as e:
            logger.error(f"Error processing option selection: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Note: Quota refund is handled automatically by safe_generate method if it was called
            # No manual refund needed here for processing errors
            
            user_lang = self._get_user_language(update.effective_user)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=L.get("msg.error_occurred", user_lang)
            )
    
    # Legacy method removed - using clean generation_manager instead
    async def _process_image_background_REMOVED(self) -> None:
        """Legacy method removed - replaced by clean generation_manager approach."""
        pass
    
    # Legacy animate background method also removed 
    async def _animate_result_background_REMOVED(self) -> None:
        """Legacy animate background method - replaced by generation_manager."""
        pass
    
    # Legacy auto-resume method removed
    async def _check_and_handle_auto_resume_REMOVED(self) -> None:
        """Legacy auto-resume method - replaced by simple callback system."""
        pass
    
    async def _handle_language_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
        """Handle language change requests."""
        user_id = update.effective_user.id
        redis_client.set_user_language(user_id, lang)
        
        logger.info(f"User {user_id} changed language to {lang}")
        
        # Show updated settings page in the new language
        settings_text = (
            "⚙️ **Personal Settings**\n\n"
            f"🌐 Language: {L.get('lang_name', lang)}\n"
            f"👤 User ID: `{user_id}`\n"
            f"📊 Status: {'Premium' if redis_client.is_user_premium(user_id) else '🆓 Free'}\n\n"
            "Use the buttons below to modify your settings:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(L.get("btn.back", lang), callback_data="main_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        # Also show a quick confirmation with a fun effect
        confirmation_text = "Language changed to English! 🇺🇸" if lang == 'en' else "Язык изменен на русский! 🇷🇺"
        await update.callback_query.answer(confirmation_text, show_alert=True)
    
    async def _handle_invite_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle invite callback from about page."""
        await self.invite_command(update, context)
    
    async def _show_referral_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show referral statistics."""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(update.effective_user)
        
        # Mock data for now - implement actual referral tracking later
        referral_count = 0
        rewards_earned = 0
        
        stats_text = (
            "📊 **Your Referral Statistics**\n\n"
            f"👥 Friends Invited: {referral_count}\n"
            f"🎁 Rewards Earned: {rewards_earned} days premium\n"
            f"🏆 Next Reward: {'5 referrals for exclusive styles' if referral_count < 5 else '10 referrals for permanent premium'}\n\n"
            "Keep sharing to unlock more rewards! 🚀"
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 Share More", callback_data="invite_friends")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_faq(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show frequently asked questions."""
        user_lang = self._get_user_language(update.effective_user)
        
        faq_text = (
            "📚 **Frequently Asked Questions**\n\n"
            "**Q: How long does processing take?**\n"
            "A: Usually 30-60 seconds depending on complexity.\n\n"
            "**Q: What file formats are supported?**\n"
            "A: JPEG, PNG up to 10MB.\n\n"
            "**Q: How do I get premium features?**\n"
            "A: Use /premium command to see subscription options.\n\n"
            "**Q: Can I use my own prompts?**\n"
            "A: Currently we use pre-defined styles for best results.\n\n"
            "**Q: Is my data safe?**\n"
            "A: Yes, all images are processed securely and deleted after 24 hours."
        )
        
        keyboard = [
            [InlineKeyboardButton("💬 Ask Support", url="https://t.me/StyleTransferSupport")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            faq_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_bug_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show bug report information."""
        user_lang = self._get_user_language(update.effective_user)
        user_id = update.effective_user.id
        
        bug_text = (
            "🐛 **Report a Bug**\n\n"
            "Help us improve by reporting any issues you encounter!\n\n"
            "**To report a bug, please include:**\n"
            "• 📝 What you were trying to do\n"
            "• ❌ What went wrong\n"
            "• 📱 Your device type\n"
            "• 🆔 Your User ID (for reference)\n\n"
            f"**Your User ID:** `{user_id}`\n\n"
            "Send your bug report to @StyleTransferSupport"
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 Report Bug", url="https://t.me/StyleTransferSupport")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        await update.callback_query.edit_message_text(
            bug_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _handle_retry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle Random button - generate random hairstyles with gender preservation or fallback to varied processing."""
        try:
            from generation_manager import generation_manager
            
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            # Remove buttons from the result message to prevent confusion
            try:
                await update.callback_query.edit_message_reply_markup(reply_markup=None)
                logger.info(f"🗑️ Removed buttons from result message for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to remove buttons from result message: {e}")
            
            # Get last processing parameters
            last_processing = context.user_data.get('last_processing')
            if not last_processing:
                await update.callback_query.answer("⚠️ No previous processing to retry", show_alert=True)
                return
            
            category = last_processing['category']
            gender = last_processing.get('gender', 'neutral')
            
            logger.info(f"🎲 RANDOM_BUTTON_DEBUG for user {user_id}:")
            logger.info(f"   - Original category: {category}")
            logger.info(f"   - Detected gender: {gender}")
            logger.info(f"   - Original option: {last_processing['selected_option']}")
            
            # 🎲 SMART RANDOM GENERATION LOGIC
            if self._is_hairstyle_category(category):
                logger.info(f"🎯 HAIRSTYLE DETECTED! Generating smart random hairstyle for user {user_id}")
                
                # Create random hairstyle option based on gender preference
                if gender == 'men':
                    logger.info(f"👨 ENHANCED DEBUG: Generating random men's hairstyle for user {user_id}")
                    logger.info(f"   - Original category: {category}")
                    logger.info(f"   - Original gender: {gender}")
                    logger.info(f"   - Will use prompt: RANDOM_MENS_HAIRSTYLE")
                    random_option = {
                        'label_key': 'hair.men_random',
                        'prompt': 'RANDOM_MENS_HAIRSTYLE'
                    }
                    answer_text = "🎲 Generating random men's hairstyle..."
                elif gender == 'women':
                    logger.info(f"👩 Generating random women's hairstyle")
                    random_option = {
                        'label_key': 'hair.women_random', 
                        'prompt': 'RANDOM_WOMENS_HAIRSTYLE'
                    }
                    answer_text = "🎲 Generating random women's hairstyle..."
                else:
                    # Fallback to random gender hairstyle
                    logger.info(f"🎲 Generating random gender hairstyle (neutral/unknown)")
                    random_option = {
                        'label_key': 'hair.random_any',
                        'prompt': 'RANDOM_HAIRSTYLE'
                    }
                    answer_text = "🎲 Generating random hairstyle..."
                
                # Use hairstyle category for generation
                hairstyle_category = self._get_hairstyle_category_from_original(category, gender)
                
                await generation_manager.retry_generation(
                    update, context, last_processing['photo_file_id'], 
                    hairstyle_category, random_option, user_lang
                )
                
                await update.callback_query.answer(answer_text)
                
            elif self._is_dress_category(category):
                logger.info(f"🎯 DRESS/OUTFIT DETECTED! Generating smart random outfit for user {user_id}")
                
                # Create random dress/outfit option based on gender preference
                if gender == 'men':
                    logger.info(f"👨 Generating random men's outfit")
                    random_option = {
                        'label_key': 'mens.random',
                        'prompt': 'RANDOM_MENS_OUTFIT'
                    }
                    answer_text = "🎲 Generating random men's outfit..."
                elif gender == 'women':
                    logger.info(f"👩 Generating random women's dress")
                    random_option = {
                        'label_key': 'dress.random',
                        'prompt': 'RANDOM_DRESS'
                    }
                    answer_text = "🎲 Generating random women's dress..."
                else:
                    # Fallback to random gender outfit
                    logger.info(f"🎲 Generating random gender outfit (neutral/unknown)")
                    random_option = {
                        'label_key': 'outfit.random_any',
                        'prompt': 'RANDOM_DRESS'  # Will be handled by variation system
                    }
                    answer_text = "🎲 Generating random outfit..."
                
                # Use dress/outfit category for generation
                dress_category = self._get_dress_category_from_original(category, gender)
                
                await generation_manager.retry_generation(
                    update, context, last_processing['photo_file_id'], 
                    dress_category, random_option, user_lang
                )
                
                await update.callback_query.answer(answer_text)
                
            else:
                # Not a hairstyle or dress category - use original varied logic
                logger.info(f"📝 Non-specific category, using varied option logic")
                varied_option = self._create_varied_option(
                    last_processing['category'],
                    last_processing['selected_option'],
                    gender
                )
                
                await generation_manager.retry_generation(
                    update, context, last_processing['photo_file_id'], 
                    last_processing['category'], varied_option, user_lang
                )
                
                await update.callback_query.answer("🎲 Creating random variation...")
            
        except Exception as e:
            logger.error(f"Error in random handler: {e}")
            await update.callback_query.answer("❌ Error occurred", show_alert=True)

    def _is_hairstyle_category(self, category: str) -> bool:
        """Check if the category is hairstyle-related."""
        hairstyle_categories = [
            'new_hairstyle', 'new_hairstyle_women', 'new_hairstyle_men', 
            'new_hairstyle_random'
        ]
        return category in hairstyle_categories

    def _get_hairstyle_category_from_original(self, original_category: str, gender: str) -> str:
        """Map original category to appropriate hairstyle category based on gender."""
        if gender == 'men':
            return 'new_hairstyle_men'
        elif gender == 'women':
            return 'new_hairstyle_women'
        else:
            # Fallback to random gender hairstyle
            return 'new_hairstyle_random'

    def _is_dress_category(self, category: str) -> bool:
        """Check if the category is dress/outfit-related."""
        dress_categories = [
            'new_look', 'new_look_women', 'new_look_men', 
            'new_look_random'
        ]
        return category in dress_categories

    def _get_dress_category_from_original(self, original_category: str, gender: str) -> str:
        """Map original category to appropriate dress/outfit category based on gender."""
        if gender == 'men':
            return 'new_look_men'
        elif gender == 'women':
            return 'new_look_women'
        else:
            # Fallback to random gender outfit
            return 'new_look_random'

    async def _handle_repeat_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle repeat video button - repeat the same video generation, keep original message."""
        try:
            from generation_manager import generation_manager
            
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            # Remove buttons from the result message to prevent confusion
            try:
                await update.callback_query.edit_message_reply_markup(reply_markup=None)
                logger.info(f"🗑️ Removed buttons from result message for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to remove buttons from result message: {e}")
            
            # Get last processing parameters
            last_processing = context.user_data.get('last_processing')
            if not last_processing:
                await update.callback_query.answer("⚠️ No previous video to repeat", show_alert=True)
                return
            
            # Check if the last processing was a video
            if last_processing['category'] != "animate":
                await update.callback_query.answer("⚠️ Last operation was not a video", show_alert=True)
                return
            
            logger.info(f"User {user_id} requested repeat video")
            
            # Use the original option (not varied) for exact repeat
            original_option = last_processing['selected_option']
            
            # Use special retry method that doesn't remove the result message
            await generation_manager.retry_generation(
                update, context, last_processing['photo_file_id'], 
                last_processing['category'], original_option, user_lang
            )
            
            await update.callback_query.answer("🔄 Repeating video...")
            
        except Exception as e:
            logger.error(f"Error in repeat video handler: {e}")
            await update.callback_query.answer("❌ Error occurred", show_alert=True)
    
    async def _handle_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle edit button - use result image as base for new edits."""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            # Remove buttons from the result message to prevent confusion
            try:
                await update.callback_query.edit_message_reply_markup(reply_markup=None)
                logger.info(f"🗑️ Removed buttons from result message for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to remove buttons from result message: {e}")
            
            logger.info(f"User {user_id} requested edit (using result image)")
            
            # ENHANCED DEBUGGING FOR CHAINED EDITS
            logger.info(f"🔍 EDIT_BUTTON_DEBUG for user {user_id}:")
            logger.info(f"   - Current context current_photo: {context.user_data.get('current_photo')}")
            logger.info(f"   - Current context last_processing: {context.user_data.get('last_processing')}")
            logger.info(f"   - Message type: {type(update.callback_query.message)}")
            logger.info(f"   - Message has photo: {bool(update.callback_query.message.photo)}")
            if update.callback_query.message.photo:
                logger.info(f"   - Photo count: {len(update.callback_query.message.photo)}")
                logger.info(f"   - All photo file_ids: {[p.file_id for p in update.callback_query.message.photo]}")
            
            # Extract the result image from current message and set as new current_photo
            try:
                # Get the photo from the current message (result message)
                if update.callback_query.message.photo:
                    # Get the largest photo version (highest resolution)
                    result_photo = update.callback_query.message.photo[-1]
                    result_file_id = result_photo.file_id
                    
                    # ENHANCED LOGGING FOR FILE_ID TRACKING
                    logger.info(f"📷 EDIT_FILE_ID_EXTRACTION for user {user_id}:")
                    logger.info(f"   - Extracted file_id: '{result_file_id}'")
                    logger.info(f"   - File_id length: {len(result_file_id)}")
                    logger.info(f"   - Photo dimensions: {result_photo.width}x{result_photo.height}")
                    logger.info(f"   - File size: {getattr(result_photo, 'file_size', 'N/A')}")
                    logger.info(f"   - Previous current_photo: '{context.user_data.get('current_photo')}'")
                    
                    # Set this result image as the new current_photo for editing
                    context.user_data['current_photo'] = result_file_id
                    
                    # ALSO UPDATE last_processing to match for consistency
                    if 'last_processing' in context.user_data:
                        old_photo_id = context.user_data['last_processing'].get('photo_file_id')
                        context.user_data['last_processing']['photo_file_id'] = result_file_id
                        logger.info(f"🔄 EDIT_CONTEXT_UPDATE for user {user_id}:")
                        logger.info(f"   - Updated current_photo: {result_file_id}")
                        logger.info(f"   - Updated last_processing photo_file_id: {old_photo_id} → {result_file_id}")
                    
                    logger.info(f"📷 EDIT_MODE for user {user_id}:")
                    logger.info(f"   - Using result image as base: {result_file_id}")
                    logger.info(f"   - Result photo dimensions: {result_photo.width}x{result_photo.height}")
                    logger.info(f"   - File size: {getattr(result_photo, 'file_size', 'N/A')}")
                    
                    # Show enhancement menu as a reply using the result image as base
                    keyboard = self._get_enhancement_keyboard(user_lang, user_id)
                    
                    await update.callback_query.message.reply_text(
                        L.get("msg.photo_received", user_lang),
                        reply_markup=keyboard
                    )
                    
                    await update.callback_query.answer("✏️ Edit mode activated!")
                    
                else:
                    logger.warning(f"No photo found in result message for user {user_id}")
                    logger.error(f"🚨 EDIT_NO_PHOTO_ERROR for user {user_id}:")
                    logger.error(f"   - Message content: {update.callback_query.message}")
                    logger.error(f"   - Message photo: {update.callback_query.message.photo}")
                    logger.error(f"   - Message document: {getattr(update.callback_query.message, 'document', None)}")
                    logger.error(f"   - Message video: {getattr(update.callback_query.message, 'video', None)}")
                    await update.callback_query.answer("❌ No image to edit", show_alert=True)
                    
            except Exception as photo_error:
                logger.error(f"Error extracting result photo for user {user_id}: {photo_error}")
                logger.error(f"🚨 EDIT_EXTRACTION_ERROR for user {user_id}:")
                logger.error(f"   - Error type: {type(photo_error).__name__}")
                logger.error(f"   - Error message: {str(photo_error)}")
                import traceback
                logger.error(f"   - Full traceback: {traceback.format_exc()}")
                await update.callback_query.answer("❌ Error accessing image", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in edit handler: {e}")
            logger.error(f"🚨 EDIT_HANDLER_ERROR for user {user_id if 'user_id' in locals() else 'unknown'}:")
            logger.error(f"   - Error type: {type(e).__name__}")
            logger.error(f"   - Error message: {str(e)}")
            import traceback
            logger.error(f"   - Full traceback: {traceback.format_exc()}")
            await update.callback_query.answer("❌ Error occurred", show_alert=True)
    
    def _create_varied_option(self, category: str, original_option: dict, gender: str = 'neutral') -> dict:
        """Create a varied version of the selected option for repeat functionality."""
        try:
            from src.prompt_variations import prompt_variation_generator
            
            # Copy the original option
            varied_option = original_option.copy()
            
            label_key = varied_option.get('label_key', '')
            
            # Handle animation category (uses kling_prompt)
            if category == "animate":
                original_kling_prompt = varied_option.get('kling_prompt', '')
                varied_kling_prompt = prompt_variation_generator.get_varied_prompt(
                    category, label_key, original_kling_prompt, is_kling=True
                )
                varied_option['kling_prompt'] = varied_kling_prompt
                logger.info(f"Varied kling_prompt: '{original_kling_prompt}' → '{varied_kling_prompt}'")
            
            # Handle other categories (use prompt) with gender preservation
            else:
                original_prompt = varied_option.get('prompt', '')
                
                varied_prompt = prompt_variation_generator.get_varied_prompt(
                    category, label_key, original_prompt, is_kling=False, preserve_gender=gender
                )
                varied_option['prompt'] = varied_prompt
                logger.info(f"Varied prompt (gender: {gender}): '{original_prompt}' → '{varied_prompt}'")
            
            return varied_option
            
        except Exception as e:
            logger.error(f"Error creating varied option: {e}")
            # Return original option as fallback
            return original_option

    async def _handle_animate_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle animate result button - apply idle animation to the result image, keep original message."""
        try:
            from generation_manager import generation_manager
            
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            # Remove buttons from the result message to prevent confusion
            try:
                await update.callback_query.edit_message_reply_markup(reply_markup=None)
                logger.info(f"🗑️ Removed buttons from result message for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to remove buttons from result message: {e}")
            
            # Get last result URL from context.user_data instead of deprecated last_result
            last_processing = context.user_data.get('last_processing')
            if not last_processing or not last_processing.get('photo_file_id'):
                await update.callback_query.answer("⚠️ No result image to animate", show_alert=True)
                return
            
            logger.info(f"User {user_id} requested animation of result image")
            
            # Use special retry method that doesn't remove the result message (idle animation = empty prompt)
            animate_option = {'kling_prompt': ''}
            await generation_manager.retry_generation(
                update, context, last_processing['photo_file_id'], "animate", animate_option, user_lang
            )
            
            await update.callback_query.answer("📽 Animating...")
            
        except Exception as e:
            logger.error(f"Error in animate result handler: {e}")
            await update.callback_query.answer("❌ Error occurred", show_alert=True)
    
    async def _check_and_handle_auto_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Check for auto-resume flag and continue interrupted processing."""
        try:
            user_id = update.effective_user.id
            
            # Check if auto-resume is flagged
            auto_resume_key = f"user:{user_id}:auto_resume"
            if not redis_client.redis.get(auto_resume_key):
                return
            
            # Get auto-resume context from Redis
            auto_resume_context_key = f"user:{user_id}:auto_resume_context"
            auto_resume_data = redis_client.redis.hgetall(auto_resume_context_key)
            
            if not auto_resume_data:
                logger.warning(f"Auto-resume flag set but no context found for user {user_id}")
                redis_client.redis.delete(auto_resume_key)
                return
            
            # Parse auto-resume context
            auto_resume_context = {
                "photo_file_id": auto_resume_data.get("photo_file_id"),
                "category": auto_resume_data.get("category"),
                "selected_option": json.loads(auto_resume_data.get("selected_option", "{}")),
                "user_lang": auto_resume_data.get("user_lang"),
                "service_type": auto_resume_data.get("service_type"),
                "timestamp": auto_resume_data.get("timestamp")
            }
            
            logger.info(f"🔄 Auto-resuming processing for user {user_id}: {auto_resume_context['category']}")
            
            # Clean up auto-resume flag and context
            redis_client.redis.delete(auto_resume_key)
            redis_client.redis.delete(auto_resume_context_key)
            
            # Prepare processing context
            context.user_data['current_photo'] = auto_resume_context['photo_file_id']
            context.user_data['last_processing'] = {
                'photo_file_id': auto_resume_context['photo_file_id'],
                'category': auto_resume_context['category'],
                'selected_option': auto_resume_context['selected_option'],
                'user_id': user_id,
                'user_lang': auto_resume_context['user_lang'],
                'service_type': auto_resume_context['service_type']
            }
            
            # Check and consume quota for the resumed processing
            service_type = auto_resume_context['service_type']
            if not stars_billing.consume_quota(user_id, service_type, user_obj=update.effective_user):
                logger.error(f"Failed to consume quota for auto-resume for user {user_id}")
                await update.message.reply_text("❌ Failed to start processing. Please try again.")
                return
            
            # Start background processing
            asyncio.create_task(generation_manager._process_image_background(
                update.effective_chat.id,
                context.bot,
                auto_resume_context['photo_file_id'],
                auto_resume_context['category'],
                auto_resume_context['selected_option'],
                user_id,
                auto_resume_context['user_lang'],
                context,
                is_retry=False,
                processing_message=None
            ))
            
            logger.info(f"✅ Auto-resume processing started for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in auto-resume for user {update.effective_user.id}: {e}")
            # Clean up on error
            auto_resume_key = f"user:{update.effective_user.id}:auto_resume"
            auto_resume_context_key = f"user:{update.effective_user.id}:auto_resume_context"
            redis_client.redis.delete(auto_resume_key)
            redis_client.redis.delete(auto_resume_context_key)
    
    def run(self) -> None:
        """Start the bot."""
        logger.info("Starting Style Transfer Bot...")
        self.app.run_polling()


def main():
    """Main entry point."""
    global bot_instance
    
    parser = argparse.ArgumentParser(description="Style Transfer Telegram Bot")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Also check environment variable for debug mode
    debug_mode = args.debug or os.getenv("DEBUG", "false").lower() == "true"
    
    try:
        bot_instance = StyleTransferBot(debug=debug_mode)
        if debug_mode:
            logger.info("🐛 DEBUG MODE ENABLED - Debug commands available:")
            logger.info("  /debug_premium - Grant premium status")
            logger.info("  /debug_revoke - Revoke premium status")
        bot_instance.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)


# Global bot instance for access from other modules
bot_instance = None


if __name__ == "__main__":
    main() 