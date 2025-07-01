"""
Comprehensive men's hairstyle database for focused hair transformations.
This system generates random men's hairstyles while preserving the original face.
"""

import random
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class MensHairstyleGenerator:
    """Generate random men's hairstyles with face-preserving prompts."""
    
    def __init__(self):
        # 80s Power Business - Slicked back, Wall Street & executive styles
        self.eighties_power_business = [
            "Wall Street Slick Back", "80s Executive Hair", "Gordon Gekko Style", "Power Business Cut",
            "Dynasty Business Hair", "80s Corporate Style", "Executive Slick Back", "80s Power Cut",
            "Business Power Hair", "80s Wall Street", "Corporate Slick Style", "Executive Power Cut",
            "80s Business Man", "Power Suit Hair", "Wall Street Executive", "80s Professional Cut"
        ]
        
        # 90s Grunge Rebel - Longer, messy styles & alternative rebellion
        self.nineties_grunge_rebel = [
            "Kurt Cobain Grunge", "90s Alternative Hair", "Grunge Messy Cut", "90s Rebel Hair",
            "Alternative Rock Hair", "90s Indie Style", "Grunge Long Hair", "90s Messy Cut",
            "Alternative Grunge Style", "90s Rock Hair", "Grunge Shaggy Cut", "90s Underground Style",
            "Alternative Rebel Hair", "90s Casual Grunge", "Indie Rock Hair", "90s Grunge Style"
        ]
        
        # Y2K Tech Style - Frosted tips, faux hawks & early 2000s trends
        self.y2k_tech_style = [
            "Frosted Tips Y2K", "Early 2000s Faux Hawk", "Y2K Spiky Hair", "Tech Boy Hair",
            "Digital Age Cut", "Y2K Emo Hair", "Early 2000s Style", "Cyber Tech Hair",
            "Y2K Scene Hair", "Future Tech Cut", "Digital Native Hair", "Y2K Trendy Cut",
            "Millennium Hair Style", "Tech Era Cut", "Y2K Modern Style", "Digital Age Hair"
        ]
        
        # Old Money Gentleman - Classic side parts, preppy cuts & sophisticated styles
        self.old_money_gentleman = [
            "Classic Side Part", "Preppy Gentleman Cut", "Ivy League Style", "Country Club Hair",
            "Tennis Club Cut", "Elite Preppy Style", "Heritage Gentleman Cut", "Classic Prep Hair",
            "Refined Side Part", "Gentleman's Cut", "Elite Club Style", "Preppy Traditional Cut",
            "Old Money Style", "Sophisticated Cut", "Elite Gentleman Hair", "Classic Preppy Cut"
        ]
        
        # Hollywood Leading Man - James Dean, classic movie star & timeless appeal
        self.hollywood_leading_man = [
            "James Dean Style", "Classic Movie Star", "Hollywood Icon Hair", "Leading Man Cut",
            "Classic Screen Star", "Vintage Hollywood Hair", "Movie Star Style", "Classic Leading Man",
            "Hollywood Legend Hair", "Screen Icon Style", "Classic Movie Hair", "Hollywood Heartthrob",
            "Movie Star Cut", "Classic Hollywood Style", "Silver Screen Hair", "Vintage Star Cut"
        ]
        
        # Urban Streetwear - Modern fades, trendy cuts & contemporary street culture
        self.urban_streetwear = [
            "Modern Fade Cut", "Urban Street Style", "Contemporary Fade", "Street Fashion Hair",
            "Modern Urban Cut", "Street Culture Hair", "Contemporary Style", "Urban Trendy Cut",
            "Modern Street Hair", "Urban Fashion Cut", "Street Style Fade", "Contemporary Urban Hair",
            "Modern City Cut", "Urban Edge Style", "Street Trend Hair", "Contemporary Fade Cut"
        ]
        
        # Gen-Z TikTok - E-boy cuts, modern trends & social media aesthetics
        self.genz_tiktok = [
            "E-Boy Hair Cut", "TikTok Boy Hair", "Gen-Z Aesthetic Cut", "Social Media Hair",
            "TikTok Trendy Hair", "E-Boy Style", "Gen-Z Hair Trend", "Viral Hair Cut",
            "TikTok Famous Hair", "Digital Native Cut", "Gen-Z Style Hair", "Social Media Cut",
            "E-Boy Aesthetic", "TikTok Hair Style", "Gen-Z Modern Cut", "Viral Hair Style"
        ]
        
        # Disco Retro - Longer styles from the 70s, afros & retro glamour
        self.disco_retro = [
            "70s Disco Hair", "Retro Afro Style", "Disco Era Hair", "70s Long Hair",
            "Retro Disco Style", "70s Glamour Hair", "Disco Funk Hair", "Retro 70s Cut",
            "Disco Age Hair", "70s Icon Hair", "Retro Disco Cut", "70s Soul Hair",
            "Disco Fever Hair", "Retro Groove Style", "70s Disco Style", "Vintage Disco Hair"
        ]
        
        # Legacy categories (keeping for backward compatibility)
        # Modern & Trendy (massively expanded)
        self.modern_trendy = [
            "Textured Crop Fade", "Messy Quiff", "Disconnected Undercut", "French Crop with Fringe",
            "Mid Fade with Curls", "Slicked Back Pompadour", "Short Taper with Line Up", "Faux Hawk Fade",
            "Side-Parted Comb Over", "Wavy Bro Flow", "Buzz Cut with Fade", "Modern Mullet",
            "Textured Side Sweep", "Volumized Quiff", "Skin Fade Buzz", "Razor Fade Cut",
            "Choppy Layered Cut", "Tousled Beach Hair", "Angular Fringe Cut", "Spiky Textured Top",
            "Modern Caesar Cut", "Sleek Side Part", "Wavy Pompadour", "Graduated Bob Cut",
            "Layered Shag Cut", "Feathered Hair Cut", "Windswept Style", "Messy Bedhead Look",
            "Contemporary Crew Cut", "Edgy Asymmetrical Cut", "Voluminous Waves", "Slicked Forward Style",
            "Textured Crop Top", "Modern Bowl Cut", "Disconnected Fade", "Curly Top Fade"
        ]

        # Classic & Timeless (massively expanded)
        self.classic_timeless = [
            "Ivy League Cut", "Side-Part Taper", "Crew Cut", "Classic Pompadour", "Regulation Cut",
            "Flat Top", "1950s Slick-Back", "Short Back and Sides", "Gentleman's Brush Up", "Soft Waves with Side Part",
            "Traditional Crew Cut", "Military Buzz Cut", "Classic Caesar Cut", "Vintage Pompadour", "High and Tight",
            "Executive Side Part", "Distinguished Gray Cut", "Classic Businessman Cut", "Retro Slick Back",
            "Gentleman's Comb Over", "Classic Taper Cut", "Traditional Flat Top", "Vintage Brush Cut",
            "Classic Short Cut", "Professional Taper", "Traditional Buzz", "Refined Side Part", "Elegant Pompadour",
            "Classic Wave Cut", "Timeless Crew", "Vintage Fade", "Distinguished Cut", "Executive Style",
            "Classic Military Cut", "Traditional Gentleman's Cut", "Vintage Professional Style"
        ]

        # Edgy / Statement
        self.edgy_statement = [
            "High-Top Fade with Shaved Patterns",
            "Liberty Spikes",
            "Bleached Buzz Cut",
            "Mullet with Rattail",
            "Two-Block K-Pop Cut",
            "Asymmetrical Fringe",
            "Vivid Dyed Undercut",
            "Braided Top Knot",
            "Reverse Mohawk",
            "Disconnected Dreads"
        ]

        # Cultural & Traditional
        self.cultural_traditional = [
            "Samurai Top Knot",
            "Chinese Queue Braid",
            "Traditional Sikh Bun",
            "Afro with Pick",
            "West African Twist Braids",
            "Native American Long Braids",
            "Polynesian Warrior Bun",
            "Greek Hero Wavy Long Hair",
            "Cossack Oseledets",
            "Maori Feathered Top Knot"
        ]

        # Anime & Game-Inspired (content-safe descriptions)
        self.anime_inspired = [
            "Gravity-Defying Hero Spikes",
            "Tri-Color Spiky Hero Cut",
            "Wildly Layered Samurai Mane",
            "Slicked Mecha Pilot Hair",
            "Warrior Style Ponytail",
            "Half-Shaved Villain Cut",
            "Long Bangs with Standing Spike",
            "Sharp-Edged Emo Fringe",
            "Cat-Ear Spikes",
            "Hyper-Volume Fantasy Hair"
        ]

        # Hair Colors & Styles - MASSIVE EXPANSION for maximum variety
        self.hair_colors = [
            # Natural Browns - Expanded
            "jet black", "raven black", "midnight black", "coal black", "onyx black",
            "dark chocolate brown", "rich espresso brown", "deep coffee brown", "warm chestnut brown", "mahogany brown",
            "medium ash brown", "golden brown", "caramel brown", "toffee brown", "amber brown",
            "light caramel brown", "honey brown", "butterscotch brown", "cognac brown", "bronze brown",
            
            # Natural Blondes - Expanded  
            "platinum blonde", "icy blonde", "pearl blonde", "silver blonde", "white blonde",
            "golden blonde", "sunlit blonde", "champagne blonde", "butter blonde", "cream blonde",
            "honey blonde", "wheat blonde", "sandy blonde", "beige blonde", "vanilla blonde",
            "ash blonde", "cool blonde", "Nordic blonde", "strawberry blonde", "ginger blonde",
            "dirty blonde", "mushroom blonde", "bronde", "dark blonde", "medium blonde",
            
            # Natural Reds - Expanded
            "auburn red", "deep auburn", "dark auburn", "rich auburn", "copper red",
            "bright copper", "penny copper", "bronze copper", "cinnamon red", "spice red",
            "russet red", "burgundy red", "wine red", "cherry red", "crimson red",
            "strawberry red", "ginger red", "fire red", "sunset red", "rust red",
            
            # Grays & Mature Colors - Expanded
            "silver gray", "platinum gray", "steel gray", "charcoal gray", "slate gray",
            "ash gray", "pewter gray", "titanium gray", "salt and pepper", "pepper gray",
            "iron gray", "storm gray", "smoke gray", "bleached white", "snow white",
            
            # Fashion/Trendy Colors - Expanded
            "electric blue", "sapphire blue", "navy blue", "royal blue", "midnight blue",
            "ocean blue", "teal blue", "aqua blue", "steel blue", "ice blue",
            "forest green", "emerald green", "jade green", "pine green", "mint green",
            "sage green", "olive green", "lime green", "neon green", "hunter green",
            "deep purple", "violet purple", "lavender purple", "plum purple", "indigo purple",
            "royal purple", "amethyst purple", "grape purple", "magenta purple", "orchid purple",
            
            # Unique Fashion Colors
            "rose gold", "copper gold", "bronze gold", "antique gold", "champagne gold",
            "smoky pink", "dusty rose", "coral pink", "salmon pink", "peach pink"
        ]

        # Hair Effects & Styling
        self.hair_effects = [
            "with gel styling",
            "with matte finish",
            "with high shine pomade",
            "with textured wax",
            "with natural wave pattern",
            "with slight messy texture",
            "with razor-sharp edges",
            "with subtle highlights",
            "with fade gradient",
            "with designer line patterns"
        ]

        # All categories combined for easy access
        self.all_categories = {
            # New era-specific categories (matching outfits approach)
            "eighties_power_business": self.eighties_power_business,
            "nineties_grunge_rebel": self.nineties_grunge_rebel,
            "y2k_tech_style": self.y2k_tech_style,
            "old_money_gentleman": self.old_money_gentleman,
            "hollywood_leading_man": self.hollywood_leading_man,
            "urban_streetwear": self.urban_streetwear,
            "genz_tiktok": self.genz_tiktok,
            "disco_retro": self.disco_retro,
            
            # Legacy categories (for backward compatibility)
            "modern_trendy": self.modern_trendy,
            "classic_timeless": self.classic_timeless,
            "edgy_statement": self.edgy_statement,
            "cultural_traditional": self.cultural_traditional,
            "anime_inspired": self.anime_inspired
        }

    def get_random_hairstyle(self, include_color: bool = True, include_effects: bool = False) -> str:
        """
        Generate a random men's hairstyle with optional color and effects.
        
        Args:
            include_color: Whether to include random hair color
            include_effects: Whether to include hair effects/styling
            
        Returns:
            A complete men's hairstyle prompt focused only on hair changes
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
            if include_color and random.random() < 0.85:  # 85% chance to include color for men
                color = random.choice(self.hair_colors)
                prompt_parts.append(f"with {color} hair color")
            
            # Optionally add styling effects
            if include_effects and random.random() < 0.4:  # 40% chance for styling effects
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
            logger.info(f"💈 Generated men's hairstyle: {generation_info}")
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating random men's hairstyle: {e}")
            # Fallback to simple hairstyle
            return "change hairstyle to modern crew cut, preserve original face, facial features, and skin color exactly"

    def get_hairstyle_by_category(self, category_name: str, include_color: bool = True) -> str:
        """
        Get a random men's hairstyle from a specific category.
        
        Args:
            category_name: Name of the category
            include_color: Whether to include random hair color
            
        Returns:
            A men's hairstyle prompt from the specified category
        """
        try:
            if category_name not in self.all_categories:
                logger.warning(f"Unknown men's hairstyle category: {category_name}")
                return self.get_random_hairstyle(include_color)
            
            hairstyles = self.all_categories[category_name]
            base_hairstyle = random.choice(hairstyles)
            
            prompt_parts = [f"change hairstyle to {base_hairstyle}"]
            
            if include_color and random.random() < 0.80:  # 80% chance for specific categories
                color = random.choice(self.hair_colors)
                prompt_parts.append(f"with {color} hair color")
            
            full_prompt = " ".join(prompt_parts) + ", preserve original face, facial features, and skin color exactly"
            
            logger.info(f"💈 Generated {category_name} men's hairstyle: {full_prompt}")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating men's hairstyle for category {category_name}: {e}")
            return self.get_random_hairstyle(include_color)

    def get_color_only_change(self) -> str:
        """Get a prompt that only changes hair color."""
        try:
            color = random.choice(self.hair_colors)
            prompt = f"change hair color to {color}, keep exact same hairstyle and preserve original face and skin color"
            
            logger.info(f"💈 Generated men's color-only change: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating men's color change: {e}")
            return "change hair color to dark brown, keep exact same hairstyle and preserve original face and skin color"

    def get_available_categories(self) -> List[str]:
        """Get list of available men's hairstyle categories."""
        return list(self.all_categories.keys())

    def get_category_info(self) -> Dict[str, int]:
        """Get information about available categories and their counts."""
        return {category: len(styles) for category, styles in self.all_categories.items()}


# Global instance
mens_hairstyle_generator = MensHairstyleGenerator() 