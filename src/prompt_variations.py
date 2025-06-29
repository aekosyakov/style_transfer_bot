"""Prompt variation system for generating similar but different prompts on repeat."""

import random
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Import the hairstyle generator
try:
    from src.hairstyles import hairstyle_generator
except ImportError:
    logger.warning("Could not import hairstyle_generator, hairstyle variations will be limited")
    hairstyle_generator = None


class PromptVariationGenerator:
    """Generate varied prompts while maintaining semantic similarity."""
    
    def __init__(self):
        self.variations = {
            # Style Transfer Variations
            "style.anime_style": [
                "Make this modern anime style",
                "Make this classic anime style", 
                "Make this kawaii anime style",
                "Make this realistic anime style",
                "Make this detailed anime style"
            ],
            "style.digital_art": [
                "Make this modern digital art",
                "Make this stylized digital art",
                "Make this vibrant digital art", 
                "Make this detailed digital art",
                "Make this contemporary digital art"
            ],
            "style.pencil_sketch": [
                "Make this a detailed pencil sketch",
                "Make this a soft pencil sketch",
                "Make this a realistic pencil sketch",
                "Make this an artistic pencil sketch",
                "Make this a fine pencil sketch"
            ],
            "style.pop_art": [
                "Make this vibrant pop art",
                "Make this colorful pop art",
                "Make this retro pop art",
                "Make this bold pop art",
                "Make this modern pop art"
            ],
            "style.comic_book": [
                "Make this a superhero comic book",
                "Make this a vintage comic book",
                "Make this a modern comic book",
                "Make this a detailed comic book",
                "Make this a colorful comic book"
            ],
            "style.cartoon_90s": [
                "Make this a retro 90s cartoon",
                "Make this a classic 90s cartoon",
                "Make this a vibrant 90s cartoon",
                "Make this a nostalgic 90s cartoon",
                "Make this a colorful 90s cartoon"
            ],
            "style.impressionist": [
                "Make this a soft impressionist painting",
                "Make this a colorful impressionist painting",
                "Make this a detailed impressionist painting",
                "Make this a classical impressionist painting",
                "Make this a modern impressionist painting"
            ],
            "style.vintage_photo": [
                "Make this a sepia vintage photo",
                "Make this a retro vintage photo",
                "Make this a classic vintage photo",
                "Make this an aged vintage photo",
                "Make this a nostalgic vintage photo"
            ],
            "style.sci_fi_art": [
                "Make this futuristic sci-fi art",
                "Make this cyberpunk sci-fi art",
                "Make this space-age sci-fi art",
                "Make this high-tech sci-fi art",
                "Make this dystopian sci-fi art"
            ],
            "style.art_nouveau": [
                "Make this elegant Art Nouveau style",
                "Make this ornate Art Nouveau style",
                "Make this flowing Art Nouveau style",
                "Make this decorative Art Nouveau style",
                "Make this intricate Art Nouveau style"
            ],
            "style.psychedelic": [
                "Make this vibrant psychedelic art",
                "Make this swirling psychedelic art",
                "Make this colorful psychedelic art",
                "Make this trippy psychedelic art",
                "Make this kaleidoscope psychedelic art"
            ],
            "style.renaissance": [
                "Make this a classical Renaissance painting",
                "Make this an elegant Renaissance painting",
                "Make this a detailed Renaissance painting",
                "Make this a masterful Renaissance painting",
                "Make this a traditional Renaissance painting"
            ],
            "style.pixel_art": [
                "Make this retro pixel art",
                "Make this 8-bit pixel art",
                "Make this colorful pixel art",
                "Make this detailed pixel art",
                "Make this game-style pixel art"
            ],
            "style.ukiyo_e": [
                "Make this a traditional Japanese woodblock print",
                "Make this an elegant Japanese woodblock print",
                "Make this a classic Japanese woodblock print",
                "Make this a detailed Japanese woodblock print",
                "Make this a colorful Japanese woodblock print"
            ],
            "style.film_noir": [
                "Make this dramatic film noir style",
                "Make this moody film noir style",
                "Make this classic film noir style",
                "Make this shadowy film noir style",
                "Make this atmospheric film noir style"
            ],
            
            # Object Edit Variations
            "object.hair_color": [
                "change hair color to brunette, preserve original face",
                "change hair color to auburn, preserve original face", 
                "change hair color to platinum blonde, preserve original face",
                "change hair color to copper red, preserve original face",
                "change hair color to honey blonde, preserve original face",
                "change hair color to chocolate brown, preserve original face",
                "change hair color to strawberry blonde, preserve original face",
                "change hair color to ash brown, preserve original face"
            ],
            "object.add_glasses": [
                "add stylish round glasses",
                "add modern rectangular glasses", 
                "add vintage round glasses",
                "add trendy square glasses",
                "add classic aviator glasses",
                "add designer cat-eye glasses"
            ],
            "object.change_outfit": [
                "change outfit to elegant business suit",
                "change outfit to modern business attire",
                "change outfit to professional suit",
                "change outfit to stylish business wear",
                "change outfit to formal business suit",
                "change outfit to contemporary business attire"
            ],
            "object.add_hat": [
                "add elegant black top hat",
                "add stylish black top hat",
                "add classic black top hat",
                "add vintage black top hat",
                "add formal black top hat"
            ],
            
            # Background Swap Variations  
            "bg.beach": [
                "Change background to a secluded tropical beach",
                "Change background to a sunset tropical beach",
                "Change background to a pristine tropical beach",
                "Change background to a golden sand tropical beach",
                "Change background to a turquoise water tropical beach"
            ],
            "bg.forest": [
                "Change background to a mystical lush forest",
                "Change background to a sunlit lush forest",
                "Change background to a dense lush forest", 
                "Change background to a peaceful lush forest",
                "Change background to a green lush forest"
            ],
            "bg.city": [
                "Change background to a bustling modern city",
                "Change background to a nighttime modern city",
                "Change background to a skyline modern city",
                "Change background to a vibrant modern city",
                "Change background to a futuristic modern city"
            ],
            "bg.space": [
                "Change background to deep outer space with nebula",
                "Change background to starry outer space with galaxies",
                "Change background to cosmic outer space with planets",
                "Change background to vast outer space with clusters",
                "Change background to mysterious outer space with aurora"
            ],
            "bg.snow_mountains": [
                "Change background to majestic snowy mountain peaks",
                "Change background to pristine snowy mountain peaks",
                "Change background to towering snowy mountain peaks",
                "Change background to serene snowy mountain peaks",
                "Change background to dramatic snowy mountain peaks"
            ],
            "bg.cherry_blossoms": [
                "Change background to blooming cherry blossom park",
                "Change background to peaceful cherry blossom park",
                "Change background to scenic cherry blossom park",
                "Change background to springtime cherry blossom park",
                "Change background to romantic cherry blossom park"
            ],
            "bg.medieval_castle": [
                "Change background to ancient medieval castle",
                "Change background to grand medieval castle",
                "Change background to fortress medieval castle",
                "Change background to stone medieval castle",
                "Change background to imposing medieval castle"
            ],
            "bg.fantasy_realm": [
                "Change background to enchanted magical fantasy landscape",
                "Change background to mystical magical fantasy landscape",
                "Change background to ethereal magical fantasy landscape",
                "Change background to otherworldly magical fantasy landscape",
                "Change background to dreamlike magical fantasy landscape"
            ],
            "bg.cyberpunk_city": [
                "Change background to glowing neon cyberpunk city",
                "Change background to futuristic neon cyberpunk city",
                "Change background to electric neon cyberpunk city",
                "Change background to dystopian neon cyberpunk city",
                "Change background to vibrant neon cyberpunk city"
            ],
            
            # Face Enhancement Variations
            "face.natural_smile": [
                "add warm subtle smile",
                "add gentle natural smile",
                "add soft subtle smile", 
                "add bright natural smile",
                "add peaceful subtle smile"
            ],
            "face.makeup": [
                "apply elegant professional makeup subtly",
                "apply natural professional makeup subtly",
                "apply modern professional makeup subtly",
                "apply sophisticated professional makeup subtly",
                "apply glamorous professional makeup subtly"
            ],
            "face.younger": [
                "make face look 5 years younger naturally",
                "make face look 5 years younger subtly",
                "make face look 5 years younger elegantly",
                "make face look 5 years younger gracefully",
                "make face look 5 years younger smoothly"
            ],
            "face.haircut": [
                "change haircut to stylish short bob",
                "change haircut to modern short bob",
                "change haircut to elegant short bob",
                "change haircut to trendy short bob",
                "change haircut to chic short bob"
            ],
            
            # Animation Variations (using kling_prompt)
            "anim.gentle_breeze": [
                "soft breeze animating hair and clothing naturally",
                "natural wind animating hair and clothing gently", 
                "light breeze animating hair and clothing smoothly",
                "calm breeze animating hair and clothing softly",
                "mild breeze animating hair and clothing gracefully"
            ],
            "anim.portrait_life": [
                "natural facial expressions and eye movement",
                "gentle facial expressions and eye movement",
                "soft facial expressions and eye movement",
                "realistic facial expressions and eye movement",
                "lifelike facial expressions and eye movement"
            ],
            "anim.sparkle_effects": [
                "glittering magical effects around the subject",
                "shimmering magical effects around the subject",
                "twinkling magical effects around the subject",
                "gleaming magical effects around the subject",
                "radiant magical effects around the subject"
            ],
            "anim.cinematic_zoom": [
                "smooth cinematic zoom in with subtle camera movement",
                "elegant cinematic zoom in with gentle camera movement",
                "professional cinematic zoom in with fluid camera movement",
                "artistic cinematic zoom in with graceful camera movement",
                "dramatic cinematic zoom in with controlled camera movement"
            ],
            "anim.moving_lights": [
                "shifting light reflections and ambient lighting changes",
                "flowing light reflections and ambient lighting changes", 
                "dancing light reflections and ambient lighting changes",
                "gentle light reflections and ambient lighting changes",
                "dynamic light reflections and ambient lighting changes"
            ],
            "anim.wind_effects": [
                "powerful wind effects with dynamic movement",
                "intense wind effects with flowing movement", 
                "dramatic wind effects with natural movement",
                "vigorous wind effects with elegant movement",
                "forceful wind effects with graceful movement"
            ],
            "anim.mystical_glow": [
                "ethereal glowing aura around the subject",
                "magical glowing aura around the subject",
                "enchanted glowing aura around the subject",
                "supernatural glowing aura around the subject",
                "divine glowing aura around the subject"
            ]
        }
        
        # Fallback variations for categories not specifically defined
        self.generic_variations = {
            "style_transfer": [
                ", artistic interpretation",
                ", creative style", 
                ", unique artistic approach",
                ", modern interpretation",
                ", distinctive style"
            ],
            "object_edit": [
                " with natural variation",
                " with subtle difference",
                " with slight modification", 
                " with artistic touch",
                " with refined approach"
            ],
            "background_swap": [
                " with atmospheric lighting",
                " with natural ambiance",
                " with scenic beauty",
                " with environmental depth", 
                " with immersive setting"
            ],
            "face_enhance": [
                " with natural enhancement",
                " with subtle refinement",
                " with gentle improvement",
                " with artistic touch",
                " with elegant result"
            ],
            "animate": [
                " with smooth motion",
                " with natural movement", 
                " with fluid animation",
                " with graceful dynamics",
                " with organic flow"
            ]
        }
    
    def get_varied_prompt(self, category: str, label_key: str, original_prompt: str, is_kling: bool = False) -> str:
        """
        Generate a varied prompt based on category and label key.
        
        Args:
            category: The processing category (style_transfer, object_edit, etc.)
            label_key: The specific option key (style.anime_style, bg.beach, etc.)
            original_prompt: The original prompt to vary
            is_kling: Whether this is for Kling animation (uses kling_prompt)
            
        Returns:
            A varied but similar prompt
        """
        import time
        start_time = time.time()
        
        # Log the request details
        request_details = {
            "category": category,
            "label_key": label_key,
            "original_prompt": original_prompt,
            "original_prompt_length": len(original_prompt),
            "is_kling": is_kling,
            "timestamp": time.time()
        }
        
        logger.info(f"🔄 PROMPT_VARIATION_START: {request_details}")
        
        try:
            logger.info(f"Generating prompt variation for {category}.{label_key}")
            
            # Special handling for hairstyle-related prompts
            if self._is_hairstyle_prompt(label_key, original_prompt):
                return self._generate_hairstyle_variation(label_key, original_prompt)
            
            # Try to get specific variations for this label key
            if label_key in self.variations:
                available_variations = self.variations[label_key]
                varied_prompt = random.choice(available_variations)
                
                success_details = {
                    "method": "specific_variation",
                    "label_key": label_key,
                    "available_count": len(available_variations),
                    "original_prompt": original_prompt,
                    "varied_prompt": varied_prompt,
                    "duration": time.time() - start_time
                }
                logger.info(f"✅ PROMPT_VARIATION_SUCCESS: {success_details}")
                logger.info(f"Using specific variation: '{varied_prompt}'")
                return varied_prompt
            
            # Fallback to generic variations for the category
            if category in self.generic_variations:
                available_suffixes = self.generic_variations[category]
                variation_suffix = random.choice(available_suffixes)
                varied_prompt = original_prompt + variation_suffix
                
                success_details = {
                    "method": "generic_variation",
                    "category": category,
                    "available_count": len(available_suffixes),
                    "original_prompt": original_prompt,
                    "varied_prompt": varied_prompt,
                    "suffix_used": variation_suffix,
                    "duration": time.time() - start_time
                }
                logger.info(f"✅ PROMPT_VARIATION_SUCCESS: {success_details}")
                logger.info(f"Using generic variation: '{varied_prompt}'")
                return varied_prompt
            
            # Last resort: add a simple variation
            simple_variations = [
                " with artistic flair",
                " with creative touch", 
                " with unique style",
                " with refined approach",
                " with natural variation"
            ]
            variation_suffix = random.choice(simple_variations)
            varied_prompt = original_prompt + variation_suffix
            
            fallback_details = {
                "method": "simple_fallback",
                "original_prompt": original_prompt,
                "varied_prompt": varied_prompt,
                "suffix_used": variation_suffix,
                "duration": time.time() - start_time,
                "reason": "no_specific_or_generic_variations_found"
            }
            logger.warning(f"⚠️  PROMPT_VARIATION_FALLBACK: {fallback_details}")
            logger.info(f"Using simple variation: '{varied_prompt}'")
            return varied_prompt
            
        except Exception as e:
            error_details = {
                "error": "variation_generation_failed",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "original_prompt": original_prompt,
                "duration": time.time() - start_time,
                "request_details": request_details
            }
            logger.error(f"❌ PROMPT_VARIATION_ERROR: {error_details}")
            logger.error(f"Error generating prompt variation: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Return original prompt as fallback
            return original_prompt
    
    def _is_hairstyle_prompt(self, label_key: str, prompt: str) -> bool:
        """Check if this is a hairstyle-related prompt."""
        hairstyle_keywords = [
            "RANDOM_HAIRSTYLE", "MODERN_HAIRSTYLE", "CLASSIC_HAIRSTYLE", 
            "EDGY_HAIRSTYLE", "UPDO_HAIRSTYLE", "CULTURAL_HAIRSTYLE", 
            "ANIME_HAIRSTYLE", "haircut", "hairstyle"
        ]
        return any(keyword in prompt or keyword in label_key for keyword in hairstyle_keywords)
    
    def _generate_hairstyle_variation(self, label_key: str, original_prompt: str) -> str:
        """Generate hairstyle variation using the specialized hairstyle generator."""
        if not hairstyle_generator:
            logger.warning("Hairstyle generator not available, using fallback")
            return original_prompt + ", preserve original face"
        
        try:
            # Determine which type of hairstyle generation to use
            if "RANDOM_HAIRSTYLE" in original_prompt:
                return hairstyle_generator.get_random_hairstyle(include_color=True, include_effects=False)
            elif "MODERN_HAIRSTYLE" in original_prompt:
                return hairstyle_generator.get_hairstyle_by_category("modern_trendy", include_color=True)
            elif "CLASSIC_HAIRSTYLE" in original_prompt:
                return hairstyle_generator.get_hairstyle_by_category("classic_timeless", include_color=True)
            elif "EDGY_HAIRSTYLE" in original_prompt:
                return hairstyle_generator.get_hairstyle_by_category("edgy_statement", include_color=True)
            elif "UPDO_HAIRSTYLE" in original_prompt:
                return hairstyle_generator.get_hairstyle_by_category("updos_braids", include_color=True)
            elif "CULTURAL_HAIRSTYLE" in original_prompt:
                return hairstyle_generator.get_hairstyle_by_category("cultural_traditional", include_color=True)
            elif "ANIME_HAIRSTYLE" in original_prompt:
                return hairstyle_generator.get_hairstyle_by_category("anime_inspired", include_color=True)
            elif "hair_color" in label_key:
                return hairstyle_generator.get_color_only_change()
            else:
                # General hairstyle variation
                return hairstyle_generator.get_random_hairstyle(include_color=False, include_effects=False)
                
        except Exception as e:
            logger.error(f"Error generating hairstyle variation: {e}")
            return original_prompt + ", preserve original face and facial features exactly"
    
    def get_random_seed(self) -> int:
        """Generate a random seed for additional variation."""
        import time
        seed = random.randint(1, 1000000)
        
        logger.debug(f"🎲 RANDOM_SEED_GENERATED: {{'seed': {seed}, 'timestamp': {time.time()}}}")
        return seed


# Global instance
prompt_variation_generator = PromptVariationGenerator() 