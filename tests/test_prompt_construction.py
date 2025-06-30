#!/usr/bin/env python3
"""
Comprehensive prompt construction analysis for Style Transfer Bot.
This script shows exactly how prompts are built using REAL generators from the codebase.
"""

import os
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up minimal environment
os.environ.setdefault('STYLE_TRANSFER_BOT_TOKEN', 'test_token')
os.environ.setdefault('REPLICATE_API_TOKEN', 'test_token')

# Import REAL generators from the codebase
from src.config import config
from src.prompt_variations import PromptVariationGenerator
from src.dresses import dress_generator
from src.mens_outfits import mens_outfit_generator
from src.hairstyles import hairstyle_generator
from src.mens_hairstyles import mens_hairstyle_generator
from src.womens_hairstyles import womens_hairstyle_generator

import logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise


def show_dress_prompt_construction():
    """Show exactly how women's dress prompts are constructed."""
    
    print("🔍 WOMEN'S DRESS PROMPT CONSTRUCTION (REAL GENERATOR)")
    print("=" * 70)
    
    # Show the REAL components from dress_generator
    print("\n📦 Available dress categories (from REAL generator):")
    for category in dress_generator.get_available_categories():
        count = len(dress_generator.all_categories[category])
        sample_dresses = dress_generator.all_categories[category][:2]
        print(f"   - {category}: {count} dresses (e.g., {sample_dresses})")
        
    print(f"\n🎨 Available colors ({len(dress_generator.dress_colors)} total):")
    print(f"   {dress_generator.dress_colors}")
    
    print(f"\n🧵 Available materials ({len(dress_generator.dress_materials)} total):")
    print(f"   {dress_generator.dress_materials}")
    
    # Show actual construction using REAL generator
    print("\n🔨 REAL CONSTRUCTION EXAMPLES:")
    
    # Show 5 different examples to demonstrate variety
    for i in range(5):
        prompt = dress_generator.get_random_dress(include_color=True, include_material=True, include_effects=False)
        print(f"   Example {i+1}: {prompt}")


def show_mens_outfit_construction():
    """Show exactly how men's outfit prompts are constructed."""
    
    print("\n\n👔 MEN'S OUTFIT PROMPT CONSTRUCTION (REAL GENERATOR)")
    print("=" * 70)
    
    # Show the REAL components from mens_outfit_generator
    print("\n📦 Available outfit categories (from REAL generator):")
    for category in mens_outfit_generator.get_available_categories():
        count = len(mens_outfit_generator.all_categories[category])
        sample_outfits = mens_outfit_generator.all_categories[category][:2]
        print(f"   - {category}: {count} outfits (e.g., {sample_outfits})")
        
    print(f"\n🎨 Available colors ({len(mens_outfit_generator.outfit_colors)} total):")
    print(f"   {mens_outfit_generator.outfit_colors}")
    
    print(f"\n🧵 Available materials ({len(mens_outfit_generator.outfit_materials)} total):")
    print(f"   {mens_outfit_generator.outfit_materials}")
    
    # Show actual construction using REAL generator
    print("\n🔨 REAL CONSTRUCTION EXAMPLES:")
    
    # Show 5 different examples to demonstrate variety
    for i in range(5):
        prompt = mens_outfit_generator.get_random_outfit(include_color=True, include_material=True, include_effects=False)
        print(f"   Example {i+1}: {prompt}")


def show_hairstyle_construction():
    """Show exactly how hairstyle prompts are constructed."""
    
    print("\n\n💇‍♀️ HAIRSTYLE PROMPT CONSTRUCTION (REAL GENERATORS)")
    print("=" * 70)
    
    # Women's hairstyles
    print("\n👩 WOMEN'S HAIRSTYLES:")
    print(f"📦 Available categories ({len(womens_hairstyle_generator.get_available_categories())} total):")
    for category in womens_hairstyle_generator.get_available_categories():
        count = len(womens_hairstyle_generator.all_categories[category])
        sample_styles = womens_hairstyle_generator.all_categories[category][:2]
        print(f"   - {category}: {count} hairstyles (e.g., {sample_styles})")
        
    print(f"\n🎨 Available hair colors ({len(womens_hairstyle_generator.hair_colors)} total):")
    print(f"   {womens_hairstyle_generator.hair_colors}")
    
    print("\n🔨 REAL CONSTRUCTION EXAMPLES (Women's):")
    for i in range(3):
        prompt = womens_hairstyle_generator.get_random_hairstyle(include_color=True, include_effects=False)
        print(f"   Example {i+1}: {prompt}")
        
    # Men's hairstyles
    print("\n👨 MEN'S HAIRSTYLES:")
    print(f"📦 Available categories ({len(mens_hairstyle_generator.get_available_categories())} total):")
    for category in mens_hairstyle_generator.get_available_categories():
        count = len(mens_hairstyle_generator.all_categories[category])
        sample_styles = mens_hairstyle_generator.all_categories[category][:2]
        print(f"   - {category}: {count} hairstyles (e.g., {sample_styles})")
        
    print(f"\n🎨 Available hair colors ({len(mens_hairstyle_generator.hair_colors)} total):")
    print(f"   {mens_hairstyle_generator.hair_colors}")
    
    print("\n🔨 REAL CONSTRUCTION EXAMPLES (Men's):")
    for i in range(3):
        prompt = mens_hairstyle_generator.get_random_hairstyle(include_color=True, include_effects=False)
        print(f"   Example {i+1}: {prompt}")


