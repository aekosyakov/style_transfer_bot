"""Stars-only billing system for Telegram Stars (XTR) payments."""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from redis_client import redis_client
from localization import L

logger = logging.getLogger(__name__)


class StarsBillingManager:
    """Handle Telegram Stars billing and pass management."""
    
    def __init__(self):
        # Pass prices and quotas (Stars, FLUX, Kling, margin)
        self.passes = {
            "pro_1day": {
                "price_stars": 499,
                "flux_quota": 50,
                "kling_quota": 10,
                "duration_hours": 24,
                "margin_percent": 61.8,
                "name_key": "billing.pass.pro_1day"
            },
            "creator_7day": {
                "price_stars": 2999,
                "flux_quota": 500,
                "kling_quota": 50,
                "duration_hours": 24 * 7,
                "margin_percent": 42.5,
                "name_key": "billing.pass.creator_7day"
            },
            "studio_30day": {
                "price_stars": 9999,
                "flux_quota": 2000,
                "kling_quota": 200,
                "duration_hours": 24 * 30,
                "margin_percent": 31.1,
                "name_key": "billing.pass.studio_30day"
            }
        }
        
        # Pay-as-you-go prices
        self.payg_prices = {
            "flux_extra": {
                "price_stars": 25,
                "quota": 1,
                "margin_percent": 88,
                "name_key": "billing.payg.flux_extra"
            },
            "kling_extra": {
                "price_stars": 50,
                "quota": 1,
                "margin_percent": 92,
                "name_key": "billing.payg.kling_extra"
            }
        }
    
    def get_user_pass_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's active pass information."""
        try:
            pass_key = f"user:{user_id}:pass"
            pass_data = redis_client.redis.hgetall(pass_key)
            
            if not pass_data:
                return None
            
            # Parse the data
            pass_info = {
                "pass_type": pass_data.get("pass_type"),
                "expires_at": pass_data.get("expires_at"),
                "flux_quota": int(pass_data.get("flux_quota", 0)),
                "kling_quota": int(pass_data.get("kling_quota", 0)),
                "purchased_at": pass_data.get("purchased_at")
            }
            
            # Check if pass is still valid
            if pass_info["expires_at"]:
                expires_dt = datetime.fromisoformat(pass_info["expires_at"])
                if datetime.now() >= expires_dt:
                    # Pass expired, clean up
                    self._cleanup_expired_pass(user_id)
                    return None
            
            return pass_info
            
        except Exception as e:
            logger.error(f"Error getting pass info for user {user_id}: {e}")
            return None
    
    def get_user_quota(self, user_id: int, service: str) -> int:
        """Get remaining quota for user (FLUX or Kling)."""
        try:
            quota_key = f"user:{user_id}:quota:{service}"
            quota = redis_client.redis.get(quota_key)
            return int(quota) if quota else 0
        except Exception as e:
            logger.error(f"Error getting {service} quota for user {user_id}: {e}")
            return 0
    
    def has_quota(self, user_id: int, service: str, amount: int = 1) -> bool:
        """Check if user has enough quota for service."""
        current_quota = self.get_user_quota(user_id, service)
        return current_quota >= amount
    
    def consume_quota(self, user_id: int, service: str, amount: int = 1) -> bool:
        """Consume quota for service. Returns True if successful."""
        try:
            quota_key = f"user:{user_id}:quota:{service}"
            
            # Use Redis transaction to ensure atomic decrement
            with redis_client.redis.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch(quota_key)
                        current_quota = pipe.get(quota_key)
                        current_quota = int(current_quota) if current_quota else 0
                        
                        if current_quota < amount:
                            pipe.unwatch()
                            return False
                        
                        pipe.multi()
                        pipe.decrby(quota_key, amount)
                        pipe.execute()
                        break
                        
                    except redis_client.redis.WatchError:
                        # Retry on watch error
                        continue
            
            logger.info(f"Consumed {amount} {service} quota for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error consuming {service} quota for user {user_id}: {e}")
            return False
    
    def refund_quota(self, user_id: int, service: str, amount: int = 1) -> bool:
        """Refund quota to user (for failed generations)."""
        try:
            quota_key = f"user:{user_id}:quota:{service}"
            redis_client.redis.incrby(quota_key, amount)
            logger.info(f"Refunded {amount} {service} quota to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error refunding {service} quota for user {user_id}: {e}")
            return False
    
    def activate_pass(self, user_id: int, pass_type: str) -> bool:
        """Activate a pass for user."""
        try:
            if pass_type not in self.passes:
                logger.error(f"Invalid pass type: {pass_type}")
                return False
            
            pass_info = self.passes[pass_type]
            expires_at = datetime.now() + timedelta(hours=pass_info["duration_hours"])
            
            # Store pass information
            pass_key = f"user:{user_id}:pass"
            pass_data = {
                "pass_type": pass_type,
                "expires_at": expires_at.isoformat(),
                "flux_quota": pass_info["flux_quota"],
                "kling_quota": pass_info["kling_quota"],
                "purchased_at": datetime.now().isoformat()
            }
            
            redis_client.redis.hset(pass_key, mapping=pass_data)
            redis_client.redis.expire(pass_key, int(pass_info["duration_hours"] * 3600))
            
            # Set quota counters with TTL
            flux_key = f"user:{user_id}:quota:flux"
            kling_key = f"user:{user_id}:quota:kling"
            
            redis_client.redis.setex(
                flux_key, 
                int(pass_info["duration_hours"] * 3600), 
                pass_info["flux_quota"]
            )
            redis_client.redis.setex(
                kling_key, 
                int(pass_info["duration_hours"] * 3600), 
                pass_info["kling_quota"]
            )
            
            logger.info(f"Activated {pass_type} pass for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating pass for user {user_id}: {e}")
            return False
    
    def add_payg_quota(self, user_id: int, service: str, amount: int) -> bool:
        """Add pay-as-you-go quota to user."""
        try:
            quota_key = f"user:{user_id}:quota:{service}"
            
            # Add quota with 30-day expiration
            current_quota = redis_client.redis.get(quota_key)
            if current_quota:
                # Extend existing quota
                redis_client.redis.incrby(quota_key, amount)
            else:
                # Create new quota with expiration
                redis_client.redis.setex(quota_key, 30 * 24 * 3600, amount)
            
            logger.info(f"Added {amount} {service} pay-as-you-go quota to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding payg quota for user {user_id}: {e}")
            return False
    
    def _cleanup_expired_pass(self, user_id: int) -> None:
        """Clean up expired pass data."""
        try:
            pass_key = f"user:{user_id}:pass"
            redis_client.redis.delete(pass_key)
            logger.info(f"Cleaned up expired pass for user {user_id}")
        except Exception as e:
            logger.error(f"Error cleaning up expired pass for user {user_id}: {e}")
    
    async def create_stars_invoice(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        item_type: str,
        item_id: str
    ) -> bool:
        """Create Telegram Stars invoice."""
        try:
            user_lang = L.get_user_language(update.effective_user)
            
            # Determine price and description
            if item_type == "pass":
                if item_id not in self.passes:
                    logger.error(f"Invalid pass ID: {item_id}")
                    return False
                
                item_info = self.passes[item_id]
                price = item_info["price_stars"]
                title = L.get(item_info["name_key"], user_lang)
                description = L.get("billing.pass_description", user_lang, 
                                   flux=item_info["flux_quota"], 
                                   kling=item_info["kling_quota"],
                                   duration=item_info["duration_hours"] // 24 if item_info["duration_hours"] >= 24 else f"{item_info['duration_hours']}h")
                
            elif item_type == "payg":
                if item_id not in self.payg_prices:
                    logger.error(f"Invalid payg ID: {item_id}")
                    return False
                
                item_info = self.payg_prices[item_id]
                price = item_info["price_stars"]
                title = L.get(item_info["name_key"], user_lang)
                description = L.get("billing.payg_description", user_lang)
                
            else:
                logger.error(f"Invalid item type: {item_type}")
                return False
            
            # Create payload for tracking
            payload = f"stars_{item_type}_{item_id}_{update.effective_user.id}"
            
            # Send Stars invoice
            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=title,
                description=description,
                payload=payload,
                currency="XTR",  # Telegram Stars currency
                prices=[{"label": title, "amount": price}],
                start_parameter="stars_billing"
            )
            
            logger.info(f"Sent Stars invoice to user {update.effective_user.id}: {item_type}_{item_id}, price: {price} ⭐")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Stars invoice: {e}")
            await update.message.reply_text(
                L.get("billing.system_unavailable", user_lang)
            )
            return False
    
    async def handle_successful_stars_payment(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle successful Stars payment."""
        try:
            if not update.message.successful_payment:
                logger.error("No successful payment in update")
                return
            
            payment = update.message.successful_payment
            payload = payment.invoice_payload
            user_id = update.effective_user.id
            user_lang = L.get_user_language(update.effective_user)
            
            # Parse payload
            parts = payload.split("_")
            if len(parts) < 4 or parts[0] != "stars":
                logger.error(f"Invalid Stars payment payload: {payload}")
                return
            
            item_type = parts[1]  # "pass" or "payg"
            item_id = parts[2]    # pass/payg identifier
            
            success = False
            
            if item_type == "pass":
                success = self.activate_pass(user_id, item_id)
                if success:
                    pass_info = self.passes[item_id]
                    # Get pass duration for display
                    hours = pass_info["duration_hours"]
                    if hours >= 24:
                        days = hours // 24
                        duration_text = f"{days}-Day" if days == 1 else f"{days}-Day"
                    else:
                        duration_text = f"{hours}-Hour"
                    
                    # Create success message with specific format
                    success_msg = (
                        f"💎 {duration_text} Pro activated until 23:59 UTC!\n"
                        f"{pass_info['flux_quota']} style / {pass_info['kling_quota']} video credits now available.\n"
                        f"Send a photo to start."
                    )
                    
                    await update.message.reply_text(success_msg)
                    
            elif item_type == "payg":
                payg_info = self.payg_prices[item_id]
                service = "flux" if "flux" in item_id else "kling"
                success = self.add_payg_quota(user_id, service, payg_info["quota"])
                if success:
                    service_name = "style" if service == "flux" else "video"
                    success_msg = (
                        f"⚡ +{payg_info['quota']} {service_name} credit added!\n"
                        f"Total: {self.get_user_quota(user_id, service)} credits available.\n"
                        f"Send a photo to start."
                    )
                    await update.message.reply_text(success_msg)
            
            if not success:
                # Refund should be handled by Telegram automatically for Stars
                logger.error(f"Failed to process Stars payment for user {user_id}")
                await update.message.reply_text(
                    L.get("billing.processing_error", user_lang)
                )
            
        except Exception as e:
            logger.error(f"Error handling successful Stars payment: {e}")
    
    async def show_billing_menu(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show main billing/purchase menu."""
        try:
            user_id = update.effective_user.id
            user_lang = L.get_user_language(update.effective_user)
            
            # Get current pass info
            pass_info = self.get_user_pass_info(user_id)
            flux_quota = self.get_user_quota(user_id, "flux")
            kling_quota = self.get_user_quota(user_id, "kling")
            
            # Build status message
            if pass_info:
                expires_dt = datetime.fromisoformat(pass_info["expires_at"])
                time_left = expires_dt - datetime.now()
                days_left = max(0, time_left.days)
                hours_left = max(0, time_left.seconds // 3600)
                
                status_text = L.get("billing.current_status", user_lang,
                                   pass_name=L.get(self.passes[pass_info["pass_type"]]["name_key"], user_lang),
                                   days=days_left,
                                   hours=hours_left,
                                   flux=flux_quota,
                                   kling=kling_quota)
            else:
                status_text = L.get("billing.no_active_pass", user_lang,
                                   flux=flux_quota,
                                   kling=kling_quota)
            
            # Create keyboard
            keyboard = [
                [InlineKeyboardButton(L.get("billing.view_passes", user_lang), callback_data="billing_passes")],
                [InlineKeyboardButton(L.get("billing.buy_extra", user_lang), callback_data="billing_payg")],
                [InlineKeyboardButton(L.get("btn.back", user_lang), callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    status_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    status_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error showing billing menu: {e}")
    
    async def show_passes_menu(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show available passes for purchase."""
        try:
            user_lang = L.get_user_language(update.effective_user)
            
            text = L.get("billing.available_passes", user_lang)
            
            keyboard = []
            for pass_id, pass_info in self.passes.items():
                button_text = L.get("billing.pass_button", user_lang,
                                   name=L.get(pass_info["name_key"], user_lang),
                                   price=pass_info["price_stars"])
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"buy_pass_{pass_id}")])
            
            keyboard.append([InlineKeyboardButton(L.get("btn.back", user_lang), callback_data="billing_menu")])
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing passes menu: {e}")
    
    async def show_payg_menu(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show pay-as-you-go options."""
        try:
            user_lang = L.get_user_language(update.effective_user)
            
            text = L.get("billing.payg_options", user_lang)
            
            keyboard = []
            for payg_id, payg_info in self.payg_prices.items():
                service = "FLUX" if "flux" in payg_id else "Kling"
                button_text = f"{service} +{payg_info['quota']} - {payg_info['price_stars']} ⭐"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"buy_payg_{payg_id}")])
            
            keyboard.append([InlineKeyboardButton(L.get("btn.back", user_lang), callback_data="billing_menu")])
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing payg menu: {e}")
    
    async def check_quota_with_warnings(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        service: str
    ) -> str:
        """
        Check quota with gentle warnings and hard blocks.
        Returns: 'ok', 'gentle_warning', or 'hard_block'
        """
        user_id = update.effective_user.id
        current_quota = self.get_user_quota(user_id, service)
        
        if current_quota <= 0:
            # Hard block - no quota left
            await self._show_hard_block_upsell(update, context, service)
            return 'hard_block'
        elif current_quota <= 3:
            # Gentle warning - low quota
            await self._show_gentle_warning(update, context, service, current_quota)
            return 'gentle_warning'
        else:
            # All good
            return 'ok'
    
    async def check_quota_and_upsell(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        service: str
    ) -> bool:
        """Check quota and show upsell if needed. Returns True if quota available."""
        user_id = update.effective_user.id
        
        if self.has_quota(user_id, service):
            return True
        
        # No quota, show hard block
        await self._show_hard_block_upsell(update, context, service)
        return False
    
    async def _show_gentle_warning(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        service: str,
        remaining_quota: int
    ) -> None:
        """Show gentle warning when quota is low (≤3)."""
        try:
            user_lang = L.get_user_language(update.effective_user)
            service_name = "style" if service == "flux" else "video"
            
            text = f"⚡ You have only {remaining_quota} {service_name} credits left today."
            
            # Create invoice links for quick purchase
            keyboard = [
                [
                    InlineKeyboardButton("Buy 1-Day Pass — 499⭐", callback_data="buy_pass_pro_1day"),
                    InlineKeyboardButton(f"Extra {self.payg_prices[f'{service}_extra']['price_stars']} ⭐", callback_data=f"buy_payg_{service}_extra")
                ]
            ]
            
            # Use callback query edit to avoid spamming chat
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
        except Exception as e:
            logger.error(f"Error showing gentle warning: {e}")
    
    async def _show_hard_block_upsell(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        service: str
    ) -> None:
        """Show hard block when quota is depleted (≤0)."""
        try:
            user_lang = L.get_user_language(update.effective_user)
            service_name = "styles" if service == "flux" else "videos"
            
            text = f"🚫 No credits left for {service_name} today.\nGet more:"
            
            # Create invoice links for all options
            keyboard = [
                [InlineKeyboardButton(f"Extra Image {self.payg_prices[f'{service}_extra']['price_stars']}⭐", callback_data=f"buy_payg_{service}_extra")],
                [InlineKeyboardButton("1-Day Pass 499⭐", callback_data="buy_pass_pro_1day")],
                [InlineKeyboardButton("7-Day Pass 2,999⭐", callback_data="buy_pass_creator_7day")]
            ]
            
            # Use callback query edit to avoid spamming chat
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
        except Exception as e:
            logger.error(f"Error showing hard block upsell: {e}")
    
    async def _show_upsell_message(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        service: str
    ) -> None:
        """Show upsell message when quota is depleted."""
        # Redirect to hard block upsell
        await self._show_hard_block_upsell(update, context, service)
    
    async def safe_generate(
        self,
        user_id: int,
        service: str,
        generation_func,
        *args,
        **kwargs
    ) -> any:
        """
        Safely execute generation with automatic quota refund on failure.
        Args:
            user_id: User ID for quota management
            service: Service type ('flux' or 'kling')
            generation_func: Async function to call for generation
            *args, **kwargs: Arguments to pass to generation_func
        Returns:
            Result from generation_func or None if failed
        """
        try:
            logger.info(f"Safe generation started for user {user_id}, service {service}")
            result = await generation_func(*args, **kwargs)
            
            if result:
                logger.info(f"Safe generation succeeded for user {user_id}")
                return result
            else:
                logger.warning(f"Safe generation failed (empty result) for user {user_id}")
                # Refund quota on empty result
                self.refund_quota(user_id, service, 1)
                return None
                
        except Exception as e:
            logger.error(f"Safe generation exception for user {user_id}: {e}")
            # Refund quota on exception
            self.refund_quota(user_id, service, 1) 
            return None


# Global Stars billing manager instance
stars_billing = StarsBillingManager() 