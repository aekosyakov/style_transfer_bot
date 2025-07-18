"""Configuration management for the Style Transfer Bot."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    """Application configuration management."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
            
        # Load environment variables
        self.bot_token = os.getenv("STYLE_TRANSFER_BOT_TOKEN") or os.getenv("STYLE_TRANSFER_BOT_TOKEN")
        self.provider_token = os.getenv("PROVIDER_TOKEN")
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Validate required environment variables
        self._validate_env_vars()
        
        # Determine environment
        self.is_test = os.getenv("ENV") == "test"
        
        # ========================================
        # 🚨 TESTING FLAG - PREMIUM FEATURES FREE
        # ========================================
        # Set this to False when you want to re-enable premium restrictions
        # When True: ALL users get access to premium features for testing
        self.premium_features_free = True
        # ========================================
        
        # Load categories
        self.categories = self._load_categories()
        
        logger.info(f"Configuration loaded - Test mode: {self.is_test}")
        
        if self.premium_features_free:
            logger.warning("🎉 TESTING MODE ACTIVE: Premium features are FREE for ALL users!")
            logger.warning("🎉 All style transfer options will be available to everyone")
    
    def _validate_env_vars(self) -> None:
        """Validate that required environment variables are set."""
        required_vars = {
            "STYLE_TRANSFER_BOT_TOKEN": self.bot_token,
            "REPLICATE_API_TOKEN": self.replicate_token,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def _load_categories(self) -> Dict[str, Any]:
        """Load categories configuration from JSON file."""
        try:
            config_file = "categories.test.json" if self.is_test else "categories.prod.json"
            config_path = Path(__file__).parent.parent / "config" / config_file
            
            with open(config_path, "r", encoding="utf-8") as f:
                categories = json.load(f)
            
            logger.debug(f"Loaded categories from {config_file}")
            return categories
        
        except FileNotFoundError:
            logger.error(f"Categories file not found: {config_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in categories file: {e}")
            raise
    
    def get_category_options(self, category: str, is_premium: bool = False, show_all: bool = True) -> list:
        """Get available options for a category. Always shows all options for better UX."""
        if category not in self.categories:
            logger.warning(f"Unknown category: {category}")
            return []
        
        category_data = self.categories[category]
        
        # Check if this is a submenu category
        if category_data.get("submenu", False):
            # Return submenu options
            return category_data.get("options", [])
        
        options = []
        
        # Always add free options
        options.extend(category_data.get("free", []))
        
        # Always add premium options for better UX (show_all=True by default)
        # Premium check will be handled during processing
        if show_all or is_premium:
            options.extend(category_data.get("premium", []))
        
        return options
    
    def is_submenu_category(self, category: str) -> bool:
        """Check if a category has a submenu."""
        if category not in self.categories:
            return False
        return self.categories[category].get("submenu", False)
    
    def is_premium_option(self, category: str, option_identifier: str) -> bool:
        """Check if a specific option is premium."""
        if category not in self.categories:
            return False
        
        premium_options = self.categories[category].get("premium", [])
        # Check both new label_key format and old label format for backward compatibility
        return any(
            option.get("label_key") == option_identifier or 
            option.get("label") == option_identifier 
            for option in premium_options
        )
    
    @property
    def flux_models(self) -> Dict[str, str]:
        """Available FLUX models."""
        return {
            "pro": "black-forest-labs/flux-kontext-pro",
            "max": "black-forest-labs/flux-kontext-max"
        }
    
    @property
    def kling_models(self) -> Dict[str, str]:
        """Available Kling models."""
        return {
            "lite": "kwaivgi/kling-v1.6-lite",
            "pro": "kwaivgi/kling-v1.6-pro"
        }


# Global config instance
config = Config(debug=os.getenv("DEBUG", "false").lower() == "true") 