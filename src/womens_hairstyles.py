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
        # 80s Big Hair Power - Volume, perms, teased hair & bold styles
        self.eighties_big_hair = [
            "Big Hair Perm", "Teased Volume Hair", "Madonna Big Hair", "80s Poodle Perm",
            "Dynasty Hair Volume", "Cyndi Lauper Style", "80s Crimped Hair", "Big Hair Layered Perm",
            "Volumized Side Perm", "80s Rock Hair", "Teased Bangs Style", "Big Hair Mullet",
            "80s Power Hair", "Voluminous Feathered Hair", "80s Glam Hair", "Big Hair Side Sweep"
        ]
        
        # 90s Grunge Layers - Face-framing layers, alternative & casual rebellion  
        self.nineties_grunge_layers = [
            "Rachel Green Layers", "Grunge Face-Framing Layers", "90s Shaggy Bob", "Alternative Layers",
            "Messy Grunge Cut", "90s Chunky Highlights", "Face-Framing Shag", "90s Alternative Bob",
            "Layered Grunge Style", "90s Casual Layers", "Messy Layered Cut", "Grunge Pixie Cut",
            "90s Indie Hair", "Alternative Shag Cut", "Grunge Bob Cut", "90s Relaxed Layers"
        ]
        
        # Y2K Cyber Glam - Pin-straight hair, chunky highlights & futuristic elements
        self.y2k_cyber_glam = [
            "Pin-Straight Y2K Hair", "Chunky Blonde Highlights", "Y2K Face-Framing Pieces", "Cyber Straight Hair",
            "Y2K Flippy Ends", "Early 2000s Highlights", "Y2K Side Bangs", "Futuristic Straight Hair",
            "Y2K Emo Fringe", "Cyber Goth Hair", "Y2K Scene Hair", "Digital Age Hair",
            "Tech Girl Hair", "Y2K Metallic Hair", "Cyber Punk Hair", "Future Hair Style"
        ]
        
        # Old Money Elegance - Classic bobs, sophisticated updos & timeless sophistication
        self.old_money_elegance = [
            "Classic French Bob", "Elegant Chignon", "Preppy Bob Cut", "Sophisticated Updo",
            "Old Money Waves", "Grace Kelly Hair", "Classic Side Part", "Timeless Bob Cut",
            "Elegant French Twist", "Preppy Ponytail", "Classic Low Bun", "Refined Bob Cut",
            "Country Club Hair", "Tennis Club Style", "Elite Updo", "Heritage Hair Style"
        ]
        
        # Hollywood Red Carpet - Glamorous waves, vintage curls & movie star styles
        self.hollywood_red_carpet = [
            "Old Hollywood Waves", "Red Carpet Curls", "Movie Star Hair", "Glamorous Side Waves",
            "Vintage Hollywood Curls", "Classic Screen Siren", "Red Carpet Updo", "Hollywood Glamour Waves",
            "Marilyn Monroe Curls", "Grace Kelly Waves", "Classic Movie Star", "Vintage Glamour Hair",
            "Hollywood Diva Hair", "Red Carpet Style", "Classic Starlet Hair", "Timeless Glamour"
        ]
        
        # Urban Streetwear - Modern, edgy cuts & contemporary street culture
        self.urban_streetwear = [
            "Urban Pixie Cut", "Street Style Bob", "Modern Undercut", "City Girl Hair",
            "Urban Shag Cut", "Street Fashion Hair", "Modern Edge Cut", "Urban Chic Style",
            "Street Style Layers", "Contemporary Urban Cut", "Modern City Hair", "Urban Trendy Cut",
            "Street Culture Hair", "Modern Edgy Bob", "Urban Fashion Cut", "City Street Style"
        ]
        
        # Gen-Z Viral Hair - TikTok trends, e-girl styles & social media aesthetics
        self.genz_viral_hair = [
            "E-Girl Hair Style", "TikTok Trendy Hair", "Gen-Z Aesthetic Hair", "Viral Hair Trend",
            "Social Media Hair", "E-Girl Bangs", "TikTok Famous Hair", "Gen-Z Hair Trend",
            "Viral Hair Cut", "Internet Culture Hair", "Digital Native Hair", "Gen-Z Style Hair",
            "TikTok Hair Style", "Social Media Trend", "Viral Hair Look", "E-Girl Hair Cut"
        ]
        
        # Disco Era Feathers - Feathered hair, Farrah Fawcett styles & 70s glamour
        self.disco_era_feathers = [
            "Farrah Fawcett Feathers", "70s Feathered Hair", "Disco Era Hair", "Feathered Shag",
            "70s Layered Feathers", "Disco Glam Hair", "Feathered Flip Hair", "70s Angel Hair",
            "Disco Feathered Layers", "70s Glamour Hair", "Feathered Side Sweep", "Disco Hair Style",
            "70s Icon Hair", "Feathered Hair Cut", "Disco Era Layers", "70s Feathered Bob"
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
            # New era-specific categories (matching outfits approach)
            "eighties_big_hair": self.eighties_big_hair,
            "nineties_grunge_layers": self.nineties_grunge_layers,
            "y2k_cyber_glam": self.y2k_cyber_glam,
            "old_money_elegance": self.old_money_elegance,
            "hollywood_red_carpet": self.hollywood_red_carpet,
            "urban_streetwear": self.urban_streetwear,
            "genz_viral_hair": self.genz_viral_hair,
            "disco_era_feathers": self.disco_era_feathers,
            
            # Legacy categories (for backward compatibility)
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
            
            # Combine with face and skin color preservation instruction
            full_prompt = " ".join(prompt_parts) + ", preserve original face, facial features, and skin color exactly"
            
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
            return "change hairstyle to modern bob cut, preserve original face, facial features, and skin color exactly"

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
            
            full_prompt = " ".join(prompt_parts) + ", preserve original face, facial features, and skin color exactly"
            
            logger.info(f"💇‍♀️ Generated {category_name} women's hairstyle: {full_prompt}")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating women's hairstyle for category {category_name}: {e}")
            return self.get_random_hairstyle(include_color)

    def get_color_only_change(self) -> str:
        """Get a prompt that only changes hair color."""
        try:
            color = random.choice(self.hair_colors)
            prompt = f"change hair color to {color}, keep exact same hairstyle and preserve original face and skin color"
            
            logger.info(f"💇‍♀️ Generated women's color-only change: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating women's color change: {e}")
            return "change hair color to blonde, keep exact same hairstyle and preserve original face and skin color"

    def get_available_categories(self) -> List[str]:
        """Get list of available women's hairstyle categories."""
        return list(self.all_categories.keys())

    def get_category_info(self) -> Dict[str, int]:
        """Get information about available categories and their counts."""
        return {category: len(styles) for category, styles in self.all_categories.items()}


# Global instance
womens_hairstyle_generator = WomensHairstyleGenerator() 