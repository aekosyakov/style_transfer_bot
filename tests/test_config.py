import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from src.config import Config


class TestConfig:
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test config initialization with valid environment."""
        with patch.dict(os.environ, {
            'STYLE_TRANSFER_BOT_TOKEN': 'test_bot_token',
            'REPLICATE_API_TOKEN': 'test_replicate_token',
            'REDIS_URL': 'redis://localhost:6379/0'
        }):
            config = Config()
            assert config.bot_token == 'test_bot_token'
            assert config.replicate_token == 'test_replicate_token'
            assert config.redis_url == 'redis://localhost:6379/0'
    
    def test_config_missing_required_vars(self):
        """Test config initialization with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                Config()
    
    @patch('builtins.open', mock_open(read_data='{"test_category": {"free": [], "premium": []}}'))
    def test_load_categories(self):
        """Test loading categories from JSON file."""
        with patch.dict(os.environ, {
            'STYLE_TRANSFER_BOT_TOKEN': 'test_token',
            'REPLICATE_API_TOKEN': 'test_token'
        }):
            config = Config()
            assert 'test_category' in config.categories
    
    def test_get_category_options_free(self):
        """Test getting free category options."""
        with patch.dict(os.environ, {
            'STYLE_TRANSFER_BOT_TOKEN': 'test_token',
            'REPLICATE_API_TOKEN': 'test_token'
        }):
            config = Config()
            config.categories = {
                'style_transfer': {
                    'free': [{'label': 'Free Style', 'prompt': 'free prompt'}],
                    'premium': [{'label': 'Premium Style', 'prompt': 'premium prompt'}]
                }
            }
            
            options = config.get_category_options('style_transfer', is_premium=False)
            assert len(options) == 1
            assert options[0]['label'] == 'Free Style'
    
    def test_get_category_options_premium(self):
        """Test getting premium category options."""
        with patch.dict(os.environ, {
            'STYLE_TRANSFER_BOT_TOKEN': 'test_token',
            'REPLICATE_API_TOKEN': 'test_token'
        }):
            config = Config()
            config.categories = {
                'style_transfer': {
                    'free': [{'label': 'Free Style', 'prompt': 'free prompt'}],
                    'premium': [{'label': 'Premium Style', 'prompt': 'premium prompt'}]
                }
            }
            
            options = config.get_category_options('style_transfer', is_premium=True)
            assert len(options) == 2
            assert any(opt['label'] == 'Free Style' for opt in options)
            assert any(opt['label'] == 'Premium Style' for opt in options)
    
    def test_flux_models(self):
        """Test FLUX model configuration."""
        with patch.dict(os.environ, {
            'STYLE_TRANSFER_BOT_TOKEN': 'test_token',
            'REPLICATE_API_TOKEN': 'test_token'
        }):
            config = Config()
            models = config.flux_models
            assert 'pro' in models
            assert 'max' in models
            assert models['pro'] == 'black-forest-labs/flux-kontext-pro'
    
    def test_kling_models(self):
        """Test Kling model configuration."""
        with patch.dict(os.environ, {
            'STYLE_TRANSFER_BOT_TOKEN': 'test_token',
            'REPLICATE_API_TOKEN': 'test_token'
        }):
            config = Config()
            models = config.kling_models
            assert 'lite' in models
            assert 'pro' in models
            assert models['pro'] == 'kwaivgi/kling-v1.6-pro' 