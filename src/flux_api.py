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
        strength: float = 0.6,
        seed: Optional[int] = None
    ) -> Optional[str]:
        """
        Process image with FLUX Kontext.
        
        Args:
            image_url: URL or base64 encoded image
            prompt: Enhancement prompt
            model_type: 'pro' or 'max'
            strength: Edit strength (0-1)
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
                "image": image_url,
                "model_version": f"flux-kontext-{model_type}",
                "strength": strength
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
    
    def get_prompt_template(self, category: str, style_or_effect: str) -> str:
        """
        Generate prompt based on category and desired effect.
        
        Args:
            category: Enhancement category
            style_or_effect: Desired style or effect
            
        Returns:
            Formatted prompt
        """
        templates = {
            "style_transfer": f"{style_or_effect} painting, keep composition",
            "object_edit": f"Replace object with {style_or_effect} while preserving lighting",
            "text_edit": f"replace text with '{style_or_effect}'",
            "background_swap": f"Change background to {style_or_effect}, keep subject position",
            "face_enhance": f"Add {style_or_effect} to the face, preserve identity"
        }
        
        template = templates.get(category, style_or_effect)
        logger.debug(f"Generated prompt template for {category}: {template}")
        return template
    
    async def style_transfer(
        self, 
        image_url: str, 
        style: str, 
        strength: float = 0.6
    ) -> Optional[str]:
        """Apply style transfer to image."""
        prompt = self.get_prompt_template("style_transfer", style)
        return await self.process_image(image_url, prompt, strength=strength)
    
    async def edit_object(
        self, 
        image_url: str, 
        object_description: str, 
        strength: float = 0.7
    ) -> Optional[str]:
        """Edit objects in image."""
        prompt = self.get_prompt_template("object_edit", object_description)
        return await self.process_image(image_url, prompt, strength=strength)
    
    async def edit_text(
        self, 
        image_url: str, 
        old_text: str, 
        new_text: str, 
        strength: float = 0.8
    ) -> Optional[str]:
        """Edit text in image."""
        prompt = f"replace '{old_text}' with '{new_text}'"
        return await self.process_image(image_url, prompt, strength=strength)
    
    async def swap_background(
        self, 
        image_url: str, 
        background_description: str, 
        strength: float = 0.7
    ) -> Optional[str]:
        """Swap image background."""
        prompt = self.get_prompt_template("background_swap", background_description)
        return await self.process_image(image_url, prompt, strength=strength)
    
    async def enhance_face(
        self, 
        image_url: str, 
        enhancement: str, 
        strength: float = 0.5
    ) -> Optional[str]:
        """Enhance faces in image."""
        prompt = self.get_prompt_template("face_enhance", enhancement)
        return await self.process_image(image_url, prompt, strength=strength)
    
    def validate_image_url(self, url: str) -> bool:
        """Validate image URL format."""
        try:
            # Basic validation - could be enhanced
            return url.startswith(('http://', 'https://')) or url.startswith('data:image/')
        except Exception:
            return False


# Global FLUX API instance
flux_api = FluxAPI() 