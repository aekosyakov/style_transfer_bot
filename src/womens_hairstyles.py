"""
Comprehensive women's hairstyle database for focused hair transformations.
This system generates random women's hairstyles while preserving the original face.
"""

import random
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class WomensHairstyleGenerator:
    """Generate random women's hairstyles with face-preserving prompts."""
    
    def __init__(self):
        # Modern & Trendy
        self.modern_trendy = [
            "Long Textured Waves",
            "Curtain Bangs Bob",
            "Wolf Cut with Shaggy Layers",
            "French Girl Chin Bob",
            "Sleek High Ponytail",
            "Airy Pixie with Side Bangs",
            "Face-Framing Layered Lob",
            "Blunt Cut with Micro Fringe",
            "Bubble Braids",
            "Half-Up Space Buns"
        ]

        # Classic & Timeless
        self.classic_timeless = [
            "Hollywood Glamour Waves",
            "Elegant Chignon Bun",
            "Soft Romantic Curls",
            "Traditional French Twist",
            "Pinned-Back Half Updo",
            "Pageboy with Side Part",
            "Long Straight Center Part",
            "Voluminous 1960s Beehive",
            "Classic Side Braid",
            "Retro Victory Rolls"
        ]

        # Edgy / Statement
        self.edgy_statement = [
            "Undercut with Shaved Design",
            "Rainbow Balayage Layers",
            "Asymmetrical Lob",
            "Geometric Bowl Cut",
            "Two-Tone Split Dye",
            "Extra Long Rapunzel Braid",
            "Shaggy Mullet with Bangs",
            "High-Contrast Roots",
            "Micro Braided Top Knots",
            "Faux Hawk Ponytail"
        ]

        # Cultural & Traditional
        self.cultural_traditional = [
            "Traditional Japanese Shimada Bun",
            "Chinese Double-Loop Buns",
            "Indian Bridal Braided Updo",
            "Fulani Braids with Beads",
            "West African Cornrows",
            "Victorian Ringlet Curls",
            "Renaissance Crown Braid",
            "Greek Goddess Updo",
            "Spanish Flamenco Low Bun",
            "Russian Kokoshnik Braids"
        ]

        # Anime & Game-Inspired (content-safe descriptions)
        self.anime_inspired = [
            "Twin Tails with Ribbons",
            "Double Buns with Long Pigtails",
            "Super Spiky Heroine Cut",
            "Mega-Volume Drill Curls",
            "Cat Ear Buns",
            "Long Hime Cut with Face Panels",
            "Jagged Side Bangs",
            "Rainbow Gradient Layered Hair",
            "Oversized Clip Accessories",
            "Holographic Anime Bob"
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
            "cultural_traditional": self.cultural_traditional,
            "anime_inspired": self.anime_inspired
        }

    def get_random_hairstyle(self, include_color: bool = True, include_effects: bool = False) -> str:
        """
        Generate a random women's hairstyle with optional color and effects.
        
        Args:
            include_color: Whether to include random hair color
            include_effects: Whether to include hair effects/accessories
            
        Returns:
            A complete women's hairstyle prompt focused only on hair changes
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
            logger.info(f"💇‍♀️ Generated women's hairstyle: {generation_info}")
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating random women's hairstyle: {e}")
            # Fallback to simple hairstyle
            return "change hairstyle to modern bob cut, preserve original face and facial features exactly"

    def get_hairstyle_by_category(self, category_name: str, include_color: bool = True) -> str:
        """
        Get a random women's hairstyle from a specific category.
        
        Args:
            category_name: Name of the category
            include_color: Whether to include random hair color
            
        Returns:
            A women's hairstyle prompt from the specified category
        """
        try:
            if category_name not in self.all_categories:
                logger.warning(f"Unknown women's hairstyle category: {category_name}")
                return self.get_random_hairstyle(include_color)
            
            hairstyles = self.all_categories[category_name]
            base_hairstyle = random.choice(hairstyles)
            
            prompt_parts = [f"change hairstyle to {base_hairstyle}"]
            
            if include_color and random.random() < 0.6:  # 60% chance for specific categories
                color = random.choice(self.hair_colors)
                prompt_parts.append(f"with {color} hair color")
            
            full_prompt = " ".join(prompt_parts) + ", preserve original face and facial features exactly"
            
            logger.info(f"💇‍♀️ Generated {category_name} women's hairstyle: {full_prompt}")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating women's hairstyle for category {category_name}: {e}")
            return self.get_random_hairstyle(include_color)

    def get_color_only_change(self) -> str:
        """Get a prompt that only changes hair color."""
        try:
            color = random.choice(self.hair_colors)
            prompt = f"change hair color to {color}, keep exact same hairstyle and preserve original face"
            
            logger.info(f"💇‍♀️ Generated women's color-only change: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating women's color change: {e}")
            return "change hair color to blonde, keep exact same hairstyle and preserve original face"

    def get_available_categories(self) -> List[str]:
        """Get list of available women's hairstyle categories."""
        return list(self.all_categories.keys())

    def get_category_info(self) -> Dict[str, int]:
        """Get information about available categories and their counts."""
        return {category: len(styles) for category, styles in self.all_categories.items()}


# Global instance
womens_hairstyle_generator = WomensHairstyleGenerator() 