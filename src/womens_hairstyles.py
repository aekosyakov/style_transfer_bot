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
        # Modern & Trendy (massively expanded)
        self.modern_trendy = [
            "Long Textured Waves", "Curtain Bangs Bob", "Wolf Cut with Shaggy Layers", "French Girl Chin Bob",
            "Sleek High Ponytail", "Airy Pixie with Side Bangs", "Face-Framing Layered Lob", "Blunt Cut with Micro Fringe",
            "Bubble Braids", "Half-Up Space Buns", "Textured Beach Waves", "Modern Shag Cut", "Butterfly Haircut",
            "Wispy Bangs Bob", "Layered Curtain Bangs", "Messy Bun Updo", "Slicked Back Ponytail", "Chunky Highlights Bob",
            "Face-Framing Layers", "Textured Pixie Cut", "Modern Mullet", "Asymmetrical Bob", "Wavy Lob",
            "Feathered Layers", "Tousled Waves", "Edgy Pixie", "Voluminous Curls", "Sleek Straight Hair",
            "Layered Shag", "Bouncy Blowout", "Textured Crop", "Modern Fringe", "Wavy Bob", "Choppy Layers",
            "Effortless Waves", "Trendy Bangs", "Lived-in Color", "Undone Waves", "Contemporary Cut"
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

        # Hair Colors & Effects - ULTIMATE EXPANSION for infinite variety
        self.hair_colors = [
            # Premium Blondes - Expanded
            "platinum blonde", "ice blonde", "white blonde", "pearl blonde", "silver blonde",
            "honey blonde", "golden honey", "warm honey", "dark honey", "liquid honey",
            "strawberry blonde", "rose blonde", "pink blonde", "coral blonde", "peach blonde",
            "ash blonde", "cool ash blonde", "Nordic blonde", "Scandinavian blonde", "mushroom blonde",
            "golden blonde", "sun-kissed blonde", "champagne blonde", "butter blonde", "cream blonde",
            "bronde", "dark bronde", "caramel bronde", "baby blonde", "vanilla blonde",
            "wheat blonde", "sandy blonde", "beige blonde", "dirty blonde", "medium blonde",
            
            # Luxurious Browns - Expanded
            "chocolate brown", "dark chocolate", "milk chocolate", "white chocolate", "cocoa brown",
            "espresso brown", "coffee brown", "mocha brown", "latte brown", "cappuccino brown",
            "caramel brown", "salted caramel", "burnt caramel", "golden caramel", "rich caramel",
            "chestnut brown", "warm chestnut", "deep chestnut", "mahogany brown", "rich mahogany",
            "toffee brown", "butterscotch brown", "amber brown", "cognac brown", "bronze brown",
            "ash brown", "cool brown", "mushroom brown", "taupe brown", "cinnamon brown",
            
            # Stunning Reds - Expanded
            "auburn red", "deep auburn", "dark auburn", "rich auburn", "vibrant auburn",
            "copper red", "bright copper", "rose copper", "penny copper", "bronze copper",
            "burgundy red", "wine red", "deep wine", "merlot red", "cabernet red",
            "cherry red", "bright cherry", "dark cherry", "fire red", "crimson red",
            "strawberry red", "coral red", "sunset red", "rust red", "ginger red",
            "cinnamon red", "spice red", "paprika red", "rose gold", "copper rose",
            
            # Dramatic Darks & Lights
            "jet black", "raven black", "midnight black", "coal black", "onyx black",
            "blue-black", "brown-black", "soft black", "off-black", "charcoal black",
            "silver gray", "platinum gray", "ash gray", "steel gray", "pewter gray",
            "pearl white", "ivory white", "cream white", "snow white", "alabaster white",
            
            # Pastel Paradise - Expanded
            "pastel pink", "baby pink", "cotton candy pink", "rose quartz pink", "blush pink",
            "lavender purple", "lilac purple", "orchid purple", "periwinkle purple", "wisteria purple",
            "mint green", "sage green", "eucalyptus green", "seafoam green", "pistachio green",
            "peach blonde", "apricot blonde", "coral blonde", "salmon blonde", "sunset blonde",
            "lilac gray", "lavender gray", "mauve gray", "dusty rose gray", "smoky lilac",
            
            # Fantasy & Fashion Colors - Expanded
            "ocean blue", "mermaid blue", "teal blue", "aqua blue", "turquoise blue",
            "sapphire blue", "royal blue", "navy blue", "midnight blue", "steel blue",
            "emerald green", "forest green", "jade green", "pine green", "hunter green",
            "deep purple", "violet purple", "royal purple", "amethyst purple", "grape purple",
            "magenta purple", "fuchsia purple", "plum purple", "eggplant purple", "indigo purple",
            
            # Multi-Dimensional Colors
            "rainbow ombré", "sunset ombré", "galaxy gradient", "aurora borealis", "prism effect",
            "oil slick", "holographic", "iridescent", "color-changing", "tie-dye effect",
            "mermaid gradient", "unicorn pastel mix", "fairy tale blend", "sunset gradient", "ocean waves",
            "cosmic blend", "northern lights", "peacock colors", "butterfly wing", "opal effect",
            
            # Sophisticated Tones
            "rose gold", "copper gold", "bronze gold", "champagne gold", "antique gold",
            "dusty rose", "mauve", "taupe", "mushroom", "greige",
            "smoky pink", "dusty purple", "sage", "olive", "khaki"
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
            
            # Optionally add color (increased probability for more appealing results)
            if include_color and random.random() < 0.90:  # 90% chance to include color
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
            
            if include_color and random.random() < 0.85:  # 85% chance for specific categories
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