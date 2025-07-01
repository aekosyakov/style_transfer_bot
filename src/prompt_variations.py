"""Prompt variation system for generating similar but different prompts on repeat."""

import random
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Import the hairstyle and dress generators
try:
    from src.hairstyles import hairstyle_generator
except ImportError:
    logger.warning("Could not import hairstyle_generator, hairstyle variations will be limited")
    hairstyle_generator = None

try:
    from src.dresses import dress_generator
except ImportError:
    logger.warning("Could not import dress_generator, dress variations will be limited")
    dress_generator = None

try:
    from src.mens_outfits import mens_outfit_generator
except ImportError:
    logger.warning("Could not import mens_outfit_generator, mens outfit variations will be limited")
    mens_outfit_generator = None

try:
    from src.mens_hairstyles import mens_hairstyle_generator
except ImportError:
    logger.warning("Could not import mens_hairstyle_generator, mens hairstyle variations will be limited")
    mens_hairstyle_generator = None

try:
    from src.womens_hairstyles import womens_hairstyle_generator
except ImportError:
    logger.warning("Could not import womens_hairstyle_generator, womens hairstyle variations will be limited")
    womens_hairstyle_generator = None


class PromptVariationGenerator:
    """Generate varied prompts while maintaining semantic similarity."""
    
    def __init__(self):
        self.variations = {
            # Cartoon Variations
            "cartoon.retro_classic": [
                "Make this a vintage retro classic cartoon",
                "Make this a nostalgic retro classic cartoon",
                "Make this a timeless retro classic cartoon",
                "Make this a charming retro classic cartoon",
                "Make this a colorful retro classic cartoon"
            ],
            "cartoon.80s_toon": [
                "Make this a vibrant 80s cartoon style",
                "Make this a neon 80s cartoon style",
                "Make this a retro 80s cartoon style",
                "Make this a classic 80s cartoon style",
                "Make this a nostalgic 80s cartoon style"
            ],
            "cartoon.90s_toon": [
                "Make this a retro 90s cartoon style",
                "Make this a classic 90s cartoon style",
                "Make this a vibrant 90s cartoon style",
                "Make this a nostalgic 90s cartoon style",
                "Make this a colorful 90s cartoon style"
            ],
            "cartoon.2000s_disney": [
                "Make this a modern 2000s Disney/Pixar style",
                "Make this a 3D 2000s Disney/Pixar style",
                "Make this a polished 2000s Disney/Pixar style",
                "Make this a smooth 2000s Disney/Pixar style",
                "Make this a detailed 2000s Disney/Pixar style"
            ],
            "cartoon.modern_3d": [
                "Make this a sleek modern 3D cartoon",
                "Make this a sophisticated modern 3D cartoon",
                "Make this a polished modern 3D cartoon",
                "Make this a detailed modern 3D cartoon",
                "Make this a vibrant modern 3D cartoon"
            ],
            "cartoon.saturday_morning": [
                "Make this a classic Saturday morning cartoon",
                "Make this a nostalgic Saturday morning cartoon",
                "Make this a colorful Saturday morning cartoon",
                "Make this a fun Saturday morning cartoon",
                "Make this a energetic Saturday morning cartoon"
            ],
            "cartoon.pixel_art": [
                "Make this a retro pixel art cartoon",
                "Make this an 8-bit pixel art cartoon",
                "Make this a colorful pixel art cartoon",
                "Make this a detailed pixel art cartoon",
                "Make this a game-style pixel art cartoon"
            ],

            # Anime Variations  
            "anime.magical_girl": [
                "Make this a sparkly magical girl/shojo anime style",
                "Make this an elegant magical girl/shojo anime style",
                "Make this a colorful magical girl/shojo anime style",
                "Make this a detailed magical girl/shojo anime style",
                "Make this a romantic magical girl/shojo anime style"
            ],
            "anime.shonen_action": [
                "Make this an intense shōnen action anime style",
                "Make this a dynamic shōnen action anime style",
                "Make this an energetic shōnen action anime style",
                "Make this a powerful shōnen action anime style",
                "Make this a heroic shōnen action anime style"
            ],
            "anime.studio_ghibli": [
                "Make this a magical Studio Ghibli anime style",
                "Make this a whimsical Studio Ghibli anime style",
                "Make this a detailed Studio Ghibli anime style",
                "Make this a dreamy Studio Ghibli anime style",
                "Make this a beautiful Studio Ghibli anime style"
            ],
            "anime.classic_90s": [
                "Make this a nostalgic 90s classic anime style",
                "Make this a traditional 90s classic anime style",
                "Make this a retro 90s classic anime style",
                "Make this a detailed 90s classic anime style",
                "Make this a authentic 90s classic anime style"
            ],
            "anime.chibi_kawaii": [
                "Make this an adorable chibi/kawaii anime style",
                "Make this a cute chibi/kawaii anime style",
                "Make this a super kawaii chibi anime style",
                "Make this a sweet chibi/kawaii anime style",
                "Make this a colorful chibi/kawaii anime style"
            ],
            "anime.cyberpunk": [
                "Make this a futuristic cyberpunk anime style",
                "Make this a neon cyberpunk anime style",
                "Make this a dark cyberpunk anime style",
                "Make this a high-tech cyberpunk anime style",
                "Make this a dystopian cyberpunk anime style"
            ],
            "anime.webtoon": [
                "Make this a modern webtoon/manhwa style",
                "Make this a colorful webtoon/manhwa style",
                "Make this a detailed webtoon/manhwa style",
                "Make this a stylized webtoon/manhwa style",
                "Make this a romantic webtoon/manhwa style"
            ],
            "anime.princess_royal": [
                "Make this an elegant princess/royal anime style",
                "Make this a regal princess/royal anime style",
                "Make this a graceful princess/royal anime style",
                "Make this a majestic princess/royal anime style",
                "Make this a beautiful princess/royal anime style"
            ],

            # Comics Variations
            "comics.western_comic": [
                "Make this a classic western comic book style",
                "Make this a vintage western comic book style",
                "Make this a colorful western comic book style",
                "Make this a detailed western comic book style",
                "Make this a superhero western comic book style"
            ],
            "comics.newspaper_strip": [
                "Make this a classic newspaper comic strip style",
                "Make this a vintage newspaper comic strip style",
                "Make this a simple newspaper comic strip style",
                "Make this a humorous newspaper comic strip style",
                "Make this a daily newspaper comic strip style"
            ],
            "comics.noir_comic": [
                "Make this a dark noir comic style",
                "Make this a shadowy noir comic style",
                "Make this a dramatic noir comic style",
                "Make this a moody noir comic style",
                "Make this a atmospheric noir comic style"
            ],
            "comics.manga_bw": [
                "Make this a detailed black and white manga style",
                "Make this a traditional black and white manga style",
                "Make this a authentic black and white manga style",
                "Make this a classic black and white manga style",
                "Make this a professional black and white manga style"
            ],
            "comics.pop_art_comic": [
                "Make this a vibrant pop art comic style",
                "Make this a colorful pop art comic style",
                "Make this a bold pop art comic style",
                "Make this a retro pop art comic style",
                "Make this a modern pop art comic style"
            ],
            "comics.adult_animation": [
                "Make this a sophisticated adult animation style",
                "Make this a mature adult animation style",
                "Make this a detailed adult animation style",
                "Make this a stylized adult animation style",
                "Make this a modern adult animation style"
            ],
            "comics.superhero_classic": [
                "Make this a heroic classic superhero comic style",
                "Make this a vintage classic superhero comic style",
                "Make this a dramatic classic superhero comic style",
                "Make this a powerful classic superhero comic style",
                "Make this a colorful classic superhero comic style"
            ],

            # Art Styles Variations
            "art.pencil_sketch": [
                "Make this a detailed pencil sketch",
                "Make this a soft pencil sketch",
                "Make this a realistic pencil sketch",
                "Make this an artistic pencil sketch",
                "Make this a fine pencil sketch"
            ],
            "art.digital_art": [
                "Make this modern digital art",
                "Make this stylized digital art",
                "Make this vibrant digital art", 
                "Make this detailed digital art",
                "Make this contemporary digital art"
            ],
            "art.pop_art": [
                "Make this vibrant pop art",
                "Make this colorful pop art",
                "Make this retro pop art",
                "Make this bold pop art",
                "Make this modern pop art"
            ],
            "art.impressionist": [
                "Make this a soft impressionist painting",
                "Make this a colorful impressionist painting",
                "Make this a detailed impressionist painting",
                "Make this a classical impressionist painting",
                "Make this a modern impressionist painting"
            ],
            "art.renaissance": [
                "Make this a classical Renaissance painting",
                "Make this an elegant Renaissance painting",
                "Make this a detailed Renaissance painting",
                "Make this a masterful Renaissance painting",
                "Make this a traditional Renaissance painting"
            ],
            "art.psychedelic": [
                "Make this vibrant psychedelic art",
                "Make this swirling psychedelic art",
                "Make this colorful psychedelic art",
                "Make this trippy psychedelic art",
                "Make this kaleidoscope psychedelic art"
            ],
            "art.art_nouveau": [
                "Make this elegant Art Nouveau style",
                "Make this ornate Art Nouveau style",
                "Make this flowing Art Nouveau style",
                "Make this decorative Art Nouveau style",
                "Make this intricate Art Nouveau style"
            ],
            "art.vintage_photo": [
                "Make this a sepia vintage photo",
                "Make this a retro vintage photo",
                "Make this a classic vintage photo",
                "Make this an aged vintage photo",
                "Make this a nostalgic vintage photo"
            ],
            "art.sci_fi_art": [
                "Make this futuristic sci-fi art",
                "Make this cyberpunk sci-fi art",
                "Make this space-age sci-fi art",
                "Make this high-tech sci-fi art",
                "Make this dystopian sci-fi art"
            ],
            "art.ukiyo_e": [
                "Make this a traditional Japanese woodblock print",
                "Make this an elegant Japanese woodblock print",
                "Make this a classic Japanese woodblock print",
                "Make this a detailed Japanese woodblock print",
                "Make this a colorful Japanese woodblock print"
            ],
            "art.film_noir": [
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
            "cartoon": [
                ", animated interpretation",
                ", cartoon style", 
                ", unique cartoon approach",
                ", modern cartoon interpretation",
                ", distinctive cartoon style"
            ],
            "anime": [
                ", anime interpretation",
                ", anime style", 
                ", unique anime approach",
                ", modern anime interpretation",
                ", distinctive anime style"
            ],
            "comics": [
                ", comic interpretation",
                ", comic style", 
                ", unique comic approach",
                ", modern comic interpretation",
                ", distinctive comic style"
            ],
            "art_styles": [
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
    
    def get_varied_prompt(self, category: str, label_key: str, original_prompt: str, is_kling: bool = False, preserve_gender: str = 'neutral') -> str:
        """
        Generate a varied prompt based on category and label key.
        
        Args:
            category: The processing category (style_transfer, object_edit, etc.)
            label_key: The specific option key (style.anime_style, bg.beach, etc.)
            original_prompt: The original prompt to vary
            is_kling: Whether this is for Kling animation (uses kling_prompt)
            preserve_gender: Gender to preserve ('men', 'women', 'neutral')
            
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
            
            # Special handling for dress-related prompts with gender preservation
            if self._is_dress_prompt(label_key, original_prompt):
                return self._generate_dress_variation(label_key, original_prompt, preserve_gender)
            
            # Handle random placeholders for new categories
            if any(placeholder in original_prompt for placeholder in ['RANDOM_CARTOON', 'RANDOM_ANIME', 'RANDOM_COMICS', 'RANDOM_ART_STYLE']):
                return self._generate_random_category_variation(original_prompt)
            
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
            "ANIME_HAIRSTYLE", "haircut", "hairstyle", "hair.",
            
            # Men's hairstyle placeholders - NEW ERA-SPECIFIC STYLES
            "EIGHTIES_POWER_BUSINESS_HAIR", "NINETIES_GRUNGE_REBEL", "Y2K_TECH_STYLE",
            "OLD_MONEY_GENTLEMAN_HAIR", "HOLLYWOOD_LEADING_MAN", "URBAN_STREETWEAR_HAIR_MEN",
            "GENZ_TIKTOK_HAIR", "DISCO_RETRO_HAIR",
            
            # Women's hairstyle placeholders - NEW ERA-SPECIFIC STYLES  
            "EIGHTIES_BIG_HAIR", "NINETIES_GRUNGE_LAYERS", "Y2K_CYBER_GLAM",
            "OLD_MONEY_ELEGANCE", "HOLLYWOOD_RED_CARPET", "URBAN_STREETWEAR_HAIR",
            "GENZ_VIRAL_HAIR", "DISCO_ERA_FEATHERS",
            
            # Gender-specific hairstyle placeholders - LEGACY (CRITICAL FOR DETECTION!)
            "RANDOM_MENS_HAIRSTYLE", "MODERN_MENS_HAIRSTYLE", "CLASSIC_MENS_HAIRSTYLE",
            "EDGY_MENS_HAIRSTYLE", "CULTURAL_MENS_HAIRSTYLE", "ANIME_MENS_HAIRSTYLE",
            "RANDOM_WOMENS_HAIRSTYLE", "MODERN_WOMENS_HAIRSTYLE", "CLASSIC_WOMENS_HAIRSTYLE",
            "EDGY_WOMENS_HAIRSTYLE", "CULTURAL_WOMENS_HAIRSTYLE", "ANIME_WOMENS_HAIRSTYLE"
        ]
        
        is_hairstyle = any(keyword in prompt or keyword in label_key for keyword in hairstyle_keywords)
        
        # Debug logging for hairstyle detection
        matching_keywords = [k for k in hairstyle_keywords if k in prompt or k in label_key]
        logger.info(f"🔍 HAIRSTYLE_DETECTION: label_key='{label_key}', prompt='{prompt}' -> {is_hairstyle}")
        if matching_keywords:
            logger.info(f"   ✅ Matching keywords: {matching_keywords}")
        else:
            logger.info(f"   ❌ No matching keywords found")
            
        return is_hairstyle
    
    def _is_dress_prompt(self, label_key: str, prompt: str) -> bool:
        """Check if this is a dress/outfit-related prompt."""
        dress_keywords = [
            # Women's dress placeholders
            "RANDOM_DRESS", "NINETIES_REVIVAL_DRESS", "EIGHTIES_POWER_POP_DRESS",
            "OLD_MONEY_STYLE_DRESS", "DISCO_GLAM_DRESS", "Y2K_FUTURIST_DRESS",
            "HOLLYWOOD_GLAMOUR_DRESS", "URBAN_STREETSTYLE_DRESS", "GENZ_VIRAL_MIX_DRESS",
            "MODERN_DRESS", "CLASSIC_DRESS", "EDGY_DRESS", "EVENING_DRESS", 
            "CULTURAL_DRESS", "ANIME_DRESS", "CASUAL_OUTFIT", "dress.", "outfit",
            
            # Men's outfit placeholders - NEW ERA-SPECIFIC
            "EIGHTIES_POWER_BUSINESS", "NINETIES_GRUNGE_OUTFIT", "OLD_MONEY_GENTLEMAN",
            "DISCO_RETRO_STYLE", "Y2K_CYBER_STYLE", "HOLLYWOOD_CLASSIC",
            "URBAN_STREETWEAR", "GENZ_VIRAL_TRENDS",
            
            # Men's outfit placeholders - LEGACY
            "RANDOM_MENS_OUTFIT", "CASUAL_MENS_OUTFIT", "MODERN_MENS_OUTFIT",
            "CLASSIC_MENS_OUTFIT", "EDGY_MENS_OUTFIT", "EVENING_MENS_OUTFIT",
            "CULTURAL_MENS_OUTFIT", "ANIME_MENS_OUTFIT", "mens."
        ]
        return any(keyword in prompt or keyword in label_key for keyword in dress_keywords)
    
    def _generate_hairstyle_variation(self, label_key: str, original_prompt: str) -> str:
        """Generate hairstyle variation using the specialized hairstyle generator."""
        if not hairstyle_generator:
            logger.warning("Hairstyle generator not available, using fallback")
            return original_prompt + ", preserve original face"
        
        try:
            # IMPORTANT: Check gender-specific patterns FIRST before general patterns
            # to avoid both men's and women's hairstyles matching "RANDOM_HAIRSTYLE"
            
            # Men's era-specific hairstyles (NEW CATEGORIES)
            if "EIGHTIES_POWER_BUSINESS_HAIR" in original_prompt:
                logger.info("🎯 Generating 80s power business men's hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("eighties_power_business", include_color=True)
            elif "NINETIES_GRUNGE_REBEL" in original_prompt:
                logger.info("🎯 Generating 90s grunge rebel men's hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("nineties_grunge_rebel", include_color=True)
            elif "Y2K_TECH_STYLE" in original_prompt:
                logger.info("🎯 Generating Y2K tech style men's hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("y2k_tech_style", include_color=True)
            elif "OLD_MONEY_GENTLEMAN_HAIR" in original_prompt:
                logger.info("🎯 Generating old money gentleman men's hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("old_money_gentleman", include_color=True)
            elif "HOLLYWOOD_LEADING_MAN" in original_prompt:
                logger.info("🎯 Generating Hollywood leading man hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("hollywood_leading_man", include_color=True)
            elif "URBAN_STREETWEAR_HAIR_MEN" in original_prompt:
                logger.info("🎯 Generating urban streetwear men's hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("urban_streetwear", include_color=True)
            elif "GENZ_TIKTOK_HAIR" in original_prompt:
                logger.info("🎯 Generating Gen-Z TikTok men's hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("genz_tiktok", include_color=True)
            elif "DISCO_RETRO_HAIR" in original_prompt:
                logger.info("🎯 Generating disco retro men's hairstyle")
                return mens_hairstyle_generator.get_hairstyle_by_category("disco_retro", include_color=True)
                
            # Women's era-specific hairstyles (NEW CATEGORIES)
            elif "EIGHTIES_BIG_HAIR" in original_prompt:
                logger.info("🎯 Generating 80s big hair women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("eighties_big_hair", include_color=True)
            elif "NINETIES_GRUNGE_LAYERS" in original_prompt:
                logger.info("🎯 Generating 90s grunge layers women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("nineties_grunge_layers", include_color=True)
            elif "Y2K_CYBER_GLAM" in original_prompt:
                logger.info("🎯 Generating Y2K cyber glam women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("y2k_cyber_glam", include_color=True)
            elif "OLD_MONEY_ELEGANCE" in original_prompt:
                logger.info("🎯 Generating old money elegance women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("old_money_elegance", include_color=True)
            elif "HOLLYWOOD_RED_CARPET" in original_prompt:
                logger.info("🎯 Generating Hollywood red carpet women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("hollywood_red_carpet", include_color=True)
            elif "URBAN_STREETWEAR_HAIR" in original_prompt:
                logger.info("🎯 Generating urban streetwear women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("urban_streetwear", include_color=True)
            elif "GENZ_VIRAL_HAIR" in original_prompt:
                logger.info("🎯 Generating Gen-Z viral women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("genz_viral_hair", include_color=True)
            elif "DISCO_ERA_FEATHERS" in original_prompt:
                logger.info("🎯 Generating disco era feathers women's hairstyle")
                return womens_hairstyle_generator.get_hairstyle_by_category("disco_era_feathers", include_color=True)
                
            # Gender-specific random hairstyles (LEGACY)
            elif "RANDOM_MENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating random men's hairstyle")
                return hairstyle_generator.get_mens_hairstyle(include_color=True, include_effects=False)
            elif "RANDOM_WOMENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating random women's hairstyle")
                return hairstyle_generator.get_womens_hairstyle(include_color=True, include_effects=False)
            
            # Gender-specific category hairstyles
            elif "MODERN_MENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating modern men's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('men', 'modern_trendy', include_color=True)
            elif "CLASSIC_MENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating classic men's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('men', 'classic_timeless', include_color=True)
            elif "EDGY_MENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating edgy men's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('men', 'edgy_statement', include_color=True)
            elif "CULTURAL_MENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating cultural men's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('men', 'cultural_traditional', include_color=True)
            elif "ANIME_MENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating anime men's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('men', 'anime_inspired', include_color=True)
            
            elif "MODERN_WOMENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating modern women's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('women', 'modern_trendy', include_color=True)
            elif "CLASSIC_WOMENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating classic women's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('women', 'classic_timeless', include_color=True)
            elif "EDGY_WOMENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating edgy women's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('women', 'edgy_statement', include_color=True)
            elif "CULTURAL_WOMENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating cultural women's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('women', 'cultural_traditional', include_color=True)
            elif "ANIME_WOMENS_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating anime women's hairstyle")
                return hairstyle_generator.get_hairstyle_by_gender_and_category('women', 'anime_inspired', include_color=True)
            
            # Gender-neutral/general patterns (check AFTER gender-specific patterns)
            elif "RANDOM_HAIRSTYLE" in original_prompt:
                logger.info("🎯 Generating general random hairstyle")
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
                logger.info("🎯 Generating general hairstyle variation")
                return hairstyle_generator.get_random_hairstyle(include_color=False, include_effects=False)
                
        except Exception as e:
            logger.error(f"Error generating hairstyle variation: {e}")
            return original_prompt + ", preserve original face, facial features, and skin color exactly"
    
    def _generate_dress_variation(self, label_key: str, original_prompt: str, preserve_gender: str = 'neutral') -> str:
        """Generate dress variation using the specialized dress generator with gender preservation."""
        # Determine gender from preserve_gender parameter or original prompt
        is_mens_prompt = (preserve_gender == 'men' or 
                         any(keyword in original_prompt for keyword in [
                             # New era-specific men's placeholders
                             "EIGHTIES_POWER_BUSINESS", "NINETIES_GRUNGE_OUTFIT", "OLD_MONEY_GENTLEMAN",
                             "DISCO_RETRO_STYLE", "Y2K_CYBER_STYLE", "HOLLYWOOD_CLASSIC",
                             "URBAN_STREETWEAR", "GENZ_VIRAL_TRENDS",
                             # Legacy men's placeholders
                             "RANDOM_MENS_OUTFIT", "CASUAL_MENS_OUTFIT", "MODERN_MENS_OUTFIT", 
                             "CLASSIC_MENS_OUTFIT", "EDGY_MENS_OUTFIT", "EVENING_MENS_OUTFIT", 
                             "CULTURAL_MENS_OUTFIT", "ANIME_MENS_OUTFIT"
                         ]))
        
        is_womens_prompt = (preserve_gender == 'women' or 
                           any(keyword in original_prompt for keyword in ["RANDOM_DRESS", "MODERN_DRESS", "CLASSIC_DRESS", "EDGY_DRESS", "EVENING_DRESS", "CULTURAL_DRESS", "ANIME_DRESS", "CASUAL_OUTFIT"]))
        
        logger.info(f"🎯 Gender preservation: preserve_gender='{preserve_gender}', is_mens={is_mens_prompt}, is_womens={is_womens_prompt}")
        
        # Handle men's outfit prompts
        if is_mens_prompt:
            if not mens_outfit_generator:
                logger.warning("Men's outfit generator not available, using fallback")
                return original_prompt + ", preserve original face, body, and skin color"
            
            try:
                # Determine which type of men's outfit generation to use
                # New era-specific categories (matching women's approach)
                if "EIGHTIES_POWER_BUSINESS" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("eighties_power_business", include_color=True, include_material=True)
                elif "NINETIES_GRUNGE_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("nineties_grunge_style", include_color=True, include_material=True)
                elif "OLD_MONEY_GENTLEMAN" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("old_money_gentleman", include_color=True, include_material=True)
                elif "DISCO_RETRO_STYLE" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("disco_retro_style", include_color=True, include_material=True)
                elif "Y2K_CYBER_STYLE" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("y2k_cyber_style", include_color=True, include_material=True)
                elif "HOLLYWOOD_CLASSIC" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("hollywood_classic", include_color=True, include_material=True)
                elif "URBAN_STREETWEAR" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("urban_streetwear", include_color=True, include_material=True)
                elif "GENZ_VIRAL_TRENDS" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("genz_viral_trends", include_color=True, include_material=True)
                
                # Legacy categories (for backward compatibility)
                elif "RANDOM_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_random_outfit(include_color=True, include_material=True, include_effects=False)
                elif "CASUAL_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_casual_outfit()
                elif "MODERN_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("modern_trendy", include_color=True, include_material=True)
                elif "CLASSIC_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("classic_timeless", include_color=True, include_material=True)
                elif "EDGY_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("edgy_statement", include_color=True, include_material=True)
                elif "EVENING_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("evening_occasion", include_color=True, include_material=True)
                elif "CULTURAL_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("cultural_traditional", include_color=True, include_material=True)
                elif "ANIME_MENS_OUTFIT" in original_prompt:
                    return mens_outfit_generator.get_outfit_by_category("anime_inspired", include_color=True, include_material=True)
                else:
                    # General men's outfit variation
                    return mens_outfit_generator.get_random_outfit(include_color=True, include_material=True, include_effects=False)
                    
            except Exception as e:
                logger.error(f"Error generating men's outfit variation: {e}")
                return original_prompt + ", preserve original face, body proportions, and skin color exactly"
        
        # Handle women's dress prompts or default when gender is neutral/ambiguous
        if is_womens_prompt or (preserve_gender == 'neutral' and not is_mens_prompt):
            if not dress_generator:
                logger.warning("Dress generator not available, using fallback")
                return original_prompt + ", preserve original face, body, and skin color"
        
        try:
            # Determine which type of dress generation to use
            if "RANDOM_DRESS" in original_prompt:
                return dress_generator.get_random_dress(include_color=True, include_material=True, include_effects=False)
            # New trendy categories
            elif "NINETIES_REVIVAL_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("nineties_revival", include_color=True, include_material=True)
            elif "EIGHTIES_POWER_POP_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("eighties_power_pop", include_color=True, include_material=True)
            elif "OLD_MONEY_STYLE_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("old_money_style", include_color=True, include_material=True)
            elif "DISCO_GLAM_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("disco_glam", include_color=True, include_material=True)
            elif "Y2K_FUTURIST_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("y2k_futurist", include_color=True, include_material=True)
            elif "HOLLYWOOD_GLAMOUR_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("hollywood_glamour", include_color=True, include_material=True)
            elif "URBAN_STREETSTYLE_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("urban_streetstyle", include_color=True, include_material=True)
            elif "GENZ_VIRAL_MIX_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("genz_viral_mix", include_color=True, include_material=True)
            # Legacy categories (for backward compatibility)
            elif "MODERN_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("nineties_revival", include_color=True, include_material=True)  # Map to closest new category
            elif "CLASSIC_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("old_money_style", include_color=True, include_material=True)  # Map to closest new category
            elif "EDGY_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("y2k_futurist", include_color=True, include_material=True)  # Map to closest new category
            elif "EVENING_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("hollywood_glamour", include_color=True, include_material=True)  # Map to closest new category
            elif "CULTURAL_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("old_money_style", include_color=True, include_material=True)  # Map to closest new category
            elif "ANIME_DRESS" in original_prompt:
                return dress_generator.get_dress_by_category("genz_viral_mix", include_color=True, include_material=True)  # Map to closest new category
            elif "CASUAL_OUTFIT" in original_prompt:
                return dress_generator.get_casual_outfit()
            elif "change_outfit" in label_key or "outfit" in original_prompt:
                return dress_generator.get_random_dress(include_color=True, include_material=False, include_effects=False)
            else:
                # General dress variation
                return dress_generator.get_random_dress(include_color=True, include_material=True, include_effects=False)
                
        except Exception as e:
            logger.error(f"Error generating dress variation: {e}")
            return original_prompt + ", preserve original face, body proportions, and skin color exactly"
        
        # If we reach here, handle cases where preserve_gender is set but no specific prompt detected
        if preserve_gender == 'men' and mens_outfit_generator:
            logger.info(f"🎯 Forcing men's outfit generation due to preserve_gender='men'")
            try:
                return mens_outfit_generator.get_random_outfit(include_color=True, include_material=True, include_effects=False)
            except Exception as e:
                logger.error(f"Error generating forced men's outfit: {e}")
                return "change outfit to casual men's shirt and pants, preserve original face, body proportions, and skin color exactly"
        
        elif preserve_gender == 'women' and dress_generator:
            logger.info(f"🎯 Forcing women's dress generation due to preserve_gender='women'")
            try:
                return dress_generator.get_random_dress(include_color=True, include_material=True, include_effects=False)
            except Exception as e:
                logger.error(f"Error generating forced women's dress: {e}")
                return "change outfit to elegant dress, preserve original face, body proportions, and skin color exactly"
        
        # Ultimate fallback
        logger.warning(f"⚠️ No gender-specific generation possible, using original prompt")
        return original_prompt + ", preserve original face, body proportions, and skin color exactly"
    
    def _generate_random_category_variation(self, original_prompt: str) -> str:
        """Generate variation for random category placeholders."""
        try:
            if 'RANDOM_CARTOON' in original_prompt:
                cartoon_styles = [
                    "Make this a retro classic cartoon",
                    "Make this an 80s cartoon style",
                    "Make this a 90s cartoon style", 
                    "Make this a 2000s Disney/Pixar style",
                    "Make this a modern 3D cartoon",
                    "Make this a Saturday morning cartoon",
                    "Make this a pixel art cartoon"
                ]
                return random.choice(cartoon_styles)
                
            elif 'RANDOM_ANIME' in original_prompt:
                anime_styles = [
                    "Make this a magical girl/shojo anime style",
                    "Make this a shōnen action anime style",
                    "Make this a Studio Ghibli anime style",
                    "Make this a 90s classic anime style",
                    "Make this a chibi/kawaii anime style",
                    "Make this a cyberpunk anime style",
                    "Make this a webtoon/manhwa style",
                    "Make this a princess/royal anime style"
                ]
                return random.choice(anime_styles)
                
            elif 'RANDOM_COMICS' in original_prompt:
                comic_styles = [
                    "Make this a western comic book style",
                    "Make this a newspaper comic strip style",
                    "Make this a noir comic style",
                    "Make this a black and white manga style",
                    "Make this a pop art comic style",
                    "Make this an adult animation style",
                    "Make this a classic superhero comic style"
                ]
                return random.choice(comic_styles)
                
            elif 'RANDOM_ART_STYLE' in original_prompt:
                art_styles = [
                    "Make this a pencil sketch",
                    "Make this digital art",
                    "Make this pop art",
                    "Make this an impressionist painting",
                    "Make this a Renaissance painting",
                    "Make this psychedelic art",
                    "Make this Art Nouveau style",
                    "Make this a vintage photo",
                    "Make this sci-fi art",
                    "Make this a Japanese woodblock print",
                    "Make this film noir style"
                ]
                return random.choice(art_styles)
                
            else:
                # Fallback to original if no match
                return original_prompt + " with artistic variation"
                
        except Exception as e:
            logger.error(f"Error generating random category variation: {e}")
            return original_prompt

    def get_random_seed(self) -> int:
        """Generate a random seed for additional variation."""
        import time
        seed = random.randint(1, 1000000)
        
        logger.debug(f"🎲 RANDOM_SEED_GENERATED: {{'seed': {seed}, 'timestamp': {time.time()}}}")
        return seed


# Global instance
prompt_variation_generator = PromptVariationGenerator() 