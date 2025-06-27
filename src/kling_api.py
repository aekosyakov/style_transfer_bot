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
        animation_prompt: str,
        model_type: str = "pro",
        duration_seconds: int = 5,
        fps: int = 24
    ) -> Optional[str]:
        """
        Animate image with Kling AI.
        
        Args:
            image_url: URL of source image
            animation_prompt: Description of desired animation
            model_type: 'lite' or 'pro'
            duration_seconds: Animation duration
            fps: Frames per second
            
        Returns:
            URL of animated video or None if failed
        """
        try:
            model_id = config.kling_models.get(model_type, self.default_model)
            
            input_params = {
                "prompt": animation_prompt,
                "start_image": image_url,
                "seconds": duration_seconds
            }
            
            # Add FPS if supported by model
            if model_type == "pro":
                input_params["fps"] = fps
            
            logger.info(f"Animating image with Kling {model_type}, prompt: '{animation_prompt[:50]}...'")
            logger.debug(f"Kling input parameters: {input_params}")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.client.run(model_id, input=input_params)
            )
            
            if result:
                logger.info("Kling animation completed successfully")
                return result
            else:
                logger.warning("Kling returned empty result")
                return None
                
        except Exception as e:
            logger.error(f"Kling animation failed: {e}")
            return None
    
    def get_animation_prompt(self, animation_type: str, custom_prompt: Optional[str] = None) -> str:
        """
        Generate animation prompt based on type.
        
        Args:
            animation_type: Type of animation
            custom_prompt: Custom animation description
            
        Returns:
            Formatted animation prompt
        """
        if custom_prompt:
            return custom_prompt
        
        animation_prompts = {
            "gentle_breeze": "gentle breeze animating hair and clothing",
            "sparkle": "sparkling magical effects around the subject",
            "zoom": "slow cinematic zoom in with subtle camera movement", 
            "lights": "moving light reflections and ambient lighting changes",
            "water": "water ripples and reflections",
            "fire": "flickering fire effects and warm lighting",
            "snow": "gentle snowfall with natural particle movement",
            "clouds": "moving clouds in the background",
            "portrait": "subtle facial expressions and eye movement",
            "nature": "leaves rustling and natural environment movement"
        }
        
        prompt = animation_prompts.get(animation_type, f"{animation_type} animation effect")
        logger.debug(f"Generated animation prompt for {animation_type}: {prompt}")
        return prompt
    
    async def animate_with_breeze(self, image_url: str, model_type: str = "pro") -> Optional[str]:
        """Animate image with gentle breeze effect."""
        prompt = self.get_animation_prompt("gentle_breeze")
        return await self.animate_image(image_url, prompt, model_type=model_type)
    
    async def animate_with_sparkle(self, image_url: str, model_type: str = "pro") -> Optional[str]:
        """Animate image with sparkle effects."""
        prompt = self.get_animation_prompt("sparkle")
        return await self.animate_image(image_url, prompt, model_type=model_type)
    
    async def animate_with_zoom(self, image_url: str, model_type: str = "pro") -> Optional[str]:
        """Animate image with cinematic zoom."""
        prompt = self.get_animation_prompt("zoom")
        return await self.animate_image(image_url, prompt, model_type=model_type)
    
    async def animate_with_lights(self, image_url: str, model_type: str = "pro") -> Optional[str]:
        """Animate image with moving lights."""
        prompt = self.get_animation_prompt("lights")
        return await self.animate_image(image_url, prompt, model_type=model_type)
    
    async def animate_portrait(self, image_url: str, model_type: str = "pro") -> Optional[str]:
        """Animate portrait with subtle expressions."""
        prompt = self.get_animation_prompt("portrait")
        return await self.animate_image(image_url, prompt, model_type=model_type)
    
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
    
    def get_animation_types(self, is_premium: bool = False) -> list:
        """Get available animation types based on user tier."""
        free_animations = [
            {"type": "gentle_breeze", "label": "🍃 Gentle Breeze", "description": "Subtle movement"},
        ]
        
        premium_animations = [
            {"type": "sparkle", "label": "✨ Sparkle Effects", "description": "Magical sparkles"},
            {"type": "zoom", "label": "🎞️ Cinematic Zoom", "description": "Professional camera movement"},
            {"type": "lights", "label": "💡 Moving Lights", "description": "Dynamic lighting"},
            {"type": "water", "label": "🌊 Water Effects", "description": "Ripples and reflections"},
            {"type": "fire", "label": "🔥 Fire Effects", "description": "Flickering flames"},
            {"type": "snow", "label": "❄️ Snow Fall", "description": "Gentle snowfall"},
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