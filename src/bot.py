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
        
        # Debug commands (only in debug mode)
        if self.debug:
            self.app.add_handler(CommandHandler("debug_premium", self.debug_premium_command))
            self.app.add_handler(CommandHandler("debug_revoke", self.debug_revoke_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
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
            
            welcome_msg = L.get("msg.welcome", user_lang, name=user.first_name)
            keyboard = self._get_main_menu_keyboard(user_lang, user.id)
            
            await update.message.reply_text(
                welcome_msg,
                reply_markup=keyboard
                # Removed effect ID to prevent "Effect_id_invalid" crashes
            )
            
            logger.info(f"User {user.id} started the bot")
            
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
            f"📊 Status: {'💎 Premium' if redis_client.is_user_premium(user_id) else '🆓 Free'}\n\n"
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
            "• 💎 Permanent premium at 10 referrals\n\n"
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
            elif data == "restart":
                await self._handle_restart(update, context)
            elif data == "animate_result":
                await self._handle_animate_result(update, context)
            elif data.startswith("upgrade_"):
                plan_type = data.replace("upgrade_", "")
                await payment_processor.create_premium_invoice(update, context, plan_type)
            elif data.startswith("category_"):
                await self._handle_category_selection(update, context, data)
            elif data in ["new_look_men", "new_look_women", "new_look_random", "new_hairstyle_men", "new_hairstyle_women", "new_hairstyle_random"]:
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
        await payment_processor.handle_successful_payment(update, context)
    
    def _get_main_menu_keyboard(self, lang: str, user_id: int) -> InlineKeyboardMarkup:
        """Get main menu keyboard."""
        is_premium = redis_client.is_user_premium(user_id)
        
        premium_text = L.get("btn.premium_features", lang) if is_premium else L.get("btn.upgrade_to_premium", lang)
        
        keyboard = [
            [InlineKeyboardButton(L.get("btn.upload_photo", lang), callback_data="upload_prompt")],
            [InlineKeyboardButton(premium_text, callback_data="premium_info")],
            [InlineKeyboardButton(L.get("btn.help", lang), callback_data="help")],
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def _get_enhancement_keyboard(self, lang: str, user_id: int) -> InlineKeyboardMarkup:
        """Get enhancement options keyboard."""
        is_premium = redis_client.is_user_premium(user_id)
        
        keyboard = [
            [InlineKeyboardButton(L.get("btn.cartoon", lang), callback_data="category_cartoon")],
            [InlineKeyboardButton(L.get("btn.anime", lang), callback_data="category_anime")],
            [InlineKeyboardButton(L.get("btn.comics", lang), callback_data="category_comics")],
            [InlineKeyboardButton(L.get("btn.art_styles", lang), callback_data="category_art_styles")],
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
            
            # Get photo from context
            photo_file_id = context.user_data.get('current_photo')
            if not photo_file_id:
                logger.warning(f"No photo found in context for user {user_id}")
                try:
                    await update.callback_query.edit_message_text(
                        L.get("msg.upload_photo_first", user_lang)
                    )
                except Exception as e:
                    # If edit_message_text fails, it might be a photo message, try edit_message_caption
                    if "no text in the message to edit" in str(e).lower():
                        logger.info("Message has no text, trying to edit caption instead for upload photo message")
                        await update.callback_query.edit_message_caption(
                            caption=L.get("msg.upload_photo_first", user_lang)
                        )
                    else:
                        raise e
                return
            
            logger.info(f"Processing photo {photo_file_id} for user {user_id}")
            
            # Store processing parameters for retry functionality
            context.user_data['last_processing'] = {
                'photo_file_id': photo_file_id,
                'category': category,
                'selected_option': selected_option,
                'user_id': user_id,
                'user_lang': user_lang
            }
            
            # Show processing message
            try:
                await update.callback_query.edit_message_text(L.get("msg.processing", user_lang))
            except Exception as e:
                # If edit_message_text fails, it might be a photo message, try edit_message_caption
                if "no text in the message to edit" in str(e).lower():
                    logger.info("Message has no text, trying to edit caption instead for processing message")
                    await update.callback_query.edit_message_caption(
                        caption=L.get("msg.processing", user_lang)
                    )
                else:
                    raise e
            
            # Start background processing (non-blocking)
            asyncio.create_task(self._process_image_background(
                update.effective_chat.id,
                context.bot,
                photo_file_id,
                category,
                selected_option,
                user_id,
                user_lang,
                context
            ))
            
            logger.info(f"Started background processing for user {user_id}, category {category}")
                
        except Exception as e:
            logger.error(f"Error processing option selection: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            user_lang = self._get_user_language(update.effective_user)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=L.get("msg.error_occurred", user_lang)
            )
    
    async def _process_image_background(
        self, 
        chat_id: int, 
        bot, 
        photo_file_id: str, 
        category: str, 
        selected_option: dict, 
        user_id: int, 
        user_lang: str,
        context: ContextTypes.DEFAULT_TYPE,
        is_retry: bool = False,
        request_id: str = None
    ) -> None:
        """Process image in background without blocking main bot handler."""
        if not request_id:
            request_id = generate_request_id()
        
        start_time = time.time()
        option_identifier = selected_option.get('label_key', selected_option.get('label', 'unknown'))
        
        log_processing_step("background_processing_started", request_id, user_id, {
            "category": category,
            "option_identifier": option_identifier,
            "is_retry": is_retry,
            "photo_file_id": photo_file_id
        }, success=True)
        
        try:
            logger.info(f"🚀 Background processing started for user {user_id}, category {category}")
            
            # Get photo URL
            try:
                photo_file_start = time.time()
                
                # Use retry logic for get_file operation
                async def get_file_operation():
                    return await bot.get_file(photo_file_id)
                
                photo_file = await retry_telegram_request(get_file_operation)
                photo_url = photo_file.file_path
                photo_file_duration = time.time() - photo_file_start
                
                log_processing_step("get_photo_url", request_id, user_id, {
                    "photo_url": photo_url,
                    "duration": photo_file_duration
                }, success=True)
                
                logger.info(f"Got photo URL: {photo_url} (took {photo_file_duration:.2f}s)")
                
            except Exception as e:
                log_processing_step("get_photo_url", request_id, user_id, {
                    "photo_file_id": photo_file_id
                }, success=False, error=str(e))
                logger.error(f"Failed to get photo file: {e}")
                
                # Use retry logic for error message
                async def send_error_operation():
                    return await bot.send_message(
                        chat_id=chat_id,
                        text=L.get("msg.error_occurred", user_lang)
                    )
                
                try:
                    await retry_telegram_request(send_error_operation)
                except Exception as send_error:
                    logger.error(f"Failed to send error message after retries: {send_error}")
                return
            
            # Process based on category
            result_url = None
            api_start_time = time.time()
            
            try:
                log_processing_step("api_processing_started", request_id, user_id, {
                    "category": category,
                    "option_identifier": option_identifier,
                    "is_retry": is_retry
                }, success=True)
                
                logger.info(f"Starting {category} processing")
                
                if category in ["cartoon", "anime", "comics", "art_styles"]:
                    # Handle style transfer for new categorized styles
                    style_prompt = selected_option['prompt']
                    
                    # Handle special style prompts (like RANDOM_CARTOON, RANDOM_ANIME, etc.)
                    if self._is_style_option(selected_option):
                        style_prompt = self._generate_style_prompt(selected_option, is_retry, category)
                        logger.info(f"Generated {category} style prompt: {style_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{style_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": style_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for {category} style: {option_identifier}")
                    log_api_call(f"flux_{category}_style", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, style_prompt)
                    else:
                        result_url = await flux_api.style_transfer(photo_url, style_prompt)
                        
                elif category == "new_look_women":
                    # Handle women's dress/outfit changes
                    edit_prompt = selected_option['prompt']
                    
                    # Handle special dress prompts
                    if self._is_dress_option(selected_option):
                        edit_prompt = self._generate_dress_prompt(selected_option, is_retry)
                        logger.info(f"Generated women's dress prompt: {edit_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{edit_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": edit_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for women's outfit editing: {option_identifier}")
                    log_api_call("flux_womens_outfit_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, edit_prompt)
                    else:
                        result_url = await flux_api.edit_object(photo_url, edit_prompt)
                        
                elif category == "new_look_men":
                    # Handle men's outfit changes
                    edit_prompt = selected_option['prompt']
                    
                    # Handle special men's outfit prompts
                    if self._is_mens_outfit_option(selected_option):
                        edit_prompt = self._generate_mens_outfit_prompt(selected_option, is_retry)
                        logger.info(f"Generated men's outfit prompt: {edit_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{edit_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": edit_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for men's outfit editing: {option_identifier}")
                    log_api_call("flux_mens_outfit_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, edit_prompt)
                    else:
                        result_url = await flux_api.edit_object(photo_url, edit_prompt)
                        
                elif category == "new_look_random":
                    # Handle random gender outfit changes
                    edit_prompt = selected_option['prompt']
                    
                    # Handle random outfit generation (mix of men's and women's)
                    if 'RANDOM_ANY_OUTFIT' in edit_prompt or 'SURPRISE_OUTFIT' in edit_prompt:
                        import random
                        from src.dresses import dress_generator
                        from src.mens_outfits import mens_outfit_generator
                        
                        # Randomly choose between men's and women's outfits
                        if random.choice([True, False]):
                            edit_prompt = dress_generator.get_random_dress(include_color=True, include_material=True, include_effects=False)
                            logger.info(f"Generated random women's outfit: {edit_prompt}")
                        else:
                            edit_prompt = mens_outfit_generator.get_random_outfit(include_color=True, include_material=True, include_effects=False)
                            logger.info(f"Generated random men's outfit: {edit_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{edit_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": edit_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for random outfit editing: {option_identifier}")
                    log_api_call("flux_random_outfit_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, edit_prompt)
                    else:
                        result_url = await flux_api.edit_object(photo_url, edit_prompt)
                        
                elif category == "new_hairstyle":
                    # Handle hairstyle changes (legacy support)
                    edit_prompt = selected_option['prompt']
                    
                    # Handle special hairstyle prompts
                    if self._is_hairstyle_option(selected_option):
                        edit_prompt = self._generate_hairstyle_prompt(selected_option, is_retry)
                        logger.info(f"Generated hairstyle prompt: {edit_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{edit_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": edit_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for hairstyle editing: {option_identifier}")
                    log_api_call("flux_hairstyle_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, edit_prompt)
                    else:
                        result_url = await flux_api.edit_object(photo_url, edit_prompt)
                        
                elif category == "new_hairstyle_women":
                    # Handle women's hairstyle changes
                    edit_prompt = selected_option['prompt']
                    
                    # Handle special women's hairstyle prompts
                    if self._is_womens_hairstyle_option(selected_option):
                        edit_prompt = self._generate_womens_hairstyle_prompt(selected_option, is_retry)
                        logger.info(f"Generated women's hairstyle prompt: {edit_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{edit_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": edit_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for women's hairstyle editing: {option_identifier}")
                    log_api_call("flux_womens_hairstyle_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, edit_prompt)
                    else:
                        result_url = await flux_api.edit_object(photo_url, edit_prompt)
                        
                elif category == "new_hairstyle_men":
                    # Handle men's hairstyle changes
                    edit_prompt = selected_option['prompt']
                    
                    # Handle special men's hairstyle prompts
                    if self._is_mens_hairstyle_option(selected_option):
                        edit_prompt = self._generate_mens_hairstyle_prompt(selected_option, is_retry)
                        logger.info(f"Generated men's hairstyle prompt: {edit_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{edit_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": edit_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for men's hairstyle editing: {option_identifier}")
                    log_api_call("flux_mens_hairstyle_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, edit_prompt)
                    else:
                        result_url = await flux_api.edit_object(photo_url, edit_prompt)
                        
                elif category == "new_hairstyle_random":
                    # Handle random gender hairstyle changes
                    edit_prompt = selected_option['prompt']
                    
                    # Handle special random hairstyle prompts
                    if self._is_random_hairstyle_option(selected_option):
                        edit_prompt = self._generate_random_hairstyle_prompt(selected_option, is_retry)
                        logger.info(f"Generated random hairstyle prompt: {edit_prompt}")
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{edit_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": edit_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for random hairstyle editing: {option_identifier}")
                    log_api_call("flux_random_hairstyle_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, edit_prompt)
                    else:
                        result_url = await flux_api.edit_object(photo_url, edit_prompt)
                        
                elif category == "replace_text":
                    text_prompt = selected_option['prompt']
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{text_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": text_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for text editing: {option_identifier}")
                    log_api_call("flux_text_edit", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, text_prompt)
                    else:
                        result_url = await flux_api.edit_text(photo_url, "old text", "new text")
                        
                elif category == "change_background":
                    bg_prompt = selected_option.get('prompt', 'Change background to beautiful landscape')
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{bg_prompt}'")
                    
                    api_params = {"photo_url": photo_url, "prompt": bg_prompt, "is_retry": is_retry}
                    
                    logger.info(f"Using FLUX API for background change: {option_identifier}")
                    log_api_call("flux_background_swap", request_id, user_id, api_params)
                    
                    if is_retry:
                        result_url = await flux_api.process_image_with_variation(photo_url, bg_prompt)
                    else:
                        result_url = await flux_api.swap_background(photo_url, bg_prompt)
                        

                        
                elif category == "animate":
                    animation_prompt = selected_option.get('kling_prompt', '')
                    
                    # Log the EXACT prompt being sent to API
                    logger.info(f"📝 FINAL_PROMPT for {category}: '{animation_prompt}' (empty=idle animation)")
                    
                    api_params = {"photo_url": photo_url, "animation_prompt": animation_prompt}
                    
                    logger.info(f"Using Kling AI for animation: {option_identifier}")
                    log_api_call("kling_animate", request_id, user_id, api_params)
                    
                    result_url = await kling_api.animate_by_prompt(photo_url, animation_prompt)
                else:
                    logger.warning(f"Unknown category: {category}")
                    log_processing_step("unknown_category", request_id, user_id, {
                        "category": category
                    }, success=False, error="Unknown category")
                
                api_duration = time.time() - api_start_time
                
                if result_url:
                    log_api_call(f"{category}_api", request_id, user_id, api_params, 
                               duration=api_duration, success=True)
                    log_processing_step("api_processing_completed", request_id, user_id, {
                        "result_url": result_url,
                        "duration": api_duration
                    }, success=True)
                    logger.info(f"Processing result for {category}: {result_url} (took {api_duration:.2f}s)")
                else:
                    log_api_call(f"{category}_api", request_id, user_id, api_params, 
                               duration=api_duration, success=False, error="Empty result")
                    log_processing_step("api_processing_failed", request_id, user_id, {
                        "duration": api_duration
                    }, success=False, error="API returned empty result")
                    logger.warning(f"API returned empty result for {category} (took {api_duration:.2f}s)")
                
            except Exception as e:
                api_duration = time.time() - api_start_time
                error_msg = str(e)
                
                log_api_call(f"{category}_api", request_id, user_id, 
                           {"photo_url": photo_url, "category": category}, 
                           duration=api_duration, success=False, error=error_msg)
                log_processing_step("api_processing_exception", request_id, user_id, {
                    "duration": api_duration,
                    "exception_type": type(e).__name__
                }, success=False, error=error_msg)
                
                logger.error(f"Error during {category} processing: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                result_url = None
            
            # Send result
            if result_url:
                logger.info(f"✅ Successfully processed image, sending result to user {user_id}")
                
                # Store result URL in context for animation
                context.user_data['last_result'] = result_url
                
                # Create result action buttons
                keyboard = [
                    [
                        InlineKeyboardButton(L.get("btn.retry", user_lang), callback_data="retry"),
                        InlineKeyboardButton(L.get("btn.restart", user_lang), callback_data="restart")
                    ],
                    [InlineKeyboardButton(L.get("btn.animate_result", user_lang), callback_data="animate_result")]
                ]
                
                # Send result based on category type
                if category == "animate":
                    # Animation results should be sent as video/animation
                    logger.info(f"Sending animation result as video: {result_url}")
                    
                    # Try sending as animation first with retry logic
                    async def send_animation_operation():
                        return await bot.send_animation(
                            chat_id=chat_id,
                            animation=result_url,
                            caption=L.get("msg.success", user_lang),
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            has_spoiler=True
                        )
                    
                    try:
                        await retry_telegram_request(send_animation_operation)
                    except Exception as e:
                        logger.warning(f"Failed to send animation result as animation, trying as video: {e}")
                        
                        # Fallback: try as video with retry logic
                        async def send_video_operation():
                            return await bot.send_video(
                                chat_id=chat_id,
                                video=result_url,
                                caption=L.get("msg.success", user_lang),
                                reply_markup=InlineKeyboardMarkup(keyboard),
                                has_spoiler=True
                            )
                        
                        try:
                            await retry_telegram_request(send_video_operation)
                        except Exception as e2:
                            logger.error(f"Failed to send animation result as video, sending as document: {e2}")
                            
                            # Final fallback: send as document with retry logic
                            async def send_document_operation():
                                return await bot.send_document(
                                    chat_id=chat_id,
                                    document=result_url,
                                    caption=L.get("msg.success", user_lang) + " (Download to view)",
                                    reply_markup=InlineKeyboardMarkup(keyboard)
                                )
                            
                            try:
                                await retry_telegram_request(send_document_operation)
                            except Exception as e3:
                                logger.error(f"All animation sending methods failed: {e3}")
                                # Final fallback: send as text message
                                async def send_text_fallback():
                                    return await bot.send_message(
                                        chat_id=chat_id,
                                        text=f"🎬 {L.get('msg.success', user_lang)}\n📹 Animation: {result_url}",
                                        reply_markup=InlineKeyboardMarkup(keyboard)
                                    )
                                try:
                                    await retry_telegram_request(send_text_fallback)
                                except Exception as final_error:
                                    logger.error(f"Even text fallback failed: {final_error}")
                else:
                    # Regular image results with retry logic
                    async def send_photo_operation():
                        return await bot.send_photo(
                            chat_id=chat_id,
                            photo=result_url,
                            caption=L.get("msg.success", user_lang),
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            has_spoiler=True
                        )
                    
                    try:
                        await retry_telegram_request(send_photo_operation)
                    except Exception as e:
                        logger.error(f"Failed to send photo result after retries: {e}")
                        # Try sending as message instead
                        async def send_message_fallback():
                            return await bot.send_message(
                                chat_id=chat_id,
                                text=f"✅ {L.get('msg.success', user_lang)}\n🖼️ Result: {result_url}",
                                reply_markup=InlineKeyboardMarkup(keyboard)
                            )
                        try:
                            await retry_telegram_request(send_message_fallback)
                        except Exception as fallback_error:
                            logger.error(f"Even fallback message failed: {fallback_error}")
            else:
                logger.error(f"❌ Processing failed for user {user_id}, category {category}")
                
                # Use retry logic for failure message
                async def send_failure_operation():
                    return await bot.send_message(
                        chat_id=chat_id,
                        text=L.get("msg.error", user_lang)
                    )
                
                try:
                    await retry_telegram_request(send_failure_operation)
                except Exception as send_error:
                    logger.error(f"Failed to send failure message after retries: {send_error}")
                
        except Exception as e:
            logger.error(f"Error in background processing for user {user_id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Use retry logic for general error message
            async def send_general_error_operation():
                return await bot.send_message(
                    chat_id=chat_id,
                    text=L.get("msg.error_occurred", user_lang)
                )
            
            try:
                await retry_telegram_request(send_general_error_operation)
            except Exception as send_error:
                logger.error(f"Failed to send general error message after retries: {send_error}")
    
    def _is_dress_option(self, option: dict) -> bool:
        """Check if an option is a dress-related option."""
        option_identifier = option.get('label_key', '')
        return option_identifier.startswith('dress.')
    
    def _is_mens_outfit_option(self, option: dict) -> bool:
        """Check if an option is a men's outfit-related option."""
        option_identifier = option.get('label_key', '')
        return option_identifier.startswith('mens.')
    
    def _is_style_option(self, option: dict) -> bool:
        """Check if an option is a style-related option."""
        option_identifier = option.get('label_key', '')
        return (option_identifier.startswith('cartoon.') or 
                option_identifier.startswith('anime.') or 
                option_identifier.startswith('comics.') or 
                option_identifier.startswith('art.'))
    
    def _generate_style_prompt(self, option: dict, is_retry: bool = False, category: str = None) -> str:
        """Generate style prompt with random variations."""
        option_identifier = option.get('label_key', '')
        original_prompt = option.get('prompt', '')
        
        logger.info(f"Generating {category} style prompt for {option_identifier}, original: {original_prompt}")
        
        # Handle random styles by category
        if option_identifier == 'cartoon.random' or 'RANDOM_CARTOON' in original_prompt:
            cartoon_styles = [
                "Make this a retro classic cartoon",
                "Make this an 80s cartoon style",
                "Make this a 90s cartoon style", 
                "Make this a 2000s Disney/Pixar style",
                "Make this a modern 3D cartoon",
                "Make this a Saturday morning cartoon",
                "Make this a pixel art cartoon"
            ]
            import random
            generated_prompt = random.choice(cartoon_styles)
            logger.info(f"Generated random cartoon: {generated_prompt}")
            return generated_prompt
            
        elif option_identifier == 'anime.random' or 'RANDOM_ANIME' in original_prompt:
            anime_styles = [
                "Make this a magical girl/shojo anime style",
                "Make this a shōnen action anime style",
                "Make this a Studio Ghibli anime style",
                "Make this a 90s classic anime style",
                "Make this a chibi/kawaii anime style",
                "Make this a cyberpunk anime style",
                "Make this a webtoon/manhwa style",
                "Make this a princess/royal anime style"
            ]
            import random
            generated_prompt = random.choice(anime_styles)
            logger.info(f"Generated random anime: {generated_prompt}")
            return generated_prompt
            
        elif option_identifier == 'comics.random' or 'RANDOM_COMICS' in original_prompt:
            comic_styles = [
                "Make this a western comic book style",
                "Make this a newspaper comic strip style",
                "Make this a noir comic style",
                "Make this a black and white manga style",
                "Make this a pop art comic style",
                "Make this an adult animation style",
                "Make this a classic superhero comic style"
            ]
            import random
            generated_prompt = random.choice(comic_styles)
            logger.info(f"Generated random comic: {generated_prompt}")
            return generated_prompt
            
        elif option_identifier == 'art.random' or 'RANDOM_ART_STYLE' in original_prompt:
            art_styles = [
                "Make this a pencil sketch",
                "Make this digital art",
                "Make this pop art",
                "Make this an impressionist painting",
                "Make this a Renaissance painting",
                "Make this psychedelic art",
                "Make this Art Nouveau style",
                "Make this a vintage photo",
                "Make this sci-fi art",
                "Make this a Japanese woodblock print",
                "Make this film noir style"
            ]
            import random
            generated_prompt = random.choice(art_styles)
            logger.info(f"Generated random art style: {generated_prompt}")
            return generated_prompt
        else:
            # For specific style options, return the original prompt
            logger.info(f"Using original {category} style prompt: {original_prompt}")
            return original_prompt
    
    def _generate_dress_prompt(self, option: dict, is_retry: bool = False) -> str:
        """Generate dress prompt using DressGenerator."""
        from src.dresses import dress_generator
        
        option_identifier = option.get('label_key', '')
        original_prompt = option.get('prompt', '')
        
        logger.info(f"Generating dress prompt for {option_identifier}, original: {original_prompt}")
        
        if option_identifier == 'dress.random' or 'RANDOM_DRESS' in original_prompt:
            # Random dress generation
            generated_prompt = dress_generator.get_random_dress(include_color=True, include_material=True, include_effects=False)
            logger.info(f"Generated random dress: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'dress.casual_outfit':
            # Casual outfit change
            generated_prompt = dress_generator.get_casual_outfit()
            logger.info(f"Generated casual outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'dress.modern_dress' or 'MODERN_DRESS' in original_prompt:
            generated_prompt = dress_generator.get_dress_by_category("modern_trendy", include_color=True, include_material=True)
            logger.info(f"Generated modern dress: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'dress.classic_dress' or 'CLASSIC_DRESS' in original_prompt:
            generated_prompt = dress_generator.get_dress_by_category("classic_timeless", include_color=True, include_material=True)
            logger.info(f"Generated classic dress: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'dress.edgy_dress' or 'EDGY_DRESS' in original_prompt:
            generated_prompt = dress_generator.get_dress_by_category("edgy_statement", include_color=True, include_material=True)
            logger.info(f"Generated edgy dress: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'dress.evening_dress' or 'EVENING_DRESS' in original_prompt:
            generated_prompt = dress_generator.get_dress_by_category("evening_occasion", include_color=True, include_material=True)
            logger.info(f"Generated evening dress: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'dress.cultural_dress' or 'CULTURAL_DRESS' in original_prompt:
            generated_prompt = dress_generator.get_dress_by_category("cultural_traditional", include_color=True, include_material=True)
            logger.info(f"Generated cultural dress: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'dress.anime_dress' or 'ANIME_DRESS' in original_prompt:
            generated_prompt = dress_generator.get_dress_by_category("anime_inspired", include_color=True, include_material=True)
            logger.info(f"Generated anime dress: {generated_prompt}")
            return generated_prompt
        else:
            # Fallback for other dress options
            fallback_prompt = "change outfit to elegant dress, preserve original face and body proportions exactly"
            logger.info(f"Using fallback dress: {fallback_prompt}")
            return fallback_prompt
    
    def _generate_mens_outfit_prompt(self, option: dict, is_retry: bool = False) -> str:
        """Generate men's outfit prompt using MensOutfitGenerator."""
        from src.mens_outfits import mens_outfit_generator
        
        option_identifier = option.get('label_key', '')
        original_prompt = option.get('prompt', '')
        
        logger.info(f"Generating men's outfit prompt for {option_identifier}, original: {original_prompt}")
        
        if option_identifier == 'mens.random' or 'RANDOM_MENS_OUTFIT' in original_prompt:
            # Random men's outfit generation
            generated_prompt = mens_outfit_generator.get_random_outfit(include_color=True, include_material=True, include_effects=False)
            logger.info(f"Generated random men's outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'mens.casual_outfit' or 'CASUAL_MENS_OUTFIT' in original_prompt:
            # Casual men's outfit change
            generated_prompt = mens_outfit_generator.get_casual_outfit()
            logger.info(f"Generated casual men's outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'mens.modern_outfit' or 'MODERN_MENS_OUTFIT' in original_prompt:
            generated_prompt = mens_outfit_generator.get_outfit_by_category("modern_trendy", include_color=True, include_material=True)
            logger.info(f"Generated modern men's outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'mens.classic_outfit' or 'CLASSIC_MENS_OUTFIT' in original_prompt:
            generated_prompt = mens_outfit_generator.get_outfit_by_category("classic_timeless", include_color=True, include_material=True)
            logger.info(f"Generated classic men's outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'mens.edgy_outfit' or 'EDGY_MENS_OUTFIT' in original_prompt:
            generated_prompt = mens_outfit_generator.get_outfit_by_category("edgy_statement", include_color=True, include_material=True)
            logger.info(f"Generated edgy men's outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'mens.evening_outfit' or 'EVENING_MENS_OUTFIT' in original_prompt:
            generated_prompt = mens_outfit_generator.get_outfit_by_category("evening_occasion", include_color=True, include_material=True)
            logger.info(f"Generated evening men's outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'mens.cultural_outfit' or 'CULTURAL_MENS_OUTFIT' in original_prompt:
            generated_prompt = mens_outfit_generator.get_outfit_by_category("cultural_traditional", include_color=True, include_material=True)
            logger.info(f"Generated cultural men's outfit: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'mens.anime_outfit' or 'ANIME_MENS_OUTFIT' in original_prompt:
            generated_prompt = mens_outfit_generator.get_outfit_by_category("anime_inspired", include_color=True, include_material=True)
            logger.info(f"Generated anime men's outfit: {generated_prompt}")
            return generated_prompt
        else:
            # Fallback for other men's outfit options
            fallback_prompt = "change outfit to casual shirt and jeans, preserve original face and body proportions exactly"
            logger.info(f"Using fallback men's outfit: {fallback_prompt}")
            return fallback_prompt
    
    def _is_hairstyle_option(self, option: dict) -> bool:
        """Check if an option is a hairstyle-related option."""
        option_identifier = option.get('label_key', '')
        return option_identifier.startswith('hair.')
    
    def _is_womens_hairstyle_option(self, option: dict) -> bool:
        """Check if an option is a women's hairstyle-related option."""
        option_identifier = option.get('label_key', '')
        return option_identifier.startswith('hair.women_') or option_identifier.startswith('hair.color_only')
    
    def _is_mens_hairstyle_option(self, option: dict) -> bool:
        """Check if an option is a men's hairstyle-related option.""" 
        option_identifier = option.get('label_key', '')
        return option_identifier.startswith('hair.men_')
    
    def _is_random_hairstyle_option(self, option: dict) -> bool:
        """Check if an option is a random hairstyle-related option."""
        option_identifier = option.get('label_key', '')
        return option_identifier.startswith('hair.random_') or option_identifier.startswith('hair.surprise_')
    
    def _generate_hairstyle_prompt(self, option: dict, is_retry: bool = False) -> str:
        """Generate hairstyle prompt using HairstyleGenerator."""
        from src.hairstyles import hairstyle_generator
        
        option_identifier = option.get('label_key', '')
        original_prompt = option.get('prompt', '')
        
        logger.info(f"Generating hairstyle prompt for {option_identifier}, original: {original_prompt}")
        
        if option_identifier == 'hair.random' or 'RANDOM_HAIRSTYLE' in original_prompt:
            # Random hairstyle generation
            generated_prompt = hairstyle_generator.get_random_hairstyle(include_color=True, include_effects=False)
            logger.info(f"Generated random hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.color_only':
            # Color only change
            generated_prompt = hairstyle_generator.get_color_only_change()
            logger.info(f"Generated color change: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.modern_hairstyle' or 'MODERN_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_category("modern_trendy", include_color=True)
            logger.info(f"Generated modern hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.classic_hairstyle' or 'CLASSIC_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_category("classic_timeless", include_color=True)
            logger.info(f"Generated classic hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.edgy_hairstyle' or 'EDGY_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_category("edgy_statement", include_color=True)
            logger.info(f"Generated edgy hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.updo_hairstyle' or 'UPDO_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_category("updos_braids", include_color=True)
            logger.info(f"Generated updo hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.cultural_hairstyle' or 'CULTURAL_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_category("cultural_traditional", include_color=True)
            logger.info(f"Generated cultural hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.anime_hairstyle' or 'ANIME_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_category("anime_inspired", include_color=True)
            logger.info(f"Generated anime hairstyle: {generated_prompt}")
            return generated_prompt
        else:
            # Fallback for other hairstyle options
            fallback_prompt = "change hairstyle to modern bob cut, preserve original face and facial features exactly"
            logger.info(f"Using fallback hairstyle: {fallback_prompt}")
            return fallback_prompt
    
    def _generate_womens_hairstyle_prompt(self, option: dict, is_retry: bool = False) -> str:
        """Generate women's hairstyle prompt using HairstyleGenerator."""
        from src.hairstyles import hairstyle_generator
        
        option_identifier = option.get('label_key', '')
        original_prompt = option.get('prompt', '')
        
        logger.info(f"Generating women's hairstyle prompt for {option_identifier}, original: {original_prompt}")
        
        if option_identifier == 'hair.women_random' or 'RANDOM_WOMENS_HAIRSTYLE' in original_prompt:
            # Random women's hairstyle generation
            generated_prompt = hairstyle_generator.get_womens_hairstyle(include_color=True, include_effects=False)
            logger.info(f"Generated random women's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.color_only':
            # Color only change
            generated_prompt = hairstyle_generator.get_color_only_change()
            logger.info(f"Generated color change: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.women_modern' or 'MODERN_WOMENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("women", "modern_trendy", include_color=True)
            logger.info(f"Generated modern women's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.women_classic' or 'CLASSIC_WOMENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("women", "classic_timeless", include_color=True)
            logger.info(f"Generated classic women's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.women_edgy' or 'EDGY_WOMENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("women", "edgy_statement", include_color=True)
            logger.info(f"Generated edgy women's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.women_cultural' or 'CULTURAL_WOMENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("women", "cultural_traditional", include_color=True)
            logger.info(f"Generated cultural women's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.women_anime' or 'ANIME_WOMENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("women", "anime_inspired", include_color=True)
            logger.info(f"Generated anime women's hairstyle: {generated_prompt}")
            return generated_prompt
        else:
            # Fallback for other women's hairstyle options
            fallback_prompt = "change hairstyle to modern women's bob cut, preserve original face and facial features exactly"
            logger.info(f"Using fallback women's hairstyle: {fallback_prompt}")
            return fallback_prompt
    
    def _generate_mens_hairstyle_prompt(self, option: dict, is_retry: bool = False) -> str:
        """Generate men's hairstyle prompt using HairstyleGenerator."""
        from src.hairstyles import hairstyle_generator
        
        option_identifier = option.get('label_key', '')
        original_prompt = option.get('prompt', '')
        
        logger.info(f"Generating men's hairstyle prompt for {option_identifier}, original: {original_prompt}")
        
        if option_identifier == 'hair.men_random' or 'RANDOM_MENS_HAIRSTYLE' in original_prompt:
            # Random men's hairstyle generation
            generated_prompt = hairstyle_generator.get_mens_hairstyle(include_color=True, include_effects=False)
            logger.info(f"Generated random men's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.men_color_only':
            # Color only change for men
            generated_prompt = hairstyle_generator.get_color_only_change()
            logger.info(f"Generated men's color change: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.men_modern' or 'MODERN_MENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("men", "modern_trendy", include_color=True)
            logger.info(f"Generated modern men's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.men_classic' or 'CLASSIC_MENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("men", "classic_timeless", include_color=True)
            logger.info(f"Generated classic men's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.men_edgy' or 'EDGY_MENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("men", "edgy_statement", include_color=True)
            logger.info(f"Generated edgy men's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.men_cultural' or 'CULTURAL_MENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("men", "cultural_traditional", include_color=True)
            logger.info(f"Generated cultural men's hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.men_anime' or 'ANIME_MENS_HAIRSTYLE' in original_prompt:
            generated_prompt = hairstyle_generator.get_hairstyle_by_gender_and_category("men", "anime_inspired", include_color=True)
            logger.info(f"Generated anime men's hairstyle: {generated_prompt}")
            return generated_prompt
        else:
            # Fallback for other men's hairstyle options
            fallback_prompt = "change hairstyle to modern men's crew cut, preserve original face and facial features exactly"
            logger.info(f"Using fallback men's hairstyle: {fallback_prompt}")
            return fallback_prompt
    
    def _generate_random_hairstyle_prompt(self, option: dict, is_retry: bool = False) -> str:
        """Generate random gender hairstyle prompt using HairstyleGenerator."""
        from src.hairstyles import hairstyle_generator
        
        option_identifier = option.get('label_key', '')
        original_prompt = option.get('prompt', '')
        
        logger.info(f"Generating random hairstyle prompt for {option_identifier}, original: {original_prompt}")
        
        if option_identifier == 'hair.random_any' or 'RANDOM_ANY_HAIRSTYLE' in original_prompt:
            # Random gender hairstyle generation  
            generated_prompt = hairstyle_generator.get_random_gender_hairstyle(include_color=True, include_effects=False)
            logger.info(f"Generated random gender hairstyle: {generated_prompt}")
            return generated_prompt
        elif option_identifier == 'hair.surprise_me' or 'SURPRISE_HAIRSTYLE' in original_prompt:
            # Surprise hairstyle with random gender and effects
            generated_prompt = hairstyle_generator.get_random_gender_hairstyle(include_color=True, include_effects=True)
            logger.info(f"Generated surprise hairstyle: {generated_prompt}")
            return generated_prompt
        else:
            # Fallback to random gender hairstyle
            fallback_prompt = hairstyle_generator.get_random_gender_hairstyle(include_color=True, include_effects=False)
            logger.info(f"Using fallback random hairstyle: {fallback_prompt}")
            return fallback_prompt
    
    async def _handle_animation_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
        """Handle animation requests."""
        # Implementation for animation handling
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
            f"📊 Status: {'💎 Premium' if redis_client.is_user_premium(user_id) else '🆓 Free'}\n\n"
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
        """Handle retry button - repeat with similar but varied processing."""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            # Get last processing parameters
            last_processing = context.user_data.get('last_processing')
            if not last_processing:
                await update.callback_query.answer("⚠️ No previous processing to retry", show_alert=True)
                return
            
            logger.info(f"User {user_id} requested retry for {last_processing['category']}")
            
            # Create varied version of the selected option
            varied_option = self._create_varied_option(
                last_processing['category'],
                last_processing['selected_option']
            )
            
            # Show processing message
            await update.callback_query.edit_message_caption(
                caption=L.get("msg.processing", user_lang)
            )
            
            # Start background processing with variation (non-blocking)
            asyncio.create_task(self._process_image_background(
                update.effective_chat.id,
                context.bot,
                last_processing['photo_file_id'],
                last_processing['category'],
                varied_option,  # Use varied option instead of original
                user_id,
                user_lang,
                context,
                is_retry=True  # Flag to indicate this is a retry with variations
            ))
            
            await update.callback_query.answer("🔄 Creating new variation...")
            
        except Exception as e:
            logger.error(f"Error in retry handler: {e}")
            await update.callback_query.answer("❌ Error occurred", show_alert=True)
    
    async def _handle_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle restart button - show categories menu."""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            logger.info(f"User {user_id} requested restart")
            
            # Show enhancement menu
            keyboard = self._get_enhancement_keyboard(user_lang, user_id)
            
            await update.callback_query.edit_message_caption(
                caption=L.get("msg.photo_received", user_lang),
                reply_markup=keyboard
            )
            
            await update.callback_query.answer("🏠 Restarted!")
            
        except Exception as e:
            logger.error(f"Error in restart handler: {e}")
            await update.callback_query.answer("❌ Error occurred", show_alert=True)
    
    def _create_varied_option(self, category: str, original_option: dict) -> dict:
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
            
            # Handle other categories (use prompt)
            else:
                original_prompt = varied_option.get('prompt', '')
                varied_prompt = prompt_variation_generator.get_varied_prompt(
                    category, label_key, original_prompt, is_kling=False
                )
                varied_option['prompt'] = varied_prompt
                logger.info(f"Varied prompt: '{original_prompt}' → '{varied_prompt}'")
            
            return varied_option
            
        except Exception as e:
            logger.error(f"Error creating varied option: {e}")
            # Return original option as fallback
            return original_option

    async def _handle_animate_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle animate result button - apply idle animation to the result image."""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(update.effective_user)
            
            # Get last result URL
            last_result = context.user_data.get('last_result')
            if not last_result:
                await update.callback_query.answer("⚠️ No result image to animate", show_alert=True)
                return
            
            logger.info(f"User {user_id} requested animation of result image")
            
            # Show processing message
            await update.callback_query.edit_message_caption(
                caption="🎬 Creating idle animation... This may take a moment!"
            )
            
            # Start animation processing
            asyncio.create_task(self._animate_result_background(
                update.effective_chat.id,
                context.bot,
                last_result,
                user_id,
                user_lang
            ))
            
            await update.callback_query.answer("📽 Animating...")
            
        except Exception as e:
            logger.error(f"Error in animate result handler: {e}")
            await update.callback_query.answer("❌ Error occurred", show_alert=True)
    
    async def _animate_result_background(
        self, 
        chat_id: int, 
        bot, 
        result_image_url: str, 
        user_id: int, 
        user_lang: str
    ) -> None:
        """Animate result image in background."""
        try:
            logger.info(f"🎬 Starting idle animation for user {user_id}")
            
            # Apply idle animation (empty prompt)
            animation_result = await kling_api.animate_by_prompt(result_image_url, "", duration=5)
            
            if animation_result:
                logger.info(f"✅ Animation completed for user {user_id}")
                logger.info(f"Sending video URL: {animation_result}")
                
                try:
                    # Try sending as animation first (MP4/GIF) with retry logic
                    async def send_result_animation_operation():
                        return await bot.send_animation(
                            chat_id=chat_id,
                            animation=animation_result,
                            caption="🎬 Your animated result is ready!",
                            has_spoiler=True
                        )
                    
                    await retry_telegram_request(send_result_animation_operation)
                except Exception as e:
                    logger.warning(f"Failed to send as animation, trying as video: {e}")
                    
                    # Fallback: try as video with retry logic
                    async def send_result_video_operation():
                        return await bot.send_video(
                            chat_id=chat_id,
                            video=animation_result,
                            caption="🎬 Your animated result is ready!",
                            has_spoiler=True
                        )
                    
                    try:
                        await retry_telegram_request(send_result_video_operation)
                    except Exception as e2:
                        logger.error(f"Failed to send video, sending as document: {e2}")
                        
                        # Final fallback: send as document with retry logic
                        async def send_result_document_operation():
                            return await bot.send_document(
                                chat_id=chat_id,
                                document=animation_result,
                                caption="🎬 Your animated result is ready! (Download to view)"
                            )
                        
                        try:
                            await retry_telegram_request(send_result_document_operation)
                        except Exception as e3:
                            logger.error(f"All animation result sending methods failed: {e3}")
            else:
                logger.error(f"❌ Animation failed for user {user_id}")
                
                # Use retry logic for animation failure message
                async def send_animation_failure_operation():
                    return await bot.send_message(
                        chat_id=chat_id,
                        text="❌ Animation failed. Please try again later."
                    )
                
                try:
                    await retry_telegram_request(send_animation_failure_operation)
                except Exception as send_error:
                    logger.error(f"Failed to send animation failure message after retries: {send_error}")
                
        except Exception as e:
            logger.error(f"Error in background animation for user {user_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Use retry logic for animation error message
            async def send_animation_error_operation():
                return await bot.send_message(
                    chat_id=chat_id,
                    text="❌ Animation failed due to an error."
                )
            
            try:
                await retry_telegram_request(send_animation_error_operation)
            except Exception as send_error:
                logger.error(f"Failed to send animation error message after retries: {send_error}")
    
    def run(self) -> None:
        """Start the bot."""
        logger.info("Starting Style Transfer Bot...")
        self.app.run_polling()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Style Transfer Telegram Bot")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Also check environment variable for debug mode
    debug_mode = args.debug or os.getenv("DEBUG", "false").lower() == "true"
    
    try:
        bot = StyleTransferBot(debug=debug_mode)
        if debug_mode:
            logger.info("🐛 DEBUG MODE ENABLED - Debug commands available:")
            logger.info("  /debug_premium - Grant premium status")
            logger.info("  /debug_revoke - Revoke premium status")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 