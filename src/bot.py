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
            
            welcome_msg = (
                f"🎨 Welcome to Style Transfer Bot, {user.first_name}!\n\n"
                f"Transform your images with AI-powered enhancements:\n"
                f"• 🖌️ Style Transfer\n"
                f"• 👗 Object Editing\n"
                f"• ✏️ Text Modification\n"
                f"• 🌆 Background Swaps\n"
                f"• 🧑 Face Enhancement\n"
                f"• 📽 Image Animation\n\n"
                f"Send me a photo to get started!"
            )
            
            keyboard = self._get_main_menu_keyboard(user_lang, user.id)
            
            await update.message.reply_text(
                welcome_msg,
                reply_markup=keyboard
            )
            
            logger.info(f"User {user.id} started the bot")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Welcome! Send me a photo to enhance it with AI.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "🤖 *Style Transfer Bot Help*\n\n"
            "*How to use:*\n"
            "1. Send me any photo\n"
            "2. Choose enhancement type\n"
            "3. Select specific style/effect\n"
            "4. Wait for AI processing\n\n"
            "*Features:*\n"
            "🎨 Style Transfer - Apply artistic styles\n"
            "👗 Object Edit - Modify objects/clothing\n"
            "✏️ Text Edit - Change text in images\n"
            "🌆 Background Swap - Replace backgrounds\n"
            "🧑 Face Enhancement - Improve portraits\n"
            "📽 Animation - Bring images to life\n\n"
            "*Premium Benefits:*\n"
            "💎 Access to premium effects\n"
            "🚀 Priority processing\n"
            "✨ Higher quality results\n"
            "🎬 Longer animations\n\n"
            "Use /premium to upgrade!"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /premium command."""
        user_id = update.effective_user.id
        is_premium = redis_client.is_user_premium(user_id)
        
        if is_premium:
            await update.message.reply_text(
                "✨ You already have Premium access!\n"
                "Enjoy unlimited features and priority processing."
            )
        else:
            await self._show_premium_options(update, context)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        user_id = update.effective_user.id
        is_premium = redis_client.is_user_premium(user_id)
        
        status_text = f"👤 *User Status*\n\n"
        status_text += f"🆔 ID: `{user_id}`\n"
        status_text += f"💎 Premium: {'✅ Active' if is_premium else '❌ Not Active'}\n"
        
        if not is_premium:
            status_text += f"\n💡 Upgrade to Premium for unlimited access!"
        
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
                "🎨 Great photo! What would you like to do with it?",
                reply_markup=keyboard
            )
            
            logger.info(f"User {user_id} uploaded photo: {photo.file_id}")
            
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            await update.message.reply_text("Error processing photo. Please try again.")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages."""
        text = update.message.text.lower()
        
        if "help" in text:
            await self.help_command(update, context)
        elif "premium" in text:
            await self.premium_command(update, context)
        else:
            await update.message.reply_text(
                "Send me a photo to start enhancing it with AI! 📸"
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
                await query.edit_message_text("Unknown option selected.")
                
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
        
        keyboard = [
            [InlineKeyboardButton("📸 Upload Photo", callback_data="upload_prompt")],
            [InlineKeyboardButton("💎 Premium Features" if is_premium else "💎 Upgrade to Premium", 
                                callback_data="premium_info")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
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
            keyboard.append([InlineKeyboardButton("💎 Unlock All Features", callback_data="premium_info")])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show main menu."""
        user_lang = L.get_user_language(update.effective_user)
        keyboard = self._get_main_menu_keyboard(user_lang, update.effective_user.id)
        
        await update.callback_query.edit_message_text(
            "🎨 Style Transfer Bot - Main Menu",
            reply_markup=keyboard
        )
    
    async def _show_premium_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show premium subscription options."""
        premium_text = (
            "💎 *Premium Subscription*\n\n"
            "*Premium Features:*\n"
            "✨ All style effects unlocked\n"
            "🎬 Extended animations\n"
            "🚀 Priority processing\n"
            "🎨 Higher quality results\n"
            "👑 Exclusive premium styles\n\n"
            "*Choose your plan:*"
        )
        
        keyboard = [
            [InlineKeyboardButton("📅 Monthly - $9.99", callback_data="upgrade_monthly")],
            [InlineKeyboardButton("📅 Yearly - $59.99 (Save 50%!)", callback_data="upgrade_yearly")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
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
        is_premium = redis_client.is_user_premium(user_id)
        
        # Get available options for category
        options = config.get_category_options(category, is_premium)
        
        if not options:
            await update.callback_query.edit_message_text("No options available for this category.")
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
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_enhancements")])
        
        await update.callback_query.edit_message_text(
            f"Choose your {category.replace('_', ' ')} option:",
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
            
            # Get photo from context
            photo_file_id = context.user_data.get('current_photo')
            if not photo_file_id:
                await update.callback_query.edit_message_text(
                    "Please upload a photo first!"
                )
                return
            
            # Show processing message
            await update.callback_query.edit_message_text("🔄 Processing your image... This may take a moment!")
            
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
                    caption="✨ Your enhanced image is ready!"
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Processing failed. Please try again."
                )
                
        except Exception as e:
            logger.error(f"Error processing option selection: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred during processing."
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