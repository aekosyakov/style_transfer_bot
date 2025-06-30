"""
Clean Generation Manager - Single entry points for all image and video generation.
This replaces the complex scattered quota logic with simple, maintainable code.
"""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, Callable
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from stars_billing import stars_billing
from localization import L
from redis_client import redis_client
from flux_api import flux_api
from kling_api import kling_api

logger = logging.getLogger(__name__)


class PaymentCallback:
    """Simple payment callback system - no complex context storage."""
    
    def __init__(self, callback_func: Callable, *args, **kwargs):
        self.callback_func = callback_func
        self.args = args
        self.kwargs = kwargs
        self.created_at = datetime.now()
    
    async def execute(self):
        """Execute the stored callback."""
        try:
            return await self.callback_func(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(f"Payment callback execution failed: {e}")
            return None


class GenerationManager:
    """Single entry point for all image and video generation with clean quota management."""
    
    def __init__(self):
        self.pending_callbacks = {}  # user_id -> PaymentCallback
    
    async def generate_image(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        photo_file_id: str,
        category: str,
        selected_option: Dict[str, Any],
        user_lang: str,
        is_retry: bool = False
    ) -> bool:
        """
        Single entry point for ALL image generation.
        Returns True if generation started, False if payment needed.
        """
        user_id = update.effective_user.id
        
        # 1. Single quota check
        if not stars_billing.has_quota(user_id, "flux", user_obj=update.effective_user):
            # Store payment callback and show payment options
            callback = PaymentCallback(
                self.generate_image,
                update, context, photo_file_id, category, selected_option, user_lang, is_retry
            )
            self.pending_callbacks[user_id] = callback
            await self._show_payment_options(update, context, "flux")
            return False
        
        # 2. Consume quota
        if not stars_billing.consume_quota(user_id, "flux", user_obj=update.effective_user):
            await update.callback_query.edit_message_text("❌ Failed to process request. Please try again.")
            return False
        
        # 3. Start generation
        await self._start_image_processing(
            update, context, photo_file_id, category, selected_option, user_lang, is_retry
        )
        return True
    
    async def generate_video(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        photo_file_id: str,
        animation_prompt: str,
        user_lang: str
    ) -> bool:
        """
        Single entry point for ALL video generation.
        Returns True if generation started, False if payment needed.
        """
        user_id = update.effective_user.id
        
        # 1. Single quota check
        if not stars_billing.has_quota(user_id, "kling", user_obj=update.effective_user):
            # Store payment callback and show payment options
            callback = PaymentCallback(
                self.generate_video,
                update, context, photo_file_id, animation_prompt, user_lang
            )
            self.pending_callbacks[user_id] = callback
            await self._show_payment_options(update, context, "kling")
            return False
        
        # 2. Consume quota
        if not stars_billing.consume_quota(user_id, "kling", user_obj=update.effective_user):
            await update.callback_query.edit_message_text("❌ Failed to process request. Please try again.")
            return False
        
        # 3. Start generation
        await self._start_video_processing(
            update, context, photo_file_id, animation_prompt, user_lang
        )
        return True
    
    async def handle_payment_success(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle successful payment - execute stored callback."""
        user_id = update.effective_user.id
        
        callback = self.pending_callbacks.get(user_id)
        if callback:
            # Remove callback and execute it
            del self.pending_callbacks[user_id]
            await callback.execute()
        else:
            # No callback found - just show success message
            await update.message.reply_text("✅ Payment successful! Send a photo to start.")
    
    async def _show_payment_options(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        service: str
    ) -> None:
        """Show payment options when quota is insufficient."""
        user_lang = L.get_user_language(update.effective_user)
        service_name = "style" if service == "flux" else "video"
        
        text = f"🚫 No credits left for {service_name} generation today. Get more:"
        
        # Get pricing dynamically
        extra_price = stars_billing.payg_prices[f'{service}_extra']['price_stars']
        pro_pass_price = stars_billing.passes["pro_1day"]["price_stars"]
        creator_pass_price = stars_billing.passes["creator_7day"]["price_stars"]
        
        keyboard = [
            [InlineKeyboardButton(f"Extra {service_name.title()} {extra_price}⭐", callback_data=f"buy_payg_{service}_extra")],
            [InlineKeyboardButton(f"1-Day Pass {pro_pass_price}⭐", callback_data="buy_pass_pro_1day")],
            [InlineKeyboardButton(f"7-Day Pass {creator_pass_price}⭐", callback_data="buy_pass_creator_7day")]
        ]
        
        try:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            if "no text in the message to edit" in str(e).lower():
                await update.callback_query.edit_message_caption(
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                raise e
    
    async def _start_image_processing(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        photo_file_id: str,
        category: str,
        selected_option: Dict[str, Any],
        user_lang: str,
        is_retry: bool = False
    ) -> None:
        """Start image processing - clean implementation."""
        try:
            # Show processing message
            await self._show_processing_message(update, context, user_lang, "image")
            
            # Start background processing
            asyncio.create_task(self._process_image_background(
                update.effective_chat.id,
                context.bot,
                photo_file_id,
                category,
                selected_option,
                update.effective_user.id,
                user_lang,
                is_retry
            ))
            
        except Exception as e:
            logger.error(f"Failed to start image processing: {e}")
            await update.callback_query.edit_message_text("❌ Failed to start processing. Please try again.")
    
    async def _start_video_processing(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        photo_file_id: str,
        animation_prompt: str,
        user_lang: str
    ) -> None:
        """Start video processing - clean implementation."""
        try:
            # Show processing message
            await self._show_processing_message(update, context, user_lang, "video")
            
            # Start background processing
            asyncio.create_task(self._process_video_background(
                update.effective_chat.id,
                context.bot,
                photo_file_id,
                animation_prompt,
                update.effective_user.id,
                user_lang
            ))
            
        except Exception as e:
            logger.error(f"Failed to start video processing: {e}")
            await update.callback_query.edit_message_text("❌ Failed to start processing. Please try again.")
    
    async def _show_processing_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_lang: str,
        generation_type: str
    ) -> None:
        """Show processing message with appropriate chat action."""
        try:
            # Send chat action
            action = "record_video" if generation_type == "video" else "upload_photo"
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)
            
            # Show processing message
            await update.callback_query.edit_message_text(L.get("msg.processing", user_lang))
        except Exception as e:
            if "no text in the message to edit" in str(e).lower():
                await update.callback_query.edit_message_caption(
                    caption=L.get("msg.processing", user_lang)
                )
            else:
                raise e
    
    async def _process_image_background(
        self,
        chat_id: int,
        bot,
        photo_file_id: str,
        category: str,
        selected_option: Dict[str, Any],
        user_id: int,
        user_lang: str,
        is_retry: bool = False
    ) -> None:
        """Background image processing with automatic quota refund on failure."""
        try:
            # Get photo URL
            photo_file = await bot.get_file(photo_file_id)
            photo_url = photo_file.file_path
            
            # Process based on category
            result_url = await self._generate_image_by_category(
                photo_url, category, selected_option, user_id, is_retry
            )
            
            if result_url:
                # Send success result
                await self._send_image_result(bot, chat_id, result_url, user_lang, category, selected_option)
            else:
                # Processing failed - quota already refunded by safe_generate
                await bot.send_message(chat_id, L.get("msg.error", user_lang))
                
        except Exception as e:
            logger.error(f"Image processing error for user {user_id}: {e}")
            # Refund quota on exception
            stars_billing.refund_quota(user_id, "flux", 1)
            await bot.send_message(chat_id, L.get("msg.error_occurred", user_lang))
    
    async def _process_video_background(
        self,
        chat_id: int,
        bot,
        photo_file_id: str,
        animation_prompt: str,
        user_id: int,
        user_lang: str
    ) -> None:
        """Background video processing with automatic quota refund on failure."""
        try:
            # Get photo URL
            photo_file = await bot.get_file(photo_file_id)
            photo_url = photo_file.file_path
            
            # Generate video
            result_url = await stars_billing.safe_generate(
                user_id, "kling",
                kling_api.animate_by_prompt, photo_url, animation_prompt
            )
            
            if result_url:
                # Send success result
                await self._send_video_result(bot, chat_id, result_url, user_lang)
            else:
                # Processing failed - quota already refunded by safe_generate
                await bot.send_message(chat_id, L.get("msg.error", user_lang))
                
        except Exception as e:
            logger.error(f"Video processing error for user {user_id}: {e}")
            # Refund quota on exception
            stars_billing.refund_quota(user_id, "kling", 1)
            await bot.send_message(chat_id, L.get("msg.error_occurred", user_lang))
    
    async def _generate_image_by_category(
        self,
        photo_url: str,
        category: str,
        selected_option: Dict[str, Any],
        user_id: int,
        is_retry: bool = False
    ) -> Optional[str]:
        """Generate image based on category using safe_generate for auto-refund."""
        prompt = selected_option.get('prompt', '')
        
        # Use safe_generate to handle quota refund automatically
        if category in ["style_transfer", "cartoon", "anime", "comics", "art_styles"]:
            if is_retry:
                return await stars_billing.safe_generate(
                    user_id, "flux",
                    flux_api.process_image_with_variation, photo_url, prompt
                )
            else:
                return await stars_billing.safe_generate(
                    user_id, "flux",
                    flux_api.style_transfer, photo_url, prompt
                )
        
        elif category in ["new_look_women", "new_hairstyle", "new_hairstyle_women", "new_hairstyle_men", "new_hairstyle_random"]:
            if is_retry:
                return await stars_billing.safe_generate(
                    user_id, "flux",
                    flux_api.process_image_with_variation, photo_url, prompt
                )
            else:
                return await stars_billing.safe_generate(
                    user_id, "flux",
                    flux_api.edit_object, photo_url, prompt
                )
        
        elif category == "change_background":
            if is_retry:
                return await stars_billing.safe_generate(
                    user_id, "flux",
                    flux_api.process_image_with_variation, photo_url, prompt
                )
            else:
                return await stars_billing.safe_generate(
                    user_id, "flux",
                    flux_api.swap_background, photo_url, prompt
                )
        
        else:
            logger.warning(f"Unknown category: {category}")
            return None
    
    async def _send_image_result(
        self,
        bot,
        chat_id: int,
        result_url: str,
        user_lang: str,
        category: str,
        selected_option: Dict[str, Any]
    ) -> None:
        """Send image result with retry and animate buttons."""
        keyboard = [
            [
                InlineKeyboardButton(L.get("btn.retry", user_lang), callback_data="btn.retry"),
                InlineKeyboardButton(L.get("btn.animate", user_lang), callback_data="btn.animate")
            ],
            [InlineKeyboardButton(L.get("btn.new_photo", user_lang), callback_data="main_menu")]
        ]
        
        await bot.send_photo(
            chat_id=chat_id,
            photo=result_url,
            caption=L.get("msg.success", user_lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            has_spoiler=True
        )
    
    async def _send_video_result(
        self,
        bot,
        chat_id: int,
        result_url: str,
        user_lang: str
    ) -> None:
        """Send video result."""
        keyboard = [
            [InlineKeyboardButton(L.get("btn.new_photo", user_lang), callback_data="main_menu")]
        ]
        
        try:
            await bot.send_animation(
                chat_id=chat_id,
                animation=result_url,
                caption=L.get("msg.success", user_lang),
                reply_markup=InlineKeyboardMarkup(keyboard),
                has_spoiler=True
            )
        except Exception:
            # Fallback to video
            await bot.send_video(
                chat_id=chat_id,
                video=result_url,
                caption=L.get("msg.success", user_lang),
                reply_markup=InlineKeyboardMarkup(keyboard),
                has_spoiler=True
            )


# Global instance
generation_manager = GenerationManager() 