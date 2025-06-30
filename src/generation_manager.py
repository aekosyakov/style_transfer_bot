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
        logger.info(f"📞 Executing payment callback: {self.callback_func.__name__}")
        try:
            result = await self.callback_func(*self.args, **self.kwargs)
            logger.info(f"✅ Payment callback execution successful")
            return result
        except Exception as e:
            logger.error(f"❌ Payment callback execution failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
            logger.info(f"🚫 User {user_id} has insufficient FLUX quota, storing payment callback")
            callback = PaymentCallback(
                self.generate_image,
                update, context, photo_file_id, category, selected_option, user_lang, is_retry
            )
            self.pending_callbacks[user_id] = callback
            logger.info(f"💾 Stored payment callback for user {user_id}, total pending: {len(self.pending_callbacks)}")
            await self._show_payment_options(update, context, "flux")
            return False
        
        # 2. Consume quota
        logger.info(f"⚡ Attempting to consume FLUX quota for user {user_id}")
        if not stars_billing.consume_quota(user_id, "flux", user_obj=update.effective_user):
            logger.error(f"❌ Failed to consume FLUX quota for user {user_id}")
            await update.callback_query.edit_message_text("❌ Failed to process request. Please try again.")
            return False
        logger.info(f"✅ Successfully consumed FLUX quota for user {user_id}")
        
        # 3. Store processing context for retry functionality
        context.user_data['last_processing'] = {
            'photo_file_id': photo_file_id,
            'category': category,
            'selected_option': selected_option,
            'user_id': user_id,
            'user_lang': user_lang
        }
        
        # 4. Start generation
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
            logger.info(f"🚫 User {user_id} has insufficient KLING quota, storing payment callback")
            callback = PaymentCallback(
                self.generate_video,
                update, context, photo_file_id, animation_prompt, user_lang
            )
            self.pending_callbacks[user_id] = callback
            logger.info(f"💾 Stored payment callback for user {user_id}, total pending: {len(self.pending_callbacks)}")
            await self._show_payment_options(update, context, "kling")
            return False
        
        # 2. Consume quota
        logger.info(f"⚡ Attempting to consume KLING quota for user {user_id}")
        if not stars_billing.consume_quota(user_id, "kling", user_obj=update.effective_user):
            logger.error(f"❌ Failed to consume KLING quota for user {user_id}")
            await update.callback_query.edit_message_text("❌ Failed to process request. Please try again.")
            return False
        logger.info(f"✅ Successfully consumed KLING quota for user {user_id}")
        
        # 3. Store processing context for retry functionality
        context.user_data['last_processing'] = {
            'photo_file_id': photo_file_id,
            'category': 'animate',
            'selected_option': {'kling_prompt': animation_prompt},
            'user_id': user_id,
            'user_lang': user_lang
        }
        
        # 4. Start generation
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
        logger.info(f"💳 Payment success handler called for user {user_id}")
        
        callback = self.pending_callbacks.get(user_id)
        if callback:
            logger.info(f"✅ Found pending callback for user {user_id}, executing generation")
            # Remove callback and execute it
            del self.pending_callbacks[user_id]
            logger.info(f"🗑️ Removed callback for user {user_id}, remaining pending: {len(self.pending_callbacks)}")
            
            # Show processing message before starting generation
            user_lang = L.get_user_language(update.effective_user)
            logger.info(f"📱 Sending processing message to user {user_id}")
            await update.message.reply_text(f"⚡ {L.get('msg.processing', user_lang)}")
            
            logger.info(f"🚀 Executing payment callback for user {user_id}")
            try:
                await callback.execute()
                logger.info(f"✅ Successfully executed payment callback for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Failed to execute payment callback for user {user_id}: {e}")
                await update.message.reply_text("❌ Failed to start processing after payment. Please try again.")
        else:
            # No callback found - just show success message
            logger.warning(f"⚠️ No pending callback found for user {user_id} after payment")
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
            # Send new processing message
            processing_message = await self._send_processing_message(update, context, user_lang, "image")
            
            # Start background processing
            asyncio.create_task(self._process_image_background(
                update.effective_chat.id,
                context.bot,
                photo_file_id,
                category,
                selected_option,
                update.effective_user.id,
                user_lang,
                is_retry,
                processing_message
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
            # Send new processing message
            processing_message = await self._send_processing_message(update, context, user_lang, "video")
            
            # Start background processing
            asyncio.create_task(self._process_video_background(
                update.effective_chat.id,
                context.bot,
                photo_file_id,
                animation_prompt,
                update.effective_user.id,
                user_lang,
                processing_message
            ))
            
        except Exception as e:
            logger.error(f"Failed to start video processing: {e}")
            await update.callback_query.edit_message_text("❌ Failed to start processing. Please try again.")
    
    async def _send_processing_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_lang: str,
        generation_type: str
    ):
        """Send new processing message with appropriate chat action."""
        try:
            # Send chat action
            action = "record_video" if generation_type == "video" else "upload_photo"
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)
            
            # Send new processing message
            processing_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=L.get("msg.processing", user_lang)
            )
            return processing_message
        except Exception as e:
            logger.error(f"Failed to send processing message: {e}")
            return None
    
    async def _process_image_background(
        self,
        chat_id: int,
        bot,
        photo_file_id: str,
        category: str,
        selected_option: Dict[str, Any],
        user_id: int,
        user_lang: str,
        is_retry: bool = False,
        processing_message = None
    ) -> None:
        """Background image processing with automatic quota refund on failure."""
        logger.info(f"🖼️ Starting background image processing for user {user_id}, category: {category}, retry: {is_retry}")
        try:
            # Get photo URL
            logger.info(f"📁 Getting photo file for user {user_id}: {photo_file_id}")
            photo_file = await bot.get_file(photo_file_id)
            photo_url = photo_file.file_path
            logger.info(f"📁 Got photo URL for user {user_id}: {photo_url}")
            
            # Process based on category
            logger.info(f"⚙️ Starting image generation for user {user_id}, category: {category}")
            result_url = await self._generate_image_by_category(
                photo_url, category, selected_option, user_id, is_retry
            )
            
            if result_url:
                logger.info(f"✅ Image generation successful for user {user_id}: {result_url}")
                # Delete processing message before sending result
                if processing_message:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=processing_message.message_id)
                        logger.info(f"🗑️ Deleted processing message for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete processing message: {e}")
                
                # Send success result
                await self._send_image_result(bot, chat_id, result_url, user_lang, category, selected_option)
                logger.info(f"📤 Sent image result to user {user_id}")
            else:
                logger.error(f"❌ Image generation failed for user {user_id} (empty result)")
                # Delete processing message on error
                if processing_message:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=processing_message.message_id)
                        logger.info(f"🗑️ Deleted processing message for user {user_id} (error)")
                    except Exception as e:
                        logger.warning(f"Failed to delete processing message: {e}")
                
                # Processing failed - quota already refunded by safe_generate
                await bot.send_message(chat_id, L.get("msg.error", user_lang))
                
        except Exception as e:
            logger.error(f"❌ Image processing exception for user {user_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Delete processing message on exception
            if processing_message:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=processing_message.message_id)
                    logger.info(f"🗑️ Deleted processing message for user {user_id} (exception)")
                except Exception as delete_e:
                    logger.warning(f"Failed to delete processing message: {delete_e}")
            
            # Refund quota on exception
            stars_billing.refund_quota(user_id, "flux", 1)
            logger.info(f"💰 Refunded FLUX quota for user {user_id} due to exception")
            await bot.send_message(chat_id, L.get("msg.error_occurred", user_lang))
    
    async def _process_video_background(
        self,
        chat_id: int,
        bot,
        photo_file_id: str,
        animation_prompt: str,
        user_id: int,
        user_lang: str,
        processing_message = None
    ) -> None:
        """Background video processing with automatic quota refund on failure."""
        logger.info(f"🎬 Starting background video processing for user {user_id}, prompt: {animation_prompt}")
        try:
            # Get photo URL
            logger.info(f"📁 Getting photo file for user {user_id}: {photo_file_id}")
            photo_file = await bot.get_file(photo_file_id)
            photo_url = photo_file.file_path
            logger.info(f"📁 Got photo URL for user {user_id}: {photo_url}")
            
            # Generate video
            logger.info(f"⚙️ Starting video generation for user {user_id}")
            result_url = await stars_billing.safe_generate(
                user_id, "kling",
                kling_api.animate_by_prompt, photo_url, animation_prompt
            )
            
            if result_url:
                logger.info(f"✅ Video generation successful for user {user_id}: {result_url}")
                # Delete processing message before sending result
                if processing_message:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=processing_message.message_id)
                        logger.info(f"🗑️ Deleted processing message for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete processing message: {e}")
                
                # Send success result
                await self._send_video_result(bot, chat_id, result_url, user_lang)
                logger.info(f"📤 Sent video result to user {user_id}")
            else:
                logger.error(f"❌ Video generation failed for user {user_id} (empty result)")
                # Delete processing message on error
                if processing_message:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=processing_message.message_id)
                        logger.info(f"🗑️ Deleted processing message for user {user_id} (error)")
                    except Exception as e:
                        logger.warning(f"Failed to delete processing message: {e}")
                
                # Processing failed - quota already refunded by safe_generate
                await bot.send_message(chat_id, L.get("msg.error", user_lang))
                
        except Exception as e:
            logger.error(f"❌ Video processing exception for user {user_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Delete processing message on exception
            if processing_message:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=processing_message.message_id)
                    logger.info(f"🗑️ Deleted processing message for user {user_id} (exception)")
                except Exception as delete_e:
                    logger.warning(f"Failed to delete processing message: {delete_e}")
            
            # Refund quota on exception
            stars_billing.refund_quota(user_id, "kling", 1)
            logger.info(f"💰 Refunded KLING quota for user {user_id} due to exception")
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
        """Send image result with retry, restart, and animate buttons."""
        keyboard = [
            [InlineKeyboardButton(L.get("btn.retry", user_lang), callback_data="retry")],
            [InlineKeyboardButton(L.get("btn.restart", user_lang), callback_data="restart")],
            [InlineKeyboardButton(L.get("btn.animate", user_lang), callback_data="animate_result")]
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
        """Send video result with repeat and restart buttons."""
        keyboard = [
            [InlineKeyboardButton(L.get("btn.repeat", user_lang), callback_data="repeat_video")],
            [InlineKeyboardButton(L.get("btn.restart", user_lang), callback_data="restart")]
        ]
        
        # Video success message
        video_caption = f"🎬 {L.get('msg.video_ready', user_lang)}"
        
        try:
            await bot.send_animation(
                chat_id=chat_id,
                animation=result_url,
                caption=video_caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                has_spoiler=True
            )
        except Exception:
            # Fallback to video
            await bot.send_video(
                chat_id=chat_id,
                video=result_url,
                caption=video_caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                has_spoiler=True
            )


# Global instance
generation_manager = GenerationManager() 