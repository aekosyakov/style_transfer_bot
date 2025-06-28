#!/usr/bin/env python3
"""Main Telegram Style Transfer Bot."""

import os
import sys
import logging
import asyncio
import argparse
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, PreCheckoutQueryHandler
)

from config import config
from localization import L
from redis_client import redis_client
from flux_api import flux_api
from kling_api import kling_api
from payments import payment_processor

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StyleTransferBot:
    """Main bot class handling all operations."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
        
        self.app = Application.builder().token(config.bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Set up all bot handlers."""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("premium", self.premium_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        
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
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        try:
            user = update.effective_user
            user_lang = L.get_user_language(user)
            
            # Store user language preference
            redis_client.set_user_language(user.id, user_lang)
            
            welcome_msg = L.get("msg.welcome", user_lang, name=user.first_name)
            keyboard = self._get_main_menu_keyboard(user_lang, user.id)
            
            await update.message.reply_text(
                welcome_msg,
                reply_markup=keyboard
            )
            
            logger.info(f"User {user.id} started the bot")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            fallback_msg = L.get("msg.welcome_fallback", L.get_user_language(update.effective_user))
            await update.message.reply_text(fallback_msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        user_lang = L.get_user_language(update.effective_user)
        
        help_text = (
            f"{L.get('help.title', user_lang)}\n\n"
            f"{L.get('help.how_to_use', user_lang)}\n\n"
            f"{L.get('help.features', user_lang)}\n\n"
            f"{L.get('help.premium_benefits', user_lang)}\n\n"
            f"{L.get('help.upgrade_note', user_lang)}"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /premium command."""
        user_id = update.effective_user.id
        user_lang = L.get_user_language(update.effective_user)
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
        user_lang = L.get_user_language(update.effective_user)
        is_premium = redis_client.is_user_premium(user_id)
        
        status_text = f"{L.get('status.title', user_lang)}\n\n"
        status_text += f"{L.get('status.user_id', user_lang, user_id=user_id)}\n"
        
        if is_premium:
            status_text += L.get('status.premium_active', user_lang)
        else:
            status_text += L.get('status.premium_inactive', user_lang)
            status_text += L.get('status.upgrade_note', user_lang)
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def debug_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Debug command to grant premium status."""
        if not self.debug:
            return
        
        user_id = update.effective_user.id
        user_lang = L.get_user_language(update.effective_user)
        
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
            )
        else:
            await update.message.reply_text("❌ DEBUG: Failed to grant premium status")
    
    async def debug_revoke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Debug command to revoke premium status."""
        if not self.debug:
            return
        
        user_id = update.effective_user.id
        user_lang = L.get_user_language(update.effective_user)
        
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
            user_lang = L.get_user_language(update.effective_user)
            
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
            user_lang = L.get_user_language(update.effective_user)
            await update.message.reply_text(L.get("msg.error_photo", user_lang))
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages."""
        text = update.message.text.lower()
        user_lang = L.get_user_language(update.effective_user)
        
        if "help" in text:
            await self.help_command(update, context)
        elif "premium" in text:
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
            user_lang = L.get_user_language(update.effective_user)
            
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
            elif data.startswith("upgrade_"):
                plan_type = data.replace("upgrade_", "")
                await payment_processor.create_premium_invoice(update, context, plan_type)
            elif data.startswith("category_"):
                await self._handle_category_selection(update, context, data)
            elif data.startswith("option_"):
                await self._handle_option_selection(update, context, data)
            elif data.startswith("animate_"):
                await self._handle_animation_request(update, context, data)
            else:
                await query.edit_message_text(L.get("msg.unknown_option", user_lang))
                
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
            [InlineKeyboardButton(L.get("btn.style_transfer", lang), callback_data="category_style_transfer")],
            [InlineKeyboardButton(L.get("btn.object_edit", lang), callback_data="category_object_edit")],
            [InlineKeyboardButton(L.get("btn.text_edit", lang), callback_data="category_text_edit")],
            [InlineKeyboardButton(L.get("btn.background_swap", lang), callback_data="category_background_swap")],
            [InlineKeyboardButton(L.get("btn.face_enhance", lang), callback_data="category_face_enhance")],
            [InlineKeyboardButton(L.get("btn.animate", lang), callback_data="category_animate")],
        ]
        
        if not is_premium:
            keyboard.append([InlineKeyboardButton(L.get("btn.unlock_all_features", lang), callback_data="premium_info")])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show main menu."""
        user_lang = L.get_user_language(update.effective_user)
        keyboard = self._get_main_menu_keyboard(user_lang, update.effective_user.id)
        
        await update.callback_query.edit_message_text(
            L.get("msg.main_menu", user_lang),
            reply_markup=keyboard
        )
    
    async def _show_premium_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show premium subscription options."""
        user_lang = L.get_user_language(update.effective_user)
        
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
        user_lang = L.get_user_language(update.effective_user)
        user_id = update.effective_user.id
        keyboard = self._get_enhancement_keyboard(user_lang, user_id)
        
        await update.callback_query.edit_message_text(
            L.get("msg.photo_received", user_lang),
            reply_markup=keyboard
        )
    
    async def _show_upload_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show upload photo prompt."""
        user_lang = L.get_user_language(update.effective_user)
        
        await update.callback_query.edit_message_text(
            L.get("msg.photo_upload_prompt", user_lang)
        )
    
    async def _show_help_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help message."""
        user_lang = L.get_user_language(update.effective_user)
        
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
        user_lang = L.get_user_language(update.effective_user)
        is_premium = redis_client.is_user_premium(user_id)
        
        # Get available options for category (always show all options for better UX)
        options = config.get_category_options(category, is_premium, show_all=True)
        
        if not options:
            await update.callback_query.edit_message_text(L.get("msg.no_options", user_lang))
            return
        
        # Store category in context
        context.user_data['current_category'] = category
        
        # Create keyboard with options
        keyboard = []
        for option in options:
            keyboard.append([InlineKeyboardButton(
                option['label'], 
                callback_data=f"option_{category}_{hash(option['label'])}"
            )])
        
        keyboard.append([InlineKeyboardButton(L.get("btn.back", user_lang), callback_data="back_to_enhancements")])
        
        # Get localized category name
        category_name = L.get(f"category.{category}", user_lang)
        
        await update.callback_query.edit_message_text(
            L.get("msg.category_selection", user_lang, category=category_name),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
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
            user_lang = L.get_user_language(update.effective_user)
            is_premium = redis_client.is_user_premium(user_id)
            
            logger.info(f"User {user_id} selected category: {category}, option hash: {option_hash}")
            
            # Get the selected option details
            options = config.get_category_options(category, is_premium)
            selected_option = None
            for option in options:
                if str(hash(option['label'])) == option_hash:
                    selected_option = option
                    break
            
            if not selected_option:
                logger.error(f"Could not find selected option for hash {option_hash}")
                await update.callback_query.edit_message_text(
                    L.get("msg.error_occurred", user_lang)
                )
                return
            
            logger.info(f"Selected option: {selected_option}")
            
            # Check if this is a premium option and user has premium access
            option_label = selected_option['label']
            is_premium_option = config.is_premium_option(category, option_label)
            
            # Check if premium features are temporarily free for testing
            user_has_premium_access = is_premium or config.premium_features_free
            
            if config.premium_features_free and is_premium_option and not is_premium:
                logger.info(f"🎉 TESTING MODE: Granting free access to premium option {option_label} for user {user_id}")
            
            if is_premium_option and not user_has_premium_access:
                # User selected premium option but doesn't have premium access
                logger.info(f"User {user_id} tried to use premium option {option_label} without premium access")
                
                upgrade_text = (
                    f"🔒 **{option_label}** is a premium feature!\n\n"
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
                
                await update.callback_query.edit_message_text(
                    upgrade_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
            
            # Get photo from context
            photo_file_id = context.user_data.get('current_photo')
            if not photo_file_id:
                logger.warning(f"No photo found in context for user {user_id}")
                await update.callback_query.edit_message_text(
                    L.get("msg.upload_photo_first", user_lang)
                )
                return
            
            logger.info(f"Processing photo {photo_file_id} for user {user_id}")
            
            # Show processing message
            await update.callback_query.edit_message_text(L.get("msg.processing", user_lang))
            
            # Start background processing (non-blocking)
            asyncio.create_task(self._process_image_background(
                update.effective_chat.id,
                context.bot,
                photo_file_id,
                category,
                selected_option,
                user_id,
                user_lang
            ))
            
            logger.info(f"Started background processing for user {user_id}, category {category}")
                
        except Exception as e:
            logger.error(f"Error processing option selection: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            user_lang = L.get_user_language(update.effective_user)
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
        user_lang: str
    ) -> None:
        """Process image in background without blocking main bot handler."""
        try:
            logger.info(f"🚀 Background processing started for user {user_id}, category {category}")
            
            # Get photo URL
            try:
                photo_file = await bot.get_file(photo_file_id)
                photo_url = photo_file.file_path
                logger.info(f"Got photo URL: {photo_url}")
            except Exception as e:
                logger.error(f"Failed to get photo file: {e}")
                await bot.send_message(
                    chat_id=chat_id,
                    text=L.get("msg.error_occurred", user_lang)
                )
                return
            
            # Process based on category
            result_url = None
            try:
                logger.info(f"Starting {category} processing")
                
                if category == "style_transfer":
                    logger.info(f"Using FLUX API for style transfer: {selected_option['label']}")
                    style_prompt = selected_option['prompt']
                    result_url = await flux_api.style_transfer(photo_url, style_prompt)
                elif category == "object_edit":
                    logger.info(f"Using FLUX API for object editing: {selected_option['label']}")
                    edit_prompt = selected_option['prompt']
                    result_url = await flux_api.edit_object(photo_url, edit_prompt)
                elif category == "text_edit":
                    logger.info(f"Using FLUX API for text editing: {selected_option['label']}")
                    text_prompt = selected_option['prompt']
                    result_url = await flux_api.edit_text(photo_url, "old text", "new text")
                elif category == "background_swap":
                    logger.info(f"Using FLUX API for background swap: {selected_option['label']}")
                    bg_prompt = selected_option.get('bg_file', selected_option.get('prompt', 'beautiful landscape'))
                    result_url = await flux_api.swap_background(photo_url, bg_prompt)
                elif category == "face_enhance":
                    logger.info(f"Using FLUX API for face enhancement: {selected_option['label']}")
                    face_prompt = selected_option['prompt']
                    result_url = await flux_api.enhance_face(photo_url, face_prompt)
                elif category == "animate":
                    logger.info(f"Using Kling AI for animation: {selected_option['label']}")
                    animation_prompt = selected_option.get('kling_prompt', 'gentle animation')
                    result_url = await kling_api.animate_with_breeze(photo_url)
                else:
                    logger.warning(f"Unknown category: {category}")
                
                logger.info(f"Processing result for {category}: {result_url}")
                
            except Exception as e:
                logger.error(f"Error during {category} processing: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                result_url = None
            
            # Send result
            if result_url:
                logger.info(f"✅ Successfully processed image, sending result to user {user_id}")
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=result_url,
                    caption=L.get("msg.success", user_lang)
                )
            else:
                logger.error(f"❌ Processing failed for user {user_id}, category {category}")
                await bot.send_message(
                    chat_id=chat_id,
                    text=L.get("msg.error", user_lang)
                )
                
        except Exception as e:
            logger.error(f"Error in background processing for user {user_id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=L.get("msg.error_occurred", user_lang)
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
    
    async def _handle_animation_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
        """Handle animation requests."""
        # Implementation for animation handling
        pass
    
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