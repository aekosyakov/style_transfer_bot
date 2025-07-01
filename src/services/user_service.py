"""User service for managing user language preferences and premium status."""

import logging
from typing import Optional
from src.redis_client import redis_client
from src.localization import L

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user-related functionality."""
    
    def __init__(self, redis_client=None, localization=None):
        # Use dependency injection for better testing
        if redis_client is None:
            from src.redis_client import redis_client as default_redis
            self.redis_client = default_redis
        else:
            self.redis_client = redis_client
            
        if localization is None:
            from src.localization import L as default_localization
            self.localization = default_localization
        else:
            self.localization = localization
    
    def get_user_language(self, telegram_user) -> str:
        """
        Get user's preferred language, checking Redis first, then Telegram detection.
        
        This method combines the functionality of:
        - _get_user_language() from bot.py (line 227)
        - redis_client.get_user_language() 
        - L.get_user_language() fallback
        
        Args:
            telegram_user: Telegram user object with id and language_code
            
        Returns:
            Language code (e.g., 'en', 'ru')
        """
        try:
            user_id = telegram_user.id
            
            # First check Redis for stored language preference
            stored_lang = self.redis_client.get_user_language(user_id)
            if stored_lang and stored_lang in self.localization.get_available_languages():
                logger.debug(f"Using stored language preference for user {user_id}: {stored_lang}")
                return stored_lang
            
            # Fall back to Telegram's language detection
            detected_lang = self.localization.get_user_language(telegram_user)
            logger.debug(f"Using detected language for user {user_id}: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Error getting user language for {telegram_user.id}: {e}")
            return self.localization.default_lang
    
    def set_user_language(self, user_id: int, language: str) -> bool:
        """
        Set user's preferred language.
        
        Args:
            user_id: Telegram user ID
            language: Language code (e.g., 'en', 'ru')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.redis_client.set_user_language(user_id, language)
            if success:
                logger.info(f"Set language preference for user {user_id}: {language}")
            else:
                logger.error(f"Failed to set language preference for user {user_id}: {language}")
            return success
            
        except Exception as e:
            logger.error(f"Error setting user language for {user_id}: {e}")
            return False
    
    def is_user_premium(self, user_id: int) -> bool:
        """
        Check if user has premium status.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user has premium access, False otherwise
        """
        try:
            return self.redis_client.is_user_premium(user_id)
            
        except Exception as e:
            logger.error(f"Error checking premium status for user {user_id}: {e}")
            return False
    
    def set_user_premium(self, user_id: int, is_premium: bool = True, duration_days: int = 30) -> bool:
        """
        Set user's premium status.
        
        Args:
            user_id: Telegram user ID
            is_premium: Whether to grant or revoke premium
            duration_days: Duration in days (only used if granting premium)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.redis_client.set_user_premium(user_id, is_premium, duration_days)
            if success:
                action = "granted" if is_premium else "revoked"
                logger.info(f"Premium status {action} for user {user_id}")
            else:
                logger.error(f"Failed to set premium status for user {user_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error setting premium status for user {user_id}: {e}")
            return False
    
    def get_user_premium_status_text(self, user_id: int, language: str) -> str:
        """
        Get localized premium status text for user.
        
        Args:
            user_id: Telegram user ID
            language: User's language preference
            
        Returns:
            Localized premium status text
        """
        try:
            is_premium = self.is_user_premium(user_id)
            
            if is_premium:
                return self.localization.get('status.premium_active', language)
            else:
                return self.localization.get('status.premium_inactive', language)
                
        except Exception as e:
            logger.error(f"Error getting premium status text for user {user_id}: {e}")
            return "Status unavailable"
    
    def initialize_user_language(self, telegram_user) -> str:
        """
        Initialize language for new user and store preference.
        
        This combines language detection and storage for new user setup.
        Used in command handlers like start_command.
        
        Args:
            telegram_user: Telegram user object
            
        Returns:
            The detected/set language code
        """
        try:
            # Get language (checking stored preference first)
            user_lang = self.get_user_language(telegram_user)
            
            # Store the language preference (in case it was detected from Telegram)
            self.set_user_language(telegram_user.id, user_lang)
            
            return user_lang
            
        except Exception as e:
            logger.error(f"Error initializing user language for {telegram_user.id}: {e}")
            return self.localization.default_lang


# Global user service instance
user_service = UserService() 