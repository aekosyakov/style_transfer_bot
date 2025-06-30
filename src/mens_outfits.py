"""
Comprehensive men's outfit database for focused outfit transformations.
This system generates random men's outfits while preserving the original face and body.
"""

import random
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class MensOutfitGenerator:
    """Generate random men's outfits with face and body-preserving prompts."""
    
    def __init__(self):
        # Modern & Trendy Silhouettes
        self.modern_trendy = [
            "Modern Business Suit",
            "Streetwear Hoodie",
            "Bomber Jacket",
            "Utility Vest",
            "Oversized Shirt",
            "Athletic Tracksuit",
            "Denim Jacket",
            "Varsity Jacket",
            "Cropped Blazer",
            "Resort Shirt"
        ]
        
        # Classic & Timeless
        self.classic_timeless = [
            "Three-Piece Suit",
            "Oxford Shirt",
            "Navy Blazer",
            "Knit Sweater",
            "Trench Coat",
            "Classic Tuxedo",
            "V-Neck Sweater",
            "Polo Shirt",
            "Leather Jacket",
            "Cardigan"
        ]
        
        # Edgy / Statement Styles
        self.edgy_statement = [
            "Biker Jacket",
            "Neon Windbreaker",
            "Flannel Shirt",
            "Mesh Tank Top",
            "Distressed Denim",
            "Harness Vest",
            "Holographic Bomber",
            "Studded Jacket",
            "Tie-Dye Hoodie",
            "Vinyl Coat"
        ]
        
        # Evening & Occasion Showstoppers
        self.evening_occasion = [
            "Velvet Smoking Jacket",
            "Black Tie Tuxedo",
            "White Dinner Jacket",
            "Sequin Blazer",
            "Mandarin Collar Suit",
            "Dinner Suit",
            "Silk Waistcoat",
            "Party Shirt",
            "White Summer Suit",
            "Velvet Suit"
        ]
        
        # Cultural & Traditional Icons
        self.cultural_traditional = [
            "Japanese Kimono",
            "African Agbada",
            "Scottish Kilt",
            "Indian Sherwani",
            "Chinese Tang Suit",
            "Moroccan Djellaba",
            "Middle Eastern Thobe",
            "Mexican Charro",
            "Russian Tunic",
            "Greek Fustanella"
        ]
        
        # Stylized Character-Inspired (content-safe descriptions)
        self.anime_inspired = [
            "Martial Arts Gi",
            "Cyberpunk Outfit",
            "Military Uniform",
            "Fantasy Robe",
            "Pilot Jumpsuit",
            "Punk Ensemble",
            "Samurai Uniform",
            "Stage Jacket",
            "Gothic Tailcoat",
            "Steampunk Suit"
        ]
        
        # Outfit Colors & Fabrics
        self.outfit_colors = [
            "charcoal gray",
            "midnight navy",
            "olive green",
            "sand beige",
            "classic black",
            "powder blue",
            "burgundy red",
            "white linen",
            "camel brown",
            "deep forest",
            "wine red",
            "rust orange",
            "steel blue",
            "platinum silver",
            "graphite",
            "ivory"
        ]
        
        # Outfit Materials & Textures
        self.outfit_materials = [
            "wool",
            "cashmere",
            "linen",
            "tweed",
            "cotton",
            "suede",
            "leather",
            "denim",
            "corduroy",
            "velvet",
            "satin",
            "silk",
            "polyester",
            "mesh",
            "sequined",
            "embellished"
        ]
        
        # Effects & Accessories
        self.outfit_effects = [
            "with chain necklace",
            "with pocket watch",
            "with silk scarf",
            "with snapback cap",
            "with leather gloves",
            "with crossbody satchel",
            "with oversized sunglasses",
            "with patterned socks",
            "with layered bracelets",
            "with fingerless gloves"
        ]
        
        # All categories combined for easy access
        self.all_categories = {
            "modern_trendy": self.modern_trendy,
            "classic_timeless": self.classic_timeless,
            "edgy_statement": self.edgy_statement,
            "evening_occasion": self.evening_occasion,
            "cultural_traditional": self.cultural_traditional,
            "anime_inspired": self.anime_inspired
        }

    def get_random_outfit(self, include_color: bool = True, include_material: bool = True, include_effects: bool = False) -> str:
        """
        Generate a random men's outfit with optional color, material and effects.
        
        Args:
            include_color: Whether to include random outfit color
            include_material: Whether to include fabric/material specification
            include_effects: Whether to include outfit effects/accessories
            
        Returns:
            A complete men's outfit prompt focused only on outfit changes
        """
        try:
            # Select random category and outfit
            category = random.choice(list(self.all_categories.keys()))
            outfits = self.all_categories[category]
            base_outfit = random.choice(outfits)
            
            # Build the prompt components
            prompt_parts = []
            
            # Always include the base outfit
            prompt_parts.append(f"change outfit to {base_outfit}")
            
            # Optionally add color
            if include_color and random.random() < 0.8:  # 80% chance to include color
                color = random.choice(self.outfit_colors)
                prompt_parts.append(f"in {color}")
            
            # Optionally add material
            if include_material and random.random() < 0.6:  # 60% chance for material
                material = random.choice(self.outfit_materials)
                prompt_parts.append(f"{material} fabric")
            
            # Optionally add effects
            if include_effects and random.random() < 0.3:  # 30% chance for effects
                effect = random.choice(self.outfit_effects)
                prompt_parts.append(effect)
            
            # Combine with face and body preservation instruction
            full_prompt = " ".join(prompt_parts) + ", preserve original face and body proportions exactly"
            
            # Log the generation
            generation_info = {
                "category": category,
                "base_outfit": base_outfit,
                "include_color": include_color,
                "include_material": include_material,
                "include_effects": include_effects,
                "final_prompt": full_prompt
            }
            logger.info(f"👔 Generated men's outfit: {generation_info}")
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating random men's outfit: {e}")
            # Fallback to simple outfit
            return "change outfit to casual shirt and jeans, preserve original face and body proportions exactly"

    def get_outfit_by_category(self, category_name: str, include_color: bool = True, include_material: bool = True) -> str:
        """
        Get a random men's outfit from a specific category.
        
        Args:
            category_name: Name of the category
            include_color: Whether to include random outfit color
            include_material: Whether to include fabric/material specification
            
        Returns:
            A men's outfit prompt from the specified category
        """
        try:
            if category_name not in self.all_categories:
                logger.warning(f"Unknown men's outfit category: {category_name}")
                return self.get_random_outfit(include_color, include_material)
            
            outfits = self.all_categories[category_name]
            base_outfit = random.choice(outfits)
            
            prompt_parts = [f"change outfit to {base_outfit}"]
            
            if include_color and random.random() < 0.7:  # 70% chance for specific categories
                color = random.choice(self.outfit_colors)
                prompt_parts.append(f"in {color}")
            
            if include_material and random.random() < 0.5:  # 50% chance for material
                material = random.choice(self.outfit_materials)
                prompt_parts.append(f"{material} fabric")
            
            full_prompt = " ".join(prompt_parts) + ", preserve original face and body proportions exactly"
            
            logger.info(f"👔 Generated {category_name} men's outfit: {full_prompt}")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating men's outfit for category {category_name}: {e}")
            return self.get_random_outfit(include_color, include_material)

    def get_casual_outfit(self) -> str:
        """Get a casual men's outfit change."""
        casual_outfits = [
            "casual t-shirt",
            "polo shirt",
            "hoodie",
            "button-up shirt",
            "sweater",
            "denim jacket",
            "henley shirt",
            "flannel shirt"
        ]
        
        try:
            outfit = random.choice(casual_outfits)
            color = random.choice(self.outfit_colors)
            prompt = f"change outfit to {outfit} in {color}, preserve original face and body proportions exactly"
            
            logger.info(f"👔 Generated casual men's outfit: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating casual men's outfit: {e}")
            return "change outfit to casual t-shirt and jeans, preserve original face and body proportions exactly"

    def get_available_categories(self) -> List[str]:
        """Get list of available men's outfit categories."""
        return list(self.all_categories.keys())

    def get_category_info(self) -> Dict[str, int]:
        """Get information about available categories and their counts."""
        return {category: len(outfits) for category, outfits in self.all_categories.items()}

    def generate_random_mens_outfit_prompt(self, include_color: bool = True, include_material: bool = True, include_effects: bool = False) -> str:
        """Backward compatibility method for prompt variation system."""
        return self.get_random_outfit(include_color, include_material, include_effects)


# Global instance
mens_outfit_generator = MensOutfitGenerator() 