def show_config_to_prompt_mapping():
    """Show how config categories map to actual prompts using REAL system."""
    
    print("\n\n🗺️ CONFIG TO PROMPT MAPPING (REAL SYSTEM)")
    print("=" * 70)
    
    prompt_variations = PromptVariationGenerator()
    
    # Women's dress mappings
    print("\n👗 WOMEN'S DRESS CONFIG MAPPINGS:")
    women_options = config.get_category_options("new_look_women")
    for option in women_options:
        label_key = option.get('label_key')
        config_prompt = option.get('prompt')
        
        print(f"\n📋 {label_key} -> {config_prompt}")
        
        if config_prompt and "DRESS" in config_prompt:
            # Show what REAL variation system produces
            actual_prompt = prompt_variations._generate_dress_variation(label_key, config_prompt, preserve_gender='women')
            print(f"🎯 Becomes: {actual_prompt}")
            
    # Men's outfit mappings
    print("\n👔 MEN'S OUTFIT CONFIG MAPPINGS:")
    men_options = config.get_category_options("new_look_men")
    for option in men_options:
        label_key = option.get('label_key')
        config_prompt = option.get('prompt')
        
        print(f"\n📋 {label_key} -> {config_prompt}")
        
        if config_prompt and "MENS_OUTFIT" in config_prompt:
            # Show what REAL variation system produces
            actual_prompt = prompt_variations._generate_dress_variation(label_key, config_prompt, preserve_gender='men')
            print(f"🎯 Becomes: {actual_prompt}")


def show_gender_preservation():
    """Show how gender preservation works in REAL system."""
    
    print("\n\n🚻 GENDER PRESERVATION (REAL SYSTEM)")
    print("=" * 70)
    
    prompt_variations = PromptVariationGenerator()
    
    print("\n👨 MEN'S OUTFIT PRESERVATION:")
    mens_prompt = "RANDOM_MENS_OUTFIT"
    print(f"Base prompt: {mens_prompt}")
    print("With preserve_gender='men':")
    for i in range(3):
        preserved = prompt_variations._generate_dress_variation(
            "mens.test", mens_prompt, preserve_gender='men'
        )
        print(f"   Preserved {i+1}: {preserved}")
        
    print("\n👩 WOMEN'S DRESS PRESERVATION:")
    womens_prompt = "RANDOM_DRESS"
    print(f"Base prompt: {womens_prompt}")
    print("With preserve_gender='women':")
    for i in range(3):
        preserved = prompt_variations._generate_dress_variation(
            "dress.test", womens_prompt, preserve_gender='women'
        )
        print(f"   Preserved {i+1}: {preserved}")


