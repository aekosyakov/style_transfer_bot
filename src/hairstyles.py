"""
Comprehensive hairstyle database for focused hair transformations.
This system generates random hairstyles while preserving the original face.
"""

import random
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class HairstyleGenerator:
    """Generate random hairstyles with face-preserving prompts."""
    
    def __init__(self):
        # Modern & Trendy Cuts
        self.modern_trendy = [
            "Textured Crop Fade haircut",
            "French Crop with grown-out fringe haircut", 
            "Wolf Cut hairstyle",
            "Curtain Bangs Bob haircut",
            "Blunt Lob (Long Bob) haircut",
            "Jaw-Length Italian Bob haircut",
            "Shag Mullet hairstyle",
            "Undercut Pompadour haircut",
            "Skin-Fade Quiff hairstyle",
            "Disconnected Slick-Back haircut",
            "Burst-Fade Mohawk hairstyle",
            "Bubble Textured Pixie haircut",
            "Soft-Edge Caesar haircut"
        ]
        
        # Classic & Timeless
        self.classic_timeless = [
            "Side-Part Taper haircut",
            "1950s Slick-Back hairstyle",
            "Traditional Pompadour haircut",
            "Layered Shoulder-Length haircut",
            "Classic Pageboy haircut",
            "Classic Crew Cut haircut",
            "Ivy League (Princeton) haircut",
            "Finger-Wave Bob hairstyle",
            "Hollywood Veronica Lake Waves hairstyle",
            "Classic Chignon Bun hairstyle"
        ]
        
        # Fun / Edgy Statement Styles
        self.edgy_statement = [
            "Faux Hawk with shaved lines haircut",
            "Asymmetrical Undercut Bob haircut",
            "Rainbow Layered Shag hairstyle",
            "Two-Tone Split Dye Lob haircut",
            "Micro-Fringe Pixie haircut",
            "Geometric Bowl Cut 2.0 haircut",
            "Liberty Spikes hairstyle",
            "Heart-Shaped Space Buns hairstyle",
            "Reverse Mohawk haircut",
            "Braided Mohawk with Fade hairstyle"
        ]
        
        # Updos & Braids
        self.updos_braids = [
            "High Sleek Ponytail hairstyle",
            "Dutch Boxer Braids hairstyle",
            "Crown Halo Braid hairstyle",
            "Messy Textured Top Knot hairstyle",
            "Infinity Braid Ponytail hairstyle",
            "Fishtail Side Sweep hairstyle",
            "Gibson Tuck Roll hairstyle",
            "Bubble Ponytail hairstyle",
            "Waterfall Braid Cascade hairstyle",
            "Low Double Buns (Minnie Buns) hairstyle"
        ]
        
        # Cultural & Traditional Icons
        self.cultural_traditional = [
            "Samurai Topknot (Chonmage-inspired) hairstyle",
            "Victorian Gibson Girl Updo hairstyle",
            "1920s Finger Waves hairstyle",
            "Maang-Tikka Center-Part Braid hairstyle",
            "Fulani Feed-In Braids hairstyle",
            "Box Braids Bob hairstyle",
            "Afro Picked High hairstyle",
            "Cornrow Straight-Backs hairstyle",
            "Traditional Chinese Double-Loop Buns hairstyle",
            "Regency Ribbon-Tied Ringlets hairstyle"
        ]
        
        # Anime & Game-Inspired
        self.anime_inspired = [
            "Shōnen Gravity-Defying Spikes (Goku style) hairstyle",
            "Tri-Color Pharaoh Spikes (Yugi style) hairstyle",
            "Side-Swept Bangs with Ahoge (antenna sprout) hairstyle",
            "Odango Buns with Long Tails (Sailor Moon) hairstyle",
            "Twin Tails with Ribbons (Hatsune Miku length) hairstyle",
            "Spiky Wolf Ears Fringe (Inuyasha vibe) hairstyle",
            "Massive Drill Curls (Lady Oscar style) hairstyle",
            "Jagged Layered Emo Fringe (Sasuke style) hairstyle",
            "Short Bob with Cat Ears (Neko aesthetic) hairstyle",
            "Super Long Straight Hime Cut hairstyle"
        ]
        
        # Hair Colors & Effects
        self.hair_colors = [
            "platinum blonde",
            "honey blonde", 
            "strawberry blonde",
            "ash blonde",
            "copper red",
            "auburn red",
            "burgundy red",
            "chocolate brown",
            "ash brown",
            "caramel brown", 
            "jet black",
            "silver gray",
            "pastel pink",
            "lavender purple",
            "ocean blue",
            "mint green",
            "rose gold",
            "rainbow ombré",
            "galaxy gradient"
        ]
        
        # Hair Effects & Accessories
        self.hair_effects = [
            "with glitter highlights",
            "with neon tips",
            "with pastel ombré",
            "with galaxy gradient",
            "with butterfly clips",
            "with pearl hairpins",
            "with bandana wrap",
            "with patterned head-scarf",
            "with LED fiber optic strands",
            "with holographic highlights"
        ]
        
        # All categories combined for easy access
        self.all_categories = {
            "modern_trendy": self.modern_trendy,
            "classic_timeless": self.classic_timeless,
            "edgy_statement": self.edgy_statement,
            "updos_braids": self.updos_braids,
            "cultural_traditional": self.cultural_traditional,
            "anime_inspired": self.anime_inspired
        }
    
    def get_random_hairstyle(self, include_color: bool = True, include_effects: bool = False) -> str:
        """
        Generate a random hairstyle with optional color and effects.
        
        Args:
            include_color: Whether to include random hair color
            include_effects: Whether to include hair effects/accessories
            
        Returns:
            A complete hairstyle prompt focused only on hair changes
        """
        try:
            # Select random category and hairstyle
            category = random.choice(list(self.all_categories.keys()))
            hairstyles = self.all_categories[category]
            base_hairstyle = random.choice(hairstyles)
            
            # Build the prompt components
            prompt_parts = []
            
            # Always include the base hairstyle
            prompt_parts.append(f"change hairstyle to {base_hairstyle}")
            
            # Optionally add color
            if include_color and random.random() < 0.7:  # 70% chance to include color
                color = random.choice(self.hair_colors)
                prompt_parts.append(f"with {color} hair color")
            
            # Optionally add effects
            if include_effects and random.random() < 0.3:  # 30% chance for effects
                effect = random.choice(self.hair_effects)
                prompt_parts.append(effect)
            
            # Combine with face preservation instruction
            full_prompt = " ".join(prompt_parts) + ", preserve original face and facial features exactly"
            
            # Log the generation
            generation_info = {
                "category": category,
                "base_hairstyle": base_hairstyle,
                "include_color": include_color,
                "include_effects": include_effects,
                "final_prompt": full_prompt
            }
            logger.info(f"🎨 Generated hairstyle: {generation_info}")
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating random hairstyle: {e}")
            # Fallback to simple hairstyle
            return "change hairstyle to modern bob cut, preserve original face and facial features exactly"
    
    def get_hairstyle_by_category(self, category_name: str, include_color: bool = True) -> str:
        """
        Get a random hairstyle from a specific category.
        
        Args:
            category_name: Name of the category
            include_color: Whether to include random hair color
            
        Returns:
            A hairstyle prompt from the specified category
        """
        try:
            if category_name not in self.all_categories:
                logger.warning(f"Unknown hairstyle category: {category_name}")
                return self.get_random_hairstyle(include_color)
            
            hairstyles = self.all_categories[category_name]
            base_hairstyle = random.choice(hairstyles)
            
            prompt_parts = [f"change hairstyle to {base_hairstyle}"]
            
            if include_color and random.random() < 0.6:  # 60% chance for specific categories
                color = random.choice(self.hair_colors)
                prompt_parts.append(f"with {color} hair color")
            
            full_prompt = " ".join(prompt_parts) + ", preserve original face and facial features exactly"
            
            logger.info(f"🎨 Generated {category_name} hairstyle: {full_prompt}")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating hairstyle for category {category_name}: {e}")
            return self.get_random_hairstyle(include_color)
    
    def get_color_only_change(self) -> str:
        """Get a prompt that only changes hair color."""
        try:
            color = random.choice(self.hair_colors)
            prompt = f"change hair color to {color}, keep exact same hairstyle and preserve original face"
            
            logger.info(f"🎨 Generated color-only change: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating color change: {e}")
            return "change hair color to blonde, keep exact same hairstyle and preserve original face"
    
    def get_available_categories(self) -> List[str]:
        """Get list of available hairstyle categories."""
        return list(self.all_categories.keys())
    
    def get_category_info(self) -> Dict[str, int]:
        """Get information about available categories and their counts."""
        return {category: len(styles) for category, styles in self.all_categories.items()}


# Global instance
hairstyle_generator = HairstyleGenerator() 