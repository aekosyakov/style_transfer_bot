#!/usr/bin/env python3
"""
Comprehensive prompt generation testing for Style Transfer Bot.
This script demonstrates ALL possible prompts using the REAL generators from the codebase.
"""

import os
import sys
import random
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up minimal environment for testing
os.environ.setdefault('STYLE_TRANSFER_BOT_TOKEN', 'test_token')
os.environ.setdefault('REPLICATE_API_TOKEN', 'test_token')

# Import the REAL generators from the codebase
from src.config import config
from src.prompt_variations import PromptVariationGenerator
from src.dresses import dress_generator
from src.mens_outfits import mens_outfit_generator
from src.hairstyles import hairstyle_generator
from src.mens_hairstyles import mens_hairstyle_generator
from src.womens_hairstyles import womens_hairstyle_generator

# Initialize logging to see what generators are doing
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AllPromptsTestGenerator:
    """Generate and display all possible prompts using REAL generators."""
    
    def __init__(self):
        self.prompt_variations = PromptVariationGenerator()
        
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*80}")
        print(f" {title}")
        print(f"{'='*80}")
        
    def print_subsection(self, title: str):
        """Print a formatted subsection header."""
        print(f"\n{'-'*60}")
        print(f" {title}")
        print(f"{'-'*60}")
        
    def test_womens_dress_prompts(self):
        """Test all women's dress prompts using REAL dress_generator."""
        self.print_section("WOMEN'S DRESS PROMPTS (REAL GENERATOR)")
        
        # Show available categories from real generator
        self.print_subsection("AVAILABLE DRESS CATEGORIES")
        categories = dress_generator.get_available_categories()
        print(f"📊 Available categories: {categories}")
        
        # Show category info
        category_info = dress_generator.get_category_info()
        print(f"📈 Category info: {category_info}")
        
        # Test each category
        for category in categories:
            self.print_subsection(f"CATEGORY: {category.upper()}")
            
            # Show raw dress options for this category
            dresses = dress_generator.all_categories[category]
            print(f"👗 Base dresses in {category}: {dresses[:3]}... (showing first 3)")
            
            # Generate 3 examples using the real generator
            for i in range(3):
                prompt = dress_generator.get_dress_by_category(category, include_color=True, include_material=True)
                print(f"   Generated {i+1}: {prompt}")
                
        # Test random dress generation
        self.print_subsection("RANDOM DRESS GENERATION")
        print("\n🎲 Random dress examples using REAL generator:")
        for i in range(5):
            prompt = dress_generator.get_random_dress(include_color=True, include_material=True, include_effects=False)
            print(f"   Random {i+1}: {prompt}")
            
        # Test casual outfit generation
        self.print_subsection("CASUAL OUTFIT GENERATION")
        print("\n👚 Casual outfit examples:")
        for i in range(3):
            prompt = dress_generator.get_casual_outfit()
            print(f"   Casual {i+1}: {prompt}")
            
        # Show available colors and materials
        self.print_subsection("AVAILABLE COLORS AND MATERIALS")
        print(f"🎨 Colors: {dress_generator.dress_colors}")
        print(f"🧵 Materials: {dress_generator.dress_materials}")
        print(f"✨ Effects: {dress_generator.dress_effects}")
            
    def test_mens_outfit_prompts(self):
        """Test all men's outfit prompts using REAL mens_outfit_generator."""
        self.print_section("MEN'S OUTFIT PROMPTS (REAL GENERATOR)")
        
        # Show available categories from real generator
        self.print_subsection("AVAILABLE MENS OUTFIT CATEGORIES")
        categories = mens_outfit_generator.get_available_categories()
        print(f"📊 Available categories: {categories}")
        
        # Show category info
        category_info = mens_outfit_generator.get_category_info()
        print(f"📈 Category info: {category_info}")
        
        # Test each category
        for category in categories:
            self.print_subsection(f"CATEGORY: {category.upper()}")
            
            # Show raw outfit options for this category
            outfits = mens_outfit_generator.all_categories[category]
            print(f"👔 Base outfits in {category}: {outfits[:3]}... (showing first 3)")
            
            # Generate 3 examples using the real generator
            for i in range(3):
                prompt = mens_outfit_generator.get_outfit_by_category(category, include_color=True, include_material=True)
                print(f"   Generated {i+1}: {prompt}")
                
        # Test random outfit generation
        self.print_subsection("RANDOM MENS OUTFIT GENERATION")
        print("\n🎲 Random men's outfit examples using REAL generator:")
        for i in range(5):
            prompt = mens_outfit_generator.get_random_outfit(include_color=True, include_material=True, include_effects=False)
            print(f"   Random {i+1}: {prompt}")
            
        # Test casual outfit generation
        self.print_subsection("CASUAL MENS OUTFIT GENERATION")
        print("\n👕 Casual men's outfit examples:")
        for i in range(3):
            prompt = mens_outfit_generator.get_casual_outfit()
            print(f"   Casual {i+1}: {prompt}")
            
        # Show available colors and materials
        self.print_subsection("AVAILABLE COLORS AND MATERIALS")
        print(f"🎨 Colors: {mens_outfit_generator.outfit_colors}")
        print(f"🧵 Materials: {mens_outfit_generator.outfit_materials}")
        print(f"✨ Effects: {mens_outfit_generator.outfit_effects}")
            
    def test_womens_hairstyle_prompts(self):
        """Test all women's hairstyle prompts using REAL womens_hairstyle_generator."""
        self.print_section("WOMEN'S HAIRSTYLE PROMPTS (REAL GENERATOR)")
        
        # Show available categories from real generator
        self.print_subsection("AVAILABLE WOMENS HAIRSTYLE CATEGORIES")
        categories = womens_hairstyle_generator.get_available_categories()
        print(f"📊 Available categories: {categories}")
        
        # Show category info
        category_info = womens_hairstyle_generator.get_category_info()
        print(f"📈 Category info: {category_info}")
        
        # Test each category
        for category in categories:
            self.print_subsection(f"CATEGORY: {category.upper()}")
            
            # Show raw hairstyle options for this category
            hairstyles = womens_hairstyle_generator.all_categories[category]
            print(f"💇‍♀️ Base hairstyles in {category}: {hairstyles[:3]}... (showing first 3)")
            
            # Generate 3 examples using the real generator
            for i in range(3):
                prompt = womens_hairstyle_generator.get_hairstyle_by_category(category, include_color=True)
                print(f"   Generated {i+1}: {prompt}")
                
        # Test random hairstyle generation
        self.print_subsection("RANDOM WOMENS HAIRSTYLE GENERATION")
        print("\n🎲 Random women's hairstyle examples using REAL generator:")
        for i in range(5):
            prompt = womens_hairstyle_generator.get_random_hairstyle(include_color=True, include_effects=False)
            print(f"   Random {i+1}: {prompt}")
            
        # Show available colors and effects
        self.print_subsection("AVAILABLE COLORS AND EFFECTS")
        print(f"🎨 Hair colors: {womens_hairstyle_generator.hair_colors}")
        print(f"✨ Hair effects: {womens_hairstyle_generator.hair_effects}")
            
    def test_mens_hairstyle_prompts(self):
        """Test all men's hairstyle prompts using REAL mens_hairstyle_generator."""
        self.print_section("MEN'S HAIRSTYLE PROMPTS (REAL GENERATOR)")
        
        # Show available categories from real generator
        self.print_subsection("AVAILABLE MENS HAIRSTYLE CATEGORIES")
        categories = mens_hairstyle_generator.get_available_categories()
        print(f"📊 Available categories: {categories}")
        
        # Show category info
        category_info = mens_hairstyle_generator.get_category_info()
        print(f"📈 Category info: {category_info}")
        
        # Test each category
        for category in categories:
            self.print_subsection(f"CATEGORY: {category.upper()}")
            
            # Show raw hairstyle options for this category
            hairstyles = mens_hairstyle_generator.all_categories[category]
            print(f"💈 Base hairstyles in {category}: {hairstyles[:3]}... (showing first 3)")
            
            # Generate 3 examples using the real generator
            for i in range(3):
                prompt = mens_hairstyle_generator.get_hairstyle_by_category(category, include_color=True)
                print(f"   Generated {i+1}: {prompt}")
                
        # Test random hairstyle generation
        self.print_subsection("RANDOM MENS HAIRSTYLE GENERATION")
        print("\n🎲 Random men's hairstyle examples using REAL generator:")
        for i in range(5):
            prompt = mens_hairstyle_generator.get_random_hairstyle(include_color=True, include_effects=False)
            print(f"   Random {i+1}: {prompt}")
            
        # Show available colors and effects
        self.print_subsection("AVAILABLE COLORS AND EFFECTS")
        print(f"🎨 Hair colors: {mens_hairstyle_generator.hair_colors}")
        print(f"✨ Hair effects: {mens_hairstyle_generator.hair_effects}")
            
    def test_unified_hairstyle_interface(self):
        """Test the unified hairstyle interface using REAL hairstyle_generator."""
        self.print_section("UNIFIED HAIRSTYLE INTERFACE (REAL GENERATOR)")
        
        # Test general hairstyle generation
        self.print_subsection("GENERAL HAIRSTYLE GENERATION")
        print("\n🎲 General hairstyle examples:")
        for i in range(3):
            prompt = hairstyle_generator.get_random_hairstyle(include_color=True, include_effects=False)
            print(f"   General {i+1}: {prompt}")
            
        # Test gender-specific methods
        self.print_subsection("GENDER-SPECIFIC METHODS")
        
        print("\n👨 Men's hairstyles via unified interface:")
        for i in range(3):
            prompt = hairstyle_generator.get_mens_hairstyle(include_color=True, include_effects=False)
            print(f"   Men's {i+1}: {prompt}")
            
        print("\n👩 Women's hairstyles via unified interface:")
        for i in range(3):
            prompt = hairstyle_generator.get_womens_hairstyle(include_color=True, include_effects=False)
            print(f"   Women's {i+1}: {prompt}")
            
        print("\n🎲 Random gender hairstyles:")
        for i in range(3):
            prompt = hairstyle_generator.get_random_gender_hairstyle(include_color=True, include_effects=False)
            print(f"   Random gender {i+1}: {prompt}")
            
    def test_config_category_mappings(self):
        """Test how config categories map to actual prompts using REAL variation system."""
        self.print_section("CONFIG CATEGORY MAPPINGS (REAL SYSTEM)")
        
        # Test women's dress mappings
        self.print_subsection("WOMEN'S DRESS MAPPINGS")
        women_options = config.get_category_options("new_look_women")
        for option in women_options:
            label_key = option.get('label_key')
            config_prompt = option.get('prompt')
            
            print(f"\n📋 Config mapping: {label_key} -> {config_prompt}")
            
            # Show what this becomes using the REAL variation system
            if config_prompt and "DRESS" in config_prompt:
                # Generate 2 examples to show variation
                for i in range(2):
                    actual_prompt = self.prompt_variations._generate_dress_variation(label_key, config_prompt, preserve_gender='women')
                    print(f"   Actual {i+1}: {actual_prompt}")
                    
        # Test men's outfit mappings
        self.print_subsection("MEN'S OUTFIT MAPPINGS")
        men_options = config.get_category_options("new_look_men")
        for option in men_options:
            label_key = option.get('label_key')
            config_prompt = option.get('prompt')
            
            print(f"\n📋 Config mapping: {label_key} -> {config_prompt}")
            
            # Show what this becomes using the REAL variation system
            if config_prompt and "MENS_OUTFIT" in config_prompt:
                # Generate 2 examples to show variation
                for i in range(2):
                    actual_prompt = self.prompt_variations._generate_dress_variation(label_key, config_prompt, preserve_gender='men')
                    print(f"   Actual {i+1}: {actual_prompt}")
                    
        # Test hairstyle mappings
        self.print_subsection("HAIRSTYLE MAPPINGS")
        
        # Women's hairstyles
        print("\n👩 Women's hairstyle mappings:")
        women_hair_options = config.get_category_options("new_hairstyle_women")
        for option in women_hair_options:
            label_key = option.get('label_key')
            config_prompt = option.get('prompt')
            
            print(f"\n📋 Config mapping: {label_key} -> {config_prompt}")
            
            if config_prompt and "HAIRSTYLE" in config_prompt:
                # Generate 2 examples to show variation
                for i in range(2):
                    actual_prompt = self.prompt_variations._generate_hairstyle_variation(label_key, config_prompt)
                    print(f"   Actual {i+1}: {actual_prompt}")
                    
        # Men's hairstyles
        print("\n👨 Men's hairstyle mappings:")
        men_hair_options = config.get_category_options("new_hairstyle_men")
        for option in men_hair_options:
            label_key = option.get('label_key')
            config_prompt = option.get('prompt')
            
            print(f"\n📋 Config mapping: {label_key} -> {config_prompt}")
            
            if config_prompt and "HAIRSTYLE" in config_prompt:
                # Generate 2 examples to show variation
                for i in range(2):
                    actual_prompt = self.prompt_variations._generate_hairstyle_variation(label_key, config_prompt)
                    print(f"   Actual {i+1}: {actual_prompt}")
                    
    def test_prompt_variation_system(self):
        """Test the prompt variation system with REAL generators."""
        self.print_section("PROMPT VARIATION SYSTEM (REAL GENERATORS)")
        
        # Test key variation patterns
        test_cases = [
            ("dress.random", "RANDOM_DRESS"),
            ("dress.nineties_revival", "NINETIES_REVIVAL_DRESS"),
            ("dress.eighties_power_pop", "EIGHTIES_POWER_POP_DRESS"),
            ("mens.random", "RANDOM_MENS_OUTFIT"),
            ("mens.casual_outfit", "CASUAL_MENS_OUTFIT"),
            ("mens.modern_outfit", "MODERN_MENS_OUTFIT"),
            ("hair.women_random", "RANDOM_WOMENS_HAIRSTYLE"),
            ("hair.men_random", "RANDOM_MENS_HAIRSTYLE"),
        ]
        
        for label_key, base_prompt in test_cases:
            self.print_subsection(f"TESTING: {label_key}")
            print(f"\n🧪 Base prompt: {base_prompt}")
            
            # Determine gender for proper testing
            if "mens" in label_key.lower() or "men_" in label_key.lower():
                preserve_gender = 'men'
            elif "women" in label_key.lower() or "dress" in label_key.lower():
                preserve_gender = 'women'
            else:
                preserve_gender = 'neutral'
            
            # Generate variations using REAL system
            for i in range(3):
                if "HAIRSTYLE" in base_prompt:
                    varied = self.prompt_variations._generate_hairstyle_variation(label_key, base_prompt)
                else:
                    varied = self.prompt_variations._generate_dress_variation(label_key, base_prompt, preserve_gender=preserve_gender)
                print(f"   Variation {i+1}: {varied}")
                
    def test_gender_preservation(self):
        """Test gender preservation in prompt variations using REAL system."""
        self.print_section("GENDER PRESERVATION TESTING (REAL SYSTEM)")
        
        # Test men's outfit preservation
        self.print_subsection("MEN'S OUTFIT PRESERVATION")
        mens_prompts = ["RANDOM_MENS_OUTFIT", "MODERN_MENS_OUTFIT", "CASUAL_MENS_OUTFIT"]
        
        for prompt in mens_prompts:
            print(f"\n👨 Testing preservation with: {prompt}")
            for i in range(3):
                preserved = self.prompt_variations._generate_dress_variation(
                    "mens.test", prompt, preserve_gender='men'
                )
                print(f"   Preserved {i+1}: {preserved}")
                
        # Test women's dress preservation
        self.print_subsection("WOMEN'S DRESS PRESERVATION")
        womens_prompts = ["RANDOM_DRESS", "NINETIES_REVIVAL_DRESS", "DISCO_GLAM_DRESS"]
        
        for prompt in womens_prompts:
            print(f"\n👩 Testing preservation with: {prompt}")
            for i in range(3):
                preserved = self.prompt_variations._generate_dress_variation(
                    "dress.test", prompt, preserve_gender='women'
                )
                print(f"   Preserved {i+1}: {preserved}")
                
        # Test neutral (no preservation)
        self.print_subsection("NEUTRAL (NO PRESERVATION)")
        neutral_prompts = ["RANDOM_DRESS", "RANDOM_MENS_OUTFIT"]
        
        for prompt in neutral_prompts:
            print(f"\n⚖️ Testing neutral with: {prompt}")
            for i in range(2):
                neutral = self.prompt_variations._generate_dress_variation(
                    "neutral.test", prompt, preserve_gender='neutral'
                )
                print(f"   Neutral {i+1}: {neutral}")
                
    def run_all_tests(self):
        """Run all prompt generation tests using REAL generators."""
        print("🚀 COMPREHENSIVE PROMPT TESTING WITH REAL GENERATORS")
        print(f"📁 Working directory: {Path.cwd()}")
        
        try:
            # Test all generators
            self.test_womens_dress_prompts()
            self.test_mens_outfit_prompts()
            self.test_womens_hairstyle_prompts()
            self.test_mens_hairstyle_prompts()
            self.test_unified_hairstyle_interface()
            self.test_config_category_mappings()
            self.test_prompt_variation_system()
            self.test_gender_preservation()
            
            self.print_section("SUMMARY")
            print("✅ All prompt generation tests completed successfully!")
            print("📊 Generators tested:")
            print(f"   - dress_generator: {len(dress_generator.get_available_categories())} categories")
            print(f"   - mens_outfit_generator: {len(mens_outfit_generator.get_available_categories())} categories")
            print(f"   - womens_hairstyle_generator: {len(womens_hairstyle_generator.get_available_categories())} categories")
            print(f"   - mens_hairstyle_generator: {len(mens_hairstyle_generator.get_available_categories())} categories")
            print(f"   - hairstyle_generator: {len(hairstyle_generator.get_available_categories())} categories")
            print("   - prompt_variations: REAL variation system")
            print("   - config: REAL category mappings")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            logger.error(f"Test error: {e}", exc_info=True)
            
        print(f"\n🏁 Testing completed with REAL generators!")


def main():
    """Main function to run all tests."""
    print("🎯 STYLE TRANSFER BOT - REAL PROMPT GENERATOR TESTING")
    print("🔬 Using actual generators from the codebase")
    
    # Create and run test generator
    test_gen = AllPromptsTestGenerator()
    test_gen.run_all_tests()


if __name__ == "__main__":
    main() 