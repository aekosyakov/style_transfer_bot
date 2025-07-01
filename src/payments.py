"""Payment processing for premium subscriptions."""

import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from src.config import config
from redis_client import redis_client
from localization import L

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Handle Telegram payments and premium subscriptions."""
    
    def __init__(self):
        self.provider_token = config.provider_token
        self.premium_prices = {
            "monthly": {"amount": 999, "duration_days": 30},    # $9.99
            "yearly": {"amount": 5999, "duration_days": 365},   # $59.99
        }
    
    async def create_premium_invoice(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        plan_type: str = "monthly"
    ) -> bool:
        """Create and send premium subscription invoice."""
        try:
            user_lang = L.get_user_language(update.effective_user)
            
            if not self.provider_token:
                logger.error("Provider token not configured")
                await update.message.reply_text(L.get("payment.system_unavailable", user_lang))
                return False
            
            plan = self.premium_prices.get(plan_type, self.premium_prices["monthly"])
            
            # Create price list
            prices = [LabeledPrice(
                label=L.get("payment.premium_subscription", user_lang), 
                amount=plan["amount"]
            )]
            
            payload = f"premium_{plan_type}_{update.effective_user.id}"
            
            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=L.get("payment.invoice_title", user_lang),
                description=L.get("payment.invoice_description", user_lang, duration=plan['duration_days']),
                payload=payload,
                provider_token=self.provider_token,
                currency="USD",
                prices=prices,
                start_parameter="premium_subscription"
            )
            
            logger.info(f"Sent premium invoice to user {update.effective_user.id}, plan: {plan_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create premium invoice: {e}")
            return False
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle successful payment and activate premium."""
        try:
            payment = update.message.successful_payment
            payload = payment.invoice_payload
            user_id = update.effective_user.id
            user_lang = L.get_user_language(update.effective_user)
            
            # Parse payload to get plan type
            parts = payload.split("_")
            if len(parts) >= 2 and parts[0] == "premium":
                plan_type = parts[1]
                plan = self.premium_prices.get(plan_type, self.premium_prices["monthly"])
                
                # Activate premium subscription
                redis_client.set_user_premium(user_id, is_premium=True, duration_days=plan["duration_days"])
                
                await update.message.reply_text(
                    L.get("payment.success_message", user_lang, 
                          plan_type=plan_type, duration=plan['duration_days'])
                )
                
                logger.info(f"Premium activated for user {user_id}, plan: {plan_type}")
                
        except Exception as e:
            logger.error(f"Error handling successful payment: {e}")


# Global payment processor instance
payment_processor = PaymentProcessor() 