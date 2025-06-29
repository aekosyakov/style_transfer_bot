"""
Comprehensive dress database for focused outfit transformations.
This system generates random dresses while preserving the original face and body proportions.
"""

import random
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class DressGenerator:
    """Generate random dresses with face and body-preserving prompts."""
    
    def __init__(self):
        # Modern & Trendy Silhouettes
        self.modern_trendy = [
            "Slip-Dress Midi ('90s Revive) dress",
            "Cut-Out Bodycon Mini dress",
            "Cottagecore Puff-Sleeve Sundress",
            "Asymmetric Hem Ribbed Knit dress",
            "Corset-Waist Satin Midi dress",
            "Tiered Babydoll Mini dress",
            "Shirt-Dress With Oversize Pockets",
            "One-Shoulder Column Dress",
            "Cargo-Utility Maxi dress with D-rings",
            "Plissé Pleated Halter Midi dress"
        ]
        
        # Classic & Timeless
        self.classic_timeless = [
            "Little Black Dress (LBD) Sheath",
            "A-Line Tea-Length dress",
            "Wrap Dress (Diane von Furstenberg style)",
            "Fit-and-Flare Knee-Length dress",
            "Column Evening Gown",
            "Princess-Seamed Ball Gown",
            "Boat-Neck Shift Dress",
            "Pencil Dress with Cap Sleeves",
            "Empire-Waist Regency Gown",
            "Vintage 1950s Full-Skirt Swing dress"
        ]
        
        # Fun / Edgy Statement Styles
        self.edgy_statement = [
            "PVC Vinyl Mini (Cyber-Club) dress",
            "Neon Mesh Layered Slip dress",
            "Fringe Flapper Re-Boot dress",
            "Holographic Skater Dress",
            "Two-Tone Split Dye Bodycon dress",
            "Laser-Cut Scuba A-Line dress",
            "Oversized Hoodie Dress With Thigh-High Slits",
            "Patchwork Denim Midi dress",
            "Cage-Strap Harness Dress",
            "LED Fiber-Optic Party Gown"
        ]
        
        # Evening & Occasion Showstoppers
        self.evening_occasion = [
            "Sequin Mermaid Gown",
            "High-Slit Jersey Goddess dress",
            "Tulle Ruffled Ball Dress",
            "Velvet Off-Shoulder Trumpet dress",
            "Feather-Trim Cocktail Mini dress",
            "Beaded Fluted Column dress",
            "Cape-Back Crepe Gown",
            "Illusion Lace Bodice A-Line dress",
            "One-Sleeve Draped Satin dress",
            "Metallic Foil Plunge Maxi dress"
        ]
        
        # Cultural & Traditional Icons
        self.cultural_traditional = [
            "Cheongsam / Qipao Midi dress",
            "Kimono-Sleeve Obi-Belt Dress",
            "Sari-Drape Gown Hybrid",
            "Hanbok Jeogori & Chima Fusion dress",
            "Dirndl Bodice Dress",
            "Kaftan Embroidered Maxi dress",
            "Boubou West-African Flow dress",
            "Flamenco Ruffle Bata de Cola dress",
            "Greek Chiton-Inspired Drape dress",
            "Maasai Beaded Collar Dress"
        ]
        
        # Anime & Game-Inspired
        self.anime_inspired = [
            "Magical-Girl Layered Ruffle Skirt (Sailor silhouette) dress",
            "Battle-Ready Bodysuit + Skater Skirt (Asuka plugsuit vibe)",
            "Victorian Lolita One-Piece (Sweet Lolita) dress",
            "Cyberpunk High-Collar Coat-Dress (Arasaka chic)",
            "School Uniform Seifuku Sailor Dress",
            "Traditional Hime-Sama Gown (Princess long train)",
            "Mecha Pilot Flight Dress (utility pockets)",
            "Fantasy Mage Robe-Dress With Capelet",
            "Idol Stage Frilly Mini With Bows dress",
            "Gothic Lolita Cage-Crinoline Dress"
        ]
        
        # Dress Colors & Fabrics
        self.dress_colors = [
            "emerald green",
            "royal blue",
            "burgundy red",
            "blush pink",
            "midnight black",
            "ivory white",
            "champagne gold",
            "silver metallic",
            "lavender purple",
            "coral orange",
            "navy blue",
            "rose gold",
            "deep teal",
            "wine red",
            "powder blue",
            "forest green",
            "sunset orange",
            "pearl white",
            "charcoal gray"
        ]
        
        # Dress Materials & Textures
        self.dress_materials = [
            "silk",
            "satin",
            "velvet",
            "chiffon",
            "lace",
            "tulle",
            "organza",
            "crepe",
            "jersey",
            "brocade",
            "taffeta",
            "georgette",
            "mesh",
            "sequined",
            "beaded",
            "embroidered"
        ]
        
        # Dress Effects & Accessories
        self.dress_effects = [
            "with statement chain belt",
            "with oversize bow sash",
            "with detachable capelet",
            "with transparent organza overlay",
            "with 3-D floral appliqués",
            "with galaxy gradient print",
            "with puff-sleeve clip-ons",
            "with faux-fur stole",
            "with sequin shoulder epaulettes",
            "with crystal embellishments"
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
    
    def get_random_dress(self, include_color: bool = True, include_material: bool = True, include_effects: bool = False) -> str:
        """
        Generate a random dress with optional color, material and effects.
        
        Args:
            include_color: Whether to include random dress color
            include_material: Whether to include fabric/material specification
            include_effects: Whether to include dress effects/accessories
            
        Returns:
            A complete dress prompt focused only on outfit changes
        """
        try:
            # Select random category and dress
            category = random.choice(list(self.all_categories.keys()))
            dresses = self.all_categories[category]
            base_dress = random.choice(dresses)
            
            # Build the prompt components
            prompt_parts = []
            
            # Always include the base dress
            prompt_parts.append(f"change outfit to {base_dress}")
            
            # Optionally add color
            if include_color and random.random() < 0.8:  # 80% chance to include color
                color = random.choice(self.dress_colors)
                prompt_parts.append(f"in {color}")
            
            # Optionally add material
            if include_material and random.random() < 0.6:  # 60% chance for material
                material = random.choice(self.dress_materials)
                prompt_parts.append(f"{material} fabric")
            
            # Optionally add effects
            if include_effects and random.random() < 0.3:  # 30% chance for effects
                effect = random.choice(self.dress_effects)
                prompt_parts.append(effect)
            
            # Combine with face and body preservation instruction
            full_prompt = " ".join(prompt_parts) + ", preserve original face and body proportions exactly"
            
            # Log the generation
            generation_info = {
                "category": category,
                "base_dress": base_dress,
                "include_color": include_color,
                "include_material": include_material,
                "include_effects": include_effects,
                "final_prompt": full_prompt
            }
            logger.info(f"👗 Generated dress: {generation_info}")
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating random dress: {e}")
            # Fallback to simple dress
            return "change outfit to elegant black dress, preserve original face and body proportions exactly"
    
    def get_dress_by_category(self, category_name: str, include_color: bool = True, include_material: bool = True) -> str:
        """
        Get a random dress from a specific category.
        
        Args:
            category_name: Name of the category
            include_color: Whether to include random dress color
            include_material: Whether to include fabric specification
            
        Returns:
            A dress prompt from the specified category
        """
        try:
            if category_name not in self.all_categories:
                logger.warning(f"Unknown dress category: {category_name}")
                return self.get_random_dress(include_color, include_material)
            
            dresses = self.all_categories[category_name]
            base_dress = random.choice(dresses)
            
            prompt_parts = [f"change outfit to {base_dress}"]
            
            if include_color and random.random() < 0.7:  # 70% chance for specific categories
                color = random.choice(self.dress_colors)
                prompt_parts.append(f"in {color}")
            
            if include_material and random.random() < 0.5:  # 50% chance for material
                material = random.choice(self.dress_materials)
                prompt_parts.append(f"{material} fabric")
            
            full_prompt = " ".join(prompt_parts) + ", preserve original face and body proportions exactly"
            
            logger.info(f"👗 Generated {category_name} dress: {full_prompt}")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error generating dress for category {category_name}: {e}")
            return self.get_random_dress(include_color, include_material)
    
    def get_color_only_change(self) -> str:
        """Get a prompt that only changes dress color."""
        try:
            color = random.choice(self.dress_colors)
            material = random.choice(self.dress_materials)
            prompt = f"change dress color to {color} {material}, keep exact same dress style and preserve original face and body"
            
            logger.info(f"👗 Generated color-only change: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating dress color change: {e}")
            return "change dress color to navy blue, keep exact same dress style and preserve original face and body"
    
    def get_casual_outfit(self) -> str:
        """Get a casual outfit change."""
        casual_outfits = [
            "casual jeans and t-shirt",
            "comfortable sweater and leggings",
            "denim jacket and skirt",
            "casual blazer and pants",
            "oversized hoodie and shorts",
            "cardigan and midi skirt",
            "casual button-up and jeans",
            "knit dress and sneakers style"
        ]
        
        try:
            outfit = random.choice(casual_outfits)
            color = random.choice(self.dress_colors)
            prompt = f"change outfit to {outfit} in {color}, preserve original face and body proportions exactly"
            
            logger.info(f"👗 Generated casual outfit: {prompt}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating casual outfit: {e}")
            return "change outfit to casual jeans and t-shirt, preserve original face and body proportions exactly"
    
    def get_available_categories(self) -> List[str]:
        """Get list of available dress categories."""
        return list(self.all_categories.keys())
    
    def get_category_info(self) -> Dict[str, int]:
        """Get information about available categories and their counts."""
        return {category: len(dresses) for category, dresses in self.all_categories.items()}


# Global instance
dress_generator = DressGenerator() 