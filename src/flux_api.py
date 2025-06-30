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
        import time
        start_time = time.time()
        
        # Log the detailed request parameters
        request_details = {
            "model_type": model_type,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:100],
            "image_url": image_url,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "safety_tolerance": safety_tolerance,
            "seed": seed,
            "timestamp": time.time()
        }
        
        logger.info(f"🔄 FLUX_REQUEST_START: {request_details}")
        
        try:
            logger.info(f"Starting FLUX processing - Model: {model_type}, Prompt: '{prompt[:100]}...'")
            logger.info(f"Image URL: {image_url}")
            
            # Check if we have a valid API token
            if not config.replicate_token:
                error_details = {
                    "error": "missing_api_token",
                    "duration": time.time() - start_time
                }
                logger.error(f"❌ FLUX_REQUEST_FAILED: {error_details}")
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
            api_call_start = time.time()
            loop = asyncio.get_event_loop()
            
            try:
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.client.run(model_id, input=input_params)
                )
                api_call_duration = time.time() - api_call_start
                
                logger.info(f"Replicate API call completed in {api_call_duration:.2f}s. Result type: {type(result)}")
                logger.info(f"Result content: {result}")
                
                if result:
                    success_details = {
                        "success": True,
                        "result_url": result,
                        "api_duration": api_call_duration,
                        "total_duration": time.time() - start_time,
                        "model_id": model_id
                    }
                    logger.info(f"✅ FLUX_REQUEST_SUCCESS: {success_details}")
                    logger.info("FLUX processing completed successfully")
                    logger.info(f"Result URL: {result}")
                    return result
                else:
                    failure_details = {
                        "error": "empty_result",
                        "api_duration": api_call_duration,
                        "total_duration": time.time() - start_time,
                        "model_id": model_id,
                        "input_params": input_params
                    }
                    logger.error(f"❌ FLUX_REQUEST_FAILED: {failure_details}")
                    logger.warning("FLUX returned empty result")
                    return None
                    
            except Exception as e:
                api_call_duration = time.time() - api_call_start
                
                # Check for content filtering error (E005)
                if "E005" in str(e) or "flagged as sensitive" in str(e):
                    api_error_details = {
                        "error": "content_filtered",
                        "error_code": "E005",
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                        "api_duration": api_call_duration,
                        "total_duration": time.time() - start_time,
                        "model_id": model_id
                    }
                    logger.warning(f"🚫 FLUX_CONTENT_FILTERED: {api_error_details}")
                    logger.warning(f"Content flagged as sensitive by Replicate: {e}")
                    # Return special indicator for content filtering
                    return "CONTENT_FILTERED_E005"
                
                api_error_details = {
                    "error": "api_exception",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "api_duration": api_call_duration,
                    "total_duration": time.time() - start_time,
                    "model_id": model_id,
                    "input_params": input_params
                }
                logger.error(f"❌ FLUX_API_EXCEPTION: {api_error_details}")
                logger.error(f"Replicate API call failed: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                return None
                
        except Exception as e:
            general_error_details = {
                "error": "general_exception",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "total_duration": time.time() - start_time,
                "request_details": request_details
            }
            logger.error(f"❌ FLUX_GENERAL_EXCEPTION: {general_error_details}")
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
        # Apply prompt variations for special placeholders
        try:
            from src.prompt_variations import prompt_variation_generator
            
            # Check if this is a special placeholder that needs variation
            if any(placeholder in style for placeholder in [
                'RANDOM_CARTOON', 'RANDOM_ANIME', 'RANDOM_COMICS', 'RANDOM_ART_STYLE'
            ]):
                # Apply prompt variations
                varied_prompt = prompt_variation_generator.get_varied_prompt(
                    category="style_transfer", 
                    label_key="style.transfer", 
                    original_prompt=style
                )
                logger.info(f"🔄 Applied prompt variation for style transfer:")
                logger.info(f"   - Original: '{style}'")
                logger.info(f"   - Varied: '{varied_prompt}'")
                style = varied_prompt
        except Exception as e:
            logger.warning(f"Failed to apply prompt variations for style transfer: {e}")
            # Continue with original prompt if variation fails
        
        # Use the (possibly varied) style prompt
        return await self.process_image(image_url, style, safety_tolerance=safety_tolerance)
    
    async def edit_object(
        self, 
        image_url: str, 
        object_description: str, 
        safety_tolerance: int = 2
    ) -> Optional[str]:
        """Edit objects in image."""
        # Apply prompt variations for special placeholders
        try:
            from src.prompt_variations import prompt_variation_generator
            
            # Check if this is a special placeholder that needs variation
            if any(placeholder in object_description for placeholder in [
                'RANDOM_MENS_OUTFIT', 'CASUAL_MENS_OUTFIT', 'MODERN_MENS_OUTFIT', 
                'CLASSIC_MENS_OUTFIT', 'EDGY_MENS_OUTFIT', 'EVENING_MENS_OUTFIT',
                'CULTURAL_MENS_OUTFIT', 'ANIME_MENS_OUTFIT',
                'RANDOM_DRESS', 'CASUAL_OUTFIT', 'MODERN_DRESS', 'CLASSIC_DRESS',
                'EDGY_DRESS', 'EVENING_DRESS', 'CULTURAL_DRESS', 'ANIME_DRESS',
                'RANDOM_HAIRSTYLE', 'MODERN_HAIRSTYLE', 'CLASSIC_HAIRSTYLE',
                'EDGY_HAIRSTYLE', 'CULTURAL_HAIRSTYLE', 'ANIME_HAIRSTYLE',
                # Gender-specific hairstyle placeholders (MISSING - THIS WAS THE BUG!)
                'RANDOM_MENS_HAIRSTYLE', 'MODERN_MENS_HAIRSTYLE', 'CLASSIC_MENS_HAIRSTYLE',
                'EDGY_MENS_HAIRSTYLE', 'CULTURAL_MENS_HAIRSTYLE', 'ANIME_MENS_HAIRSTYLE',
                'RANDOM_WOMENS_HAIRSTYLE', 'MODERN_WOMENS_HAIRSTYLE', 'CLASSIC_WOMENS_HAIRSTYLE',
                'EDGY_WOMENS_HAIRSTYLE', 'CULTURAL_WOMENS_HAIRSTYLE', 'ANIME_WOMENS_HAIRSTYLE'
            ]):
                # Apply prompt variations
                varied_prompt = prompt_variation_generator.get_varied_prompt(
                    category="object_edit", 
                    label_key="object.edit", 
                    original_prompt=object_description
                )
                logger.info(f"🔄 Applied prompt variation for object edit:")
                logger.info(f"   - Original: '{object_description}'")
                logger.info(f"   - Varied: '{varied_prompt}'")
                object_description = varied_prompt
        except Exception as e:
            logger.warning(f"Failed to apply prompt variations for object edit: {e}")
            # Continue with original prompt if variation fails
        
        # Use the (possibly varied) prompt
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

    async def process_image_with_variation(
        self,
        image_url: str,
        prompt: str,
        model_type: str = "pro",
        aspect_ratio: str = "match_input_image",
        output_format: str = "jpg",
        safety_tolerance: int = 2,
        use_random_seed: bool = True
    ) -> Optional[str]:
        """Process image with optional random seed for variation on repeat."""
        try:
            from src.prompt_variations import prompt_variation_generator
            
            seed = prompt_variation_generator.get_random_seed() if use_random_seed else None
            logger.info(f"Processing with variation - Seed: {seed}, Prompt: '{prompt[:50]}...'")
            
            return await self.process_image(
                image_url=image_url,
                prompt=prompt,
                model_type=model_type,
                aspect_ratio=aspect_ratio,
                output_format=output_format,
                safety_tolerance=safety_tolerance,
                seed=seed
            )
        except Exception as e:
            logger.error(f"Error in process_image_with_variation: {e}")
            # Fallback to regular processing without seed
            return await self.process_image(
                image_url=image_url,
                prompt=prompt,
                model_type=model_type,
                aspect_ratio=aspect_ratio,
                output_format=output_format,
                safety_tolerance=safety_tolerance
            )


# Global FLUX API instance
flux_api = FluxAPI() 