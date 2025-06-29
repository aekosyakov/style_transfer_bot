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
            "Slim-Fit Double-Breasted Suit with Turtleneck",
            "Streetwear Layered Hoodie with Cargo Joggers",
            "Oversized Bomber Jacket and Ripped Jeans",
            "Techwear Utility Vest and Tapered Pants",
            "Relaxed Fit Shirt with Wide-Leg Trousers",
            "Monochrome Tracksuit with Chunky Sneakers",
            "Denim Trucker Jacket and Graphic Tee",
            "Varsity Jacket with Patchwork Details",
            "Boxy Cropped Blazer and Pleated Trousers",
            "Printed Resort Shirt and Tailored Shorts"
        ]
        
        # Classic & Timeless
        self.classic_timeless = [
            "Three-Piece Wool Suit with Pocket Square",
            "Oxford Shirt and Slim Chinos",
            "Double-Breasted Navy Blazer with Gray Slacks",
            "Cable Knit Sweater and Straight Jeans",
            "Trench Coat over Business Suit",
            "Single-Breasted Tuxedo with Bow Tie",
            "Argyle V-Neck Sweater with Collared Shirt",
            "Polo Shirt and Tailored Shorts",
            "Leather Moto Jacket and Black Jeans",
            "Cashmere Cardigan and Dress Pants"
        ]
        
        # Edgy / Statement Styles
        self.edgy_statement = [
            "Faux Leather Biker Jacket with Zipper Details",
            "Neon Windbreaker with Graphic Joggers",
            "Oversized Flannel Shirt with Chains",
            "Mesh Layered Tank Top and Cargo Pants",
            "Distressed Denim Set with Bandana",
            "Harness Vest over Longline Tee",
            "Futuristic Holographic Bomber",
            "Studded Denim Jacket and Leather Pants",
            "Tie-Dye Hoodie with Ripped Skinny Jeans",
            "Vinyl Trench Coat and Platform Boots"
        ]
        
        # Evening & Occasion Showstoppers
        self.evening_occasion = [
            "Velvet Smoking Jacket with Satin Lapels",
            "Classic Black Tie Tuxedo",
            "White Dinner Jacket with Silk Scarf",
            "Sequin Blazer with Slim-Fit Pants",
            "Embroidered Mandarin Collar Suit",
            "Double-Breasted Dinner Suit",
            "Velvet Bow Tie and Silk Waistcoat",
            "Silk Jacquard Party Shirt with Dress Pants",
            "All-White Summer Suit",
            "Midnight Blue Velvet Suit"
        ]
        
        # Cultural & Traditional Icons
        self.cultural_traditional = [
            "Japanese Kimono with Obi Sash",
            "West African Agbada Robe",
            "Scottish Tartan Kilt with Prince Charlie Jacket",
            "Indian Sherwani with Embroidered Stole",
            "Chinese Tang Suit with Brocade Patterns",
            "Moroccan Djellaba with Fez Hat",
            "Middle Eastern Thobe with Bisht Cloak",
            "Mexican Charro Suit",
            "Russian Cossack Tunic with Sash",
            "Greek Fustanella with Waistcoat"
        ]
        
        # Stylized Character-Inspired (content-safe descriptions)
        self.anime_inspired = [
            "Martial Arts Gi with High Collar",
            "Cyberpunk Street Ninja Outfit",
            "High-Collar Military-Style Uniform",
            "Fantasy Mage Robe with Armor Accents",
            "Pilot Jumpsuit with Utility Harness",
            "Layered Punk Ensemble with Studs",
            "Samurai-Inspired Uniform",
            "Stage Jacket with Glitter Accents",
            "Aristocrat Tailcoat with Gothic Details",
            "Steampunk Inventor's Suit with Goggles"
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
            "casual t-shirt and jeans",
            "polo shirt and chinos",
            "hoodie and joggers",
            "button-up shirt and shorts",
            "sweater and casual pants",
            "denim jacket and khakis",
            "henley shirt and cargo pants",
            "flannel shirt and dark jeans"
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