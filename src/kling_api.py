"""Kling AI API integration for image animation."""

import logging
import asyncio
from typing import Optional, Dict, Any
import replicate
from src.config import config

logger = logging.getLogger(__name__)


class KlingAPI:
    """Kling AI API client for image animation."""
    
    def __init__(self):
        self.client = replicate.Client(api_token=config.replicate_token)
        self.default_model = config.kling_models["pro"]  # Use pro by default
    
    async def animate_image(
        self,
        image_url: str,
        animation_prompt: str = "",
        model_type: str = "pro",
        duration_seconds: int = 5,
        cfg_scale: float = 0.5,
        negative_prompt: str = "",
        aspect_ratio: str = "16:9"
    ) -> Optional[str]:
        """
        Animate image with Kling AI.
        
        Args:
            image_url: URL of source image
            animation_prompt: Description of desired animation (empty for idle animation)
            model_type: 'lite' or 'pro'
            duration_seconds: Animation duration (5 or 10 seconds)
            cfg_scale: Flexibility in video generation (0.1-1.0)
            negative_prompt: Things you don't want to see
            aspect_ratio: Aspect ratio (ignored when start_image provided)
            
        Returns:
            URL of animated video or None if failed
        """
        import time
        start_time = time.time()
        
        # Log the detailed request parameters
        request_details = {
            "model_type": model_type,
            "animation_prompt": animation_prompt,
            "prompt_length": len(animation_prompt) if animation_prompt else 0,
            "image_url": image_url,
            "duration_seconds": duration_seconds,
            "cfg_scale": cfg_scale,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
            "timestamp": time.time()
        }
        
        logger.info(f"🔄 KLING_REQUEST_START: {request_details}")
        
        try:
            model_id = config.kling_models.get(model_type, self.default_model)
            
            # Base parameters according to API docs
            input_params = {
                "prompt": animation_prompt,
                "start_image": image_url,
                "duration": duration_seconds,
                "cfg_scale": cfg_scale
            }
            
            # Add optional parameters if provided
            if negative_prompt:
                input_params["negative_prompt"] = negative_prompt
            
            # Note: aspect_ratio is ignored when start_image is provided according to docs
            # but we can include it for completeness
            input_params["aspect_ratio"] = aspect_ratio
            
            logger.info(f"Animating image with Kling {model_type}")
            logger.info(f"Prompt: '{animation_prompt}' (empty = idle animation)" if animation_prompt else "Idle animation (no prompt)")
            logger.debug(f"Kling input parameters: {input_params}")
            
            # Run in thread pool to avoid blocking
            api_call_start = time.time()
            loop = asyncio.get_event_loop()
            
            try:
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.client.run(model_id, input=input_params)
                )
                api_call_duration = time.time() - api_call_start
                
                logger.info(f"Kling API call completed in {api_call_duration:.2f}s. Result type: {type(result)}")
                
                if result:
                    success_details = {
                        "success": True,
                        "result_url": result,
                        "api_duration": api_call_duration,
                        "total_duration": time.time() - start_time,
                        "model_id": model_id
                    }
                    logger.info(f"✅ KLING_REQUEST_SUCCESS: {success_details}")
                    logger.info("Kling animation completed successfully")
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
                    logger.error(f"❌ KLING_REQUEST_FAILED: {failure_details}")
                    logger.warning("Kling returned empty result")
                    return None
                    
            except Exception as e:
                api_call_duration = time.time() - api_call_start
                api_error_details = {
                    "error": "api_exception",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "api_duration": api_call_duration,
                    "total_duration": time.time() - start_time,
                    "model_id": model_id,
                    "input_params": input_params
                }
                logger.error(f"❌ KLING_API_EXCEPTION: {api_error_details}")
                logger.error(f"Kling animation failed: {e}")
                logger.error(f"Error type: {type(e).__name__}")
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
            logger.error(f"❌ KLING_GENERAL_EXCEPTION: {general_error_details}")
            logger.error(f"Kling animation failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def get_animation_prompt(self, animation_type: str, custom_prompt: Optional[str] = None) -> str:
        """
        Generate animation prompt based on type.
        
        Args:
            animation_type: Type of animation
            custom_prompt: Custom animation description
            
        Returns:
            Formatted animation prompt (empty string for idle animation)
        """
        if custom_prompt is not None:
            return custom_prompt
        
        animation_prompts = {
            "idle": "",  # Empty prompt for idle animation
            "gentle_breeze": "gentle breeze animating hair and clothing",
            "sparkle": "sparkling magical effects around the subject",
            "zoom": "slow cinematic zoom in with subtle camera movement", 
            "lights": "moving light reflections and ambient lighting changes",
            "water": "water ripples and reflections",
            "fire": "flickering fire effects and warm lighting",
            "snow": "gentle snowfall with natural particle movement",
            "clouds": "moving clouds in the background",
            "portrait": "subtle facial expressions and eye movement",
            "nature": "leaves rustling and natural environment movement",
            "dance": "subtle dancing movement and rhythm",
            "wind": "strong wind effects with dramatic movement",
            "glow": "mystical glowing aura around the subject",
            "waves": "ocean waves and water movement in background",
            "floating": "objects floating and levitating gently"
        }
        
        prompt = animation_prompts.get(animation_type, animation_type)
        logger.debug(f"Generated animation prompt for {animation_type}: '{prompt}' (empty=idle)")
        return prompt
    
    async def animate_idle(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate image with idle movement (empty prompt)."""
        prompt = self.get_animation_prompt("idle")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def animate_with_breeze(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate image with gentle breeze effect."""
        prompt = self.get_animation_prompt("gentle_breeze")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def animate_with_sparkle(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate image with sparkle effects."""
        prompt = self.get_animation_prompt("sparkle")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def animate_with_zoom(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate image with cinematic zoom."""
        prompt = self.get_animation_prompt("zoom")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def animate_with_lights(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate image with moving lights."""
        prompt = self.get_animation_prompt("lights")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def animate_portrait(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate portrait with subtle expressions."""
        prompt = self.get_animation_prompt("portrait")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def animate_with_wind(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate image with wind effects."""
        prompt = self.get_animation_prompt("wind")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def animate_with_glow(self, image_url: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """Animate image with mystical glow."""
        prompt = self.get_animation_prompt("glow")
        return await self.animate_image(image_url, prompt, model_type=model_type, duration_seconds=duration)
    
    async def custom_animation(
        self, 
        image_url: str, 
        custom_prompt: str, 
        model_type: str = "pro",
        duration: int = 5
    ) -> Optional[str]:
        """Create custom animation with user-defined prompt."""
        return await self.animate_image(
            image_url, 
            custom_prompt, 
            model_type=model_type,
            duration_seconds=duration
        )
    
    async def animate_by_prompt(self, image_url: str, kling_prompt: str, model_type: str = "pro", duration: int = 5) -> Optional[str]:
        """
        Animate image using the prompt from categories configuration.
        This method is called from the bot when user selects an animation option.
        """
        logger.info(f"Animating with kling_prompt: '{kling_prompt}'")
        return await self.animate_image(
            image_url, 
            kling_prompt, 
            model_type=model_type,
            duration_seconds=duration
        )
    
    def get_animation_types(self, is_premium: bool = False) -> list:
        """Get available animation types based on user tier (deprecated - use categories.json)."""
        free_animations = [
            {"type": "idle", "label": "🧘 Idle", "description": "Subtle natural movement"},
            {"type": "gentle_breeze", "label": "🍃 Gentle Breeze", "description": "Subtle movement"},
        ]
        
        premium_animations = [
            {"type": "sparkle", "label": "✨ Sparkle Effects", "description": "Magical sparkles"},
            {"type": "zoom", "label": "🎞️ Cinematic Zoom", "description": "Professional camera movement"},
            {"type": "lights", "label": "💡 Moving Lights", "description": "Dynamic lighting"},
            {"type": "water", "label": "🌊 Water Effects", "description": "Ripples and reflections"},
            {"type": "fire", "label": "🔥 Fire Effects", "description": "Flickering flames"},
            {"type": "snow", "label": "❄️ Snow Fall", "description": "Gentle snowfall"},
            {"type": "wind", "label": "💨 Wind Effects", "description": "Strong wind movement"},
            {"type": "glow", "label": "🌟 Mystical Glow", "description": "Glowing aura"},
        ]
        
        animations = free_animations.copy()
        if is_premium:
            animations.extend(premium_animations)
        
        return animations
    
    def estimate_processing_time(self, model_type: str, duration_seconds: int) -> int:
        """Estimate processing time in seconds."""
        # Rough estimates based on model and duration
        base_time = {
            "lite": 30,   # 30 seconds base
            "pro": 60     # 60 seconds base
        }
        
        # Add time based on duration
        time_per_second = {
            "lite": 5,    # 5 seconds per output second
            "pro": 10     # 10 seconds per output second  
        }
        
        base = base_time.get(model_type, 60)
        additional = time_per_second.get(model_type, 10) * duration_seconds
        
        return base + additional


# Global Kling API instance
kling_api = KlingAPI() 