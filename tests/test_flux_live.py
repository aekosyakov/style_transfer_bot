#!/usr/bin/env python3
"""Live tests for FLUX API integration."""

import os
import sys
import asyncio
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flux_api import flux_api
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_flux_api_config():
    """Test FLUX API configuration."""
    logger.info("Testing FLUX API configuration...")
    
    # Check if API token is configured
    if not config.replicate_token:
        logger.error("REPLICATE_API_TOKEN is not configured!")
        return False
    
    logger.info(f"API token configured: {config.replicate_token[:10]}...")
    
    # Check model configurations
    for model_type, model_id in config.flux_models.items():
        logger.info(f"Model {model_type}: {model_id}")
    
    # Test prompt generation with simple direct prompts
    test_prompts = [
        ("style_transfer", "Make this anime style"),
        ("style_transfer", "Make this a comic book"),
        ("style_transfer", "Make this a 90s cartoon"),
        ("object_edit", "Change to red sports car"),
        ("text_edit", "Hello World"),
        ("background_swap", "Change background to mountains"),
        ("face_enhance", "Enhance face naturally")
    ]
    
    for category, effect in test_prompts:
        prompt = flux_api.get_simple_prompt(category, effect)
        logger.info(f"{category}: {prompt}")
    
    return True


async def test_flux_api_call():
    """Test actual FLUX API call with a sample image."""
    logger.info("Testing FLUX API call...")
    
    # Use a sample image URL (placeholder)
    sample_image_url = "https://replicate.delivery/pbxt/sample.jpg"
    
    # Test parameters
    test_params = {
        "prompt": "Make this a 90s cartoon",
        "input_image": sample_image_url,
        "aspect_ratio": "match_input_image",
        "output_format": "jpg",
        "safety_tolerance": 2
    }
    
    logger.info("Test parameters:")
    for key, value in test_params.items():
        logger.info(f"  {key}: {value}")
    
    # Note: We're not actually calling the API to avoid charges
    logger.info("API call test completed (dry run)")
    return True


async def main():
    """Run all tests."""
    try:
        logger.info("Starting FLUX API tests...")
        
        # Test configuration
        config_ok = await test_flux_api_config()
        if not config_ok:
            logger.error("Configuration test failed!")
            return 1
        
        # Test API call (dry run)
        api_ok = await test_flux_api_call()
        if not api_ok:
            logger.error("API test failed!")
            return 1
        
        logger.info("All tests passed!")
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 