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

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    
    async def _handle_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
        """Handle category selection."""
        category = data.replace("category_", "")
        user_id = update.effective_user.id
        user_lang = L.get_user_language(update.effective_user)
        is_premium = redis_client.is_user_premium(user_id)
        
        # Get available options for category
        options = config.get_category_options(category, is_premium)
        
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
            parts = data.split("_", 2)
            if len(parts) < 3:
                return
            
            category = parts[1]
            user_id = update.effective_user.id
            user_lang = L.get_user_language(update.effective_user)
            
            # Get photo from context
            photo_file_id = context.user_data.get('current_photo')
            if not photo_file_id:
                await update.callback_query.edit_message_text(
                    L.get("msg.upload_photo_first", user_lang)
                )
                return
            
            # Show processing message
            await update.callback_query.edit_message_text(L.get("msg.processing", user_lang))
            
            # Get photo URL
            photo_file = await context.bot.get_file(photo_file_id)
            photo_url = photo_file.file_path
            
            # Process based on category
            result_url = None
            if category == "style_transfer":
                result_url = await flux_api.style_transfer(photo_url, "watercolor painting")
            elif category == "animate":
                result_url = await kling_api.animate_with_breeze(photo_url)
            # Add other categories as needed
            
            if result_url:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=result_url,
                    caption=L.get("msg.success", user_lang)
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=L.get("msg.error", user_lang)
                )
                
        except Exception as e:
            logger.error(f"Error processing option selection: {e}")
            user_lang = L.get_user_language(update.effective_user)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=L.get("msg.error_occurred", user_lang)
            )
    
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
    
    try:
        bot = StyleTransferBot(debug=args.debug)
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 