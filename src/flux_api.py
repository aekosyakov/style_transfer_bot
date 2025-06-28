"""FLUX Kontext API integration for image processing."""

import logging
import asyncio
from typing import Optional, Dict, Any, Union
import replicate
from config import config

logger = logging.getLogger(__name__)


class FluxAPI:
    """FLUX Kontext API client for image enhancement."""
    
    def __init__(self):
        self.client = replicate.Client(api_token=config.replicate_token)
        self.default_model = config.flux_models["pro"]  # Use pro by default
    
    async def process_image(
        self,
        image_url: str,
        prompt: str,
        model_type: str = "pro",
        aspect_ratio: str = "match_input_image",
        output_format: str = "jpg",
        safety_tolerance: int = 2,
        seed: Optional[int] = None
    ) -> Optional[str]:
        """
        Process image with FLUX Kontext.
        
        Args:
            image_url: URL or base64 encoded image
            prompt: Enhancement prompt
            model_type: 'pro' or 'max'
            aspect_ratio: Aspect ratio or "match_input_image"
            output_format: Output format (jpg, png, webp)
            safety_tolerance: Safety tolerance (0-6, max 2 with input images)
            seed: Optional seed for determinism
            
        Returns:
            URL of processed image or None if failed
        """
        try:
            logger.info(f"Starting FLUX processing - Model: {model_type}, Prompt: '{prompt[:100]}...'")
            logger.info(f"Image URL: {image_url}")
            
            # Check if we have a valid API token
            if not config.replicate_token:
                logger.error("REPLICATE_API_TOKEN is not configured!")
                return None
            
            logger.info(f"REPLICATE_API_TOKEN configured: {config.replicate_token[:10]}...")
            
            model_id = config.flux_models.get(model_type, self.default_model)
            logger.info(f"Using FLUX model: {model_id}")
            
            input_params = {
                "prompt": prompt,
                "input_image": image_url,
                "aspect_ratio": aspect_ratio,
                "output_format": output_format,
                "safety_tolerance": safety_tolerance
            }
            
            if seed is not None:
                input_params["seed"] = seed
            
            logger.info(f"Processing image with FLUX {model_type}, prompt: '{prompt[:50]}...'")
            logger.debug(f"FLUX input parameters: {input_params}")
            
            # Run in thread pool to avoid blocking
            logger.info("Calling Replicate API...")
            loop = asyncio.get_event_loop()
            try:
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.client.run(model_id, input=input_params)
                )
                logger.info(f"Replicate API call completed. Result type: {type(result)}")
                logger.info(f"Result content: {result}")
            except Exception as e:
                logger.error(f"Replicate API call failed: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                return None
            
            if result:
                logger.info("FLUX processing completed successfully")
                logger.info(f"Result URL: {result}")
                return result
            else:
                logger.warning("FLUX returned empty result")
                return None
                
        except Exception as e:
            logger.error(f"FLUX processing failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def get_simple_prompt(self, category: str, prompt: str) -> str:
        """
        Return the prompt as-is for simple, direct instructions.
        
        Args:
            category: Enhancement category (for logging only)
            prompt: Direct prompt like "Make this a 90s cartoon"
            
        Returns:
            The same prompt, unchanged
        """
        logger.debug(f"Using direct prompt for {category}: {prompt}")
        return prompt
    
    async def style_transfer(
        self, 
        image_url: str, 
        style: str, 
        safety_tolerance: int = 2
    ) -> Optional[str]:
        """Apply style transfer to image."""
        # Use the style prompt directly - it should already be in format like "Make this a 90s cartoon"
        return await self.process_image(image_url, style, safety_tolerance=safety_tolerance)
    
    async def edit_object(
        self, 
        image_url: str, 
        object_description: str, 
        safety_tolerance: int = 2
    ) -> Optional[str]:
        """Edit objects in image."""
        # Use simple direct prompts
        return await self.process_image(image_url, object_description, safety_tolerance=safety_tolerance)
    
    async def edit_text(
        self, 
        image_url: str, 
        old_text: str, 
        new_text: str, 
        safety_tolerance: int = 2
    ) -> Optional[str]:
        """Edit text in image."""
        prompt = f"Replace '{old_text}' with '{new_text}'"
        return await self.process_image(image_url, prompt, safety_tolerance=safety_tolerance)
    
    async def swap_background(
        self, 
        image_url: str, 
        background_description: str, 
        safety_tolerance: int = 2
    ) -> Optional[str]:
        """Swap image background."""
        # Use simple direct prompts
        return await self.process_image(image_url, background_description, safety_tolerance=safety_tolerance)
    
    async def enhance_face(
        self, 
        image_url: str, 
        enhancement: str, 
        safety_tolerance: int = 1
    ) -> Optional[str]:
        """Enhance faces in image."""
        # Use simple direct prompts
        return await self.process_image(image_url, enhancement, safety_tolerance=safety_tolerance)
    
    def validate_image_url(self, url: str) -> bool:
        """Validate image URL format."""
        try:
            # Basic validation - could be enhanced
            return url.startswith(('http://', 'https://')) or url.startswith('data:image/')
        except Exception:
            return False


# Global FLUX API instance
flux_api = FluxAPI() 