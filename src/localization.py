"""Localization utilities for the Style Transfer Bot."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Localization:
    """Handle localization and translations."""
    
    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {}
        self.default_lang = "en"
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load all translation files."""
        locales_dir = Path(__file__).parent.parent / "config" / "locales"
        
        if not locales_dir.exists():
            logger.error(f"Locales directory not found: {locales_dir}")
            return
        
        for locale_file in locales_dir.glob("*.json"):
            lang = locale_file.stem
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    self.translations[lang] = json.load(f)
                logger.debug(f"Loaded translations for language: {lang}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load translations for {lang}: {e}")
    
    def get(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """Get localized string by key."""
        if lang is None:
            lang = self.default_lang
        
        # Fallback to default language if requested language not available
        if lang not in self.translations:
            logger.warning(f"Language '{lang}' not available, using default: {self.default_lang}")
            lang = self.default_lang
        
        # Get translation
        translation = self.translations.get(lang, {}).get(key)
        
        # Fallback to English if key not found
        if translation is None and lang != self.default_lang:
            translation = self.translations.get(self.default_lang, {}).get(key)
        
        # Final fallback to key itself
        if translation is None:
            logger.warning(f"Translation key not found: {key}")
            translation = key
        
        # Format with kwargs if provided
        try:
            return translation.format(**kwargs) if kwargs else translation
        except KeyError as e:
            logger.error(f"Missing format parameter for key '{key}': {e}")
            return translation
    
    def get_user_language(self, telegram_user) -> str:
        """Detect user language from Telegram user object."""
        if hasattr(telegram_user, 'language_code') and telegram_user.language_code:
            # Extract primary language (e.g., 'ru' from 'ru-RU')
            lang = telegram_user.language_code.split('-')[0].lower()
            
            # Check if we support this language
            if lang in self.translations:
                return lang
        
        return self.default_lang
    
    def get_available_languages(self) -> list:
        """Get list of available languages."""
        return list(self.translations.keys())


# Global localization instance
L = Localization()


def get_localized_text(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Convenience function to get localized text."""
    return L.get(key, lang, **kwargs) 