def show_comprehensive_statistics():
    """Show comprehensive statistics of all possible prompts."""
    
    print("\n\n📊 COMPREHENSIVE PROMPT STATISTICS (REAL DATA)")
    print("=" * 70)
    
    # Calculate real statistics
    dress_categories = len(dress_generator.get_available_categories())
    dress_total = sum(dress_generator.get_category_info().values())
    dress_colors = len(dress_generator.dress_colors)
    dress_materials = len(dress_generator.dress_materials)
    dress_effects = len(dress_generator.dress_effects)

    mens_categories = len(mens_outfit_generator.get_available_categories())
    mens_total = sum(mens_outfit_generator.get_category_info().values())
    mens_colors = len(mens_outfit_generator.outfit_colors)
    mens_materials = len(mens_outfit_generator.outfit_materials)
    mens_effects = len(mens_outfit_generator.outfit_effects)

    womens_hair_categories = len(womens_hairstyle_generator.get_available_categories())
    womens_hair_total = sum(womens_hairstyle_generator.get_category_info().values())
    womens_hair_colors = len(womens_hairstyle_generator.hair_colors)
    womens_hair_effects = len(womens_hairstyle_generator.hair_effects)

    mens_hair_categories = len(mens_hairstyle_generator.get_available_categories())
    mens_hair_total = sum(mens_hairstyle_generator.get_category_info().values())
    mens_hair_colors = len(mens_hairstyle_generator.hair_colors)
    mens_hair_effects = len(mens_hairstyle_generator.hair_effects)

    print(f'\n👗 WOMEN\'S DRESSES:')
    print(f'   Categories: {dress_categories}')
    print(f'   Base dresses: {dress_total}')
    print(f'   Colors: {dress_colors}')
    print(f'   Materials: {dress_materials}')
    print(f'   Effects: {dress_effects}')
    print(f'   Possible combinations: ~{dress_total * dress_colors * dress_materials:,}')

    print(f'\n👔 MEN\'S OUTFITS:')
    print(f'   Categories: {mens_categories}')
    print(f'   Base outfits: {mens_total}')
    print(f'   Colors: {mens_colors}')
    print(f'   Materials: {mens_materials}')
    print(f'   Effects: {mens_effects}')
    print(f'   Possible combinations: ~{mens_total * mens_colors * mens_materials:,}')

    print(f'\n💇‍♀️ WOMEN\'S HAIRSTYLES:')
    print(f'   Categories: {womens_hair_categories}')
    print(f'   Base hairstyles: {womens_hair_total}')
    print(f'   Colors: {womens_hair_colors}')
    print(f'   Effects: {womens_hair_effects}')
    print(f'   Possible combinations: ~{womens_hair_total * womens_hair_colors:,}')

    print(f'\n💈 MEN\'S HAIRSTYLES:')
    print(f'   Categories: {mens_hair_categories}')
    print(f'   Base hairstyles: {mens_hair_total}')
    print(f'   Colors: {mens_hair_colors}')
    print(f'   Effects: {mens_hair_effects}')
    print(f'   Possible combinations: ~{mens_hair_total * mens_hair_colors:,}')

    # Calculate totals
    total_dress_combinations = dress_total * dress_colors * dress_materials
    total_mens_combinations = mens_total * mens_colors * mens_materials
    total_womens_hair_combinations = womens_hair_total * womens_hair_colors
    total_mens_hair_combinations = mens_hair_total * mens_hair_colors

    grand_total = total_dress_combinations + total_mens_combinations + total_womens_hair_combinations + total_mens_hair_combinations

    print(f'\n🎯 GRAND TOTALS:')
    print(f'   Total dress combinations: ~{total_dress_combinations:,}')
    print(f'   Total men\'s outfit combinations: ~{total_mens_combinations:,}')
    print(f'   Total women\'s hair combinations: ~{total_womens_hair_combinations:,}')
    print(f'   Total men\'s hair combinations: ~{total_mens_hair_combinations:,}')
    print(f'   TOTAL POSSIBLE PROMPTS: ~{grand_total:,}')

    print(f'\n🔍 PROMPT PATTERNS:')
    print(f'   Dress pattern: "change outfit to [DRESS] in [COLOR] [MATERIAL] fabric, preserve original face and body proportions exactly"')
    print(f'   Men\'s pattern: "change outfit to [OUTFIT] in [COLOR] [MATERIAL] fabric, preserve original face and body proportions exactly"')
    print(f'   Hair pattern: "change hairstyle to [HAIRSTYLE] with [COLOR] hair color, preserve original face and facial features exactly"')


def main():
    """Main function."""
    print("🚀 STYLE TRANSFER BOT PROMPT CONSTRUCTION ANALYSIS")
    print("🔬 Using REAL generators from the codebase")
    print(f"📁 Working directory: {Path.cwd()}")
    
    try:
        show_dress_prompt_construction()
        show_mens_outfit_construction()
        show_hairstyle_construction()
        show_config_to_prompt_mapping()
        show_gender_preservation()
        show_comprehensive_statistics()
        
        print("\n\n✅ ANALYSIS COMPLETE!")
        print("\n💡 Key insights from REAL generators:")
        print("   - All generators use real data from your codebase")
        print("   - Outfit prompts always preserve 'original face and body proportions exactly'")
        print("   - Hairstyle prompts preserve 'original face and facial features exactly'")
        print("   - Random prompts generate true variations using probability")
        print("   - Gender preservation prevents cross-gender switching")
        print("   - Config maps simple keys to complex generation systems")
        print("   - Total possible unique prompts: Over 41,000!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
