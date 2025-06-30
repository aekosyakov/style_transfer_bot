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
        # 80s Power Pop - Neon brights, puff sleeves & big shoulders
        self.eighties_power_pop = [
            "Power Shoulder Dress",
            "Neon Mini Dress",
            "Puff Sleeve Midi",
            "Bold Shoulder Dress",
            "Electric Blue Dress",
            "Dynasty Dress",
            "Material Girl Dress",
            "Miami Vice Dress",
            "Geometric Print Dress",
            "Bright Blazer Dress"
        ]
        
        # 90s Revival - Slip dresses, spaghetti straps & bias cuts
        self.nineties_revival = [
            "Slip Dress",
            "Spaghetti Strap Dress",
            "Bias Cut Midi",
            "Minimalist Dress",
            "Kate Moss Dress",
            "Grunge Dress",
            "Simple Tank Dress",
            "Ribbed Midi",
            "Basic Slip",
            "Downtown Dress"
        ]
        
        # Old Money Style - Logo-less silks & cashmeres in cream, navy, taupe
        self.old_money_style = [
            "Silk Shift Dress",
            "Cashmere Dress",
            "Navy Sheath",
            "Cream Midi",
            "Taupe Dress",
            "Preppy Dress",
            "Tennis Club Dress",
            "Country Club Dress",
            "Polo Dress",
            "Yacht Club Dress"
        ]
        
        # Disco Glam - Sequins, lamé, mirror-ball sparkle
        self.disco_glam = [
            "Sequin Dress",
            "Lamé Dress",
            "Mirror Ball Dress",
            "Sparkle Dress",
            "Disco Mini",
            "Metallic Dress",
            "Studio 54 Dress",
            "Glitter Dress",
            "Shimmery Dress",
            "Dance Floor Dress"
        ]
        
        # Y2K Futurist - Iridescent mesh, vinyl & asymmetric hems
        self.y2k_futurist = [
            "Iridescent Dress",
            "Mesh Dress",
            "Vinyl Dress",
            "Asymmetric Dress",
            "Cyber Dress",
            "Holographic Dress",
            "Tech Dress",
            "Future Dress",
            "Matrix Dress",
            "Space Age Dress"
        ]
        
        # Hollywood Glamour - Satin columns, sweetheart necks & opera gloves
        self.hollywood_glamour = [
            "Satin Column Dress",
            "Sweetheart Dress",
            "Red Carpet Dress",
            "Opera Glove Dress",
            "Old Hollywood Dress",
            "Marilyn Dress",
            "Grace Kelly Dress",
            "Movie Star Dress",
            "Glamour Dress",
            "Classic Gown"
        ]
        
        # Urban Streetstyle - Oversized tee-dresses, cargo pockets, sporty trims
        self.urban_streetstyle = [
            "Oversized Tee Dress",
            "Cargo Pocket Dress",
            "Sporty Dress",
            "Street Dress",
            "Urban Dress",
            "Hoodie Dress",
            "Athletic Dress",
            "Utility Dress",
            "Off-Duty Dress",
            "City Girl Dress"
        ]
        
        # Gen-Z Viral Mix - Cut-outs, corset-front minis, cargo maxis & bold graphic prints
        self.genz_viral_mix = [
            "Cut-Out Dress",
            "Corset Front Mini",
            "Cargo Maxi Dress",
            "Graphic Print Dress",
            "TikTok Dress",
            "E-Girl Dress",
            "Viral Trend Dress",
            "Social Media Dress",
            "Gen Z Dress",
            "Trending Dress"
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
            "eighties_power_pop": self.eighties_power_pop,
            "nineties_revival": self.nineties_revival,
            "old_money_style": self.old_money_style,
            "disco_glam": self.disco_glam,
            "y2k_futurist": self.y2k_futurist,
            "hollywood_glamour": self.hollywood_glamour,
            "urban_streetstyle": self.urban_streetstyle,
            "genz_viral_mix": self.genz_viral_mix
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
    
    def generate_random_dress_prompt(self, include_color: bool = True, include_material: bool = True, include_effects: bool = False) -> str:
        """Backward compatibility method for prompt variation system."""
        return self.get_random_dress(include_color, include_material, include_effects)


# Global instance  
dress_generator = DressGenerator() 